from datetime import datetime, timezone
from backend import db


class ContactMessage(db.Model):
    __tablename__ = "contact_messages"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), nullable=False, index=True)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    
    # Status: 'unread', 'read', 'replied', 'archived'
    status = db.Column(db.String(50), default="unread", nullable=False, index=True)
    internal_notes = db.Column(db.Text, nullable=True)
    reply_content = db.Column(db.Text, nullable=True)
    replied_at = db.Column(db.DateTime, nullable=True)

    ip_address = db.Column(db.String(50), nullable=True)
    user_agent = db.Column(db.String(300), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "subject": self.subject,
            "message": self.message,
            "status": self.status,
            "internal_notes": self.internal_notes or "",
            "reply_content": self.reply_content or "",
            "replied_at": self.replied_at.strftime("%Y-%m-%d %H:%M UTC") if self.replied_at else None,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M UTC") if self.created_at else "",
            "ip_address": self.ip_address or "",
        }
