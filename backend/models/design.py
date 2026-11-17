from datetime import datetime, timezone
import json
from backend import db


class DesignCategory(db.Model):
    __tablename__ = "design_categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    display_order = db.Column(db.Integer, default=0, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    templates = db.relationship("DesignTemplate", backref="category", lazy="dynamic", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "display_order": self.display_order,
            "is_active": self.is_active,
            "template_count": self.templates.count(),
        }


class DesignTemplate(db.Model):
    __tablename__ = "design_templates"

    id = db.Column(db.Integer, primary_key=True)
    design_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    slug = db.Column(db.String(100), unique=True, nullable=False, index=True)
    name = db.Column(db.String(150), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("design_categories.id", ondelete="CASCADE"), nullable=False)
    description = db.Column(db.Text, nullable=False)
    thumbnail_url = db.Column(db.String(255), nullable=True)
    desktop_preview_url = db.Column(db.String(255), nullable=True)
    mobile_preview_url = db.Column(db.String(255), nullable=True)
    live_preview_html = db.Column(db.Text, nullable=True)
    color_palette = db.Column(db.JSON, nullable=False, default=list)
    typography = db.Column(db.JSON, nullable=False, default=dict)
    features = db.Column(db.JSON, nullable=False, default=list)
    pages_available = db.Column(db.JSON, nullable=False, default=list)
    status = db.Column(db.String(50), default="Available", nullable=False)
    is_featured = db.Column(db.Boolean, default=False, nullable=False)
    is_published = db.Column(db.Boolean, default=True, nullable=False)
    is_archived = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    assets = db.relationship("DesignPreviewAsset", backref="template", cascade="all, delete-orphan", lazy="dynamic")

    def get_asset(self, image_type="laptop"):
        if image_type in ("laptop", "desktop"):
            asset = self.assets.filter(DesignPreviewAsset.image_type.in_(["laptop", "desktop"])).first()
            if asset:
                return asset
        return self.assets.filter_by(image_type=image_type).first()

    def get_asset_url(self, image_type="laptop"):
        asset = self.get_asset(image_type)
        if asset:
            return f"/storage/preview/{asset.object_key}"
        if image_type in ("laptop", "desktop"):
            return self.desktop_preview_url or self.thumbnail_url
        elif image_type == "mobile":
            return self.mobile_preview_url
        return self.thumbnail_url

    def to_dict(self):
        return {
            "id": self.id,
            "design_id": self.design_id,
            "slug": self.slug,
            "name": self.name,
            "category_id": self.category_id,
            "category_name": self.category.name if self.category else "",
            "category_slug": self.category.slug if self.category else "",
            "description": self.description,
            "thumbnail_url": self.get_asset_url("laptop"),
            "desktop_preview_url": self.get_asset_url("laptop"),
            "laptop_preview_url": self.get_asset_url("laptop"),
            "tablet_preview_url": self.get_asset_url("tablet"),
            "mobile_preview_url": self.get_asset_url("mobile"),
            "assets": [a.to_dict() for a in self.assets],
            "color_palette": self.color_palette or [],
            "typography": self.typography or {},
            "features": self.features or [],
            "pages_available": self.pages_available or [],
            "status": self.status,
            "is_featured": self.is_featured,
            "is_published": self.is_published,
            "is_archived": self.is_archived,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class DesignPreviewAsset(db.Model):
    __tablename__ = "design_preview_assets"

    id = db.Column(db.Integer, primary_key=True)
    design_id = db.Column(db.String(50), db.ForeignKey("design_templates.design_id", ondelete="CASCADE"), nullable=False, index=True)
    image_type = db.Column(db.String(50), nullable=False)  # 'laptop', 'tablet', 'mobile', 'desktop'
    bucket_name = db.Column(db.String(100), default="photos", nullable=False)
    object_key = db.Column(db.String(500), nullable=False)
    content_type = db.Column(db.String(100), default="image/webp", nullable=False)
    file_size = db.Column(db.Integer, nullable=True)  # in bytes
    width = db.Column(db.Integer, nullable=True)
    height = db.Column(db.Integer, nullable=True)
    checksum = db.Column(db.String(64), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "design_id": self.design_id,
            "image_type": self.image_type,
            "bucket_name": self.bucket_name,
            "object_key": self.object_key,
            "content_type": self.content_type,
            "file_size": self.file_size,
            "width": self.width,
            "height": self.height,
            "checksum": self.checksum,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
