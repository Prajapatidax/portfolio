def test_valid_admin_login_url_accessible(client):
    response = client.get("/admin/login/version/101")
    assert response.status_code == 200
    assert b"Admin Sign In" in response.data


def test_decoy_admin_urls_must_return_404(client):
    """STRICT ROUTING RULE: /admin, /admin/login, /login/admin must return 404, not redirect!"""
    for route in ["/admin", "/admin/", "/admin/login", "/admin/login/", "/login/admin", "/login/admin/"]:
        res = client.get(route)
        assert res.status_code == 404, f"Route {route} did not return 404 (returned {res.status_code})"
        assert b"Oops! Page Not Found" in res.data


def test_unauthenticated_dashboard_access_denied(client):
    response = client.get("/admin/dashboard")
    assert response.status_code in [302, 404]
    if response.status_code == 302:
        assert "/admin/login/version/101" in response.headers["Location"]


def test_admin_login_failure(client):
    # Need session for CSRF token
    with client.session_transaction() as sess:
        sess["_csrf_token"] = "valid-test-token"

    response = client.post(
        "/admin/login/version/101",
        data={
            "email": "admin@prajapatidax.co.in",
            "password": "WrongPassword123!",
            "csrf_token": "valid-test-token",
        },
    )
    assert response.status_code == 200
    assert b"Invalid email or password credentials" in response.data


def test_admin_login_success_and_dashboard_access(client):
    with client.session_transaction() as sess:
        sess["_csrf_token"] = "valid-test-token"

    response = client.post(
        "/admin/login/version/101",
        data={
            "email": "admin@prajapatidax.co.in",
            "password": "AdminTestPassword123!",
            "csrf_token": "valid-test-token",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Portfolio &amp; Quotations Hub" in response.data or b"Portfolio & Quotations Hub" in response.data
    assert b"Quotation Requests" in response.data


def test_admin_logout(client):
    # Set session
    with client.session_transaction() as sess:
        sess["admin_id"] = 1

    res = client.get("/admin/logout", follow_redirects=True)
    assert res.status_code == 200

    # Ensure session was cleared
    dash_res = client.get("/admin/dashboard")
    assert dash_res.status_code in [302, 404]
