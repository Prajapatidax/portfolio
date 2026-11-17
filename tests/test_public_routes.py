def test_homepage(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Dax Prajapati" in response.data
    assert b"Full Stack Developer" in response.data


def test_about_page(client):
    response = client.get("/about")
    assert response.status_code == 200
    assert b"My Journey" in response.data
    assert b"LDRP-ITR" in response.data


def test_projects_page(client):
    response = client.get("/projects")
    assert response.status_code == 200
    assert b"Mindmate" in response.data
    assert b"Earth Vision" in response.data
    assert b"Sortify" in response.data


def test_contact_page(client):
    response = client.get("/contact")
    assert response.status_code == 200
    assert b"daxprajapati1707@gmail.com" in response.data


def test_design_showcase(client):
    response = client.get("/design-showcase")
    assert response.status_code == 200
    assert b"Your Vision. My Creativity." in response.data
    assert b"Minimal &amp; Professional" in response.data or b"Minimal & Professional" in response.data


def test_design_preview(client):
    response = client.get("/design-showcase/preview/zenith-minimal")
    assert response.status_code == 200
    assert b"Zenith Minimalist Editorial" in response.data
    assert b"Color Palette" in response.data


def test_quotation_wizard_page(client):
    response = client.get("/quotation")
    assert response.status_code == 200
    assert b"Project Quotation Wizard" in response.data


def test_custom_404_error_page(client):
    response = client.get("/this-route-does-not-exist-at-all")
    assert response.status_code == 404
    assert b"Oops! Page Not Found" in response.data


def test_robots_txt(client):
    response = client.get("/robots.txt")
    assert response.status_code == 200
    assert b"Disallow: /admin" in response.data
    assert b"Sitemap: https://prajapatidax.co.in/sitemap.xml" in response.data


def test_sitemap_xml(client):
    response = client.get("/sitemap.xml")
    assert response.status_code == 200
    assert b"<loc>https://prajapatidax.co.in/</loc>" in response.data
    assert b"<loc>https://prajapatidax.co.in/design-showcase</loc>" in response.data
