import os
import io
import time
import uuid
from datetime import datetime, timezone, timedelta
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    jsonify,
    abort,
    current_app,
)
from werkzeug.utils import secure_filename
from sqlalchemy import func, desc

from backend import db
from backend.models.admin import AdminUser, AdminLoginActivity
from backend.models.quotation import (
    QuotationRequest,
    QuotationSelectedDesign,
    QuotationCustomization,
    QuotationFeature,
    QuotationStatusHistory,
    AdminNote,
)
from backend.models.design import DesignCategory, DesignTemplate, DesignPreviewAsset
from backend.models.contact import ContactMessage
from backend.models.notification import AdminNotification
from backend.models.activity import AdminActivityLog
from backend.models.settings import PortfolioSetting

from backend.services.auth_service import authenticate_admin, logout_admin
from backend.services.quotation_service import (
    update_quotation_status,
    update_quotation_priority,
    toggle_quotation_archive,
    add_admin_note,
)
from backend.services.activity_service import (
    log_activity,
    notify_admin,
    get_unread_notifications_count,
    get_recent_notifications,
    mark_notification_as_read,
    mark_all_notifications_as_read,
)
from backend.services.neon_storage import storage_service

from backend.utils.decorators import admin_required, rate_limit
from backend.utils.security import get_client_ip, sanitize_text, validate_csrf_token

admin_bp = Blueprint("admin", __name__)


# ------------------------------------------------------------------------------
# CONTEXT PROCESSOR FOR ADMIN VIEWS
# ------------------------------------------------------------------------------
@admin_bp.context_processor
def inject_admin_context():
    """Injects admin user state and unread notifications count across all admin views."""
    admin_id = session.get("admin_id")
    unread_notifs = get_unread_notifications_count() if admin_id else 0
    unread_contacts = ContactMessage.query.filter_by(status="unread").count() if admin_id else 0
    return {
        "admin_name": session.get("admin_name", "Dax Prajapati"),
        "admin_email": session.get("admin_email", "admin@prajapatidax.co.in"),
        "unread_notifications_count": unread_notifs,
        "unread_contacts_count": unread_contacts,
        "current_route": request.endpoint or "",
    }


# ------------------------------------------------------------------------------
# STRICT ROUTING RULES: Invalid admin entry points MUST return HTTP 404
# ------------------------------------------------------------------------------
@admin_bp.route("/admin")
@admin_bp.route("/admin/")
@admin_bp.route("/admin/login")
@admin_bp.route("/admin/login/")
@admin_bp.route("/login/admin")
@admin_bp.route("/login/admin/")
def decoy_admin_routes():
    """These routes MUST return custom 404 and NEVER redirect to admin login."""
    abort(404)


# ------------------------------------------------------------------------------
# VALID SECRET ADMIN LOGIN ROUTE
# ------------------------------------------------------------------------------
@admin_bp.route("/admin/login/version/101", methods=["GET", "POST"])
@rate_limit("admin_login", max_attempts=5, window_seconds=600)
def admin_login():
    if session.get("admin_id"):
        return redirect(url_for("admin.dashboard"))

    error_message = None

    if request.method == "POST":
        csrf = request.form.get("csrf_token")
        if not validate_csrf_token(csrf):
            error_message = "Invalid session token. Please reload."
            return render_template("admin/login.html", error=error_message), 400

        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        client_ip = get_client_ip()
        user_agent = (request.user_agent.string or "")[:300]

        success, result = authenticate_admin(email, password, ip_address=client_ip, user_agent=user_agent)

        if success:
            log_activity(
                action_type="login_success",
                description=f"Admin signed in successfully from {client_ip}",
                admin_id=result.id,
                record_id=str(result.id),
                record_type="admin",
                ip_address=client_ip,
            )
            next_url = request.args.get("next")
            if next_url and next_url.startswith("/admin/") and not next_url.startswith("//"):
                return redirect(next_url)
            return redirect(url_for("admin.dashboard"))
        else:
            log_activity(
                action_type="login_failed",
                description=f"Failed admin login attempt for '{email}' from {client_ip} ({result})",
                result="failure",
                ip_address=client_ip,
            )
            error_message = "Invalid email or password credentials."

    return render_template(
        "admin/login.html",
        page_title="Admin Sign In",
        error=error_message,
    )


@admin_bp.route("/admin/logout", methods=["GET", "POST"])
def admin_logout():
    admin_id = session.get("admin_id")
    if admin_id:
        log_activity(
            action_type="logout",
            description="Admin signed out",
            admin_id=admin_id,
            record_id=str(admin_id),
            record_type="admin",
            ip_address=get_client_ip(),
        )
    logout_admin()
    flash("You have been signed out.", "info")
    return redirect(url_for("main.index"))


