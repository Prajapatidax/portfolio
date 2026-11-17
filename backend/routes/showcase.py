from flask import Blueprint, render_template, abort, request
from backend.models.design import DesignCategory, DesignTemplate

showcase_bp = Blueprint("showcase", __name__, url_prefix="/design-showcase")


@showcase_bp.route("")
@showcase_bp.route("/")
def index():
    categories = DesignCategory.query.filter_by(is_active=True).order_by(DesignCategory.display_order.asc()).all()
    templates = DesignTemplate.query.filter_by(is_published=True).all()

    category_slug = request.args.get("category")
    if category_slug:
        selected_category = DesignCategory.query.filter_by(slug=category_slug).first()
        if selected_category:
            templates = [t for t in templates if t.category_id == selected_category.id]

    return render_template(
        "design-showcase.html",
        page_title="Explore My Designs | Dax Prajapati",
        meta_description="Explore curated website designs, choose your preferred visual direction, and request a tailored quotation.",
        canonical_url="https://prajapatidax.co.in/design-showcase",
        og_title="Explore My Designs | Your Vision. My Creativity.",
        og_description="Explore different website designs, choose your preferred visual direction and tell me what you want to build.",
        categories=categories,
        templates=templates,
        current_category=category_slug,
    )


@showcase_bp.route("/preview/<slug>")
def preview(slug):
    template = DesignTemplate.query.filter_by(slug=slug, is_published=True).first()
    if not template:
        abort(404)

    related = DesignTemplate.query.filter(
        DesignTemplate.id != template.id,
        DesignTemplate.category_id == template.category_id,
        DesignTemplate.is_published == True
    ).limit(3).all()

    return render_template(
        "design-preview.html",
        page_title=f"{template.name} — Design Reference | Dax Prajapati",
        meta_description=f"Design reference preview of {template.name}. Explore high-resolution responsive layouts across laptop, tablet, and mobile formats.",
        canonical_url=f"https://prajapatidax.co.in/design-showcase/preview/{template.slug}",
        og_title=f"{template.name} — Design Reference Preview",
        og_description=template.description,
        template=template,
        related_templates=related,
    )


@showcase_bp.route("/frame/<slug>")
def interactive_frame(slug):
    """Render the inner interactive mock webpage for iframe display."""
    template = DesignTemplate.query.filter_by(slug=slug).first()
    if not template:
        abort(404)

    return render_template(
        "showcase-frame.html",
        template=template,
    )
