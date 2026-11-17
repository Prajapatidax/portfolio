from datetime import datetime, timezone
from flask import session
from backend import db
from backend.models.admin import AdminUser, AdminLoginActivity


def seed_initial_admin(name: str, email: str, password: str) -> AdminUser:
    """Ensure at least one admin account exists."""
    admin = AdminUser.query.filter_by(email=email.strip().lower()).first()
    if not admin:
        admin = AdminUser(
            name=name.strip(),
            email=email.strip().lower(),
            is_active=True,
        )
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
    return admin


def authenticate_admin(email: str, password: str, ip_address: str = None, user_agent: str = None):
    """Authenticate admin and log the attempt."""
    email_clean = (email or "").strip().lower()
    admin = AdminUser.query.filter_by(email=email_clean).first()

    success = False
    failure_reason = None

    if not admin:
        failure_reason = "Account not found"
    elif not admin.is_active:
        failure_reason = "Account disabled"
    elif not admin.check_password(password):
        failure_reason = "Invalid password"
    else:
        success = True

    # Log attempt
    activity = AdminLoginActivity(
        email_attempted=email_clean or "unknown",
        is_success=success,
        ip_address=ip_address,
        user_agent=user_agent,
        failure_reason=failure_reason,
    )
    db.session.add(activity)

    if success:
        admin.last_login_at = datetime.now(timezone.utc)
        db.session.commit()
        session["admin_id"] = admin.id
        session["admin_email"] = admin.email
        session["admin_name"] = admin.name
        session.permanent = True
        return True, admin
    else:
        db.session.commit()
        return False, failure_reason


def logout_admin():
    session.pop("admin_id", None)
    session.pop("admin_email", None)
    session.pop("admin_name", None)
