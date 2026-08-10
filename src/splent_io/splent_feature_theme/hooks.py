"""Template hooks for splent_feature_theme.

The theme provides the PUBLIC shell (`public_base.html`) plus a library of
composable blocks under `templates/blocks/`. Features compose the public page by
injecting into these slots (declared in public_base.html):

    layout.head     — extra <head> tags
    layout.nav      — public navigation items (header)
    layout.hero     — hero section, full-width, above the content
    layout.footer   — footer columns / social links
    layout.scripts  — scripts before </body>

The theme registers nothing into the public slots by default — products and
content features compose the page. Skins refine the theme by overriding tokens
(THEME_TOKENS) and, if needed, block templates via [tool.splent.refinement].

Breadcrumbs are not a hook. The shell renders one under the header for every
page whose template context carries a `breadcrumb` variable, and renders no
markup at all for the pages that do not, so a feature passes a list and
imports nothing:

    return render_template(
        "courses/page.html",
        breadcrumb=[
            {"label": _("Courses"), "url": url_for("courses.index")},
            {"label": course.name, "url": course_url(course)},
            {"label": page.name, "url": None},
        ],
        ...,
    )

Each entry is a plain dict with a `label` and a `url` that may be None, in
reading order from the root down. The last entry is where the reader is: it is
rendered as text with aria-current, never as a link, whatever url it carries.
An intermediate entry with no url is a level that has no page of its own and
is rendered as text too.

What the feature gets back is blocks/breadcrumb.html: a nav with a translated
accessible name, an ordered list, separators drawn in CSS so a screen reader
does not read them out, truncation instead of a trail that wraps onto three
lines, and the colours of whichever skin the product installed.

In the admin shell, the theme contributes the "Appearance" editor (the
WordPress Customizer analogue) to the authenticated sidebar.
"""

from flask import request, url_for
from flask_babel import gettext as _

from splent_framework.hooks.template_hooks import register_template_hook


def appearance_admin_link():
    """Sidebar entry for the Appearance editor (the WP Customizer analogue)."""
    active = (
        "active"
        if request.endpoint and request.endpoint == "theme.admin_appearance"
        else ""
    )
    return (
        f'<li class="sidebar-item {active}">'
        f'<a class="sidebar-link" href="{url_for("theme.admin_appearance")}">'
        '<i class="align-middle" data-feather="sliders"></i> '
        f'<span class="align-middle">{_("Appearance")}</span>'
        "</a>"
        "</li>"
    )


def menus_admin_link():
    """Sidebar entry for the Menus editor (composes the nav from features)."""
    active = (
        "active" if request.endpoint and request.endpoint == "theme.admin_menus" else ""
    )
    return (
        f'<li class="sidebar-item {active}">'
        f'<a class="sidebar-link" href="{url_for("theme.admin_menus")}">'
        '<i class="align-middle" data-feather="menu"></i> '
        f'<span class="align-middle">{_("Menus")}</span>'
        "</a>"
        "</li>"
    )


register_template_hook("layout.authenticated_sidebar", appearance_admin_link)
register_template_hook("layout.authenticated_sidebar", menus_admin_link)
