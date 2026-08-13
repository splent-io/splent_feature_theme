"""
Functional tests for the admin-managed footer links.

The footer row is stored as the ``site_footer_nav`` setting — a JSON list of
{label, href} written by the Menus editor — and rendered by the public shell
as its own list before the social links. As in test_shell.py, the templates
are rendered directly because the contract under test belongs to the shell
and to the editor template, not to any one page, and the admin routes sit
behind login. Rendering still needs a request context, since the shell reads
request.path and calls url_for.
"""

import json

import pytest
from flask import render_template
from werkzeug.datastructures import MultiDict

from splent_framework.services.service_locator import service_proxy

LINKS = [
    {"label": "Privacy", "href": "/privacy"},
    {"label": "Docs", "href": "https://docs.example.org"},
    {"label": "Contact", "href": "mailto:hello@example.org"},
]


def _set_footer_setting(app, value):
    with app.app_context():
        service_proxy("SettingsService").set("site_footer_nav", value)


@pytest.fixture
def footer_links_setting(test_app):
    """Store three footer links for one test and clear them afterwards, so
    the session-scoped app never leaks them into other tests."""
    _set_footer_setting(test_app, json.dumps(LINKS, ensure_ascii=False))
    yield LINKS
    _set_footer_setting(test_app, "")


def test_footer_renders_the_stored_links_in_order(test_app, footer_links_setting):
    with test_app.test_request_context("/"):
        html = render_template("public_base.html")

    assert '<ul class="site-footer-nav">' in html
    row = html.split('<ul class="site-footer-nav">', 1)[1].split("</ul>", 1)[0]
    privacy = row.index('<a href="/privacy">Privacy</a>')
    docs = row.index('<a href="https://docs.example.org">Docs</a>')
    contact = row.index('<a href="mailto:hello@example.org">Contact</a>')
    assert privacy < docs < contact


def test_footer_links_come_before_the_social_list(test_app, footer_links_setting):
    with test_app.test_request_context("/"):
        html = render_template("public_base.html")

    assert html.index('class="site-footer-nav"') < html.index('class="site-social"')


def test_empty_setting_renders_no_footer_nav_list(test_app):
    """No stored links must mean no markup, not an empty ul."""
    with test_app.test_request_context("/"):
        html = render_template("public_base.html")

    assert "site-footer-nav" not in html


def test_menus_page_shows_the_footer_section(test_app):
    with test_app.test_request_context("/admin/menus"):
        html = render_template(
            "theme/admin/menus.html",
            rows=[],
            footer_rows=[{"label": "Privacy", "href": "/privacy"}],
        )

    assert 'id="footer-rows"' in html
    assert 'id="add-footer-link"' in html
    assert 'name="footer_label"' in html
    assert 'name="footer_href"' in html
    assert 'value="Privacy"' in html
    assert 'value="/privacy"' in html


def test_saving_the_menus_form_persists_the_footer_entries(test_app):
    """The editor POST path end to end: parse the submitted rows the way
    admin_menus does, store the result, and read it back through the shell's
    composer. Whitespace is stripped, rows missing a label or an address are
    dropped, and unsafe hrefs never reach the store."""
    from splent_io.splent_feature_theme.nav import (
        compose_footer_nav,
        parse_footer_links,
    )

    form = MultiDict()
    for label, href in [
        ("  Privacy  ", " /privacy "),
        ("", "/dropped-no-label"),
        ("Dropped no href", ""),
        ("Dropped unsafe", "javascript:alert(1)"),
        ("Docs", "https://docs.example.org"),
    ]:
        form.add("footer_label", label)
        form.add("footer_href", href)

    links = parse_footer_links(form)
    assert links == [
        {"label": "Privacy", "href": "/privacy"},
        {"label": "Docs", "href": "https://docs.example.org"},
    ]

    _set_footer_setting(test_app, json.dumps(links, ensure_ascii=False))
    try:
        with test_app.app_context():
            assert compose_footer_nav(test_app, lambda s: s) == links
    finally:
        _set_footer_setting(test_app, "")
