"""Unit tests for the automatic breadcrumb builder."""

from unittest.mock import patch

from splent_io.splent_feature_theme.breadcrumbs import build_trail

NAV = [{"key": "post", "label": "News", "href": "/news"}]


def _labels(trail):
    return [c["label"] for c in trail]


@patch("splent_io.splent_feature_theme.breadcrumbs._", side_effect=lambda s: s)
def test_numeric_segments_draw_no_crumb(_gettext):
    """Date-shaped permalinks skip the numbers: Home > Title, not 2026 > 06."""
    trail = build_trail("/2026/06/20/diverso-days-2026/", "Diverso Days 2026", NAV)
    assert _labels(trail) == ["Home", "Diverso Days 2026"]


@patch("splent_io.splent_feature_theme.breadcrumbs._", side_effect=lambda s: s)
def test_section_crumb_comes_from_the_nav(_gettext):
    trail = build_trail("/news/category/research", "Research", NAV)
    assert _labels(trail) == ["Home", "News", "Category", "Research"]
    assert trail[1]["url"] == "/news"
