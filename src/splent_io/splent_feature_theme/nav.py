"""Compose the public main navigation from installed features + runtime override.

SPL: the BASE menu is whatever content features registered via
``register_nav_item()`` — so it tracks the product's derivation (install a
feature, its entry appears; remove it, it disappears). The admin "Menus" editor
then stores an override in the settings store (key ``site_nav``, JSON) that
reorders / hides / relabels those entries and adds custom external links. This
module reconciles the two at render time and also feeds the editor.

Override JSON shape (a list, in menu order)::

    [
      {"type": "feature", "key": "projects", "visible": true},
      {"type": "feature", "key": "team", "label": "Our team", "visible": false},
      {"type": "custom", "label": "Old site", "href": "https://…"}
    ]

The footer gets its own, simpler row of links from the same editor, stored
under ``site_footer_nav`` (a JSON list of ``{label, href}`` in order). Custom
links only — no feature entries, so there is nothing to reconcile.
"""

import json

from splent_framework.nav.nav_registry import get_nav_items, resolve_children

# The Footer links section never stores more rows than this; a footer that
# needs more links than fit on two lines is a design problem, not a menu.
FOOTER_NAV_MAX = 20


def _load_setting_list(app, key):
    """Parsed JSON list from the settings store, or None if absent/invalid."""
    try:
        from splent_framework.services.service_locator import service_proxy

        raw = service_proxy("SettingsService").get(key, None)
    except Exception:
        raw = None
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except Exception:
        return None
    return data if isinstance(data, list) else None


def compose_nav(app, translate):
    """Final render-ready nav: list of ``{label, href}``.

    Precedence: (1) override drives order/visibility/labels and may add custom
    links — feature entries no longer installed are dropped, newly-installed
    ones are appended; (2) else the registered feature entries (by order);
    (3) else legacy ``app.config['SITE_NAV']``.
    """
    base = get_nav_items()
    by_key = {i["key"]: i for i in base}
    override = _load_setting_list(app, "site_nav")

    if override is not None:
        nav = []
        seen = set()
        for entry in override:
            if not isinstance(entry, dict):
                continue
            if entry.get("type") == "custom":
                label = (entry.get("label") or "").strip()
                href = _safe_href(
                    entry.get("href")
                )  # block javascript:/data: at render too
                if label and href and entry.get("visible", True):
                    nav.append({"label": translate(label), "href": href})
                continue
            key = entry.get("key")
            if key in seen:
                continue  # duplicate key in the override -> render once
            item = by_key.get(key)
            if item is None:
                continue  # feature removed from the product
            seen.add(key)
            if entry.get("visible", True):
                label = (entry.get("label") or "").strip() or item["label"]
                nav.append(_entry(item, translate(label)))
        for item in base:  # installed but not yet in the override -> append
            if item["key"] not in seen:
                nav.append(_entry(item, translate(item["label"])))
        return nav

    if base:
        return [_entry(i, translate(i["label"])) for i in base]

    return [
        {**item, "label": translate(item["label"])} if item.get("label") else item
        for item in app.config.get("SITE_NAV", [])
    ]


def _entry(item, label):
    """One render-ready nav entry. Sub-entries (a feature's ``children``,
    resolved now) make the theme draw a dropdown; the entry itself stays a
    link, so the menu works with the keyboard and without JavaScript."""
    entry = {"label": label, "href": item["href"]}
    children = resolve_children(item)
    if children:
        entry["children"] = children
    return entry


def editor_rows(app):
    """Rows for the admin Menus editor, in effective order.

    Each row: ``{type, key, label, href, default_label, visible, missing}``.
    ``label`` is the admin's override (empty = use the feature default).
    ``missing`` flags a feature that the override references but is no longer
    installed (so the admin can clean it up).
    """
    base = get_nav_items()
    by_key = {i["key"]: i for i in base}
    override = _load_setting_list(app, "site_nav")
    rows = []
    seen = set()

    if override is not None:
        for entry in override:
            if not isinstance(entry, dict):
                continue
            if entry.get("type") == "custom":
                rows.append(
                    {
                        "type": "custom",
                        "key": "",
                        "label": (entry.get("label") or "").strip(),
                        "href": (entry.get("href") or "").strip(),
                        "default_label": "",
                        "visible": bool(entry.get("visible", True)),
                        "missing": False,
                    }
                )
                continue
            key = entry.get("key")
            if key in seen:
                continue  # duplicate key in the override -> one row
            item = by_key.get(key)
            seen.add(key)
            rows.append(
                {
                    "type": "feature",
                    "key": key,
                    "label": (entry.get("label") or "").strip(),
                    "href": item["href"] if item else "",
                    "default_label": item["label"] if item else key,
                    "visible": bool(entry.get("visible", True)),
                    "missing": item is None,
                }
            )

    for item in base:  # feature entries not represented in the override yet
        if item["key"] not in seen:
            rows.append(
                {
                    "type": "feature",
                    "key": item["key"],
                    "label": "",
                    "href": item["href"],
                    "default_label": item["label"],
                    "visible": True,
                    "missing": False,
                }
            )
    return rows


