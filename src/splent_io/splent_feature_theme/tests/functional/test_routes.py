"""
Functional tests for splent_feature_theme.

Functional tests use Flask's test client to exercise full HTTP
request/response cycles (GET, POST, redirects, rendered HTML).

The scaffolded version of this file probed "/theme", which this feature
has never served: it contributes the public shell, an appearance and menu
editor under /admin, and the language switcher. The routes asserted here
are the ones the contract actually declares.
"""


def test_appearance_editor_is_registered(test_client):
    """Anonymous callers are sent to login rather than getting a 404."""
    response = test_client.get("/admin/appearance")
    assert response.status_code in (200, 302)


def test_menu_editor_is_registered(test_client):
    response = test_client.get("/admin/menus")
    assert response.status_code in (200, 302)


def test_language_switcher_redirects(test_client):
    response = test_client.get("/lang/es")
    assert response.status_code in (200, 302)
