from flask import current_app, redirect, render_template, request, session

from splent_io.splent_feature_theme import theme_bp


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