# ------------------------------------------------------------------------------
# 1. ADMIN DASHBOARD OVERVIEW
# ------------------------------------------------------------------------------
@admin_bp.route("/admin/dashboard")
@admin_required
def dashboard():
    range_filter = request.args.get("range", "30d")
    now = datetime.now(timezone.utc)
    start_date = None

    if range_filter == "7d":
        start_date = now - timedelta(days=7)
    elif range_filter == "30d":
        start_date = now - timedelta(days=30)
    elif range_filter == "90d":
        start_date = now - timedelta(days=90)
    elif range_filter == "1y":
        start_date = now - timedelta(days=365)

    base_query = QuotationRequest.query
    if start_date:
        base_query = base_query.filter(QuotationRequest.created_at >= start_date)

    # Core Metric Counters
    total_quotes = QuotationRequest.query.count()
    new_quotes = QuotationRequest.query.filter_by(status="new").count()
    under_review = QuotationRequest.query.filter(QuotationRequest.status.in_(["under_review", "reviewing"])).count()
    quotation_sent = QuotationRequest.query.filter_by(status="quotation_sent").count()
    accepted = QuotationRequest.query.filter_by(status="accepted").count()
    rejected = QuotationRequest.query.filter_by(status="rejected").count()

    total_templates = DesignTemplate.query.count()
    published_templates = DesignTemplate.query.filter_by(is_published=True).count()
    total_contacts = ContactMessage.query.count()
    unread_contacts = ContactMessage.query.filter_by(status="unread").count()

    # Chart 1: Project Type Distribution
    project_types_raw = db.session.query(
        QuotationRequest.project_type, func.count(QuotationRequest.id)
    ).group_by(QuotationRequest.project_type).all()
    project_type_chart = {
        "labels": [p[0] for p in project_types_raw] if project_types_raw else ["No Data"],
        "data": [p[1] for p in project_types_raw] if project_types_raw else [0],
    }

    # Chart 2: Status Distribution
    status_raw = db.session.query(
        QuotationRequest.status, func.count(QuotationRequest.id)
    ).group_by(QuotationRequest.status).all()
    status_chart = {
        "labels": [s[0].replace("_", " ").title() for s in status_raw] if status_raw else ["No Data"],
        "data": [s[1] for s in status_raw] if status_raw else [0],
    }

    # Chart 3: Budget Range Distribution
    budget_raw = db.session.query(
        QuotationRequest.budget_range, func.count(QuotationRequest.id)
    ).group_by(QuotationRequest.budget_range).all()
    budget_chart = {
        "labels": [b[0] for b in budget_raw] if budget_raw else ["No Data"],
        "data": [b[1] for b in budget_raw] if budget_raw else [0],
    }

    # Recent lists
    recent_quotes = QuotationRequest.query.order_by(QuotationRequest.created_at.desc()).limit(6).all()
    recent_contacts = ContactMessage.query.order_by(ContactMessage.created_at.desc()).limit(5).all()
    recent_activities = AdminActivityLog.query.order_by(AdminActivityLog.created_at.desc()).limit(8).all()

    return render_template(
        "admin/dashboard.html",
        page_title="Admin Control Center | Dashboard",
        stats={
            "total_quotes": total_quotes,
            "new_quotes": new_quotes,
            "under_review": under_review,
            "quotation_sent": quotation_sent,
            "accepted": accepted,
            "rejected": rejected,
            "total_templates": total_templates,
            "published_templates": published_templates,
            "total_contacts": total_contacts,
            "unread_contacts": unread_contacts,
        },
        range_filter=range_filter,
        project_type_chart=project_type_chart,
        status_chart=status_chart,
        budget_chart=budget_chart,
        recent_quotes=recent_quotes,
        recent_contacts=recent_contacts,
        recent_activities=recent_activities,
    )


