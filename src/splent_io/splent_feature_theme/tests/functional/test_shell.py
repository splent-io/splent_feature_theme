"""
Functional tests for the public shell of splent_feature_theme.

These render `public_base.html` directly instead of going through a route,
because the contract under test belongs to the shell and not to any one page:
a feature hands the template context a `breadcrumb` trail and the shell does
the rest — and a page that hands it nothing gets a trail derived from the
URL and its title, governed by the `site_breadcrumbs` appearance setting.
Rendering still needs a request context, since the shell reads request.path
to mark the active nav item and calls url_for.
"""

import re

import pytest
from flask import render_template, render_template_string

from splent_framework.nav import nav_registry

TRAIL = [
    {"label": "Courses", "url": "/courses"},
    {"label": "EGC", "url": "/courses/egc"},
    {"label": "Tema 1", "url": None},
]

# A page the way features really build one: the title block carries the page
# name plus the site suffix, which the automatic trail must strip back off.
TITLED_PAGE = (
    '{% extends "public_base.html" %}{% block title %}Tema 1 — EGC Wiki{% endblock %}'
)


def _trail_text(html):
    """The words a screen reader reads out of the trail, tags stripped."""
    trail = html.split('<ol class="breadcrumb-trail">', 1)[1].split("</ol>", 1)[0]
    return re.sub(r"<[^>]+>", " ", trail).split()


def test_shell_renders_no_breadcrumb_when_the_page_gives_no_trail(test_app):
    """Most pages pass nothing, and they must get no markup, not an empty nav."""
    with test_app.test_request_context("/"):
        html = render_template("public_base.html")

    assert "block-breadcrumb" not in html
    assert "breadcrumb-trail" not in html
    assert "breadcrumb-level" not in html


def test_shell_renders_the_entries_it_is_given(test_app):
    with test_app.test_request_context("/courses/egc/tema-1"):
        html = render_template("public_base.html", breadcrumb=TRAIL)

    assert 'class="block block-breadcrumb"' in html
    assert '<a class="breadcrumb-link" href="/courses">Courses</a>' in html
    assert '<a class="breadcrumb-link" href="/courses/egc">EGC</a>' in html


def test_last_entry_is_the_current_page_and_not_a_link(test_app):
    """Where the reader already is: text, marked as current, never a link."""
    with test_app.test_request_context("/courses/egc/tema-1"):
        html = render_template("public_base.html", breadcrumb=TRAIL)

    assert '<span class="breadcrumb-current" aria-current="page">Tema 1</span>' in html
    assert ">Tema 1</a>" not in html


def test_separators_are_never_written_into_the_markup(test_app):
    """CSS draws them, so the labels are the only text in the list."""
    with test_app.test_request_context("/courses/egc/tema-1"):
        html = render_template("public_base.html", breadcrumb=TRAIL)

    assert _trail_text(html) == ["Courses", "EGC", "Tema", "1"]


# --- the automatic trail ----------------------------------------------------


@pytest.fixture
def library_nav_item():
    """One registered section for the auto trail to hang the first segment on.

    Registered under a key no real feature uses and removed afterwards, so
    the session-scoped app never leaks it into other tests.
    """
    nav_registry.register_nav_item("library", "Library", "/library", order=10)
    yield
    nav_registry._nav_items.pop("library", None)


@pytest.fixture
def breadcrumbs_mode(test_app):
    """Set SITE_BREADCRUMBS in config for one test, restoring it afterwards."""
    had_key = "SITE_BREADCRUMBS" in test_app.config
    old = test_app.config.get("SITE_BREADCRUMBS")

    def set_mode(mode):
        test_app.config["SITE_BREADCRUMBS"] = mode

    yield set_mode
    if had_key:
        test_app.config["SITE_BREADCRUMBS"] = old
    else:
        test_app.config.pop("SITE_BREADCRUMBS", None)


def test_default_mode_hides_the_auto_trail_on_a_top_level_page(
    test_app, library_nav_item
):
    """ "deep" is the default: one level down, a reader is not lost, so the
    shell emits no markup at all, exactly like a page that passes nothing."""
    with test_app.test_request_context("/library"):
        html = render_template("public_base.html")

    assert "block-breadcrumb" not in html
    assert "breadcrumb-trail" not in html


def test_default_mode_draws_home_section_and_page_on_a_deep_page(
    test_app, library_nav_item
):
    """Two levels down the trail appears on its own: Home links to /, the
    section crumb is the registered nav entry (so Menus edits are honoured),
    and the current page is the title block with its site suffix stripped."""
    with test_app.test_request_context("/library/tema-1"):
        html = render_template_string(TITLED_PAGE)

    assert 'class="block block-breadcrumb"' in html
    # Home first; its label follows the locale, so the test pins the href.
    assert '<a class="breadcrumb-link" href="/">' in html
    assert '<a class="breadcrumb-link" href="/library">Library</a>' in html
    assert '<span class="breadcrumb-current" aria-current="page">Tema 1</span>' in html
    assert "Wiki" not in _trail_text(html)


def test_intermediate_segments_render_as_prettified_text(test_app, library_nav_item):
    """A middle segment no nav entry claims is a level with no page of its
    own: text without a link, dashes to spaces, title case."""
    with test_app.test_request_context("/library/study-guides/tema-1"):
        html = render_template_string(TITLED_PAGE)

    assert '<li class="breadcrumb-level"><span>Study Guides</span></li>' in html
    assert ">Study Guides</a>" not in html


def test_mode_all_draws_the_trail_on_a_top_level_page(
    test_app, library_nav_item, breadcrumbs_mode
):
    breadcrumbs_mode("all")
    with test_app.test_request_context("/library"):
        html = render_template("public_base.html")

    assert 'class="block block-breadcrumb"' in html
    assert '<a class="breadcrumb-link" href="/">' in html


def test_mode_all_still_leaves_the_home_page_alone(test_app, breadcrumbs_mode):
    """The home is the trail's root, never a page on it."""
    breadcrumbs_mode("all")
    with test_app.test_request_context("/"):
        html = render_template("public_base.html")

    assert "block-breadcrumb" not in html


def test_mode_off_hides_the_trail_everywhere(
    test_app, library_nav_item, breadcrumbs_mode
):
    breadcrumbs_mode("off")
    with test_app.test_request_context("/library/study-guides/tema-1"):
        html = render_template_string(TITLED_PAGE)

    assert "block-breadcrumb" not in html
    assert "breadcrumb-trail" not in html


def test_an_explicit_trail_wins_over_the_automatic_one(
    test_app, library_nav_item, breadcrumbs_mode
):
    """A page that passes `breadcrumb` keeps exactly that trail, whatever the
    mode says — even "off" does not silence it."""
    breadcrumbs_mode("off")
    with test_app.test_request_context("/library/tema-1"):
        html = render_template("public_base.html", breadcrumb=TRAIL)

    assert '<a class="breadcrumb-link" href="/courses">Courses</a>' in html
    assert _trail_text(html) == ["Courses", "EGC", "Tema", "1"]
    trail = html.split('<ol class="breadcrumb-trail">', 1)[1].split("</ol>", 1)[0]
    assert 'href="/library"' not in trail
