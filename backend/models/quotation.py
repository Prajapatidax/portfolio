from datetime import datetime, timezone
from backend import db


class QuotationRequest(db.Model):
    __tablename__ = "quotation_requests"

    id = db.Column(db.Integer, primary_key=True)
    reference_id = db.Column(db.String(32), unique=True, nullable=False, index=True)
    project_type = db.Column(db.String(100), nullable=False)
    budget_range = db.Column(db.String(100), nullable=False)
    timeline = db.Column(db.String(100), nullable=False)
    customer_name = db.Column(db.String(150), nullable=False)
    customer_email = db.Column(db.String(150), nullable=False, index=True)
    customer_phone = db.Column(db.String(50), nullable=True)
    project_name = db.Column(db.String(200), nullable=False)
    project_description = db.Column(db.Text, nullable=False)
    reference_website = db.Column(db.String(255), nullable=True)
    
    # Status & Management
    status = db.Column(db.String(50), default="new", nullable=False, index=True)
    priority = db.Column(db.String(20), default="normal", nullable=False, index=True)  # low, normal, high, urgent
    is_archived = db.Column(db.Boolean, default=False, nullable=False, index=True)
    proposed_amount = db.Column(db.String(100), nullable=True)
    estimated_delivery = db.Column(db.String(100), nullable=True)

    ip_address = db.Column(db.String(50), nullable=True)
    user_agent = db.Column(db.String(300), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    selected_designs = db.relationship("QuotationSelectedDesign", backref="quotation", cascade="all, delete-orphan", lazy="joined")
    customization = db.relationship("QuotationCustomization", backref="quotation", uselist=False, cascade="all, delete-orphan")
    features = db.relationship("QuotationFeature", backref="quotation", cascade="all, delete-orphan", lazy="joined")
    status_history = db.relationship("QuotationStatusHistory", backref="quotation", cascade="all, delete-orphan", order_by="desc(QuotationStatusHistory.created_at)")
    notes = db.relationship("AdminNote", backref="quotation", cascade="all, delete-orphan", order_by="desc(AdminNote.created_at)")

    def to_dict(self):
        return {
            "id": self.id,
            "reference_id": self.reference_id,
            "project_type": self.project_type,
            "budget_range": self.budget_range,
            "timeline": self.timeline,
            "customer_name": self.customer_name,
            "customer_email": self.customer_email,
            "customer_phone": self.customer_phone or "",
            "project_name": self.project_name,
            "project_description": self.project_description,
            "reference_website": self.reference_website or "",
            "status": self.status,
            "priority": self.priority,
            "is_archived": self.is_archived,
            "proposed_amount": self.proposed_amount or "",
            "estimated_delivery": self.estimated_delivery or "",
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M UTC") if self.created_at else "",
            "selected_designs": [d.to_dict() for d in self.selected_designs],
            "customization": self.customization.to_dict() if self.customization else {},
            "features": [f.feature_label for f in self.features],
            "notes": [n.to_dict() for n in self.notes],
            "history": [h.to_dict() for h in self.status_history],
        }


class QuotationSelectedDesign(db.Model):
    __tablename__ = "quotation_selected_designs"

    id = db.Column(db.Integer, primary_key=True)
    quotation_id = db.Column(db.Integer, db.ForeignKey("quotation_requests.id", ondelete="CASCADE"), nullable=False)
    design_template_id = db.Column(db.Integer, db.ForeignKey("design_templates.id", ondelete="SET NULL"), nullable=True)
    design_id_snapshot = db.Column(db.String(50), nullable=False)
    design_name_snapshot = db.Column(db.String(150), nullable=False)
    category_snapshot = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "design_id": self.design_id_snapshot,
            "design_name": self.design_name_snapshot,
            "category": self.category_snapshot or "",
            "notes": self.notes or "",
        }


class QuotationCustomization(db.Model):
    __tablename__ = "quotation_customizations"

    id = db.Column(db.Integer, primary_key=True)
    quotation_id = db.Column(db.Integer, db.ForeignKey("quotation_requests.id", ondelete="CASCADE"), unique=True, nullable=False)
    primary_color = db.Column(db.String(50), default="#2563EB", nullable=False)
    secondary_color = db.Column(db.String(50), default="#0F172A", nullable=False)
    theme_mode = db.Column(db.String(50), default="light", nullable=False)
    typography_preference = db.Column(db.String(100), default="Plus Jakarta Sans + Inter", nullable=False)
    animation_preference = db.Column(db.String(50), default="Smooth & Subtle", nullable=False)
    layout_preference = db.Column(db.String(50), default="Modern Grid", nullable=False)
    platform_preference = db.Column(db.String(50), default="desktop-first", nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        return {
            "primary_color": self.primary_color,
            "secondary_color": self.secondary_color,
            "theme_mode": self.theme_mode,
            "typography_preference": self.typography_preference,
            "animation_preference": self.animation_preference,
            "layout_preference": self.layout_preference,
            "platform_preference": self.platform_preference,
        }


class QuotationFeature(db.Model):
    __tablename__ = "quotation_features"

    id = db.Column(db.Integer, primary_key=True)
    quotation_id = db.Column(db.Integer, db.ForeignKey("quotation_requests.id", ondelete="CASCADE"), nullable=False)
    feature_key = db.Column(db.String(100), nullable=False)
    feature_label = db.Column(db.String(150), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class QuotationStatusHistory(db.Model):
    __tablename__ = "quotation_status_history"

    id = db.Column(db.Integer, primary_key=True)
    quotation_id = db.Column(db.Integer, db.ForeignKey("quotation_requests.id", ondelete="CASCADE"), nullable=False)
    old_status = db.Column(db.String(50), nullable=True)
    new_status = db.Column(db.String(50), nullable=False)
    changed_by_admin_id = db.Column(db.Integer, db.ForeignKey("admin_users.id", ondelete="SET NULL"), nullable=True)
    comments = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "old_status": self.old_status,
            "new_status": self.new_status,
            "admin_name": self.admin.name if self.admin else "System",
            "comments": self.comments or "",
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M UTC") if self.created_at else "",
        }


class AdminNote(db.Model):
    __tablename__ = "admin_notes"

    id = db.Column(db.Integer, primary_key=True)
    quotation_id = db.Column(db.Integer, db.ForeignKey("quotation_requests.id", ondelete="CASCADE"), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey("admin_users.id", ondelete="CASCADE"), nullable=False)
    note_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "admin_name": self.admin.name if self.admin else "Admin",
            "note_text": self.note_text,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M UTC") if self.created_at else "",
        }