# ------------------------------------------------------------------------------
# 2. QUOTATION MANAGEMENT CRM
# ------------------------------------------------------------------------------
@admin_bp.route("/admin/quotations")
@admin_required
def quotations_list():
    status_filter = request.args.get("status", "").strip()
    priority_filter = request.args.get("priority", "").strip()
    project_type = request.args.get("project_type", "").strip()
    search_query = request.args.get("q", "").strip()
    archived_filter = request.args.get("archived", "0")
    page = request.args.get("page", 1, type=int)
    sort_order = request.args.get("sort", "desc")
    per_page = 15

    query = QuotationRequest.query

    if archived_filter == "1":
        query = query.filter_by(is_archived=True)
    else:
        query = query.filter_by(is_archived=False)

    if status_filter:
        query = query.filter_by(status=status_filter)
    if priority_filter:
        query = query.filter_by(priority=priority_filter)
    if project_type:
        query = query.filter_by(project_type=project_type)

    if search_query:
        pattern = f"%{search_query}%"
        query = query.filter(
            (QuotationRequest.reference_id.ilike(pattern))
            | (QuotationRequest.customer_name.ilike(pattern))
            | (QuotationRequest.customer_email.ilike(pattern))
            | (QuotationRequest.project_name.ilike(pattern))
        )

    if sort_order == "asc":
        query = query.order_by(QuotationRequest.created_at.asc())
    else:
        query = query.order_by(QuotationRequest.created_at.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    # Status counts for filter chips
    status_counts = {
        "all": QuotationRequest.query.filter_by(is_archived=False).count(),
        "new": QuotationRequest.query.filter_by(status="new", is_archived=False).count(),
        "under_review": QuotationRequest.query.filter(QuotationRequest.status.in_(["under_review", "reviewing"]), QuotationRequest.is_archived == False).count(),
        "quotation_sent": QuotationRequest.query.filter_by(status="quotation_sent", is_archived=False).count(),
        "accepted": QuotationRequest.query.filter_by(status="accepted", is_archived=False).count(),
        "rejected": QuotationRequest.query.filter_by(status="rejected", is_archived=False).count(),
        "archived": QuotationRequest.query.filter_by(is_archived=True).count(),
    }

    return render_template(
        "admin/quotations/list.html",
        page_title="Quotation Requests CRM | Dax Prajapati",
        quotations=pagination.items,
        pagination=pagination,
        status_filter=status_filter,
        priority_filter=priority_filter,
        project_type=project_type,
        search_query=search_query,
        sort_order=sort_order,
        archived_filter=archived_filter,
        status_counts=status_counts,
    )


@admin_bp.route("/admin/quotations/<int:quote_id>", methods=["GET"])
@admin_required
def quotation_detail(quote_id):
    quote = db.get_or_404(QuotationRequest, quote_id)
    if request.is_json:
        return jsonify({"status": "success", "quotation": quote.to_dict()})

    return render_template(
        "admin/quotations/detail.html",
        page_title=f"Quotation #{quote.reference_id} — {quote.customer_name} | Admin",
        quote=quote,
    )


@admin_bp.route("/admin/quotations/<int:quote_id>/status", methods=["POST"])
@admin_required
def update_status(quote_id):
    quote = db.get_or_404(QuotationRequest, quote_id)
    new_status = request.form.get("status") or (request.json.get("status") if request.is_json else "")
    proposed_amount = request.form.get("proposed_amount") or (request.json.get("proposed_amount") if request.is_json else None)
    estimated_delivery = request.form.get("estimated_delivery") or (request.json.get("estimated_delivery") if request.is_json else None)
    comments = request.form.get("comments") or (request.json.get("comments") if request.is_json else None)

    if not new_status:
        if request.is_json:
            return jsonify({"status": "error", "message": "Status is required"}), 400
        flash("Status is required.", "error")
        return redirect(url_for("admin.quotation_detail", quote_id=quote.id))

    admin_id = session.get("admin_id")
    update_quotation_status(
        quotation_id=quote.id,
        new_status=new_status,
        admin_id=admin_id,
        proposed_amount=proposed_amount,
        estimated_delivery=estimated_delivery,
        comments=comments,
    )

    if request.is_json:
        return jsonify({"status": "success", "message": f"Status updated to {new_status}"})
    flash(f"Quotation #{quote.reference_id} status updated to '{new_status.replace('_', ' ').title()}'.", "success")
    return redirect(url_for("admin.quotation_detail", quote_id=quote.id))


@admin_bp.route("/admin/quotations/<int:quote_id>/priority", methods=["POST"])
@admin_required
def update_priority(quote_id):
    quote = db.get_or_404(QuotationRequest, quote_id)
    priority = request.form.get("priority") or (request.json.get("priority") if request.is_json else "normal")
    admin_id = session.get("admin_id")

    update_quotation_priority(quote.id, priority, admin_id)
    if request.is_json:
        return jsonify({"status": "success", "priority": priority})
    flash(f"Priority set to {priority.title()}.", "success")
    return redirect(url_for("admin.quotation_detail", quote_id=quote.id))


@admin_bp.route("/admin/quotations/<int:quote_id>/note", methods=["POST"])
@admin_required
def add_note(quote_id):
    quote = db.get_or_404(QuotationRequest, quote_id)
    note_text = request.form.get("note_text") or (request.json.get("note_text") if request.is_json else "")
    if not note_text.strip():
        if request.is_json:
            return jsonify({"status": "error", "message": "Note text is required"}), 400
        flash("Note text cannot be empty.", "error")
        return redirect(url_for("admin.quotation_detail", quote_id=quote.id))

    admin_id = session.get("admin_id")
    note = add_admin_note(quote.id, admin_id, note_text)

    if request.is_json:
        return jsonify({"status": "success", "note": note.to_dict()})
    flash("Internal note added.", "success")
    return redirect(url_for("admin.quotation_detail", quote_id=quote.id))


@admin_bp.route("/admin/quotations/<int:quote_id>/archive", methods=["POST"])
@admin_required
def archive_quotation(quote_id):
    quote = db.get_or_404(QuotationRequest, quote_id)
    admin_id = session.get("admin_id")
    is_archived = toggle_quotation_archive(quote.id, admin_id)
    status_str = "archived" if is_archived else "restored"

    if request.is_json:
        return jsonify({"status": "success", "is_archived": is_archived, "message": f"Quotation {status_str}"})
    flash(f"Quotation #{quote.reference_id} {status_str}.", "info")
    return redirect(url_for("admin.quotations_list"))


@admin_bp.route("/admin/quotations/<int:quote_id>/delete", methods=["POST"])
@admin_required
def delete_quotation(quote_id):
    quote = db.get_or_404(QuotationRequest, quote_id)
    ref_id = quote.reference_id
    admin_id = session.get("admin_id")

    db.session.delete(quote)
    db.session.commit()

    log_activity(
        action_type="quotation_deleted",
        description=f"Permanently deleted quotation #{ref_id}",
        admin_id=admin_id,
        record_id=str(quote_id),
        record_type="quotation",
    )

    if request.is_json:
        return jsonify({"status": "success", "message": f"Quotation #{ref_id} deleted."})
    flash(f"Quotation #{ref_id} deleted successfully.", "success")
    return redirect(url_for("admin.quotations_list"))


# ------------------------------------------------------------------------------
# 3. UI DESIGN TEMPLATE MANAGEMENT
# ------------------------------------------------------------------------------
@admin_bp.route("/admin/designs", methods=["GET", "POST"])
@admin_required
def designs_list():
    if request.method == "POST":
        csrf = request.form.get("csrf_token")
        if not validate_csrf_token(csrf):
            flash("Invalid session token.", "error")
            return redirect(url_for("admin.designs_list"))

        name = sanitize_text(request.form.get("name", "").strip(), 150)
        category_id = request.form.get("category_id", type=int)
        description = sanitize_text(request.form.get("description", "").strip())
        status = request.form.get("status", "Available")

        if not name or not category_id or not description:
            flash("Name, category, and description are required.", "error")
            return redirect(url_for("admin.designs_list"))

        design_count = DesignTemplate.query.count() + 1
        design_id = f"DSGN-USR-{design_count:02d}"
        base_slug = name.lower().replace(" ", "-").replace("&", "and")
        slug = f"{base_slug}-{uuid.uuid4().hex[:4]}"

        template = DesignTemplate(
            design_id=design_id,
            slug=slug,
            name=name,
            category_id=category_id,
            description=description,
            status=status,
            is_published=False,  # Unset until assets exist
            color_palette=[
                {"name": "Primary", "hex": request.form.get("color_primary", "#2563EB")},
                {"name": "Secondary", "hex": request.form.get("color_secondary", "#0F172A")},
            ],
            typography={
                "heading": request.form.get("font_heading", "Plus Jakarta Sans"),
                "body": request.form.get("font_body", "Inter"),
            },
            features=[f.strip() for f in request.form.get("features", "").split("\n") if f.strip()],
            pages_available=["Home", "Services", "About", "Contact"],
        )
        db.session.add(template)
        db.session.commit()

        log_activity(
            action_type="template_created",
            description=f"Created template '{name}' ({design_id})",
            admin_id=session.get("admin_id"),
            record_id=str(template.id),
            record_type="template",
        )
        flash(f"Template '{name}' created. Please upload laptop, tablet, and mobile reference images to publish.", "success")
        return redirect(url_for("admin.design_edit", design_id=template.id))

    categories = DesignCategory.query.order_by(DesignCategory.display_order.asc()).all()
    templates = DesignTemplate.query.order_by(DesignTemplate.id.asc()).all()

    return render_template(
        "admin/designs/list.html",
        page_title="UI Design Templates | Dax Prajapati Admin",
        templates=templates,
        categories=categories,
    )


@admin_bp.route("/admin/designs/<int:design_id>", methods=["GET", "POST"])
@admin_required
def design_edit(design_id):
    tpl = db.get_or_404(DesignTemplate, design_id)
    categories = DesignCategory.query.order_by(DesignCategory.display_order.asc()).all()

    if request.method == "POST":
        csrf = request.form.get("csrf_token")
        if not validate_csrf_token(csrf):
            flash("Invalid session token.", "error")
            return redirect(url_for("admin.design_edit", design_id=tpl.id))

        name = sanitize_text(request.form.get("name", "").strip())
        description = sanitize_text(request.form.get("description", "").strip())
        category_id = request.form.get("category_id", type=int)
        status = request.form.get("status", tpl.status)
        is_published = request.form.get("is_published") == "1"

        if is_published and not (tpl.get_asset("laptop") and tpl.get_asset("tablet") and tpl.get_asset("mobile")):
            flash("Cannot publish template: laptop, tablet, and mobile reference images must all be uploaded first.", "warning")
            is_published = False

        if name:
            tpl.name = name
        if description:
            tpl.description = description
        if category_id:
            tpl.category_id = category_id
        if status:
            tpl.status = status
        tpl.is_published = is_published

        # Colors & Fonts
        tpl.color_palette = [
            {"name": "Primary", "hex": request.form.get("color_primary", "#2563EB")},
            {"name": "Secondary", "hex": request.form.get("color_secondary", "#0F172A")},
        ]
        tpl.typography = {
            "heading": request.form.get("font_heading", "Plus Jakarta Sans"),
            "body": request.form.get("font_body", "Inter"),
        }

        features_raw = request.form.get("features", "")
        if features_raw:
            tpl.features = [f.strip() for f in features_raw.split("\n") if f.strip()]

        db.session.commit()
        log_activity(
            action_type="template_updated",
            description=f"Updated template '{tpl.name}' ({tpl.design_id})",
            admin_id=session.get("admin_id"),
            record_id=str(tpl.id),
            record_type="template",
        )
        flash(f"Template '{tpl.name}' updated successfully.", "success")
        return redirect(url_for("admin.design_edit", design_id=tpl.id))

    return render_template(
        "admin/designs/edit.html",
        page_title=f"Edit Template: {tpl.name} | Admin",
        tpl=tpl,
        categories=categories,
    )


@admin_bp.route("/admin/designs/<int:design_id>/upload-asset", methods=["POST"])
@admin_required
def upload_template_asset(design_id):
    tpl = db.get_or_404(DesignTemplate, design_id)
    csrf = request.form.get("csrf_token")
    if not validate_csrf_token(csrf):
        flash("Invalid session token.", "error")
        return redirect(url_for("admin.design_edit", design_id=tpl.id))

    if "asset_file" not in request.files:
        flash("No file provided for upload.", "error")
        return redirect(url_for("admin.design_edit", design_id=tpl.id))

    file = request.files["asset_file"]
    if not file or file.filename == "":
        flash("No file selected.", "error")
        return redirect(url_for("admin.design_edit", design_id=tpl.id))

    image_type = request.form.get("image_type", "laptop")
    if image_type not in ("laptop", "desktop", "tablet", "mobile"):
        flash("Invalid device target specified.", "error")
        return redirect(url_for("admin.design_edit", design_id=tpl.id))

    cat_slug = tpl.category.slug if tpl.category else "general"
    timestamp = int(time.time())
    object_key = f"ui-templates/{cat_slug}/{tpl.slug}-{image_type}-{timestamp}.webp"

    try:
        raw_bytes = file.read()
        if image_type in ("laptop", "desktop"):
            target_w, target_h = 1920, 1200
        elif image_type == "tablet":
            target_w, target_h = 1600, 1200
        else:
            target_w, target_h = 1080, 2340

        # Upload and optimize to WebP directly into Neon S3 bucket photos
        meta = storage_service.upload_file(
            raw_bytes,
            object_key,
            optimize=True,
            target_width=target_w,
            target_height=target_h,
        )

        # Check existing asset
        asset = DesignPreviewAsset.query.filter_by(design_id=tpl.design_id, image_type=image_type).first()
        old_key = asset.object_key if asset else None

        if not asset:
            asset = DesignPreviewAsset(
                design_id=tpl.design_id,
                image_type=image_type,
                bucket_name="photos",
                object_key=object_key,
                content_type="image/webp",
                file_size=meta["file_size"],
                width=meta["width"],
                height=meta["height"],
            )
            db.session.add(asset)
        else:
            asset.object_key = object_key
            asset.file_size = meta["file_size"]
            asset.width = meta["width"]
            asset.height = meta["height"]

        if image_type in ("laptop", "desktop"):
            tpl.desktop_preview_url = f"/storage/preview/{object_key}"
            tpl.thumbnail_url = f"/storage/preview/{object_key}"
        elif image_type == "mobile":
            tpl.mobile_preview_url = f"/storage/preview/{object_key}"

        db.session.commit()

        # Clean up old object safely if different
        if old_key and old_key != object_key:
            try:
                storage_service.delete_object(old_key)
            except Exception:
                pass

        log_activity(
            action_type="asset_replaced",
            description=f"Replaced {image_type} preview image for '{tpl.name}' in Neon S3",
            admin_id=session.get("admin_id"),
            record_id=str(tpl.id),
            record_type="template",
        )
        flash(f"Successfully uploaded and synced {image_type} image to Neon Object Storage.", "success")
    except Exception as e:
        current_app.logger.error(f"Asset upload error: {e}")
        flash(f"Failed to upload asset: {str(e)}", "error")

    return redirect(url_for("admin.design_edit", design_id=tpl.id))


@admin_bp.route("/admin/designs/<int:design_id>/toggle-status", methods=["POST"])
@admin_required
def toggle_design_status(design_id):
    tpl = db.get_or_404(DesignTemplate, design_id)
    new_published = not tpl.is_published

    if new_published and not (tpl.get_asset("laptop") and tpl.get_asset("tablet") and tpl.get_asset("mobile")):
        if request.is_json:
            return jsonify({"status": "error", "message": "Cannot publish: missing laptop, tablet, or mobile reference images."}), 400
        flash("Cannot publish: missing laptop, tablet, or mobile reference images.", "warning")
        return redirect(url_for("admin.designs_list"))

    tpl.is_published = new_published
    db.session.commit()

    status_str = "published" if tpl.is_published else "hidden"
    log_activity(
        action_type=f"template_{status_str}",
        description=f"Template '{tpl.name}' is now {status_str}",
        admin_id=session.get("admin_id"),
        record_id=str(tpl.id),
        record_type="template",
    )

    if request.is_json:
        return jsonify({"status": "success", "is_published": tpl.is_published, "message": f"Template {status_str}"})
    flash(f"Template '{tpl.name}' is now {status_str}.", "info")
    return redirect(url_for("admin.designs_list"))


@admin_bp.route("/admin/designs/<int:design_id>/delete", methods=["POST"])
@admin_required
def delete_design(design_id):
    tpl = db.get_or_404(DesignTemplate, design_id)
    name = tpl.name
    # Foreign key on quotation_selected_designs is ON DELETE SET NULL, keeping history intact
    db.session.delete(tpl)
    db.session.commit()

    log_activity(
        action_type="template_deleted",
        description=f"Deleted template '{name}'",
        admin_id=session.get("admin_id"),
        record_id=str(design_id),
        record_type="template",
    )
    if request.is_json:
        return jsonify({"status": "success", "message": f"Template '{name}' deleted."})
    flash(f"Template '{name}' deleted.", "success")
    return redirect(url_for("admin.designs_list"))


# ------------------------------------------------------------------------------
# 4. CATEGORY MANAGEMENT
# ------------------------------------------------------------------------------
@admin_bp.route("/admin/categories", methods=["GET", "POST"])
@admin_required
def categories_list():
    if request.method == "POST":
        csrf = request.form.get("csrf_token")
        if not validate_csrf_token(csrf):
            flash("Invalid session token.", "error")
            return redirect(url_for("admin.categories_list"))

        name = sanitize_text(request.form.get("name", "").strip(), 100)
        slug = sanitize_text(request.form.get("slug", "").strip().lower(), 100)
        description = sanitize_text(request.form.get("description", "").strip())
        display_order = request.form.get("display_order", 0, type=int)

        if not name:
            flash("Category name is required.", "error")
            return redirect(url_for("admin.categories_list"))

        if not slug:
            slug = name.lower().replace(" ", "-").replace("&", "and")

        existing = DesignCategory.query.filter_by(slug=slug).first()
        if existing:
            flash(f"Category with slug '{slug}' already exists.", "error")
            return redirect(url_for("admin.categories_list"))

        cat = DesignCategory(
            name=name,
            slug=slug,
            description=description,
            display_order=display_order,
            is_active=True,
        )
        db.session.add(cat)
        db.session.commit()

        log_activity(
            action_type="category_created",
            description=f"Created category '{name}' ({slug})",
            admin_id=session.get("admin_id"),
            record_id=str(cat.id),
            record_type="category",
        )
        flash(f"Category '{name}' created.", "success")
        return redirect(url_for("admin.categories_list"))

    categories = DesignCategory.query.order_by(DesignCategory.display_order.asc()).all()
    return render_template(
        "admin/categories/index.html",
        page_title="Design Categories | Dax Prajapati Admin",
        categories=categories,
    )


@admin_bp.route("/admin/categories/<int:cat_id>/edit", methods=["POST"])
@admin_required
def category_edit(cat_id):
    cat = db.get_or_404(DesignCategory, cat_id)
    csrf = request.form.get("csrf_token")
    if not validate_csrf_token(csrf):
        flash("Invalid session token.", "error")
        return redirect(url_for("admin.categories_list"))

    name = sanitize_text(request.form.get("name", "").strip(), 100)
    description = sanitize_text(request.form.get("description", "").strip())
    display_order = request.form.get("display_order", cat.display_order, type=int)
    is_active = request.form.get("is_active") == "1"

    if name:
        cat.name = name
    cat.description = description
    cat.display_order = display_order
    cat.is_active = is_active
    db.session.commit()

    log_activity(
        action_type="category_updated",
        description=f"Updated category '{cat.name}'",
        admin_id=session.get("admin_id"),
        record_id=str(cat.id),
        record_type="category",
    )
    flash(f"Category '{cat.name}' updated.", "success")
    return redirect(url_for("admin.categories_list"))


@admin_bp.route("/admin/categories/<int:cat_id>/delete", methods=["POST"])
@admin_required
def category_delete(cat_id):
    cat = db.get_or_404(DesignCategory, cat_id)
    attached_templates = DesignTemplate.query.filter_by(category_id=cat.id).count()

    if attached_templates > 0:
        flash(f"Cannot delete category '{cat.name}': {attached_templates} templates are attached. Reassign them first.", "error")
        return redirect(url_for("admin.categories_list"))

    name = cat.name
    db.session.delete(cat)
    db.session.commit()

    log_activity(
        action_type="category_deleted",
        description=f"Deleted category '{name}'",
        admin_id=session.get("admin_id"),
        record_id=str(cat_id),
        record_type="category",
    )
    flash(f"Category '{name}' deleted.", "success")
    return redirect(url_for("admin.categories_list"))


# ------------------------------------------------------------------------------
# 5. CONTACT ENQUIRY MANAGEMENT
# ------------------------------------------------------------------------------
@admin_bp.route("/admin/contact-messages")
@admin_required
def contact_messages_list():
    status_filter = request.args.get("status", "").strip()
    search_query = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)
    per_page = 15

    query = ContactMessage.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    if search_query:
        pattern = f"%{search_query}%"
        query = query.filter(
            (ContactMessage.name.ilike(pattern))
            | (ContactMessage.email.ilike(pattern))
            | (ContactMessage.subject.ilike(pattern))
            | (ContactMessage.message.ilike(pattern))
        )

    pagination = query.order_by(ContactMessage.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)

    status_counts = {
        "all": ContactMessage.query.count(),
        "unread": ContactMessage.query.filter_by(status="unread").count(),
        "read": ContactMessage.query.filter_by(status="read").count(),
        "replied": ContactMessage.query.filter_by(status="replied").count(),
        "archived": ContactMessage.query.filter_by(status="archived").count(),
    }

    return render_template(
        "admin/contact/list.html",
        page_title="Contact Inquiries | Dax Prajapati Admin",
        messages=pagination.items,
        pagination=pagination,
        status_filter=status_filter,
        search_query=search_query,
        status_counts=status_counts,
    )


