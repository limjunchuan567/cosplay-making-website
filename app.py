"""
app.py — CosplayHub Flask application entry point.

This file:
  - Creates and configures the Flask app instance.
  - Registers the database helpers (db.init_app).
  - Registers all route Blueprints.
  - Provides a local development server entry point.
"""

import os
import secrets
from flask import Flask


def create_app():
    """Application factory — creates and configures the Flask app."""
    app = Flask(__name__, instance_relative_config=True)

    # ------------------------------------------------------------------ #
    # Core configuration
    # ------------------------------------------------------------------ #
    app.config.from_mapping(
        # Randomly generated secret key; override via instance/config.py in prod.
        SECRET_KEY=os.environ.get("SECRET_KEY", secrets.token_hex(32)),
        # SQLite database lives inside the 'instance' folder (not committed to git).
        DATABASE=os.path.join(app.instance_path, "cosplayhub.db"),
        # Maximum upload size for reference images: 16 MB.
        MAX_CONTENT_LENGTH=16 * 1024 * 1024,
        # Allowed image extensions for the reference board.
        ALLOWED_EXTENSIONS={"png", "jpg", "jpeg", "gif", "webp"},
    )

    # Ensure the instance folder (for the .db file) exists.
    os.makedirs(app.instance_path, exist_ok=True)

    # ------------------------------------------------------------------ #
    # Register database lifecycle helpers
    # ------------------------------------------------------------------ #
    from db import init_app as db_init_app
    db_init_app(app)

    # ------------------------------------------------------------------ #
    # Register Blueprints (routes will be added in later levels)
    # ------------------------------------------------------------------ #
    # Level 2: auth routes  (register, login, logout)
    # from auth import bp as auth_bp
    # app.register_blueprint(auth_bp)

    # Level 4: project CRUD routes
    # from projects import bp as projects_bp
    # app.register_blueprint(projects_bp)

    # Temporary root route so we can confirm the app boots correctly.
    @app.route("/")
    def index():
        return (
            "<h2>🧵 CosplayHub — Backend is alive!</h2>"
            "<p>Database and Flask app initialised successfully.</p>"
        )

    return app


# ------------------------------------------------------------------ #
# Local development entry point
# Run with:  python app.py   (or flask --app app run --debug)
# ------------------------------------------------------------------ #
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
