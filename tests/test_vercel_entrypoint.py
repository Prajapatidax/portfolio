import os
from pathlib import Path
import pytest
from api.index import app as vercel_app, application


def test_vercel_entrypoint_aliases():
    """Verify that both 'app' and 'application' are exported and identical."""
    assert vercel_app is not None
    assert application is not None
    assert vercel_app is application


def test_vercel_template_and_static_resolution():
    """Verify that template and static folders resolve to valid existing directories."""
    template_dir = Path(vercel_app.template_folder)
    static_dir = Path(vercel_app.static_folder)

    assert template_dir.exists(), f"Template folder does not exist: {template_dir}"
    assert (template_dir / "index.html").exists(), "index.html missing in template folder"
    assert (template_dir / "design-showcase.html").exists(), "design-showcase.html missing"
    assert (template_dir / "404.html").exists(), "404.html missing"

    assert static_dir.exists(), f"Static folder does not exist: {static_dir}"
    assert (static_dir / "css" / "custom.css").exists(), "custom.css missing in static folder"
    assert (static_dir / "js" / "main.js").exists(), "main.js missing in static folder"
    assert (static_dir / "assets" / "Resume.pdf").exists(), "Resume.pdf missing in static/assets folder"


def test_vercel_client_routes(client):
    """Verify that essential routes respond with 200 OK through the test client."""
    # Homepage
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"Dax Prajapati" in resp.data

    # Design Showcase
    resp = client.get("/design-showcase")
    assert resp.status_code == 200

    # Quotation Wizard
    resp = client.get("/quotation")
    assert resp.status_code == 200

    # Robots.txt
    resp = client.get("/robots.txt")
    assert resp.status_code == 200
    assert resp.content_type.startswith("text/plain")

    # Sitemap.xml
    resp = client.get("/sitemap.xml")
    assert resp.status_code == 200
    assert "xml" in resp.content_type

    # Static CSS
    resp = client.get("/static/css/custom.css")
    assert resp.status_code == 200
    assert "css" in resp.content_type

    # Resume Route
    resp = client.get("/Resume.pdf")
    assert resp.status_code == 200


def test_vercel_rewrite_path_correction(client):
    """
    Test that VercelPathCorrectionMiddleware restores PATH_INFO correctly
    when Vercel forwards requests to /api/index with x-matched-path header.
    """
    # 1. Root / homepage via Vercel rewrite
    r_home = client.get("/api/index", headers={"x-matched-path": "/"})
    assert r_home.status_code == 200
    assert b"Dax Prajapati" in r_home.data

    # 2. About page via Vercel rewrite
    r_about = client.get("/api/index", headers={"x-matched-path": "/about"})
    assert r_about.status_code == 200
    assert b"About" in r_about.data

    # 3. Design Showcase via Vercel rewrite
    r_showcase = client.get("/api/index", headers={"x-matched-path": "/design-showcase"})
    assert r_showcase.status_code == 200

    # 4. Admin login page via Vercel rewrite
    r_admin = client.get("/api/index", headers={"x-matched-path": "/admin/login/version/101"})
    assert r_admin.status_code == 200
    assert b"Sign In" in r_admin.data or b"Admin" in r_admin.data

    # 5. Direct naked call to /api/index without header falls back to homepage
    r_naked = client.get("/api/index")
    assert r_naked.status_code == 200
    assert b"Dax Prajapati" in r_naked.data


def test_vercel_rewrite_with_explicit_vercel_path(client):
    """
    Test that clicking any navigation link / route (Home, About, Projects, Showcase, Contact, Admin)
    forwards __vercel_path and loads the EXACT page requested rather than the home page.
    """
    # 1. About page
    r_about = client.get("/api/index?__vercel_path=/about")
    assert r_about.status_code == 200
    assert b"<title>About Me | Dax Prajapati</title>" in r_about.data

    # 2. Projects page
    r_projects = client.get("/api/index?__vercel_path=/projects")
    assert r_projects.status_code == 200
    assert b"<title>All Projects | Dax Prajapati</title>" in r_projects.data

    # 3. Design Showcase page
    r_showcase = client.get("/api/index?__vercel_path=/design-showcase")
    assert r_showcase.status_code == 200
    assert b"Design Showcase" in r_showcase.data

    # 4. Contact page
    r_contact = client.get("/api/index?__vercel_path=/contact")
    assert r_contact.status_code == 200
    assert b"Get In Touch" in r_contact.data or b"Contact" in r_contact.data

    # 5. Quotation Wizard page
    r_quote = client.get("/api/index?__vercel_path=/quotation")
    assert r_quote.status_code == 200
    assert b"Project Quotation Wizard" in r_quote.data

    # 6. Admin Login page
    r_admin = client.get("/api/index?__vercel_path=/admin/login/version/101")
    assert r_admin.status_code == 200
    assert b"Admin" in r_admin.data or b"Sign In" in r_admin.data
