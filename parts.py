"""
parts.py — Costume Parts Blueprint (Level 5A).

Routes:
  POST /projects/<id>/parts/add          — Add a part
  POST /projects/<id>/parts/<pid>/edit   — Edit part name/category/status
  POST /projects/<id>/parts/<pid>/delete — Delete part (cascades tasks/materials)
"""

from flask import Blueprint, flash, g, redirect, request, url_for
from db import get_db
from auth import login_required

bp = Blueprint("parts", __name__)


def _own_project(project_id):
    db = get_db()
    p = db.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    if p is None or p["user_id"] != g.user["id"]:
        flash("Project not found.", "error")
        return None
    return p


@bp.route("/projects/<int:project_id>/parts/add", methods=("POST",))
@login_required
def add(project_id):
    if not _own_project(project_id):
        return redirect(url_for("index"))

    name     = request.form.get("part_name", "").strip()
    category = request.form.get("part_category", "other")

    if not name:
        flash("Part name is required.", "error")
        return redirect(url_for("projects.view", project_id=project_id))

    db = get_db()
    # Place it at the end of the sort order
    max_order = db.execute(
        "SELECT COALESCE(MAX(sort_order), -1) as m FROM parts WHERE project_id = ?",
        (project_id,)
    ).fetchone()["m"]

    db.execute(
        "INSERT INTO parts (project_id, name, category, sort_order) VALUES (?, ?, ?, ?)",
        (project_id, name, category, max_order + 1)
    )
    db.commit()
    flash(f"Part '{name}' added.", "success")
    return redirect(url_for("projects.view", project_id=project_id))


@bp.route("/projects/<int:project_id>/parts/<int:part_id>/edit", methods=("POST",))
@login_required
def edit(project_id, part_id):
    if not _own_project(project_id):
        return redirect(url_for("index"))

    name     = request.form.get("part_name", "").strip()
    category = request.form.get("part_category", "other")
    status   = request.form.get("part_status", "not_started")

    if not name:
        flash("Part name is required.", "error")
        return redirect(url_for("projects.view", project_id=project_id))

    db = get_db()
    db.execute(
        "UPDATE parts SET name = ?, category = ?, status = ? WHERE id = ? AND project_id = ?",
        (name, category, status, part_id, project_id)
    )
    db.commit()
    flash(f"Part updated.", "success")
    return redirect(url_for("projects.view", project_id=project_id))


@bp.route("/projects/<int:project_id>/parts/<int:part_id>/delete", methods=("POST",))
@login_required
def delete(project_id, part_id):
    if not _own_project(project_id):
        return redirect(url_for("index"))

    db = get_db()
    part = db.execute("SELECT name FROM parts WHERE id = ?", (part_id,)).fetchone()
    db.execute("DELETE FROM parts WHERE id = ? AND project_id = ?", (part_id, project_id))
    db.commit()
    if part:
        flash(f"Part '{part['name']}' deleted.", "info")
    return redirect(url_for("projects.view", project_id=project_id))
