import time
from functools import wraps
from typing import Dict, List
from flask import session, redirect, url_for, request, jsonify, render_template, abort
from backend.models.admin import AdminUser
from backend.utils.security import get_client_ip

# In-memory sliding window rate limiter store
_rate_limit_store: Dict[str, List[float]] = {}


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        admin_id = session.get("admin_id")
        if not admin_id:
            if request.path.startswith("/api/"):
                return jsonify({"status": "error", "message": "Authentication required"}), 401
            # Redirect to the secret admin login URL
            return redirect(url_for("admin.admin_login"))

        from backend import db
        admin = db.session.get(AdminUser, admin_id)
        if not admin or not admin.is_active:
            session.clear()
            if request.path.startswith("/api/"):
                return jsonify({"status": "error", "message": "Account inactive or invalid"}), 401
            return redirect(url_for("admin.admin_login"))

        return f(*args, **kwargs)

    return decorated_function


def rate_limit(action_key: str, max_attempts: int, window_seconds: int):
    """
    Decorator for sliding window rate limiting per client IP.
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            ip = get_client_ip()
            now = time.time()
            store_key = f"{action_key}:{ip}"

            timestamps = _rate_limit_store.get(store_key, [])
            # Filter timestamps within window
            timestamps = [ts for ts in timestamps if now - ts < window_seconds]
            _rate_limit_store[store_key] = timestamps

            if len(timestamps) >= max_attempts:
                wait_time = int(window_seconds - (now - timestamps[0]))
                message = f"Too many requests. Please try again in {max(1, wait_time)} seconds."
                if request.is_json or request.path.startswith("/api/"):
                    return jsonify({"status": "error", "message": message, "error_code": 429}), 429
                return render_template(
                    "404.html",
                    page_title="Rate Limit Exceeded | Dax Prajapati",
                    meta_description=message,
                    custom_message=message
                ), 429

            timestamps.append(now)
            _rate_limit_store[store_key] = timestamps
            return f(*args, **kwargs)

        return wrapped
    return decorator
