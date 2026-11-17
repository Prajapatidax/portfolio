from pathlib import Path
from flask import Blueprint, render_template, send_from_directory, current_app, Response, url_for, redirect, request, flash, jsonify
from backend import db
from backend.models.design import DesignTemplate
from backend.models.contact import ContactMessage
from backend.services.activity_service import notify_admin, log_activity
from backend.utils.security import sanitize_text, get_client_ip, validate_csrf_token
from backend.utils.validators import validate_contact_payload

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
@main_bp.route("/index.html")
def index():
    return render_template(
        "index.html",
        page_title="Dax Prajapati | Full Stack Dev & Security Learner",
        meta_description="Personal portfolio of Dax Prajapati — Full Stack Developer & Cybersecurity enthusiast. Crafting fast, accessible, secure, and visually stunning web experiences.",
        canonical_url="https://prajapatidax.co.in/",
        og_title="Dax Prajapati | Full Stack Dev & Security Learner",
        og_description="Explore full-stack web applications, secure architectures, and interactive modern designs crafted by Dax Prajapati.",
        og_image="https://prajapatidax.co.in/static/assets/photo.png",
    )


@main_bp.route("/about")
@main_bp.route("/about.html")
def about():
    return render_template(
        "about.html",
        page_title="About Me | Dax Prajapati",
        meta_description="Learn more about Dax Prajapati's background, technical skills, philosophy, tools, and experience in building resilient digital products.",
        canonical_url="https://prajapatidax.co.in/about",
        og_title="About Dax Prajapati | Developer & Cybersecurity Learner",
        og_description="Background, technical skills, and journey of Dax Prajapati across full stack development and application security.",
        og_image="https://prajapatidax.co.in/static/assets/dax.jpeg",
    )


@main_bp.route("/projects")
@main_bp.route("/projects.html")
def projects():
    return render_template(
        "projects.html",
        page_title="All Projects | Dax Prajapati",
        meta_description="Browse featured projects including Devvault, Sortify, Mindmate, Earth Vision, and custom web applications by Dax Prajapati.",
        canonical_url="https://prajapatidax.co.in/projects",
        og_title="Projects Archive | Dax Prajapati",
        og_description="A curated showcase of engineering projects spanning full stack, frontend systems, AI integrations, and security utilities.",
        og_image="https://prajapatidax.co.in/static/assets/mindmate.png",
    )


