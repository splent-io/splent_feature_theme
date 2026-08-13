"""Derive the breadcrumb trail the shell draws when a page passes none.

Explicit trails came first and still win: a page that hands the shell a
`breadcrumb` list gets exactly that list (see the module docstring of
hooks.py). This module covers every other page, so a product gets a trail
everywhere without any feature wiring anything — it is derived from the URL
and from the page title the page already declared in its title block.

The section crumb is looked up in the COMPOSED nav (feature entries
reconciled with the admin Menus editor), so renaming a menu entry renames
the crumb too, and a first segment no nav entry claims degrades to plain
text. The `site_breadcrumbs` appearance setting governs visibility: "deep"
(the default) draws the trail only on pages two levels down or more, where
a reader can actually be lost; "all" draws it on every page except the
home; "off" never draws it.
"""

from flask_babel import gettext as _


def build_trail(path, page_title, nav, mode="deep"):
    """The automatic trail for `path`, or None when nothing should render.

    `nav` is compose_nav() output — {label, href} dicts — and `page_title`
    is the rendered title block of the page, whose " — <suffix>" tail (the
    site name) is stripped so the last crumb says where the reader is and
    nothing twice. Any unknown mode behaves like "deep", the default.
    """
    mode = (mode or "").strip().lower()
    if mode == "off":
        return None
    segments = [s for s in (path or "").split("/") if s]
    if not segments:
        return None  # the home is the trail's root, never a page on it
    if mode != "all" and len(segments) < 2:
        return None

    trail = [{"label": _("Home"), "url": "/"}]
    first = "/" + segments[0]
    section = next((i for i in nav if (i.get("href") or "").rstrip("/") == first), None)
    for position, segment in enumerate(segments[:-1]):
        if position == 0 and section is not None:
            trail.append({"label": section["label"], "url": section["href"]})
        elif segment.isdigit():
            # Date-shaped permalinks (/2026/06/20/slug/) would read as
            # Home > 2026 > 06 > 20 > Title; the numbers locate nothing a
            # reader can navigate to, so they draw no crumb.
            continue
        else:
            # A level with no page of its own; the block renders it as text.
            trail.append({"label": _prettify(segment), "url": None})

    title = (page_title or "").split(" — ", 1)[0].strip()
    trail.append({"label": title or _prettify(segments[-1]), "url": None})
    return trail


def _prettify(segment):
    """A URL segment as readable text: dashes to spaces, title case."""
    return segment.replace("-", " ").strip().title()
