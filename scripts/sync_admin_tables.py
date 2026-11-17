"""
Safe database sync script to create new admin tables and update existing schemas.
"""
from backend import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    # 1. Create any newly registered tables (contact_messages, admin_notifications, admin_activity_logs, portfolio_settings)
    db.create_all()
    print("db.create_all() executed.")

    # 2. For PostgreSQL (and SQLite safe alter), ensure new columns exist on existing tables
    engine = db.engine
    dialect = engine.dialect.name
    print(f"Connected to dialect: {dialect}")

    if dialect == "postgresql":
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE quotation_requests ADD COLUMN IF NOT EXISTS priority VARCHAR(20) DEFAULT 'normal';"))
            conn.execute(text("ALTER TABLE quotation_requests ADD COLUMN IF NOT EXISTS is_archived BOOLEAN DEFAULT FALSE;"))
            conn.execute(text("ALTER TABLE design_templates ADD COLUMN IF NOT EXISTS is_archived BOOLEAN DEFAULT FALSE;"))
            conn.commit()
            print("PostgreSQL columns verified and updated.")
    elif dialect == "sqlite":
        # For SQLite, check if column exists before alter
        with engine.connect() as conn:
            for table, col, col_type in [
                ("quotation_requests", "priority", "VARCHAR(20) DEFAULT 'normal'"),
                ("quotation_requests", "is_archived", "BOOLEAN DEFAULT 0"),
                ("design_templates", "is_archived", "BOOLEAN DEFAULT 0"),
            ]:
                cols = [row[1] for row in conn.execute(text(f"PRAGMA table_info({table});")).fetchall()]
                if col not in cols:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {col_type};"))
                    print(f"Added {col} to {table} in SQLite.")
            conn.commit()

    print("Database sync completed successfully.")
