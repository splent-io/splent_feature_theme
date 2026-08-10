"""
Functional tests for the SEO surface of the public shell.

The head tests render `public_base.html` directly, like the shell tests,
because the contract belongs to the shell and not to any one page: whatever
a page puts in its title block must be mirrored into og:title from a single
render, the description cascades from the page variable to the product's
tagline to nothing at all, and og:image appears only when the product really
ships one. robots.txt goes through the test client, since that contract is
an HTTP one.
"""

from flask import render_template, render_template_string, url_for

CHILD = '{% extends "public_base.html" %}{% block title %}Tema 1 · EGC{% endblock %}'


def _render(test_app, path="/", **context):
    with test_app.test_request_context(path):
        return render_template("public_base.html", **context)


# --- head: canonical / Open Graph -----------------------------------------


def test_canonical_and_og_url_point_at_the_requested_url(test_app):
    html = _render(test_app, "/courses/egc")

    assert '<link rel="canonical" href="http://localhost/courses/egc">' in html
    assert '<meta property="og:url" content="http://localhost/courses/egc">' in html


def test_og_title_mirrors_the_title_block_of_the_page(test_app):
    """A page overrides the title block once; <title> and og:title both carry
    that value, captured from a single render of the block."""
    with test_app.test_request_context("/"):
        html = render_template_string(CHILD)

    assert "<title>Tema 1 · EGC</title>" in html
    assert '<meta property="og:title" content="Tema 1 · EGC">' in html


def test_og_site_name_and_default_type(test_app):
    html = _render(test_app)

    assert '<meta property="og:site_name" content="' in html
    assert '<meta property="og:type" content="website">' in html


def test_a_page_may_override_the_og_type(test_app):
    html = _render(test_app, og_type="article")

    assert '<meta property="og:type" content="article">' in html


# --- head: description sources --------------------------------------------


def test_meta_description_prefers_the_page_variable(test_app):
    html = _render(test_app, meta_description="A page about X")

    assert '<meta name="description" content="A page about X">' in html
    assert '<meta property="og:description" content="A page about X">' in html


def test_meta_description_falls_back_to_the_site_tagline(test_app):
    had_key = "SITE_TAGLINE" in test_app.config
    old = test_app.config.get("SITE_TAGLINE")
    test_app.config["SITE_TAGLINE"] = "Wiki del curso"
    try:
        html = _render(test_app)
    finally:
        if had_key:
            test_app.config["SITE_TAGLINE"] = old
        else:
            test_app.config.pop("SITE_TAGLINE", None)

    assert '<meta name="description" content="Wiki del curso">' in html
    assert '<meta property="og:description" content="Wiki del curso">' in html


def test_no_description_meta_when_nothing_provides_one(test_app):
    old = test_app.config.pop("SITE_TAGLINE", None)
    try:
        html = _render(test_app)
    finally:
        if old is not None:
            test_app.config["SITE_TAGLINE"] = old

    assert '<meta name="description"' not in html
    assert '<meta property="og:description"' not in html


# --- head: og:image / twitter card ----------------------------------------


def test_no_og_image_and_summary_card_when_the_product_ships_none(test_app, tmp_path):
    """Point the app at an empty static folder: the theme must not fabricate
    an image, and the twitter card stays a plain summary."""
    old = test_app.static_folder
    test_app.static_folder = str(tmp_path)
    try:
        html = _render(test_app)
    finally:
        test_app.static_folder = old

    assert "og:image" not in html
    assert '<meta name="twitter:card" content="summary">' in html


def test_og_image_is_absolute_and_upgrades_the_card_when_the_product_ships_one(
    test_app, tmp_path
):
    (tmp_path / "og.png").write_bytes(b"\x89PNG")
    old = test_app.static_folder
    test_app.static_folder = str(tmp_path)
    try:
        with test_app.test_request_context("/"):
            expected = url_for("static", filename="og.png", _external=True)
            html = render_template("public_base.html")
    finally:
        test_app.static_folder = old

    assert expected.startswith("http")
    assert f'<meta property="og:image" content="{expected}">' in html
    assert '<meta name="twitter:card" content="summary_large_image">' in html


# --- robots.txt ------------------------------------------------------------


def test_robots_txt_allows_everything(test_client):
    response = test_client.get("/robots.txt")

    assert response.status_code == 200
    assert response.mimetype == "text/plain"
    body = response.get_data(as_text=True)
    assert "User-agent: *" in body
    assert "Allow: /" in body


def test_robots_sitemap_line_tracks_the_products_sitemap_endpoint(
    test_client, test_app
):
    """The theme does not depend on courses: the Sitemap line exists exactly
    when the derived product registered a courses.sitemap endpoint."""
    body = test_client.get("/robots.txt").get_data(as_text=True)

    if "courses.sitemap" in test_app.view_functions:
        assert "Sitemap: http" in body
    else:
        assert "Sitemap" not in body
