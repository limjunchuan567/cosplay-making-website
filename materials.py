"""
materials.py — Smart Bill of Materials Blueprint (Level 5B).

Routes:
  POST /projects/<id>/materials/add          — Add material item
  POST /projects/<id>/materials/<mid>/edit   — Edit material
  POST /projects/<id>/materials/<mid>/delete — Delete material
"""

from flask import Blueprint, flash, g, redirect, request, url_for
from db import get_db
from auth import login_required

bp = Blueprint("materials", __name__)


def _own_project(project_id):
    db = get_db()
    p = db.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    if p is None or p["user_id"] != g.user["id"]:
        flash("Project not found.", "error")
        return None
    return p


@bp.route("/projects/<int:project_id>/materials/add", methods=("POST",))
@login_required
def add(project_id):
    if not _own_project(project_id):
        return redirect(url_for("index"))

    item_name    = request.form.get("item_name", "").strip()
    category     = request.form.get("category", "other")
    part_id      = request.form.get("part_id") or None
    quantity     = request.form.get("quantity", "1")
    unit         = request.form.get("unit", "pcs").strip() or "pcs"
    price_est    = request.form.get("price_est", "0")
    in_stash     = 1 if request.form.get("in_stash") else 0
    vendor_url   = request.form.get("vendor_url", "").strip() or None
    notes        = request.form.get("notes", "").strip() or None

    if not item_name:
        flash("Item name is required.", "error")
        return redirect(url_for("projects.view", project_id=project_id))

    try:
        quantity  = float(quantity)
        price_est = float(price_est)
    except ValueError:
        quantity, price_est = 1.0, 0.0

    db = get_db()
    db.execute(
        """INSERT INTO materials
           (project_id, part_id, item_name, category, quantity, unit,
            price_est, in_stash, vendor_url, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (project_id, part_id, item_name, category, quantity, unit,
         price_est, in_stash, vendor_url, notes)
    )
    db.commit()
    flash(f"'{item_name}' added to materials.", "success")
    return redirect(url_for("projects.view", project_id=project_id))


@bp.route("/projects/<int:project_id>/materials/<int:mat_id>/edit", methods=("POST",))
@login_required
def edit(project_id, mat_id):
    if not _own_project(project_id):
        return redirect(url_for("index"))

    item_name    = request.form.get("item_name", "").strip()
    category     = request.form.get("category", "other")
    part_id      = request.form.get("part_id") or None
    quantity     = request.form.get("quantity", "1")
    unit         = request.form.get("unit", "pcs").strip() or "pcs"
    price_est    = request.form.get("price_est", "0")
    price_actual = request.form.get("price_actual", "").strip() or None
    in_stash     = 1 if request.form.get("in_stash") else 0
    status       = request.form.get("status", "needed")
    vendor_url   = request.form.get("vendor_url", "").strip() or None
    notes        = request.form.get("notes", "").strip() or None

    if not item_name:
        flash("Item name is required.", "error")
        return redirect(url_for("projects.view", project_id=project_id))

    try:
        quantity  = float(quantity)
        price_est = float(price_est)
        price_actual = float(price_actual) if price_actual else None
    except ValueError:
        quantity, price_est, price_actual = 1.0, 0.0, None

    db = get_db()
    db.execute(
        """UPDATE materials SET
             item_name = ?, category = ?, part_id = ?, quantity = ?, unit = ?,
             price_est = ?, price_actual = ?, in_stash = ?, status = ?,
             vendor_url = ?, notes = ?
           WHERE id = ? AND project_id = ?""",
        (item_name, category, part_id, quantity, unit,
         price_est, price_actual, in_stash, status,
         vendor_url, notes, mat_id, project_id)
    )
    db.commit()
    flash(f"'{item_name}' updated.", "success")
    return redirect(url_for("projects.view", project_id=project_id))


@bp.route("/projects/<int:project_id>/materials/<int:mat_id>/delete", methods=("POST",))
@login_required
def delete(project_id, mat_id):
    if not _own_project(project_id):
        return redirect(url_for("index"))

    db = get_db()
    mat = db.execute("SELECT item_name FROM materials WHERE id = ?", (mat_id,)).fetchone()
    db.execute("DELETE FROM materials WHERE id = ? AND project_id = ?", (mat_id, project_id))
    db.commit()
    if mat:
        flash(f"'{mat['item_name']}' removed.", "info")
    return redirect(url_for("projects.view", project_id=project_id))
