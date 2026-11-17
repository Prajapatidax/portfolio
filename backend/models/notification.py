from datetime import datetime, timezone
from backend import db


class AdminNotification(db.Model):
    __tablename__ = "admin_notifications"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    # Category: 'quotation', 'contact', 'system', 'storage', 'email'
    category = db.Column(db.String(50), default="general", nullable=False, index=True)
    link_url = db.Column(db.String(255), nullable=True)
    is_read = db.Column(db.Boolean, default=False, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "message": self.message,
            "category": self.category,
            "link_url": self.link_url or "",
            "is_read": self.is_read,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M UTC") if self.created_at else "",
        }
