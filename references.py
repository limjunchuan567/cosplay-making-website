"""
references.py — Character Visual References & AI Costume Deconstruction Blueprint.

Enables cosplayers to:
  - Upload character visual references (concept art, turnarounds, screenshots).
  - Run Gemini Vision AI to automatically decompose the outfit into discrete craftable parts.
  - Generate personalized tailoring and build measurements based on the user's saved body profile.
  - One-click import detected parts, tasks, and materials into their project.
"""

import os
import uuid
import json
from flask import (
    Blueprint, flash, g, jsonify, redirect,
    request, url_for, current_app
)
from werkzeug.utils import secure_filename
from db import get_db
from auth import login_required
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

bp = Blueprint("references", __name__, url_prefix="/projects/<int:project_id>/references")


def _own_project(project_id):
    db = get_db()
    p = db.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    if p is None or p["user_id"] != g.user["id"]:
        return None
    return p


def _get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    from google import genai
    return genai.Client(api_key=api_key)


def _allowed_file(filename):
    allowed = current_app.config.get("ALLOWED_EXTENSIONS", {"png", "jpg", "jpeg", "gif", "webp"})
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed


@bp.route("/upload", methods=("POST",))
@login_required
def upload(project_id):
    project = _own_project(project_id)
    if not project:
        flash("Project not found.", "error")
        return redirect(url_for("index"))

    file = request.files.get("reference_image")
    caption = request.form.get("caption", "").strip()
    category = request.form.get("category", "turnaround")
    if category not in ("turnaround", "detail", "color_palette", "prop_blueprint", "inspiration"):
        category = "inspiration"

    if not file or file.filename == "":
        flash("Please select an image file to upload.", "warning")
        return redirect(url_for("projects.view", project_id=project_id))

    if not _allowed_file(file.filename):
        flash("Invalid file format. Allowed: PNG, JPG, JPEG, WEBP, GIF.", "error")
        return redirect(url_for("projects.view", project_id=project_id))

    ext = file.filename.rsplit(".", 1)[1].lower()
    unique_filename = f"p{project_id}_{uuid.uuid4().hex[:10]}.{ext}"
    upload_folder = os.path.join(current_app.static_folder, "uploads")
    os.makedirs(upload_folder, exist_ok=True)
    file_path = os.path.join(upload_folder, unique_filename)
    file.save(file_path)

    # Relative path stored in database
    rel_path = f"uploads/{unique_filename}"

    db = get_db()
    db.execute(
        """INSERT INTO references_board (project_id, image_path, caption, category)
           VALUES (?, ?, ?, ?)""",
        (project_id, rel_path, caption, category)
    )
    db.commit()

    flash("Character reference image uploaded! ✨", "success")
    return redirect(url_for("projects.view", project_id=project_id))


@bp.route("/<int:ref_id>/delete", methods=("POST",))
@login_required
def delete(project_id, ref_id):
    project = _own_project(project_id)
    if not project:
        flash("Project not found.", "error")
        return redirect(url_for("index"))

    db = get_db()
    row = db.execute(
        "SELECT * FROM references_board WHERE id = ? AND project_id = ?",
        (ref_id, project_id)
    ).fetchone()

    if row:
        full_path = os.path.join(current_app.static_folder, row["image_path"])
        if os.path.exists(full_path):
            try:
                os.remove(full_path)
            except OSError:
                pass
        db.execute("DELETE FROM references_board WHERE id = ?", (ref_id,))
        db.commit()
        flash("Reference image removed.", "info")

    return redirect(url_for("projects.view", project_id=project_id))


