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

In the admin shell, the theme contributes the "Appearance" editor (the
WordPress Customizer analogue) to the authenticated sidebar.
"""

from flask import request, url_for

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
        '<span class="align-middle">Appearance</span>'
        "</a>"
        "</li>"
    )


register_template_hook("layout.authenticated_sidebar", appearance_admin_link)
