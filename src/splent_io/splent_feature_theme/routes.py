import json

from flask import (
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import login_required

from splent_io.splent_feature_theme import theme_bp
from splent_framework.services.service_locator import service_proxy

# Setting keys edited by the Appearance editor (the Customizer analogue).
APPEARANCE_FIELDS = [
    "site_name",
    "site_tagline",
    "site_logo",
    "site_brand_mode",
    "site_logo_size",
    "brand_primary",
    "brand_accent",
    "brand_bg",
    "brand_surface",
    "brand_text",
    "brand_heading",
]


@theme_bp.route("/theme/preview", methods=["GET"])
def preview():
    """Render the public shell with sample blocks — a quick visual smoke test
    of the theme engine (tokens + composable blocks)."""
    return render_template("theme/preview.html")


@theme_bp.route("/lang/<code>", methods=["GET"])
def set_language(code):
    """Language switcher: store the chosen locale in the session (read back by
    the framework's LocaleManager) and return to the previous page."""
    supported = current_app.config.get("BABEL_SUPPORTED_LOCALES", ["en"])
    if code in supported:
        session["locale"] = code
    return redirect(request.referrer or "/")


@theme_bp.route("/admin/appearance", methods=["GET", "POST"])
@login_required
def admin_appearance():
    """The Appearance editor — the WordPress Customizer analogue.

    Edits the site identity (name/tagline/logo) and the brand color tokens,
    persisting them via SettingsService. The theme reads these keys back, so
    changes apply immediately on the next render.
    """
    if request.method == "POST":
        values = {
            field: request.form.get(field, "") for field in APPEARANCE_FIELDS
        }
        service_proxy("SettingsService").set_many(values)
        flash("Appearance updated.", "success")
        return redirect(url_for("theme.admin_appearance"))

    return render_template("theme/admin/appearance.html")


@theme_bp.route("/admin/menus", methods=["GET", "POST"])
@login_required
def admin_menus():
    """The Menus editor — composes the main nav from INSTALLED features.

    SPL: the rows come from the features that registered a nav entry (so the
    menu tracks the product's derivation); the admin only reorders / hides /
    relabels them and may add custom external links. The override is stored
    under the ``site_nav`` setting and reconciled with the feature entries at
    render time.
    """
    from splent_io.splent_feature_theme.nav import editor_rows, parse_override

    if request.method == "POST":
        override = parse_override(request.form)
        service_proxy("SettingsService").set(
            "site_nav", json.dumps(override, ensure_ascii=False)
        )
        flash("Menu updated.", "success")
        return redirect(url_for("theme.admin_menus"))

    return render_template("theme/admin/menus.html", rows=editor_rows(current_app))
