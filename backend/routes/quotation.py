from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from backend.services.quotation_service import create_quotation
from backend.models.quotation import QuotationRequest
from backend.models.design import DesignTemplate, DesignCategory
from backend.utils.decorators import rate_limit
from backend.utils.security import get_client_ip, validate_csrf_token

quotation_bp = Blueprint("quotation", __name__)


@quotation_bp.route("/quotation")
def wizard_page():
    templates = DesignTemplate.query.filter_by(is_published=True).all()
    categories = DesignCategory.query.filter_by(is_active=True).order_by(DesignCategory.display_order.asc()).all()
    return render_template(
        "quotation-wizard.html",
        page_title="Request a Project Quotation | Dax Prajapati",
        meta_description="Customize your website project, select preferred design directions, and receive a transparent project quotation.",
        canonical_url="https://prajapatidax.co.in/quotation",
        templates=templates,
        categories=categories,
    )


@quotation_bp.route("/api/quotation", methods=["POST"])
@rate_limit("quotation_submit", max_attempts=15, window_seconds=3600)
def submit_quotation():
    if not request.is_json:
        return jsonify({
            "status": "error",
            "message": "Invalid request content-type. Expected application/json",
            "error_code": 400
        }), 400

    payload = request.get_json() or {}

    # Optional CSRF verification for API if token sent
    csrf_token = request.headers.get("X-CSRFToken") or payload.get("csrf_token")
    if csrf_token and not validate_csrf_token(csrf_token):
        return jsonify({
            "status": "error",
            "message": "Invalid or expired session token. Please refresh the page.",
            "error_code": 403
        }), 403

    client_ip = get_client_ip()
    user_agent = (request.user_agent.string or "")[:300]

    success, result = create_quotation(payload, ip_address=client_ip, user_agent=user_agent)

    if not success:
        return jsonify({
            "status": "error",
            "message": "Validation failed. Please correct the errors and try again.",
            "errors": result,
            "error_code": 422
        }), 422

    quotation = result
    return jsonify({
        "status": "success",
        "message": "Thank you for your interest! Your project request has been successfully submitted. I will review your requirements and get back to you.",
        "reference_id": quotation.reference_id,
        "data": {
            "reference_id": quotation.reference_id,
            "customer_name": quotation.customer_name,
            "project_name": quotation.project_name,
            "project_type": quotation.project_type,
            "budget_range": quotation.budget_range,
            "timeline": quotation.timeline,
            "status": quotation.status,
            "created_at": quotation.created_at.strftime("%Y-%m-%d %H:%M UTC") if quotation.created_at else "",
        }
    }), 201


@quotation_bp.route("/api/quotation/<reference_id>", methods=["GET"])
def get_quotation_status(reference_id):
    clean_ref = reference_id.strip().upper()
    quote = QuotationRequest.query.filter_by(reference_id=clean_ref).first()
    if not quote:
        return jsonify({
            "status": "error",
            "message": "Quotation reference not found",
            "error_code": 404
        }), 404

    return jsonify({
        "status": "success",
        "reference_id": quote.reference_id,
        "project_name": quote.project_name,
        "project_type": quote.project_type,
        "quotation_status": quote.status,
        "proposed_amount": quote.proposed_amount or None,
        "estimated_delivery": quote.estimated_delivery or None,
        "created_at": quote.created_at.strftime("%Y-%m-%d") if quote.created_at else "",
    })