@bp.route("/<int:ref_id>/analyze", methods=("POST",))
@login_required
def analyze(project_id, ref_id):
    project = _own_project(project_id)
    if not project:
        return jsonify({"success": False, "error": "Project not found"}), 404

    client = _get_gemini_client()
    if not client:
        return jsonify({
            "success": False,
            "error": "Gemini API key is not configured in .env. Please check your setup."
        }), 500

    db = get_db()
    row = db.execute(
        "SELECT * FROM references_board WHERE id = ? AND project_id = ?",
        (ref_id, project_id)
    ).fetchone()
    if not row:
        return jsonify({"success": False, "error": "Reference image not found"}), 404

    image_full_path = os.path.join(current_app.static_folder, row["image_path"])
    if not os.path.exists(image_full_path):
        return jsonify({"success": False, "error": "Image file not found on disk"}), 404

    # Fetch user body measurements
    m_row = db.execute(
        "SELECT * FROM user_measurements WHERE user_id = ?", (g.user["id"],)
    ).fetchone()
    m = dict(m_row) if m_row else {}

    measurements_summary = []
    if m.get("height_cm"): measurements_summary.append(f"Height: {m['height_cm']}cm")
    if m.get("shoulder_width_cm"): measurements_summary.append(f"Shoulder width: {m['shoulder_width_cm']}cm")
    if m.get("head_circumference_cm"): measurements_summary.append(f"Head circumference: {m['head_circumference_cm']}cm")
    if m.get("chest_bust_cm"): measurements_summary.append(f"Chest/Bust: {m['chest_bust_cm']}cm")
    if m.get("waist_cm"): measurements_summary.append(f"Waist: {m['waist_cm']}cm")
    if m.get("hips_cm"): measurements_summary.append(f"Hips: {m['hips_cm']}cm")
    if m.get("torso_length_cm"): measurements_summary.append(f"Torso length: {m['torso_length_cm']}cm")
    if m.get("arm_length_cm"): measurements_summary.append(f"Arm length: {m['arm_length_cm']}cm")
    if m.get("bicep_circumference_cm"): measurements_summary.append(f"Bicep: {m['bicep_circumference_cm']}cm")
    if m.get("inseam_cm"): measurements_summary.append(f"Inseam: {m['inseam_cm']}cm")
    if m.get("thigh_circumference_cm"): measurements_summary.append(f"Thigh: {m['thigh_circumference_cm']}cm")
    if m.get("calf_circumference_cm"): measurements_summary.append(f"Calf: {m['calf_circumference_cm']}cm")

    measurements_text = ", ".join(measurements_summary) if measurements_summary else "No body measurements recorded yet (using standard proportions)."

    char_info = f"Character: {project.get('character_name') or 'Unknown'}"
    if project.get('source_series'):
        char_info += f" from '{project['source_series']}'"

    prompt = f"""
You are an elite, highly experienced cosplay maker, tailor, and prop designer.
Analyze this character reference image ({char_info}).

The cosplayer's recorded body measurements are:
{measurements_text}

Deconstruct the character's complete costume into discrete, realistic, craftable parts.
For EVERY costume piece you see (wig/hair, tops, jackets, armor pieces, trousers/skirts, gauntlets/gloves, boots/shoes, belts, props/accessories):

1. Name the part concisely (e.g. "Cropped Biker Jacket", "Spiky Styled Wig", "Shoulder Pauldron Pair", "Cargo Combat Pants", "Knee-High Armored Boots").
2. Assign the category strictly from: "wig", "garment", "armor", "prop", "footwear", "accessory", "makeup", or "other".
3. Identify the anatomical body zone strictly from: "head", "neck", "torso", "waist", "hips", "arms", "legs", or "feet".
4. Provide customized "sizing_guide": Calculate exact tailored cutting and fitting dimensions using the user's specific measurements above (or recommend ease / allowances). For instance: "Cut with chest circumference ~101cm (+5cm comfort ease), finish length 48cm from base of neck to waist".
5. Provide "crafting_tip": Specific recommended materials (e.g. 5mm high-density EVA foam, faux leather, 4-way stretch spandex, Worbla, heat gun shaping) and construction method.

Output strict JSON with this exact schema:
{{
  "character_name": "Name of character detected or confirmed",
  "overview": "Short 1-2 sentence overview of the costume silhouette and complexity",
  "parts": [
    {{
      "name": "Part name",
      "category": "wig|garment|armor|prop|footwear|accessory|makeup|other",
      "anatomical_zone": "head|neck|torso|waist|hips|arms|legs|feet",
      "description": "Visual details and features",
      "sizing_guide": "Concrete tailored dimensions based on user's measurements",
      "crafting_tip": "Recommended fabrics, foam density, adhesives, or techniques",
      "suggested_materials": ["Material 1", "Material 2"]
    }}
  ]
}}
"""

    with open(image_full_path, "rb") as f:
        image_bytes = f.read()

    # Determine mime type
    ext_lower = row["image_path"].rsplit(".", 1)[-1].lower()
    mime = "image/png" if ext_lower == "png" else "image/webp" if ext_lower == "webp" else "image/jpeg"

    from google.genai import types

    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=[
                prompt,
                types.Part.from_bytes(data=image_bytes, mime_type=mime)
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2
            )
        )
        parsed = json.loads(response.text)
        return jsonify({
            "success": True,
            "data": parsed,
            "ref_id": ref_id,
            "image_url": url_for("static", filename=row["image_path"])
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/apply_parts", methods=("POST",))
@login_required
def apply_parts(project_id):
    project = _own_project(project_id)
    if not project:
        return jsonify({"success": False, "error": "Project not found"}), 404

    data = request.get_json(silent=True) or {}
    parts_list = data.get("parts", [])

    if not parts_list:
        return jsonify({"success": False, "error": "No parts selected"}), 400

    db = get_db()

    # Get current max sort order
    max_order = db.execute(
        "SELECT COALESCE(MAX(sort_order), -1) as m FROM parts WHERE project_id = ?",
        (project_id,)
    ).fetchone()["m"]

    valid_cats = {'wig', 'garment', 'armor', 'prop', 'footwear', 'accessory', 'makeup', 'electronics', 'other'}

    added_count = 0
    for idx, item in enumerate(parts_list):
        name = item.get("name", "").strip()
        if not name:
            continue

        cat = item.get("category", "other").lower()
        if cat not in valid_cats:
            cat = "other"

        cur_order = max_order + 1 + idx

        # Insert part
        db.execute(
            "INSERT INTO parts (project_id, name, category, sort_order) VALUES (?, ?, ?, ?)",
            (project_id, name, cat, cur_order)
        )
        part_id = db.execute("SELECT last_insert_rowid() as id").fetchone()["id"]
        added_count += 1

        # Automatically create initial task with tailoring sizing guide as task notes
        sizing_guide = item.get("sizing_guide", "")
        crafting_tip = item.get("crafting_tip", "")
        task_desc_lines = []
        if sizing_guide:
            task_desc_lines.append(f"📏 Sizing Guide: {sizing_guide}")
        if crafting_tip:
            task_desc_lines.append(f"✂️ Crafting Tip: {crafting_tip}")
        task_desc = "\n\n".join(task_desc_lines) if task_desc_lines else None

        db.execute(
            """INSERT INTO tasks (project_id, part_id, title, description, priority, status)
               VALUES (?, ?, ?, ?, 'medium', 'todo')""",
            (project_id, part_id, f"Pattern & Build {name}", task_desc)
        )

        # Optionally add suggested materials to BOM
        suggested_mats = item.get("suggested_materials", [])
        for mat_name in suggested_mats[:3]:
            if isinstance(mat_name, str) and mat_name.strip():
                # Guess category from part category
                mat_cat = 'fabric' if cat == 'garment' else 'foam' if cat == 'armor' else 'wig' if cat == 'wig' else 'other'
                db.execute(
                    """INSERT INTO materials (project_id, part_id, item_name, category, quantity, unit, price_est, in_stash)
                       VALUES (?, ?, ?, ?, 1.0, 'pcs', 0.0, 0)""",
                    (project_id, part_id, mat_name.strip(), mat_cat)
                )

    db.commit()
    return jsonify({
        "success": True,
        "added_count": added_count,
        "redirect_url": url_for("projects.view", project_id=project_id)
    })
