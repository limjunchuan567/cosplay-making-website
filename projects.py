"""
projects.py — CosplayHub Project CRUD Blueprint (Level 4).

Routes:
  GET  /projects/new          — New project form
  POST /projects/new          — Create project
  GET  /projects/<id>         — View project overview
  GET  /projects/<id>/edit    — Edit project form
  POST /projects/<id>/edit    — Save edits
  POST /projects/<id>/delete  — Delete project
"""

from flask import (
    Blueprint, flash, g, redirect, render_template,
    request, url_for, abort
)
from db import get_db
from auth import login_required

bp = Blueprint("projects", __name__, url_prefix="/projects")


def get_project(project_id, check_owner=True):
    """
    Fetch a project by ID. Aborts with 404 if not found.
    If check_owner=True, aborts with 403 if the project belongs to another user.
    """
    db = get_db()
    project = db.execute(
        "SELECT * FROM projects WHERE id = ?", (project_id,)
    ).fetchone()

    if project is None:
        abort(404, f"Project #{project_id} not found.")
    if check_owner and project["user_id"] != g.user["id"]:
        abort(403, "You do not have permission to access this project.")

    return project


# ── New Project ────────────────────────────────────────────────────────────
@bp.route("/new", methods=("GET", "POST"))
@login_required
def new():
    if request.method == "POST":
        name            = request.form.get("name", "").strip()
        character_name  = request.form.get("character_name", "").strip()
        source_series   = request.form.get("source_series", "").strip()
        convention_name = request.form.get("convention_name", "").strip()
        convention_date = request.form.get("convention_date", "").strip() or None
        budget_limit    = request.form.get("budget_limit", "0").strip()
        notes           = request.form.get("notes", "").strip()
        error           = None

        if not name:
            error = "Project name is required."
        else:
            try:
                budget_limit = float(budget_limit)
            except ValueError:
                budget_limit = 0.0

        if error is None:
            db = get_db()
            db.execute(
                """INSERT INTO projects
                   (user_id, name, character_name, source_series,
                    convention_name, convention_date, budget_limit, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (g.user["id"], name, character_name, source_series,
                 convention_name, convention_date, budget_limit, notes)
            )
            db.commit()
            project_id = db.execute(
                "SELECT last_insert_rowid() as id"
            ).fetchone()["id"]
            flash(f"Project '{name}' created!", "success")
            return redirect(url_for("projects.view", project_id=project_id))

        flash(error, "error")

    return render_template("projects/new.html")


# ── View Project ───────────────────────────────────────────────────────────
@bp.route("/<int:project_id>")
@login_required
def view(project_id):
    project = get_project(project_id)
    db      = get_db()

    parts = db.execute(
        "SELECT * FROM parts WHERE project_id = ? ORDER BY sort_order, id",
        (project_id,)
    ).fetchall()

    tasks = db.execute(
        """SELECT t.*, p.name as part_name
           FROM tasks t
           LEFT JOIN parts p ON t.part_id = p.id
           WHERE t.project_id = ?
           ORDER BY
             CASE t.priority
               WHEN 'critical' THEN 1
               WHEN 'high'     THEN 2
               WHEN 'medium'   THEN 3
               ELSE 4 END,
             t.created_at""",
        (project_id,)
    ).fetchall()

    materials = db.execute(
        """SELECT m.*, p.name as part_name
           FROM materials m
           LEFT JOIN parts p ON m.part_id = p.id
           WHERE m.project_id = ?
           ORDER BY m.status, m.item_name""",
        (project_id,)
    ).fetchall()

    # Budget summary
    budget_est = db.execute(
        """SELECT COALESCE(SUM(quantity * price_est), 0) as total
           FROM materials WHERE project_id = ? AND in_stash = 0""",
        (project_id,)
    ).fetchone()["total"]

    budget_actual = db.execute(
        """SELECT COALESCE(SUM(quantity * price_actual), 0) as total
           FROM materials
           WHERE project_id = ? AND in_stash = 0 AND price_actual IS NOT NULL""",
        (project_id,)
    ).fetchone()["total"]

    # Task progress
    task_total = len(tasks)
    task_done  = sum(1 for t in tasks if t["status"] == "done")

    # Convention countdown
    days_left = None
    if project["convention_date"]:
        from datetime import date
        try:
            con_date  = date.fromisoformat(project["convention_date"])
            days_left = (con_date - date.today()).days
        except ValueError:
            pass

    return render_template(
        "projects/view.html",
        project=project,
        parts=parts,
        tasks=tasks,
        materials=materials,
        budget_est=budget_est,
        budget_actual=budget_actual,
        task_total=task_total,
        task_done=task_done,
        days_left=days_left,
    )


# ── Edit Project ───────────────────────────────────────────────────────────
@bp.route("/<int:project_id>/edit", methods=("GET", "POST"))
@login_required
def edit(project_id):
    project = get_project(project_id)

    if request.method == "POST":
        name            = request.form.get("name", "").strip()
        character_name  = request.form.get("character_name", "").strip()
        source_series   = request.form.get("source_series", "").strip()
        status          = request.form.get("status", "planning")
        convention_name = request.form.get("convention_name", "").strip()
        convention_date = request.form.get("convention_date", "").strip() or None
        budget_limit    = request.form.get("budget_limit", "0").strip()
        notes           = request.form.get("notes", "").strip()
        error           = None

        if not name:
            error = "Project name is required."
        else:
            try:
                budget_limit = float(budget_limit)
            except ValueError:
                budget_limit = 0.0

        if error is None:
            db = get_db()
            db.execute(
                """UPDATE projects SET
                     name = ?, character_name = ?, source_series = ?,
                     status = ?, convention_name = ?, convention_date = ?,
                     budget_limit = ?, notes = ?,
                     updated_at = datetime('now')
                   WHERE id = ?""",
                (name, character_name, source_series, status,
                 convention_name, convention_date, budget_limit, notes,
                 project_id)
            )
            db.commit()
            flash("Project updated!", "success")
            return redirect(url_for("projects.view", project_id=project_id))

        flash(error, "error")

    return render_template("projects/edit.html", project=project)


# ── Delete Project ─────────────────────────────────────────────────────────
@bp.route("/<int:project_id>/delete", methods=("POST",))
@login_required
def delete(project_id):
    project = get_project(project_id)
    db      = get_db()
    db.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    db.commit()
    flash(f"Project '{project['name']}' deleted.", "info")
    return redirect(url_for("index"))