@admin_bp.route("/admin/contact-messages/<int:msg_id>", methods=["GET"])
@admin_required
def contact_message_detail(msg_id):
    msg = db.get_or_404(ContactMessage, msg_id)
    if msg.status == "unread":
        msg.status = "read"
        db.session.commit()
    return jsonify({"status": "success", "message": msg.to_dict()})


@admin_bp.route("/admin/contact-messages/<int:msg_id>/reply", methods=["POST"])
@admin_required
def contact_message_reply(msg_id):
    msg = db.get_or_404(ContactMessage, msg_id)
    reply_body = request.form.get("reply_message") or (request.json.get("reply_message") if request.is_json else "")
    if not reply_body.strip():
        flash("Reply note cannot be empty.", "error")
        return redirect(url_for("admin.contact_messages_list"))

    msg.status = "replied"
    msg.reply_content = sanitize_text(reply_body)
    msg.replied_at = datetime.now(timezone.utc)
    db.session.commit()

    log_activity(
        action_type="contact_note_recorded",
        description=f"Recorded follow-up note for inquiry from {msg.email} regarding '{msg.subject}'",
        admin_id=session.get("admin_id"),
        record_id=str(msg.id),
        record_type="contact",
        result="success",
    )
    if request.is_json:
        return jsonify({"status": "success", "message": f"Follow-up note saved for {msg.email}"})
    flash(f"Follow-up note saved for message from {msg.email}.", "success")
    return redirect(url_for("admin.contact_messages_list"))


