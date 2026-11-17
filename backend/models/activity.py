from datetime import datetime, timezone
from backend import db


class AdminActivityLog(db.Model):
    __tablename__ = "admin_activity_logs"

    id = db.Column(db.Integer, primary_key=True)
    action_type = db.Column(db.String(100), nullable=False, index=True)
    admin_id = db.Column(db.Integer, db.ForeignKey("admin_users.id", ondelete="SET NULL"), nullable=True)
    record_id = db.Column(db.String(100), nullable=True)
    record_type = db.Column(db.String(50), nullable=True)
    description = db.Column(db.Text, nullable=False)
    result = db.Column(db.String(20), default="success", nullable=False)  # 'success', 'failure'
    ip_address = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    admin = db.relationship("AdminUser", backref=db.backref("activity_logs", lazy="dynamic"))

    def to_dict(self):
        return {
            "id": self.id,
            "action_type": self.action_type,
            "admin_name": self.admin.name if self.admin else "System/Admin",
            "record_id": self.record_id or "",
            "record_type": self.record_type or "",
            "description": self.description,
            "result": self.result,
            "ip_address": self.ip_address or "",
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S UTC") if self.created_at else "",
        }
