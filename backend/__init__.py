import os
import urllib.parse
from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()


class VercelPathCorrectionMiddleware:
    """
    WSGI Middleware to restore client request PATH_INFO on Vercel.
    When Vercel processes rewrite rules (e.g. source /(.*) -> destination /api/index?__vercel_path=/$1),
    this middleware extracts the real client request path and restores PATH_INFO so Flask routes match.
    """
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        query_string = environ.get("QUERY_STRING", "")

        # 1. Primary resolution: Extract explicit path forwarded via Vercel rewrite parameter
        if "__vercel_path" in query_string:
            params = urllib.parse.parse_qs(query_string, keep_blank_values=True)
            if "__vercel_path" in params and params["__vercel_path"]:
                target_path = params.pop("__vercel_path")[0]
                if not target_path.startswith("/"):
                    target_path = "/" + target_path
                while target_path.startswith("//"):
                    target_path = target_path[1:]
                environ["PATH_INFO"] = target_path

                # Reconstruct query string without internal __vercel_path parameter
                flat_params = [(k, v) for k, vals in params.items() for v in vals]
                environ["QUERY_STRING"] = urllib.parse.urlencode(flat_params)
        else:
            # 2. Secondary fallback: Check Vercel routing headers
            matched_path = (
                environ.get("HTTP_X_MATCHED_PATH")
                or environ.get("HTTP_X_FORWARDED_URI")
                or environ.get("HTTP_X_VERCEL_FORWARDED_URI")
            )
            current_path = environ.get("PATH_INFO", "")
            if current_path in ("/api/index", "/api/index.py", "/api", "/api/"):
                if matched_path and matched_path not in ("/api/index", "/api/index.py", "/api", "/api/"):
                    clean_path = matched_path.split("?")[0]
                    environ["PATH_INFO"] = clean_path
                else:
                    environ["PATH_INFO"] = "/"

        environ["SCRIPT_NAME"] = ""
        return self.wsgi_app(environ, start_response)


def create_app(config_name=None):
    if config_name is None:
        if os.getenv("VERCEL"):
            config_name = "production"
        else:
            config_name = os.getenv("FLASK_ENV", "development")

    from config import BASE_DIR, config_by_name

    app = Flask(
        __name__,
        template_folder=str(BASE_DIR / "templates"),
        static_folder=str(BASE_DIR / "static"),
        static_url_path="/static",
    )
    
    app.config.from_object(config_by_name.get(config_name, config_by_name["default"]))

    # Apply ProxyFix middleware for reverse proxies (Vercel, Nginx, cloud load balancers)
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    # Apply Vercel path correction middleware for Vercel serverless rewrites
    app.wsgi_app = VercelPathCorrectionMiddleware(app.wsgi_app)

    # Ensure engine options only apply to PostgreSQL
    if "postgresql" not in app.config.get("SQLALCHEMY_DATABASE_URI", ""):
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {}

    # Ensure instance and upload directories exist (safely catch read-only filesystem in serverless)
    try:
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    except OSError:
        pass

    try:
        os.makedirs(app.config["BASE_DIR"] / "instance", exist_ok=True)
    except OSError:
        pass

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Register models so Alembic / SQLAlchemy knows them
    with app.app_context():
        import backend.models  # noqa: F401

    # Register Blueprints
    from backend.routes.main import main_bp
    from backend.routes.showcase import showcase_bp
    from backend.routes.quotation import quotation_bp
    from backend.routes.admin import admin_bp
    from backend.routes.api import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(showcase_bp)
    app.register_blueprint(quotation_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

    # Global Error Handlers
    register_error_handlers(app)

    # Security Headers Hook
    register_security_headers(app)

    # Helper context processor
    @app.context_processor
    def inject_global_data():
        from backend.utils.security import generate_csrf_token
        return {
            "csrf_token": generate_csrf_token,
            "site_url": "https://prajapatidax.co.in",
            "author_name": "Dax Prajapati",
            "year": 2026,
        }

    return app


def register_error_handlers(app):
    @app.errorhandler(404)
    def page_not_found(e):
        if request.path.startswith("/api/"):
            return jsonify({
                "status": "error",
                "message": "API endpoint not found",
                "error_code": 404
            }), 404
        return render_template(
            "404.html",
            page_title="Oops! Page Not Found | Dax Prajapati",
            meta_description="The page you are looking for does not exist or may have been moved."
        ), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        if request.path.startswith("/api/"):
            return jsonify({
                "status": "error",
                "message": "Internal server error occurred",
                "error_code": 500
            }), 500
        return render_template(
            "404.html",
            page_title="Internal Server Error | Dax Prajapati",
            meta_description="An unexpected server error occurred."
        ), 500

    @app.errorhandler(403)
    def forbidden(e):
        if request.path.startswith("/api/"):
            return jsonify({
                "status": "error",
                "message": "Access forbidden",
                "error_code": 403
            }), 403
        return render_template(
            "404.html",
            page_title="Forbidden | Dax Prajapati",
            meta_description="You do not have permission to view this resource."
        ), 403


def register_security_headers(app):
    @app.after_request
    def set_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        return response
