from datetime import datetime, timezone
from backend import db


class PortfolioSetting(db.Model):
    __tablename__ = "portfolio_settings"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    value = db.Column(db.Text, nullable=True)
    description = db.Column(db.String(255), nullable=True)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    @classmethod
    def get(cls, key: str, default=None):
        item = cls.query.filter_by(key=key).first()
        if item is not None and item.value is not None:
            return item.value
        return default

    @classmethod
    def set(cls, key: str, value: str, description: str = None):
        item = cls.query.filter_by(key=key).first()
        if item:
            item.value = str(value)
            if description:
                item.description = description
        else:
            item = cls(key=key, value=str(value), description=description)
            db.session.add(item)
        db.session.commit()
        return item

    def to_dict(self):
        return {
            "key": self.key,
            "value": self.value,
            "description": self.description,
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M UTC") if self.updated_at else "",
        }
