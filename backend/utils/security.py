import hmac
import hashlib
import re
import secrets
from flask import session, current_app, request


def generate_csrf_token() -> str:
    """Generate or retrieve the session CSRF token."""
    if "_csrf_token" not in session:
        session["_csrf_token"] = secrets.token_hex(32)
    return session["_csrf_token"]


def validate_csrf_token(token: str) -> bool:
    """Validate CSRF token using constant-time comparison."""
    session_token = session.get("_csrf_token")
    if not session_token or not token:
        return False
    return hmac.compare_digest(session_token, token)


def sanitize_text(text: str, max_length: int = 5000) -> str:
    """Strip dangerous characters and trim text."""
    if not text:
        return ""
    # Strip HTML tags
    clean = re.sub(r"<[^>]*>", "", str(text))
    clean = clean.strip()
    if max_length and len(clean) > max_length:
        clean = clean[:max_length]
    return clean


def hash_ip(ip: str) -> str:
    """Anonymize IP address with SHA-256."""
    if not ip:
        return ""
    salt = current_app.config.get("SECRET_KEY", "salt")
    return hashlib.sha256(f"{ip}:{salt}".encode("utf-8")).hexdigest()[:32]


def get_client_ip() -> str:
    """Extract real client IP considering reverse proxies."""
    if request.headers.get("X-Forwarded-For"):
        return request.headers.get("X-Forwarded-For").split(",")[0].strip()
    return request.remote_addr or "127.0.0.1"