def _safe_href(href):
    """Allow only safe link targets for custom links — block javascript:/data:."""
    href = (href or "").strip()
    low = href.lower()
    if low.startswith(("http://", "https://", "mailto:")) or href.startswith(
        ("/", "#")
    ):
        return href
    return ""


def parse_override(form):
    """Build the override list from the editor POST.

    Every row submits index-aligned parallel arrays so order is preserved and
    feature/custom rows interleave correctly:
    ``row_type[] row_key[] row_label[] row_href[] row_visible[]`` ("1"/"0").
    """
    types = form.getlist("row_type")
    keys = form.getlist("row_key")
    labels = form.getlist("row_label")
    hrefs = form.getlist("row_href")
    visibles = form.getlist("row_visible")

    def at(arr, i):
        return arr[i] if i < len(arr) else ""

    out = []
    for i, t in enumerate(types):
        label = at(labels, i).strip()
        if t == "custom":
            href = _safe_href(at(hrefs, i))
            if label and href:
                out.append(
                    {
                        "type": "custom",
                        "label": label,
                        "href": href,
                        "visible": at(visibles, i) == "1",
                    }
                )
        else:
            key = at(keys, i).strip()
            if not key:
                continue
            row = {"type": "feature", "key": key, "visible": at(visibles, i) == "1"}
            if label:
                row["label"] = label
            out.append(row)
    return out


def compose_footer_nav(app, translate):
    """Final render-ready footer links: list of ``{label, href}``, [] when unset.

    Read from the ``site_footer_nav`` setting written by the Menus editor.
    Custom links only, so there is no feature reconciliation — entries missing
    a label or carrying an unsafe href are skipped, and the list is capped at
    ``FOOTER_NAV_MAX`` however the stored JSON was produced.
    """
    data = _load_setting_list(app, "site_footer_nav")
    if not data:
        return []
    links = []
    for entry in data:
        if not isinstance(entry, dict):
            continue
        label = (entry.get("label") or "").strip()
        href = _safe_href(entry.get("href"))  # block javascript:/data: at render too
        if label and href:
            links.append({"label": translate(label), "href": href})
        if len(links) >= FOOTER_NAV_MAX:
            break
    return links


def footer_editor_rows(app):
    """Rows for the Footer links section of the Menus editor: ``{label, href}``.

    The stored entries as the admin typed them (stripped), in order — invalid
    rows are kept visible here so the admin can fix or remove them, while
    ``compose_footer_nav`` keeps them off the public page.
    """
    data = _load_setting_list(app, "site_footer_nav") or []
    rows = []
    for entry in data:
        if not isinstance(entry, dict):
            continue
        rows.append(
            {
                "label": (entry.get("label") or "").strip(),
                "href": (entry.get("href") or "").strip(),
            }
        )
    return rows


def parse_footer_links(form):
    """Build the footer links list from the editor POST.

    The footer rows submit index-aligned parallel arrays so order is
    preserved: ``footer_label[] footer_href[]``. A row is stored only with
    both a label and a safe href (whitespace stripped, empty rows dropped),
    and the list is capped at ``FOOTER_NAV_MAX`` entries.
    """
    labels = form.getlist("footer_label")
    hrefs = form.getlist("footer_href")

    def at(arr, i):
        return arr[i] if i < len(arr) else ""

    out = []
    for i in range(len(labels)):
        label = at(labels, i).strip()
        href = _safe_href(at(hrefs, i))
        if label and href:
            out.append({"label": label, "href": href})
        if len(out) >= FOOTER_NAV_MAX:
            break
    return out
