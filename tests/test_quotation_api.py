from backend.models.quotation import QuotationRequest


def test_quotation_submission_validation_errors(client):
    invalid_payload = {
        "project_type": "InvalidType",
        "customer_name": "A",
        "customer_email": "not-an-email",
    }
    response = client.post("/api/quotation", json=invalid_payload)
    assert response.status_code == 422
    data = response.get_json()
    assert data["status"] == "error"
    assert "project_type" in data["errors"]
    assert "customer_name" in data["errors"]
    assert "customer_email" in data["errors"]


def test_quotation_submission_success(client):
    valid_payload = {
        "project_type": "SaaS Platform",
        "budget_range": "₹25,000–₹50,000",
        "timeline": "2-3 Weeks",
        "customer_name": "Alex Mercer",
        "customer_email": "alex.mercer@example.com",
        "customer_phone": "+91 9876543210",
        "project_name": "CloudFleet Telemetry",
        "project_description": "We need an ultra-modern SaaS telemetry dashboard with dark mode and real-time graphs.",
        "reference_website": "https://example.com",
        "selected_designs": ["DSGN-MIN-01", "DSGN-DRK-03"],
        "customization": {
            "primary_color": "#06B6D4",
            "secondary_color": "#030712",
            "theme_mode": "dark",
            "typography_preference": "Plus Jakarta Sans + Inter",
            "animation_preference": "Smooth & Subtle",
            "layout_preference": "Modern Grid",
            "platform_preference": "desktop-first",
        },
        "features": [
            "Responsive design",
            "Admin dashboard",
            "API integration",
            "Search functionality",
        ],
    }

    response = client.post("/api/quotation", json=valid_payload)
    assert response.status_code == 201
    data = response.get_json()
    assert data["status"] == "success"
    assert "reference_id" in data
    ref_id = data["reference_id"]
    assert ref_id.startswith("QT-")

    # Verify database persistence
    saved = QuotationRequest.query.filter_by(reference_id=ref_id).first()
    assert saved is not None
    assert saved.customer_name == "Alex Mercer"
    assert saved.project_type == "SaaS Platform"
    assert len(saved.selected_designs) == 2
    assert saved.customization.theme_mode == "dark"
    assert len(saved.features) == 4
    assert len(saved.status_history) >= 1


def test_get_quotation_public_status(client):
    valid_payload = {
        "project_type": "Business Website",
        "budget_range": "₹10,000–₹25,000",
        "timeline": "1-2 Weeks",
        "customer_name": "Maya Patel",
        "customer_email": "maya@business.co",
        "project_name": "Maya Studio Launch",
        "project_description": "Architectural portfolio with sleek grid showcase and booking contact.",
    }
    create_res = client.post("/api/quotation", json=valid_payload)
    assert create_res.status_code == 201
    ref_id = create_res.get_json()["reference_id"]

    # Verify query by reference
    query_res = client.get(f"/api/quotation/{ref_id}")
    assert query_res.status_code == 200
    q_data = query_res.get_json()
    assert q_data["status"] == "success"
    assert q_data["reference_id"] == ref_id
    assert q_data["project_name"] == "Maya Studio Launch"
    assert q_data["quotation_status"] == "new"
