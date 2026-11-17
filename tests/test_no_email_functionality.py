import pytest
from flask import session
from backend import db
from backend.models.quotation import QuotationRequest
from backend.models.contact import ContactMessage
from backend.models.settings import PortfolioSetting


def _login_admin(client):
    with client.session_transaction() as sess:
        sess["admin_id"] = 1
        sess["admin_email"] = "admin@prajapatidax.co.in"
        sess["admin_name"] = "Test Admin"


def test_quotation_submission_persists_without_email_triggers(client):
    """
    Submitting a quotation request must validate, persist to database,
    generate a unique reference ID, and display confirmation message without sending emails.
    """
    payload = {
        "project_type": "Business Website",
        "budget_range": "₹50,000+",
        "timeline": "3-4 Weeks",
        "customer_name": "Marcus Vance",
        "customer_email": "marcus.vance@example.com",
        "customer_phone": "+91 9123456780",
        "project_name": "Vance BioTech Portal",
        "project_description": "Clean presentation website with interactive clinical trials directory.",
        "reference_website": "https://vancebiotech.com",
        "selected_designs": ["DSGN-MIN-01"],
        "customization": {
            "primary_color": "#2563EB",
            "secondary_color": "#0F172A",
            "theme_mode": "light",
            "typography_preference": "Plus Jakarta Sans + Inter",
            "animation_preference": "Smooth & Subtle",
            "layout_preference": "Modern Grid",
            "platform_preference": "desktop-first",
        },
        "features": ["Responsive design", "Contact Form"],
    }

    response = client.post("/api/quotation", json=payload)
    assert response.status_code == 201
    data = response.get_json()

    # Exact expected confirmation message
    assert data["status"] == "success"
    assert data["message"] == "Thank you for your interest! Your project request has been successfully submitted. I will review your requirements and get back to you."
    assert "reference_id" in data
    assert data["reference_id"].startswith("QT-")
    assert "email_status" not in data

    # Verify database persistence
    saved = QuotationRequest.query.filter_by(reference_id=data["reference_id"]).first()
    assert saved is not None
    assert saved.customer_email == "marcus.vance@example.com"
    assert saved.customer_name == "Marcus Vance"
    assert saved.project_type == "Business Website"
    assert saved.status == "new"


def test_all_email_endpoints_removed_and_return_404(client, app):
    """Verify that all email proposal, preview, and resend endpoints have been removed."""
    _login_admin(client)

    with app.app_context():
        quote = QuotationRequest(
            reference_id="QT-NOEMAIL01",
            project_type="SaaS Platform",
            budget_range="₹25,000–₹50,000",
            timeline="2 Weeks",
            customer_name="Diana Prince",
            customer_email="diana@example.com",
            project_name="Themyscira Systems",
            project_description="High availability project management dashboard.",
            status="new",
        )
        db.session.add(quote)
        db.session.commit()
        quote_id = quote.id

    # 1. Preview quotation email endpoint removed
    res_prev = client.post(f"/admin/quotations/{quote_id}/preview-email")
    assert res_prev.status_code == 404

    # 2. Send quotation email endpoint removed
    res_send = client.post(f"/admin/quotations/{quote_id}/send-email")
    assert res_send.status_code == 404

    # 3. Resend acknowledgement endpoint removed
    res_resend = client.post(f"/admin/quotations/{quote_id}/resend-acknowledgement")
    assert res_resend.status_code == 404


