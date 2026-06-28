"""Design tokens for the theme engine.

A product (or a `skin` refinement feature) sets ``THEME_TOKENS`` in app.config to
override the neutral defaults. The public shell renders these as CSS custom
properties (``:root { --brand-* }``), so reskinning a product means changing
tokens — not rewriting CSS. This is what replaces the old "one css and that's it".
"""

DEFAULT_TOKENS = {
    "primary": "#6366f1",
    "primary_contrast": "#ffffff",
    "accent": "#10b981",
    "bg": "#ffffff",
    "surface": "#f8fafc",
    "text": "#1f2933",
    "heading": "#0f172a",
    "muted": "#64748b",
    "border": "#e5e9f0",
    "radius": "14px",
    "container": "1140px",
    "font_body": "'Inter', system-ui, sans-serif",
    "font_heading": "'Inter', system-ui, sans-serif",
    "font_display": "'Inter', system-ui, sans-serif",
    "font_url": "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap",
}

# token key -> CSS custom property name (font_url is not a CSS var)
_CSS_VAR = {
    "primary": "--brand-primary",
    "primary_contrast": "--brand-primary-contrast",
    "accent": "--brand-accent",
    "bg": "--brand-bg",
    "surface": "--brand-surface",
    "text": "--brand-text",
    "heading": "--brand-heading",
    "muted": "--brand-muted",
    "border": "--brand-border",
    "radius": "--brand-radius",
    "container": "--brand-container",
    "font_body": "--brand-font-body",
    "font_heading": "--brand-font-heading",
    "font_display": "--brand-font-display",
}


def get_tokens(app) -> dict:
    """Merge runtime settings over product/skin overrides over defaults.

    Order (highest wins): admin Appearance settings (``brand_*``) >
    ``app.config['THEME_TOKENS']`` (product/skin) > DEFAULT_TOKENS.
    """
    tokens = dict(DEFAULT_TOKENS)
    overrides = (app.config.get("THEME_TOKENS") if app is not None else None) or {}
    tokens.update({k: v for k, v in overrides.items() if v is not None})
    # Runtime overrides from the settings store (admin-editable Appearance).
    try:
        from splent_framework.services.service_locator import service_proxy

        svc = service_proxy("SettingsService")
        for tk in ("primary", "accent", "bg", "surface", "text", "heading"):
            v = svc.get(f"brand_{tk}", None)
            if v:
                tokens[tk] = v
    except Exception:
        pass
    return tokens


def tokens_to_css(tokens: dict) -> str:
    """Render tokens as a ``:root { --brand-*: … }`` declaration block."""
    lines = [f"  {_CSS_VAR[k]}: {tokens[k]};" for k in _CSS_VAR if k in tokens]
    return ":root {\n" + "\n".join(lines) + "\n}"