@main_bp.route("/contact", methods=["GET", "POST"])
@main_bp.route("/contact.html", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        csrf = request.form.get("csrf_token")
        if not validate_csrf_token(csrf):
            flash("Session token expired. Please try submitting again.", "error")
            return redirect(url_for("main.contact"))

        raw_data = {
            "name": request.form.get("name", ""),
            "email": request.form.get("email", ""),
            "subject": request.form.get("subject", ""),
            "message": request.form.get("message", ""),
        }
        is_valid, errors = validate_contact_payload(raw_data)
        if not is_valid:
            err_msg = next(iter(errors.values())) if errors else "Invalid input"
            flash(err_msg, "error")
            return redirect(url_for("main.contact"))

        client_ip = get_client_ip()
        user_agent = (request.user_agent.string or "")[:300]

        msg = ContactMessage(
            name=sanitize_text(raw_data["name"], 150),
            email=raw_data["email"].strip().lower(),
            subject=sanitize_text(raw_data["subject"], 200),
            message=sanitize_text(raw_data["message"]),
            status="unread",
            ip_address=client_ip,
            user_agent=user_agent,
        )
        db.session.add(msg)
        db.session.commit()

        # Notify administrator
        notify_admin(
            title=f"New Message from {msg.name}",
            message=f"Subject: {msg.subject}\nFrom: {msg.email}",
            category="contact",
            link_url=f"/admin/contact-messages#{msg.id}",
        )
        log_activity(
            action_type="contact_message_received",
            description=f"Received message '{msg.subject}' from {msg.email}",
            record_id=str(msg.id),
            record_type="contact",
            ip_address=client_ip,
        )

        flash("Thank you for reaching out! Your message has been received and I'll get back to you shortly.", "success")
        return redirect(url_for("main.contact"))

    return render_template(
        "contact.html",
        page_title="Contact | Dax Prajapati",
        meta_description="Get in touch with Dax Prajapati for web development opportunities, engineering collaborations, or security audits.",
        canonical_url="https://prajapatidax.co.in/contact",
        og_title="Get In Touch | Dax Prajapati",
        og_description="Connect directly via email, GitHub, LinkedIn, or schedule an inquiry.",
        og_image="https://prajapatidax.co.in/static/assets/logo.png",
    )


@main_bp.route("/api/contact", methods=["POST"])
def api_contact():
    data = request.get_json(silent=True) or request.form.to_dict()
    csrf = request.headers.get("X-CSRF-Token") or data.get("csrf_token")
    if not validate_csrf_token(csrf):
        return jsonify({"status": "error", "message": "Invalid CSRF session token"}), 400

    is_valid, errors = validate_contact_payload(data)
    if not is_valid:
        return jsonify({"status": "error", "errors": errors}), 422

    client_ip = get_client_ip()
    user_agent = (request.user_agent.string or "")[:300]

    msg = ContactMessage(
        name=sanitize_text(data["name"], 150),
        email=data["email"].strip().lower(),
        subject=sanitize_text(data["subject"], 200),
        message=sanitize_text(data["message"]),
        status="unread",
        ip_address=client_ip,
        user_agent=user_agent,
    )
    db.session.add(msg)
    db.session.commit()

    notify_admin(
        title=f"New Message from {msg.name}",
        message=f"Subject: {msg.subject}\nFrom: {msg.email}",
        category="contact",
        link_url=f"/admin/contact-messages#{msg.id}",
    )
    log_activity(
        action_type="contact_message_received",
        description=f"Received API message '{msg.subject}' from {msg.email}",
        record_id=str(msg.id),
        record_type="contact",
        ip_address=client_ip,
    )

    return jsonify({
        "status": "success",
        "message": "Message sent successfully! Dax will get back to you shortly.",
        "id": msg.id,
    }), 201


@main_bp.route("/Resume.pdf")
@main_bp.route("/resume")
def resume():
    static_assets = Path(current_app.root_path).parent / "static" / "assets"
    return send_from_directory(static_assets, "Resume.pdf", mimetype="application/pdf")


@main_bp.route("/assets/<path:filename>")
def direct_assets(filename):
    """Serve legacy assets path directly so existing references stay 100% operational."""
    static_assets = Path(current_app.root_path).parent / "static" / "assets"
    return send_from_directory(static_assets, filename)


@main_bp.route("/robots.txt")
def robots_txt():
    content = """User-agent: *
Allow: /
Allow: /about
Allow: /projects
Allow: /contact
Allow: /design-showcase
Allow: /Resume.pdf
Disallow: /admin
Disallow: /admin/
Disallow: /api/
Disallow: /quotation/submit

Sitemap: https://prajapatidax.co.in/sitemap.xml
"""
    return Response(content, mimetype="text/plain")


@main_bp.route("/sitemap.xml")
def sitemap_xml():
    published_designs = DesignTemplate.query.filter_by(is_published=True).all()
    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        '  <url><loc>https://prajapatidax.co.in/</loc><changefreq>weekly</changefreq><priority>1.0</priority></url>',
        '  <url><loc>https://prajapatidax.co.in/about</loc><changefreq>monthly</changefreq><priority>0.8</priority></url>',
        '  <url><loc>https://prajapatidax.co.in/projects</loc><changefreq>weekly</changefreq><priority>0.9</priority></url>',
        '  <url><loc>https://prajapatidax.co.in/design-showcase</loc><changefreq>weekly</changefreq><priority>0.9</priority></url>',
        '  <url><loc>https://prajapatidax.co.in/contact</loc><changefreq>monthly</changefreq><priority>0.7</priority></url>',
    ]
    for design in published_designs:
        xml_lines.append(
            f'  <url><loc>https://prajapatidax.co.in/design-showcase/preview/{design.slug}</loc><changefreq>monthly</changefreq><priority>0.7</priority></url>'
        )
    xml_lines.append('</urlset>')
    return Response("\n".join(xml_lines), mimetype="application/xml")


@main_bp.route("/storage/preview/<path:object_key>")
def storage_preview(object_key):
    """
    Secure endpoint for rendering UI template preview images from private Neon Object Storage.
    Generates a short-lived presigned GET URL and issues a temporary redirect (307)
    with HTTP caching headers (Cache-Control: public, max-age=3600).
    """
    try:
        from backend.services.neon_storage import storage_service
        presigned_url = storage_service.generate_presigned_url(object_key, expires_in=3600)
        res = redirect(presigned_url, code=307)
        res.headers["Cache-Control"] = "public, max-age=3600"
        return res
    except Exception as e:
        current_app.logger.warning(f"Storage preview error for '{object_key}': {e}")
        static_assets = Path(current_app.root_path).parent / "static" / "assets"
        return send_from_directory(static_assets, "photo.png", mimetype="image/png")

