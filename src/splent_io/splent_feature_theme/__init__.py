from splent_framework.blueprints.base_blueprint import create_blueprint
from splent_io.splent_feature_theme.tokens import get_tokens, tokens_to_css

theme_bp = create_blueprint(__name__)


def init_feature(app):
    pass


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
    # Translate nav labels so the menu follows the active locale. The labels
    # live in product config (SITE_NAV); their translations come from the
    # content features' catalogs (e.g. "Projects" -> "Proyectos").
    nav = [
        {**item, "label": _translate(item["label"])} if item.get("label") else item
        for item in app.config.get("SITE_NAV", [])
    ]
    site = {
        "name": _s("site_name", app.config.get("SITE_NAME") or os.getenv("SPLENT_APP") or "Site"),
        "tagline": _s("site_tagline", app.config.get("SITE_TAGLINE", "")),
        "nav": nav,
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
    try:
        from flask_babel import get_locale as _get_locale
        site["locale"] = str(_get_locale() or app.config.get("BABEL_DEFAULT_LOCALE", "en"))
    except Exception:
        site["locale"] = app.config.get("BABEL_DEFAULT_LOCALE", "en")
    site["locales"] = app.config.get("BABEL_SUPPORTED_LOCALES", ["en"])
    return {
        "theme_tokens": tokens,
        "theme_tokens_css": tokens_to_css(tokens),
        "render_block": _make_render_block(),
        "site": site,
    }
