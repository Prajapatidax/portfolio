from datetime import datetime, timezone
from backend import db


class CookieConsent(db.Model):
    __tablename__ = "cookie_consents"

    id = db.Column(db.Integer, primary_key=True)
    consent_uuid = db.Column(db.String(64), unique=True, nullable=False, index=True)
    essential = db.Column(db.Boolean, default=True, nullable=False)
    analytics = db.Column(db.Boolean, default=False, nullable=False)
    marketing = db.Column(db.Boolean, default=False, nullable=False)
    version = db.Column(db.String(20), default="1.0", nullable=False)
    ip_hash = db.Column(db.String(64), nullable=True)
    user_agent = db.Column(db.String(300), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        return {
            "consent_uuid": self.consent_uuid,
            "essential": self.essential,
            "analytics": self.analytics,
            "marketing": self.marketing,
            "version": self.version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