def test_all_10_quotation_statuses_update_without_email(client, app):
    """Changing any quotation status persists directly to database without mailing triggers."""
    _login_admin(client)

    statuses = [
        "new",
        "reviewing",
        "requirements_clarification",
        "quotation_prepared",
        "quotation_sent",
        "negotiation",
        "accepted",
        "rejected",
        "completed",
        "archived",
    ]

    with app.app_context():
        quote = QuotationRequest(
            reference_id="QT-STATUS10",
            project_type="Portfolio Website",
            budget_range="₹10,000–₹25,000",
            timeline="1 Week",
            customer_name="Bruce Wayne",
            customer_email="bruce.wayne@example.com",
            project_name="Wayne Portfolio",
            project_description="Private technology holdings overview.",
            status="new",
        )
        db.session.add(quote)
        db.session.commit()
        quote_id = quote.id

    for st in statuses:
        res = client.post(
            f"/admin/quotations/{quote_id}/status",
            data={
                "csrf_token": "valid-test-csrf-token",
                "status": st,
                "proposed_amount": "₹45,000",
                "estimated_delivery": "10 days",
                "comments": f"Status transitioned to {st}",
            },
            follow_redirects=True,
        )
        assert res.status_code == 200

        with app.app_context():
            updated = db.session.get(QuotationRequest, quote_id)
            assert updated.status == st
            assert updated.proposed_amount == "₹45,000"
            assert updated.customer_email == "bruce.wayne@example.com"


def test_contact_messages_saved_and_followup_notes_without_email(client, app):
    """Contact messages save directly to database, and admin replies record notes without mailing."""
    # 1. Public user submits inquiry
    with client.session_transaction() as sess:
        sess["_csrf_token"] = "public-test-csrf"

    res_inq = client.post(
        "/api/contact",
        json={
            "csrf_token": "public-test-csrf",
            "name": "Selina Kyle",
            "email": "selina.kyle@example.com",
            "subject": "Security Consulting Inquiry",
            "message": "Need advice on cloud encryption infrastructure.",
        },
    )
    assert res_inq.status_code == 201
    msg_id = res_inq.get_json()["id"]

    with app.app_context():
        msg = db.session.get(ContactMessage, msg_id)
        assert msg is not None
        assert msg.email == "selina.kyle@example.com"
        assert msg.status == "unread"

    # 2. Admin records follow-up note (replaces outgoing email reply)
    _login_admin(client)
    res_note = client.post(
        f"/admin/contact-messages/{msg_id}/reply",
        data={
            "csrf_token": "valid-test-csrf-token",
            "reply_message": "Consulted on phone; proposed audit scheduled for next month.",
        },
        follow_redirects=True,
    )
    assert res_note.status_code == 200

    with app.app_context():
        updated_msg = db.session.get(ContactMessage, msg_id)
        assert updated_msg.status == "replied"
        assert "proposed audit scheduled" in updated_msg.reply_content
        assert updated_msg.replied_at is not None


def test_admin_quotation_detail_renders_without_email_buttons_or_modals(client, app):
    """Admin quotation detail page preserves customer email as contact info with no mailing UI."""
    _login_admin(client)

    with app.app_context():
        quote = QuotationRequest(
            reference_id="QT-CLEANUI01",
            project_type="Web Application",
            budget_range="₹25,000–₹50,000",
            timeline="2-3 Weeks",
            customer_name="Hal Jordan",
            customer_email="hal.jordan@example.com",
            project_name="Sector 2814 Monitor",
            project_description="Real-time sensor telemetry platform.",
            status="new",
        )
        db.session.add(quote)
        db.session.commit()
        quote_id = quote.id

    res = client.get(f"/admin/quotations/{quote_id}")
    assert res.status_code == 200
    html = res.data.decode("utf-8")

    # Customer email is displayed as ordinary contact info
    assert "hal.jordan@example.com" in html
    assert "mailto:hal.jordan@example.com" in html

    # Outgoing mailing buttons and modals must NOT be present
    assert "Send Quotation Email" not in html
    assert "Resend Acknowledgement Email" not in html
    assert "id=\"email-proposal-modal\"" not in html
    assert "id=\"resend-ack-modal\"" not in html
    assert "previewEmailContent" not in html
    assert "openEmailProposalModal" not in html
    assert "openResendAckModal" not in html


def test_no_email_services_or_dependencies_loaded(app):
    """Verify that backend services contain zero email sending modules."""
    import sys
    assert "backend.services.email_service" not in sys.modules
    assert "backend.services.resend_email" not in sys.modules

    # Config has no RESEND or SMTP variables
    assert "RESEND_API_KEY" not in app.config
    assert "SMTP_HOST" not in app.config
