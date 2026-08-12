"""What the site calls itself, read from the product's environment.

The shell has always taken these from ``app.config`` and nothing ever put
them there, so ``SITE_NAME=egc.us.es`` in a product's .env changed nothing
and every product's header showed the package name instead: ``egc_wiki``,
which is what the code calls it and not what anybody types into a browser.

Same shape as the language: a product's identity is configuration of the
product, and a feature that renders it has to read it from somewhere.

The runtime Appearance editor still wins over both. Order, from strongest:
the setting somebody typed in the admin panel, then this, then the package
name as a last resort so a product that says nothing still has a header.
"""

import os


def inject_config(app):
    # The name in the header, the browser tab and the footer.
    site_name = os.getenv("SITE_NAME", "").strip()
    # The line under it, where a product has one.
    tagline = os.getenv("SITE_TAGLINE", "").strip()
    # How the header brand renders when the admin panel says nothing:
    # logo, text, or both; and the logo height in pixels.
    brand_mode = os.getenv("SITE_BRAND_MODE", "").strip()
    logo_size = os.getenv("SITE_LOGO_SIZE", "").strip()

    values = {}
    if site_name:
        values["SITE_NAME"] = site_name
    if tagline:
        values["SITE_TAGLINE"] = tagline
    if brand_mode:
        values["SITE_BRAND_MODE"] = brand_mode
    if logo_size:
        values["SITE_LOGO_SIZE"] = logo_size

    # setdefault rather than assignment: a product that sets these in its own
    # config.py has said something more specific than an environment default,
    # and this must not overwrite it.
    for key, value in values.items():
        app.config.setdefault(key, value)
