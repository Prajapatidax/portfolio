import pytest
from backend import db
from backend.models.admin import AdminUser
from backend.models.quotation import QuotationRequest
from backend.models.design import DesignCategory, DesignTemplate
from backend.models.contact import ContactMessage
from backend.models.notification import AdminNotification
from backend.models.activity import AdminActivityLog
from backend.models.settings import PortfolioSetting


@pytest.fixture
def auth_client(client, app):
    """Client authenticated as administrator."""
    with app.app_context():
        admin = AdminUser.query.filter_by(email="admin@prajapatidax.co.in").first()
        if not admin:
            admin = AdminUser(name="Dax Prajapati", email="admin@prajapatidax.co.in", is_active=True)
            admin.set_password("AdminTestPassword123!")
            db.session.add(admin)
            db.session.commit()
        admin_id = admin.id

    with client.session_transaction() as sess:
        sess["admin_id"] = admin_id
        sess["admin_name"] = "Dax Prajapati"
        sess["admin_email"] = "admin@prajapatidax.co.in"
        sess["_csrf_token"] = "valid-test-csrf-token"
    return client


def test_admin_control_center_navigation_and_routes(auth_client):
    """Verify all 8 primary admin modules return HTTP 200 for authenticated admin."""
    routes = [
        "/admin/dashboard",
        "/admin/quotations",
        "/admin/designs",
        "/admin/categories",
        "/admin/contact-messages",
        "/admin/media",
        "/admin/activity",
        "/admin/settings",
    ]
    for r in routes:
        res = auth_client.get(r)
        assert res.status_code == 200, f"Route {r} must return 200 for authenticated admin"


def test_quotation_crm_detail_and_workflow(auth_client, app):
    """Verify quotation detail view, status update, priority change, and note persistence."""
    with app.app_context():
        quote = QuotationRequest(
            reference_id="QT-TEST99",
            customer_name="Samantha Ray",
            customer_email="samantha@example.com",
            customer_phone="+1 555-0199",
            project_type="SaaS Platform",
            project_name="Fintech Ledger App",
            project_description="High-frequency transaction monitoring dashboard with dark mode.",
            budget_range="₹50,000+",
            timeline="3–4 weeks",
            status="new",
            priority="normal",
        )
        db.session.add(quote)
        db.session.commit()
        quote_id = quote.id

    # 1. View Detail
    res = auth_client.get(f"/admin/quotations/{quote_id}")
    assert res.status_code == 200
    assert b"Fintech Ledger App" in res.data
    assert b"QT-TEST99" in res.data

    # 2. Update Status and proposed amount
    res_status = auth_client.post(
        f"/admin/quotations/{quote_id}/status",
        data={
            "csrf_token": "valid-test-csrf-token",
            "status": "under_review",
            "proposed_amount": "₹65,000",
            "estimated_delivery": "21 days",
            "comments": "Specifications verified with lead engineer.",
        },
        follow_redirects=True,
    )
    assert res_status.status_code == 200

    with app.app_context():
        q_updated = db.session.get(QuotationRequest, quote_id)
        assert q_updated.status == "under_review"
        assert q_updated.proposed_amount == "₹65,000"
        assert len(q_updated.status_history) >= 1

    # 3. Update Priority
    res_pri = auth_client.post(
        f"/admin/quotations/{quote_id}/priority",
        data={"csrf_token": "valid-test-csrf-token", "priority": "urgent"},
        follow_redirects=True,
    )
    assert res_pri.status_code == 200
    with app.app_context():
        assert db.session.get(QuotationRequest, quote_id).priority == "urgent"

    # 4. Add Internal Note
    res_note = auth_client.post(
        f"/admin/quotations/{quote_id}/note",
        data={"csrf_token": "valid-test-csrf-token", "note_text": "Spoke on call; confirmed deadline requirements."},
        follow_redirects=True,
    )
    assert res_note.status_code == 200
    with app.app_context():
        q_noted = db.session.get(QuotationRequest, quote_id)
        assert len(q_noted.notes) == 1
        assert "Spoke on call" in q_noted.notes[0].note_text


def test_quotation_crm_status_updates_without_email(auth_client, app):
    """Test that quotation status updates occur directly in the database with no email routes."""
    with app.app_context():
        quote = QuotationRequest.query.filter_by(reference_id="QT-TEST99").first()
        if not quote:
            quote = QuotationRequest(
                reference_id="QT-TEST99",
                customer_name="Samantha Ray",
                customer_email="samantha@example.com",
                project_type="SaaS Platform",
                project_name="Fintech Ledger App",
                project_description="High-frequency transaction monitoring dashboard.",
                budget_range="₹50,000+",
                timeline="3–4 weeks",
                status="new",
            )
            db.session.add(quote)
            db.session.commit()
        quote_id = quote.id

    # 1. Verify removed email routes return 404
    res_prev = auth_client.post(f"/admin/quotations/{quote_id}/preview-email")
    assert res_prev.status_code == 404

    res_send = auth_client.post(f"/admin/quotations/{quote_id}/send-email")
    assert res_send.status_code == 404

    res_resend = auth_client.post(f"/admin/quotations/{quote_id}/resend-acknowledgement")
    assert res_resend.status_code == 404

    # 2. Update status to 'quotation_sent' directly via CRM status control
    res_status = auth_client.post(
        f"/admin/quotations/{quote_id}/status",
        data={
            "csrf_token": "valid-test-csrf-token",
            "status": "quotation_sent",
            "proposed_amount": "₹60,000",
            "estimated_delivery": "18 days",
            "comments": "Quotation prepared and finalized internally.",
        },
        follow_redirects=True,
    )
    assert res_status.status_code == 200

    with app.app_context():
        q_sent = db.session.get(QuotationRequest, quote_id)
        assert q_sent.status == "quotation_sent"
        assert q_sent.proposed_amount == "₹60,000"
        assert q_sent.customer_email == "samantha@example.com"


