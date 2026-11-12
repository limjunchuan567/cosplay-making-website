"""
tasks.py — Tasks Blueprint (Level 5A).

Routes:
  POST /projects/<id>/tasks/add          — Add task
  POST /projects/<id>/tasks/<tid>/status — Toggle status
  POST /projects/<id>/tasks/<tid>/delete — Delete task
"""

from flask import Blueprint, flash, g, redirect, request, url_for
from db import get_db
from auth import login_required

bp = Blueprint("tasks", __name__)


def _own_project(project_id):
    db = get_db()
    p = db.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    if p is None or p["user_id"] != g.user["id"]:
        flash("Project not found.", "error")
        return None
    return p


@bp.route("/projects/<int:project_id>/tasks/add", methods=("POST",))
@login_required
def add(project_id):
    if not _own_project(project_id):
        return redirect(url_for("index"))

    title    = request.form.get("task_title", "").strip()
    part_id  = request.form.get("task_part_id") or None
    priority = request.form.get("task_priority", "medium")
    due_date = request.form.get("task_due_date", "").strip() or None

    if not title:
        flash("Task title is required.", "error")
        return redirect(url_for("projects.view", project_id=project_id))

    db = get_db()
    db.execute(
        """INSERT INTO tasks (project_id, part_id, title, priority, due_date)
           VALUES (?, ?, ?, ?, ?)""",
        (project_id, part_id, title, priority, due_date)
    )
    db.commit()
    flash(f"Task '{title}' added.", "success")
    return redirect(url_for("projects.view", project_id=project_id))


@bp.route("/projects/<int:project_id>/tasks/<int:task_id>/status", methods=("POST",))
@login_required
def toggle_status(project_id, task_id):
    if not _own_project(project_id):
        return redirect(url_for("index"))

    new_status = request.form.get("status", "todo")
    db = get_db()
    db.execute(
        "UPDATE tasks SET status = ? WHERE id = ? AND project_id = ?",
        (new_status, task_id, project_id)
    )
    db.commit()
    return redirect(url_for("projects.view", project_id=project_id))


@bp.route("/projects/<int:project_id>/tasks/<int:task_id>/delete", methods=("POST",))
@login_required
def delete(project_id, task_id):
    if not _own_project(project_id):
        return redirect(url_for("index"))

    db = get_db()
    task = db.execute("SELECT title FROM tasks WHERE id = ?", (task_id,)).fetchone()
    db.execute("DELETE FROM tasks WHERE id = ? AND project_id = ?", (task_id, project_id))
    db.commit()
    if task:
        flash(f"Task '{task['title']}' deleted.", "info")
    return redirect(url_for("projects.view", project_id=project_id))
