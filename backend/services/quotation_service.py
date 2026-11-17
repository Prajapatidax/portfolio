import secrets
import string
from typing import Dict, Any, Tuple
from backend import db
from backend.models.quotation import (
    QuotationRequest,
    QuotationSelectedDesign,
    QuotationCustomization,
    QuotationFeature,
    QuotationStatusHistory,
    AdminNote,
)
from backend.models.design import DesignTemplate
from backend.utils.security import sanitize_text
from backend.utils.validators import validate_quotation_payload


def generate_unique_reference_id() -> str:
    """Generate a clean unique quotation reference code like QT-A9C3F8."""
    chars = string.ascii_uppercase + string.digits
    for _ in range(20):
        code = "QT-" + "".join(secrets.choice(chars) for _ in range(6))
        if not QuotationRequest.query.filter_by(reference_id=code).first():
            return code
    # Fallback with timestamp suffix if collisions happen
    return f"QT-{secrets.token_hex(4).upper()}"


def create_quotation(data: Dict[str, Any], ip_address: str = None, user_agent: str = None) -> Tuple[bool, Any]:
    """Validate, sanitize, and save a full quotation request in the database."""
    is_valid, errors = validate_quotation_payload(data)
    if not is_valid:
        return False, errors

    # Check for recent identical submission to prevent double-click duplicates
    existing = QuotationRequest.query.filter_by(
        customer_email=data.get("customer_email", "").strip().lower(),
        project_name=sanitize_text(data.get("project_name", "")),
    ).order_by(QuotationRequest.created_at.desc()).first()

    if existing and existing.created_at:
        # Check if submitted within last 60 seconds
        from datetime import datetime, timezone
        diff = (datetime.now(timezone.utc) - existing.created_at.replace(tzinfo=timezone.utc)).total_seconds()
        if diff < 60:
            return True, existing

    reference_id = generate_unique_reference_id()

    # Create Quotation Request
    quotation = QuotationRequest(
        reference_id=reference_id,
        project_type=sanitize_text(data.get("project_type", "")),
        budget_range=sanitize_text(data.get("budget_range", "")),
        timeline=sanitize_text(data.get("timeline", "")),
        customer_name=sanitize_text(data.get("customer_name", "")),
        customer_email=data.get("customer_email", "").strip().lower(),
        customer_phone=sanitize_text(data.get("customer_phone", "")),
        project_name=sanitize_text(data.get("project_name", "")),
        project_description=sanitize_text(data.get("project_description", "")),
        reference_website=sanitize_text(data.get("reference_website", "")),
        status="new",
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.session.add(quotation)
    db.session.flush()

    # Link selected designs
    selected_design_ids = data.get("selected_designs", [])
    if isinstance(selected_design_ids, list):
        for d_id in selected_design_ids:
            if not d_id:
                continue
            template = DesignTemplate.query.filter(
                (DesignTemplate.design_id == str(d_id)) | (DesignTemplate.slug == str(d_id))
            ).first()

            design_record = QuotationSelectedDesign(
                quotation_id=quotation.id,
                design_template_id=template.id if template else None,
                design_id_snapshot=template.design_id if template else str(d_id),
                design_name_snapshot=template.name if template else f"Custom Selection ({d_id})",
                category_snapshot=template.category.name if (template and template.category) else "Custom",
            )
            db.session.add(design_record)

    # Save customization preferences
    cust_data = data.get("customization", {}) or {}
    customization = QuotationCustomization(
        quotation_id=quotation.id,
        primary_color=sanitize_text(cust_data.get("primary_color", "#2563EB"), 50),
        secondary_color=sanitize_text(cust_data.get("secondary_color", "#0F172A"), 50),
        theme_mode=sanitize_text(cust_data.get("theme_mode", "light"), 50),
        typography_preference=sanitize_text(cust_data.get("typography_preference", "Plus Jakarta Sans + Inter"), 100),
        animation_preference=sanitize_text(cust_data.get("animation_preference", "Smooth & Subtle"), 50),
        layout_preference=sanitize_text(cust_data.get("layout_preference", "Modern Grid"), 50),
        platform_preference=sanitize_text(cust_data.get("platform_preference", "desktop-first"), 50),
    )
    db.session.add(customization)

    # Save features
    features_list = data.get("features", [])
    if isinstance(features_list, list):
        for feat in features_list:
            if feat:
                f_record = QuotationFeature(
                    quotation_id=quotation.id,
                    feature_key=sanitize_text(feat).lower().replace(" ", "_"),
                    feature_label=sanitize_text(feat),
                )
                db.session.add(f_record)

    # Initial status history
    history = QuotationStatusHistory(
        quotation_id=quotation.id,
        old_status=None,
        new_status="new",
        comments="Quotation request submitted by customer via online wizard.",
    )
    db.session.add(history)
    db.session.commit()

    # Trigger admin notification & audit log
    try:
        from backend.services.activity_service import notify_admin, log_activity
        notify_admin(
            title=f"New Quotation #{quotation.reference_id}",
            message=f"From {quotation.customer_name} ({quotation.project_type}) - Budget: {quotation.budget_range}",
            category="quotation",
            link_url=f"/admin/quotations/{quotation.id}",
        )
        log_activity(
            action_type="quotation_submitted",
            description=f"Quotation #{quotation.reference_id} submitted by {quotation.customer_email}",
            record_id=str(quotation.id),
            record_type="quotation",
            ip_address=ip_address,
        )
    except Exception as e:
        pass

    return True, quotation


def update_quotation_status(
    quotation_id: int,
    new_status: str,
    admin_id: int,
    proposed_amount: str = None,
    estimated_delivery: str = None,
    comments: str = None,
) -> bool:
    quotation = db.session.get(QuotationRequest, quotation_id)
    if not quotation:
        return False

    old_status = quotation.status
    quotation.status = new_status

    if proposed_amount is not None:
        quotation.proposed_amount = sanitize_text(proposed_amount, 100)
    if estimated_delivery is not None:
        quotation.estimated_delivery = sanitize_text(estimated_delivery, 100)

    history = QuotationStatusHistory(
        quotation_id=quotation.id,
        old_status=old_status,
        new_status=new_status,
        changed_by_admin_id=admin_id,
        comments=sanitize_text(comments) if comments else f"Status changed from {old_status} to {new_status}",
    )
    db.session.add(history)
    db.session.commit()

    try:
        from backend.services.activity_service import log_activity, notify_admin
        log_activity(
            action_type="quotation_status_update",
            description=f"Quotation #{quotation.reference_id} status updated from '{old_status}' to '{new_status}'",
            admin_id=admin_id,
            record_id=str(quotation.id),
            record_type="quotation",
        )
        if new_status in ("accepted", "quotation_sent"):
            notify_admin(
                title=f"Quotation #{quotation.reference_id} is {new_status.replace('_', ' ').title()}",
                message=f"Customer: {quotation.customer_name} | Amount: {quotation.proposed_amount or 'N/A'}",
                category="quotation",
                link_url=f"/admin/quotations/{quotation.id}",
            )
    except Exception:
        pass

    return True


def update_quotation_priority(quotation_id: int, priority: str, admin_id: int) -> bool:
    quotation = db.session.get(QuotationRequest, quotation_id)
    if not quotation or priority not in ("low", "normal", "high", "urgent"):
        return False
    old_priority = quotation.priority
    quotation.priority = priority
    db.session.commit()

    try:
        from backend.services.activity_service import log_activity
        log_activity(
            action_type="quotation_priority_update",
            description=f"Quotation #{quotation.reference_id} priority changed from {old_priority} to {priority}",
            admin_id=admin_id,
            record_id=str(quotation.id),
            record_type="quotation",
        )
    except Exception:
        pass
    return True


def toggle_quotation_archive(quotation_id: int, admin_id: int) -> bool:
    quotation = db.session.get(QuotationRequest, quotation_id)
    if not quotation:
        return False
    quotation.is_archived = not quotation.is_archived
    db.session.commit()

    try:
        from backend.services.activity_service import log_activity
        status_word = "archived" if quotation.is_archived else "unarchived"
        log_activity(
            action_type=f"quotation_{status_word}",
            description=f"Quotation #{quotation.reference_id} was {status_word}",
            admin_id=admin_id,
            record_id=str(quotation.id),
            record_type="quotation",
        )
    except Exception:
        pass
    return quotation.is_archived


def add_admin_note(quotation_id: int, admin_id: int, note_text: str):
    quotation = db.session.get(QuotationRequest, quotation_id)
    if not quotation or not note_text:
        return None

    note = AdminNote(
        quotation_id=quotation.id,
        admin_id=admin_id,
        note_text=sanitize_text(note_text),
    )
    db.session.add(note)
    db.session.commit()

    try:
        from backend.services.activity_service import log_activity
        log_activity(
            action_type="quotation_note_added",
            description=f"Added internal note to quotation #{quotation.reference_id}",
            admin_id=admin_id,
            record_id=str(quotation.id),
            record_type="quotation",
        )
    except Exception:
        pass

    return note