@admin_bp.route("/admin/contact-messages/<int:msg_id>/status", methods=["POST"])
@admin_required
def contact_message_status(msg_id):
    msg = db.get_or_404(ContactMessage, msg_id)
    new_status = request.form.get("status") or (request.json.get("status") if request.is_json else "")
    if new_status in ("unread", "read", "replied", "archived"):
        msg.status = new_status
        db.session.commit()
    if request.is_json:
        return jsonify({"status": "success", "status": msg.status})
    flash(f"Message status set to {new_status}.", "info")
    return redirect(url_for("admin.contact_messages_list"))


@admin_bp.route("/admin/contact-messages/<int:msg_id>/delete", methods=["POST"])
@admin_required
def contact_message_delete(msg_id):
    msg = db.get_or_404(ContactMessage, msg_id)
    db.session.delete(msg)
    db.session.commit()
    log_activity(
        action_type="contact_message_deleted",
        description=f"Deleted message from {msg.email}",
        admin_id=session.get("admin_id"),
        record_id=str(msg_id),
        record_type="contact",
    )
    if request.is_json:
        return jsonify({"status": "success", "message": "Message deleted."})
    flash("Message deleted successfully.", "success")
    return redirect(url_for("admin.contact_messages_list"))


# ------------------------------------------------------------------------------
# 6. MEDIA LIBRARY (NEON OBJECT STORAGE PHOTOS BUCKET)
# ------------------------------------------------------------------------------
@admin_bp.route("/admin/media", methods=["GET", "POST"])
@admin_required
def media_library():
    if request.method == "POST":
        csrf = request.form.get("csrf_token")
        if not validate_csrf_token(csrf):
            flash("Invalid session token.", "error")
            return redirect(url_for("admin.media_library"))

        if "media_file" not in request.files:
            flash("No file uploaded.", "error")
            return redirect(url_for("admin.media_library"))

        file = request.files["media_file"]
        if not file or file.filename == "":
            flash("No file selected.", "error")
            return redirect(url_for("admin.media_library"))

        custom_folder = sanitize_text(request.form.get("folder", "general")).strip().lower()
        filename = secure_filename(file.filename)
        object_key = f"ui-templates/{custom_folder}/{filename}"

        try:
            meta = storage_service.upload_file(file.read(), object_key, optimize=True)
            log_activity(
                action_type="media_uploaded",
                description=f"Uploaded asset '{object_key}' to Neon S3",
                admin_id=session.get("admin_id"),
                record_id=object_key,
                record_type="media",
            )
            flash(f"Asset '{filename}' uploaded successfully to Neon Object Storage.", "success")
        except Exception as e:
            flash(f"Upload failed: {str(e)}", "error")
        return redirect(url_for("admin.media_library"))

    # Fetch tracked database preview assets
    assets = DesignPreviewAsset.query.order_by(DesignPreviewAsset.created_at.desc()).all()

    # Also query live Neon S3 bucket for all objects
    s3_objects = storage_service.list_objects(prefix="ui-templates/", max_keys=100)

    return render_template(
        "admin/media/index.html",
        page_title="Media Library & Neon Object Storage | Admin",
        assets=assets,
        s3_objects=s3_objects,
        bucket_name=storage_service.bucket,
    )


