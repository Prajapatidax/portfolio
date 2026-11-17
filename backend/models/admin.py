from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from backend import db


class AdminUser(db.Model):
    __tablename__ = "admin_users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    last_login_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    notes = db.relationship("AdminNote", backref="admin", lazy="dynamic")
    status_changes = db.relationship("QuotationStatusHistory", backref="admin", lazy="dynamic")

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password, method="scrypt")

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
        }


class AdminLoginActivity(db.Model):
    __tablename__ = "admin_login_activity"

    id = db.Column(db.Integer, primary_key=True)
    email_attempted = db.Column(db.String(150), nullable=False, index=True)
    is_success = db.Column(db.Boolean, nullable=False)
    ip_address = db.Column(db.String(50), nullable=True)
    user_agent = db.Column(db.String(300), nullable=True)
    failure_reason = db.Column(db.String(150), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "email_attempted": self.email_attempted,
            "is_success": self.is_success,
            "ip_address": self.ip_address,
            "failure_reason": self.failure_reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
