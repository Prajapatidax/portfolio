from datetime import datetime, timezone
from typing import Optional, List
from backend import db
from backend.models.activity import AdminActivityLog
from backend.models.notification import AdminNotification
from backend.utils.security import sanitize_text


def log_activity(
    action_type: str,
    description: str,
    admin_id: Optional[int] = None,
    record_id: Optional[str] = None,
    record_type: Optional[str] = None,
    result: str = "success",
    ip_address: Optional[str] = None,
) -> AdminActivityLog:
    """Record an immutable admin audit log entry."""
    log_entry = AdminActivityLog(
        action_type=action_type[:100],
        admin_id=admin_id,
        record_id=str(record_id)[:100] if record_id is not None else None,
        record_type=str(record_type)[:50] if record_type is not None else None,
        description=sanitize_text(description),
        result=result[:20],
        ip_address=ip_address[:50] if ip_address else None,
    )
    db.session.add(log_entry)
    db.session.commit()
    return log_entry


def notify_admin(
    title: str,
    message: str,
    category: str = "general",
    link_url: Optional[str] = None,
) -> AdminNotification:
    """Create a persistent admin notification."""
    notif = AdminNotification(
        title=sanitize_text(title, 150),
        message=sanitize_text(message),
        category=category[:50],
        link_url=link_url[:255] if link_url else None,
        is_read=False,
    )
    db.session.add(notif)
    db.session.commit()
    return notif


def get_unread_notifications_count() -> int:
    return AdminNotification.query.filter_by(is_read=False).count()


def get_recent_notifications(limit: int = 10) -> List[AdminNotification]:
    return AdminNotification.query.order_by(AdminNotification.created_at.desc()).limit(limit).all()


def mark_notification_as_read(notification_id: int) -> bool:
    notif = db.session.get(AdminNotification, notification_id)
    if notif:
        notif.is_read = True
        db.session.commit()
        return True
    return False


def mark_all_notifications_as_read() -> int:
    unread = AdminNotification.query.filter_by(is_read=False).all()
    count = len(unread)
    for n in unread:
        n.is_read = True
    db.session.commit()
    return count
