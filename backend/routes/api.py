from flask import Blueprint, request, jsonify
from datetime import datetime, timezone
import uuid
from backend import db
from backend.models.consent import CookieConsent
from backend.models.design import DesignCategory, DesignTemplate
from backend.utils.security import get_client_ip, hash_ip

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/health", methods=["GET"])
def health_check():
    db_status = "connected"
    try:
        db.session.execute(db.text("SELECT 1"))
    except Exception as e:
        db_status = f"error: {str(e)}"

    return jsonify({
        "status": "healthy" if "error" not in db_status else "degraded",
        "database": db_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "2.0.0",
    })


@api_bp.route("/cookie-consent", methods=["POST"])
def record_cookie_consent():
    data = request.get_json() or {}

    consent_uuid = data.get("consent_uuid") or str(uuid.uuid4())
    essential = True  # Always True
    analytics = bool(data.get("analytics", False))
    marketing = bool(data.get("marketing", False))
    version = str(data.get("version", "1.0"))

    client_ip = get_client_ip()
    ip_hashed = hash_ip(client_ip)
    user_agent = (request.user_agent.string or "")[:300]

    record = CookieConsent.query.filter_by(consent_uuid=consent_uuid).first()
    if not record:
        record = CookieConsent(
            consent_uuid=consent_uuid,
            essential=essential,
            analytics=analytics,
            marketing=marketing,
            version=version,
            ip_hash=ip_hashed,
            user_agent=user_agent,
        )
        db.session.add(record)
    else:
        record.analytics = analytics
        record.marketing = marketing
        record.version = version

    db.session.commit()
    return jsonify({
        "status": "success",
        "consent_uuid": consent_uuid,
        "preferences": {
            "essential": essential,
            "analytics": analytics,
            "marketing": marketing,
        }
    })


@api_bp.route("/designs", methods=["GET"])
def list_designs():
    templates = DesignTemplate.query.filter_by(is_published=True).all()
    categories = DesignCategory.query.filter_by(is_active=True).order_by(DesignCategory.display_order.asc()).all()
    return jsonify({
        "status": "success",
        "categories": [c.to_dict() for c in categories],
        "designs": [t.to_dict() for t in templates],
    })
