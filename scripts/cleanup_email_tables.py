"""
Database Cleanup Script — Safely drop email_logs table from PostgreSQL / SQLite.
Preserves all customer information and quotation data.
"""
from backend import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    engine = db.engine
    dialect = engine.dialect.name
    print(f"Connected to database dialect: {dialect}")

    with engine.connect() as conn:
        if dialect == "postgresql":
            conn.execute(text("DROP TABLE IF EXISTS email_logs CASCADE;"))
            print("PostgreSQL: Dropped table email_logs CASCADE if existed.")
        else:
            conn.execute(text("DROP TABLE IF EXISTS email_logs;"))
            print("SQLite: Dropped table email_logs if existed.")
        conn.commit()

    print("Email database cleanup completed successfully.")