@admin_bp.route("/admin/media/<int:asset_id>/delete", methods=["POST"])
@admin_required
def media_delete(asset_id):
    asset = db.get_or_404(DesignPreviewAsset, asset_id)
    # Check if attached to published template
    tpl = DesignTemplate.query.filter_by(design_id=asset.design_id).first()
    if tpl and tpl.is_published:
        flash(f"Cannot delete asset '{asset.object_key}': currently referenced by published template '{tpl.name}'.", "error")
        return redirect(url_for("admin.media_library"))

    key = asset.object_key
    try:
        storage_service.delete_object(key)
    except Exception as e:
        current_app.logger.warning(f"S3 deletion warning for {key}: {e}")

    db.session.delete(asset)
    db.session.commit()

    log_activity(
        action_type="media_deleted",
        description=f"Deleted asset '{key}' from Neon S3",
        admin_id=session.get("admin_id"),
        record_id=str(asset_id),
        record_type="media",
    )
    flash(f"Asset '{key}' deleted safely.", "success")
    return redirect(url_for("admin.media_library"))


# ------------------------------------------------------------------------------
# 7. ADMIN ACTIVITY AUDIT LOG
# ------------------------------------------------------------------------------
@admin_bp.route("/admin/activity")
@admin_required
def activity_log():
    action_type = request.args.get("action_type", "").strip()
    search_query = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)
    per_page = 20

    query = AdminActivityLog.query
    if action_type:
        query = query.filter_by(action_type=action_type)
    if search_query:
        pattern = f"%{search_query}%"
        query = query.filter(
            (AdminActivityLog.description.ilike(pattern))
            | (AdminActivityLog.ip_address.ilike(pattern))
            | (AdminActivityLog.record_id.ilike(pattern))
        )

    pagination = query.order_by(AdminActivityLog.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)

    action_types = [a[0] for a in db.session.query(AdminActivityLog.action_type).distinct().all()]

    return render_template(
        "admin/activity/index.html",
        page_title="Audit & Activity Logs | Dax Prajapati Admin",
        logs=pagination.items,
        pagination=pagination,
        action_types=action_types,
        selected_action=action_type,
        search_query=search_query,
    )


