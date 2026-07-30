"""
Functional tests for the public shell of splent_feature_theme.

These render `public_base.html` directly instead of going through a route,
because the contract under test belongs to the shell and not to any one page:
a feature hands the template context a `breadcrumb` trail and the shell does
the rest. Rendering still needs a request context, since the shell reads
request.path to mark the active nav item and calls url_for.
"""

import re

from flask import render_template

TRAIL = [
    {"label": "Courses", "url": "/courses"},
    {"label": "EGC", "url": "/courses/egc"},
    {"label": "Tema 1", "url": None},
]


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
