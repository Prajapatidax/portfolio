"""
Vercel Serverless Function Entry Point for Flask Application.
Routes all serverless requests into Dax Prajapati's Flask application.
"""
import os
import sys
from pathlib import Path

# Ensure project root is in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Import unified Flask application
from app import app, application

# Expose app instance for Vercel Python Serverless runtime
__all__ = ["app", "application"]

if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "1") == "1"
    app.run(host=host, port=port, debug=debug)
