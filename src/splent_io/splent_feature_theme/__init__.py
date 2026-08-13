from splent_framework.blueprints.base_blueprint import create_blueprint
from splent_io.splent_feature_theme.tokens import get_tokens, tokens_to_css

theme_bp = create_blueprint(__name__)


def init_feature(app):
    # The theme's base stylesheet loads first (order 0) so feature and skin
    # assets cascade on top of it. Declared through the asset registry like
    # every other feature — no hardcoded <link> in the shell.
    from splent_framework.assets.asset_registry import register_asset

    register_asset(
        "css", "theme.assets", order=0, subfolder="css", filename="public.css"
    )
    # Reading chrome for code blocks: the language, and a button that
    # copies. Registered by the shell rather than by a content feature,
    # because every feature that renders markdown gets code blocks and none
    # of them should ship their own copy button.
    register_asset(
        "js", "theme.assets", order=0, subfolder="js", filename="code_blocks.js"
    )
    # Header-offset variable and the shared lightbox: rich-text images and
    # anything marked data-lightbox open full-screen. Shell-owned for the
    # same reason as the copy button, every content feature benefits and
    # none should ship its own.
    register_asset(
        "js", "theme.assets", order=0, subfolder="js", filename="lightbox.js"
    )


def _make_render_block():
    from flask import render_template
    from markupsafe import Markup

    def render_block(name, **context):
        """Render a composable theme block: templates/blocks/<name>.html.

        Returns Markup so the rendered HTML is injected as-is (not escaped) when
        used as {{ render_block('hero', …) }} inside autoescaped templates.
        """
        return Markup(render_template(f"blocks/{name}.html", **context))

    return render_block


def inject_context_vars(app):
    """Expose design tokens, the block renderer and the product's site config.

    `site` (name/tagline/nav/social) comes from PRODUCT-level config
    (`app.config['SITE_*']`), so the theme never hardcodes a product name —
    each product is its own website.
    """
    import os

    try:
        from flask_babel import gettext as _translate
    except Exception:

        def _translate(s):
            return s

    from splent_framework.services.service_locator import service_proxy

    def _s(key, default):
        # runtime setting (admin Appearance editor) -> product config -> default
        try:
            v = service_proxy("SettingsService").get(key, None)
            return v if v not in (None, "") else default
        except Exception:
            return default

    tokens = get_tokens(app)
    # Compose the main nav from the INSTALLED features (each declares its entry
    # via register_nav_item) reconciled with the admin Menus editor's runtime
    # override (order / visibility / label + custom links). Falls back to legacy
    # SITE_NAV. Labels are translated to follow the active locale.
    from splent_io.splent_feature_theme.nav import compose_footer_nav, compose_nav

    nav = compose_nav(app, _translate)
    # The footer links row is admin-managed too (Menus editor, key
    # site_footer_nav) but custom links only, so there is no reconciliation.
    # The shell renders it before the social list and skips it when empty.
    footer_nav = compose_footer_nav(app, _translate)

    # {{ auto_breadcrumb(page_title, mode) }} — the derived trail for the
    # current request, or None when the mode hides it there. Bound to the
    # composed nav above, so a menu rename in the admin renames the section
    # crumb too. The shell calls it only when the page passed no explicit
    # `breadcrumb`; that one always wins.
    from splent_io.splent_feature_theme.breadcrumbs import build_trail

    def auto_breadcrumb(page_title, mode="deep"):
        from flask import request

        return build_trail(request.path, page_title, nav, mode)

    site = {
        "name": _s(
            "site_name",
            app.config.get("SITE_NAME") or os.getenv("SPLENT_APP") or "Site",
        ),
        "tagline": _s("site_tagline", app.config.get("SITE_TAGLINE", "")),
        "nav": nav,
        "footer_nav": footer_nav,
        "social": app.config.get("SITE_SOCIAL", []),
        "event": app.config.get("SITE_EVENT", {}),
        "sponsors": app.config.get("SITE_SPONSORS", []),
        "logo": _s("site_logo", app.config.get("SITE_LOGO", "")),
        "gallery": app.config.get("SITE_GALLERY", []),
        "hero_eyebrow": app.config.get("SITE_HERO_EYEBROW", ""),
        "hero_actions": app.config.get("SITE_HERO_ACTIONS", []),
        "highlights_title": app.config.get("SITE_HIGHLIGHTS_TITLE", ""),
        "highlights": app.config.get("SITE_HIGHLIGHTS", []),
        "sponsors_title": app.config.get("SITE_SPONSORS_TITLE", "Patrocinadores"),
        "gallery_title": app.config.get("SITE_GALLERY_TITLE", "Galería"),
        "cta": app.config.get("SITE_CTA", {}),
    }
    # Open Graph image: opt-in by shipping static/og.png with the product.
    # The shell emits og:image (and upgrades the twitter card) only when the
    # file is really there; the theme never fabricates one.
    site["og_image"] = bool(
        app.static_folder and os.path.exists(os.path.join(app.static_folder, "og.png"))
    )
    try:
        from flask_babel import get_locale as _get_locale

        site["locale"] = str(
            _get_locale() or app.config.get("BABEL_DEFAULT_LOCALE", "en")
        )
    except Exception:
        site["locale"] = app.config.get("BABEL_DEFAULT_LOCALE", "en")
    site["locales"] = app.config.get("BABEL_SUPPORTED_LOCALES", ["en"])
    return {
        "theme_tokens": tokens,
        "theme_tokens_css": tokens_to_css(tokens),
        "render_block": _make_render_block(),
        "auto_breadcrumb": auto_breadcrumb,
        "site": site,
    }