def test_category_management_lifecycle(auth_client, app):
    """Test creating, editing, and deleting a design category."""
    # 1. Create Category
    res_create = auth_client.post(
        "/admin/categories",
        data={
            "csrf_token": "valid-test-csrf-token",
            "name": "Web3 & Blockchain",
            "slug": "web3-blockchain",
            "description": "Decentralized and crypto-native landing page layouts.",
            "display_order": 99,
        },
        follow_redirects=True,
    )
    assert res_create.status_code == 200

    with app.app_context():
        cat = DesignCategory.query.filter_by(slug="web3-blockchain").first()
        assert cat is not None
        cat_id = cat.id

    # 2. Edit Category
    res_edit = auth_client.post(
        f"/admin/categories/{cat_id}/edit",
        data={
            "csrf_token": "valid-test-csrf-token",
            "name": "Web3 & Decentralized",
            "description": "Updated crypto aesthetics.",
            "display_order": 50,
            "is_active": "1",
        },
        follow_redirects=True,
    )
    assert res_edit.status_code == 200

    with app.app_context():
        cat_edited = db.session.get(DesignCategory, cat_id)
        assert cat_edited.name == "Web3 & Decentralized"
        assert cat_edited.display_order == 50

    # 3. Delete Category
    res_del = auth_client.post(
        f"/admin/categories/{cat_id}/delete",
        data={"csrf_token": "valid-test-csrf-token"},
        follow_redirects=True,
    )
    assert res_del.status_code == 200

    with app.app_context():
        assert db.session.get(DesignCategory, cat_id) is None


def test_contact_messages_inquiry_and_reply(auth_client, client, app):
    """Test submitting contact message, viewing it in admin, and replying."""
    # 1. Public user submits inquiry via /api/contact
    with client.session_transaction() as sess:
        sess["_csrf_token"] = "public-test-csrf"

    res_inq = client.post(
        "/api/contact",
        json={
            "csrf_token": "public-test-csrf",
            "name": "Liam Vance",
            "email": "liam.vance@example.com",
            "subject": "Cybersecurity Architecture Consultation",
            "message": "Looking to schedule a penetration testing review for our cloud APIs.",
        },
    )
    assert res_inq.status_code == 201
    msg_id = res_inq.get_json()["id"]

    # 2. Admin views inquiry details
    res_view = auth_client.get(f"/admin/contact-messages/{msg_id}")
    assert res_view.status_code == 200
    assert res_view.get_json()["message"]["name"] == "Liam Vance"

    # 3. Admin sends reply
    res_reply = auth_client.post(
        f"/admin/contact-messages/{msg_id}/reply",
        data={
            "csrf_token": "valid-test-csrf-token",
            "reply_message": "Hello Liam, thank you for reaching out. I would be happy to discuss an audit schedule.",
        },
        follow_redirects=True,
    )
    assert res_reply.status_code == 200

    with app.app_context():
        msg_obj = db.session.get(ContactMessage, msg_id)
        assert msg_obj.status == "replied"
        assert msg_obj.replied_at is not None


def test_admin_notifications_api(auth_client, app):
    """Test notification listing and mark-as-read endpoints."""
    with app.app_context():
        notif = AdminNotification(
            title="System Alert",
            message="Database backup completed successfully.",
            category="system",
            is_read=False,
        )
        db.session.add(notif)
        db.session.commit()
        notif_id = notif.id

    # 1. List notifications
    res = auth_client.get("/admin/api/notifications")
    assert res.status_code == 200
    data = res.get_json()
    assert data["unread_count"] >= 1

    # 2. Mark specific read
    res_read = auth_client.post(f"/admin/api/notifications/{notif_id}/read")
    assert res_read.status_code == 200

    # 3. Mark all read
    res_all = auth_client.post("/admin/api/notifications/read-all")
    assert res_all.status_code == 200
    assert res_all.get_json()["unread_count"] == 0


def test_admin_settings_password_and_portfolio_config(auth_client, app):
    """Test updating portfolio settings and changing admin password."""
    # 1. Update Portfolio Settings
    res_set = auth_client.post(
        "/admin/settings",
        data={
            "csrf_token": "valid-test-csrf-token",
            "action": "portfolio_settings",
            "contact_email": "dax.engineering@prajapatidax.co.in",
            "default_quotation_status": "under_review",
            "notify_email_quotes": "1",
        },
        follow_redirects=True,
    )
    assert res_set.status_code == 200

    with app.app_context():
        assert PortfolioSetting.get("contact_email") == "dax.engineering@prajapatidax.co.in"
        assert PortfolioSetting.get("default_quotation_status") == "under_review"

    # 2. Change Admin Password
    res_pass = auth_client.post(
        "/admin/settings",
        data={
            "csrf_token": "valid-test-csrf-token",
            "action": "change_password",
            "current_password": "AdminTestPassword123!",
            "new_password": "NewAdminPass2026!Secure",
            "confirm_password": "NewAdminPass2026!Secure",
        },
        follow_redirects=True,
    )
    assert res_pass.status_code == 200

    with app.app_context():
        admin = AdminUser.query.filter_by(email="admin@prajapatidax.co.in").first()
        assert admin.check_password("NewAdminPass2026!Secure")
        assert not admin.check_password("AdminTestPassword123!")
        # Reset back for subsequent test runs
        admin.set_password("AdminTestPassword123!")
        db.session.commit()