# ------------------------------------------------------------------------------
# 8. ADMIN SETTINGS
# ------------------------------------------------------------------------------
@admin_bp.route("/admin/settings", methods=["GET", "POST"])
@admin_required
def settings():
    admin = db.session.get(AdminUser, session["admin_id"])

    if request.method == "POST":
        csrf = request.form.get("csrf_token")
        if not validate_csrf_token(csrf):
            flash("Invalid session token.", "error")
            return redirect(url_for("admin.settings"))

        action = request.form.get("action")

        if action == "change_password":
            cur_pass = request.form.get("current_password", "")
            new_pass = request.form.get("new_password", "")
            conf_pass = request.form.get("confirm_password", "")

            if not admin.check_password(cur_pass):
                flash("Current password incorrect.", "error")
            elif len(new_pass) < 8:
                flash("New password must be at least 8 characters.", "error")
            elif new_pass != conf_pass:
                flash("New passwords do not match.", "error")
            else:
                admin.set_password(new_pass)
                db.session.commit()
                log_activity(
                    action_type="password_changed",
                    description="Admin password changed successfully",
                    admin_id=admin.id,
                    record_id=str(admin.id),
                    record_type="admin",
                )
                flash("Password updated successfully.", "success")

        elif action == "portfolio_settings":
            contact_email = sanitize_text(request.form.get("contact_email", ""))
            default_quote_status = request.form.get("default_quotation_status", "new")

            PortfolioSetting.set("contact_email", contact_email, "Public portfolio contact email")
            PortfolioSetting.set("default_quotation_status", default_quote_status, "Initial status for new quotations")

            log_activity(
                action_type="settings_updated",
                description="Updated portfolio settings",
                admin_id=admin.id,
                record_id="portfolio_settings",
                record_type="settings",
            )
            flash("Portfolio settings saved.", "success")

        return redirect(url_for("admin.settings"))

    recent_logins = AdminLoginActivity.query.order_by(AdminLoginActivity.created_at.desc()).limit(8).all()
    storage_bucket = storage_service.bucket
    storage_endpoint = os.getenv("AWS_ENDPOINT_URL_S3", "")
    storage_region = os.getenv("AWS_REGION", "ap-southeast-1")

    return render_template(
        "admin/settings/index.html",
        page_title="Admin Settings | Dax Prajapati",
        admin=admin,
        recent_logins=recent_logins,
        storage_bucket=storage_bucket,
        storage_endpoint=storage_endpoint,
        storage_region=storage_region,
        portfolio_settings={
            "contact_email": PortfolioSetting.get("contact_email", "daxprajapati1707@gmail.com"),
            "default_quotation_status": PortfolioSetting.get("default_quotation_status", "new"),
        },
    )


# ------------------------------------------------------------------------------
# 9. ADMIN NOTIFICATIONS API
# ------------------------------------------------------------------------------
@admin_bp.route("/admin/api/notifications", methods=["GET"])
@admin_required
def api_notifications():
    notifications = get_recent_notifications(limit=10)
    unread_count = get_unread_notifications_count()
    return jsonify({
        "status": "success",
        "unread_count": unread_count,
        "notifications": [n.to_dict() for n in notifications],
    })


@admin_bp.route("/admin/api/notifications/<int:notif_id>/read", methods=["POST"])
@admin_required
def api_mark_notification_read(notif_id):
    mark_notification_as_read(notif_id)
    return jsonify({"status": "success", "unread_count": get_unread_notifications_count()})


@admin_bp.route("/admin/api/notifications/read-all", methods=["POST"])
@admin_required
def api_mark_all_notifications_read():
    count = mark_all_notifications_as_read()
    return jsonify({"status": "success", "marked_read": count, "unread_count": 0})
