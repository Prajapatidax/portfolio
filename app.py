import os
from backend import create_app, db
from backend.services.auth_service import seed_initial_admin
from backend.services.design_service import seed_default_designs

app = create_app()

# Expose 'application' alias for WSGI servers and Vercel
application = app


def init_app_db(flask_app):
    """Safely initialize database tables and seed accounts if needed."""
    if os.getenv("SKIP_DB_INIT") == "1":
        return

    with flask_app.app_context():
        try:
            # Create tables safely in configured database (Neon PostgreSQL or fallback SQLite)
            db.create_all()

            # Seed initial admin account from environment configuration
            admin_name = flask_app.config.get("ADMIN_NAME", "Dax Prajapati")
            admin_email = flask_app.config.get("ADMIN_EMAIL", "admin@prajapatidax.co.in")
            admin_password = flask_app.config.get("ADMIN_PASSWORD", "AdminPass@2026!")
            seed_initial_admin(admin_name, admin_email, admin_password)

            # Seed default UI showcase categories and templates
            seed_default_designs()
        except Exception as e:
            flask_app.logger.warning(f"Database initialization warning: {e}")


# Run safe DB initialization
init_app_db(app)

if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "1") == "1"

    print("\n" + "=" * 60)
    print(" ⚡ DAX PRAJAPATI PORTFOLIO & DESIGN SHOWCASE")
    print(f" 🚀 Running on: http://{host}:{port}")
    print(f" 🌐 Primary Site: http://localhost:{port}")
    print(f" 🎨 Design Showcase: http://localhost:{port}/design-showcase")
    print(f" 🛡️  Secure Admin Login: http://localhost:{port}/admin/login/version/101")
    print("=" * 60 + "\n")

    app.run(host=host, port=port, debug=debug)
