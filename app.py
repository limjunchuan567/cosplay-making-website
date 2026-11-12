"""
app.py — CosplayHub Flask application entry point.
"""

import os
import secrets
from datetime import date
from flask import Flask, render_template, g
from auth import login_required


def create_app():
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", secrets.token_hex(32)),
        DATABASE=os.path.join(app.instance_path, "cosplayhub.db"),
        MAX_CONTENT_LENGTH=16 * 1024 * 1024,
        ALLOWED_EXTENSIONS={"png", "jpg", "jpeg", "gif", "webp"},
    )

    os.makedirs(app.instance_path, exist_ok=True)

    # ── Database ───────────────────────────────────────────────────────────
    from db import init_app as db_init_app
    db_init_app(app)

    # ── Blueprints ─────────────────────────────────────────────────────────
    from auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    from projects import bp as projects_bp
    app.register_blueprint(projects_bp)

    # ── Dashboard (root route) ─────────────────────────────────────────────
    @app.route("/")
    @login_required
    def index():
        from db import get_db
        db = get_db()

        # Fetch all projects for this user with budget spend calculated
        rows = db.execute(
            """SELECT p.*,
                      COALESCE(SUM(m.quantity * m.price_est), 0) as budget_spent
               FROM projects p
               LEFT JOIN materials m
                 ON m.project_id = p.id AND m.in_stash = 0
               WHERE p.user_id = ?
               GROUP BY p.id
               ORDER BY p.updated_at DESC""",
            (g.user["id"],)
        ).fetchall()

        # Convert to dicts and add days_left
        projects = []
        today = date.today()
        for row in rows:
            p = dict(row)
            if p.get("convention_date"):
                try:
                    con_date = date.fromisoformat(p["convention_date"])
                    p["days_left"] = (con_date - today).days
                except ValueError:
                    p["days_left"] = None
            else:
                p["days_left"] = None
            projects.append(p)

        return render_template("index.html", projects=projects)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
