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
import traceback
from flask import (
    Blueprint, flash, g, jsonify, redirect,
    request, url_for, current_app
)
from werkzeug.utils import secure_filename
from db import get_db
from auth import login_required
from dotenv import load_dotenv

# Ensure environment variables are loaded (try explicit path as well)
load_dotenv()
_HERE = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_HERE, ".env"), override=False)

# Gemini models — will try in order if one is overloaded
GEMINI_MODELS = ["gemini-3.5-flash", "gemini-3.5-pro"]

bp = Blueprint("references", __name__, url_prefix="/projects/<int:project_id>/references")


def _own_project(project_id):
    db = get_db()
    p = db.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    if p is None or p["user_id"] != g.user["id"]:
        return None
    return dict(p)


def _get_gemini_client():
    # Re-load env each call so the key is always picked up
    load_dotenv(os.path.join(_HERE, ".env"), override=False)
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    from google import genai
    return genai.Client(api_key=api_key)


def _allowed_file(filename):
    allowed = current_app.config.get("ALLOWED_EXTENSIONS", {"png", "jpg", "jpeg", "gif", "webp"})
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed


# ── Upload ────────────────────────────────────────────────────────────────────

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


# ── Delete ────────────────────────────────────────────────────────────────────

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


# ── AI Analysis ───────────────────────────────────────────────────────────────

@bp.route("/<int:ref_id>/analyze", methods=("POST",))
@login_required
def analyze(project_id, ref_id):
    """Analyze a reference image with Gemini Vision. ALWAYS returns JSON."""
    try:
        return _do_analyze(project_id, ref_id)
    except Exception as e:
        current_app.logger.error(
            "Unhandled error in /analyze: %s\n%s", e, traceback.format_exc()
        )
        return jsonify({"success": False, "error": f"Server error: {e}"}), 500


def _do_analyze(project_id, ref_id):
    """Core analysis — separated so analyze() can wrap it in a blanket try/except."""
    project = _own_project(project_id)
    if not project:
        return jsonify({"success": False, "error": "Project not found"}), 404

    client = _get_gemini_client()
    if not client:
        return jsonify({
            "success": False,
            "error": "GEMINI_API_KEY not found. Please add it to your .env file."
        }), 500

    db = get_db()
    row = db.execute(
        "SELECT * FROM references_board WHERE id = ? AND project_id = ?",
        (ref_id, project_id)
    ).fetchone()
    if not row:
        return jsonify({"success": False, "error": "Reference image not found"}), 404

    ref_dict = dict(row)
    image_full_path = os.path.join(current_app.static_folder, ref_dict["image_path"])
    if not os.path.exists(image_full_path):
        return jsonify({"success": False, "error": "Image file not found on disk"}), 404

    # --- Body measurements ---
    m_row = db.execute(
        "SELECT * FROM user_measurements WHERE user_id = ?", (g.user["id"],)
    ).fetchone()
    m = dict(m_row) if m_row else {}

    mparts = []
    for field, label in [
        ("height_cm", "Height"), ("shoulder_width_cm", "Shoulder width"),
        ("head_circumference_cm", "Head circumference"), ("neck_circumference_cm", "Neck"),
        ("chest_bust_cm", "Chest/Bust"), ("underbust_cm", "Underbust"),
        ("waist_cm", "Waist"), ("hips_cm", "Hips"),
        ("torso_length_cm", "Torso length"), ("arm_length_cm", "Arm length"),
        ("bicep_circumference_cm", "Bicep"), ("wrist_circumference_cm", "Wrist"),
        ("inseam_cm", "Inseam"), ("outseam_cm", "Outseam"),
        ("thigh_circumference_cm", "Thigh"), ("calf_circumference_cm", "Calf"),
    ]:
        if m.get(field):
            mparts.append(f"{label}: {m[field]}cm")
    measurements_text = (", ".join(mparts)
                         if mparts
                         else "No body measurements recorded yet (using standard proportions).")

    char_name = project.get("character_name") or project.get("name") or "Character"
    source = project.get("source_series") or ""
    char_info = f"Character: {char_name}" + (f" from '{source}'" if source else "")

    prompt = f"""
You are an elite, highly experienced cosplay maker, tailor, and prop designer.
Analyze this character reference image ({char_info}).

The cosplayer's recorded body measurements are:
{measurements_text}

Deconstruct the character's complete costume into discrete, realistic, craftable parts.
For EVERY costume piece you see (wig/hair, tops, jackets, armor pieces, trousers/skirts, gauntlets/gloves, boots/shoes, belts, props/accessories):

1. Name the part concisely (e.g. "Cropped Biker Jacket", "Spiky Styled Wig", "Shoulder Pauldron Pair").
2. Assign the category strictly from: "wig", "garment", "armor", "prop", "footwear", "accessory", "makeup", or "other".
3. Identify the anatomical body zone strictly from: "head", "neck", "torso", "waist", "hips", "arms", "legs", or "feet".
4. Provide "sizing_guide": exact tailored cutting and fitting dimensions using the user's measurements above.
5. Provide "crafting_tip": recommended materials and construction method.
6. For category "prop" only, include a "blueprint" object with:
   - "total_length_cm": estimated length scaled to cosplayer height
   - "core_material": recommended structural core (e.g. "10mm PVC pipe", "EVA foam block")
   - "build_steps": array of 4–6 step-by-step construction instructions as plain strings
   - "con_compliance": convention safety notes (blunted edges, orange tip, length limits, etc.)
   For all other categories, set "blueprint" to null.

Output ONLY valid JSON — no markdown, no code fences, no commentary outside the JSON:
{{
  "character_name": "Name of character",
  "overview": "1-2 sentence costume overview",
  "parts": [
    {{
      "name": "Part name",
      "category": "wig|garment|armor|prop|footwear|accessory|makeup|other",
      "anatomical_zone": "head|neck|torso|waist|hips|arms|legs|feet",
      "description": "Visual details",
      "sizing_guide": "Tailored dimensions",
      "crafting_tip": "Materials and technique",
      "suggested_materials": ["Material 1", "Material 2"],
      "blueprint": null
    }}
  ]
}}
"""

    with open(image_full_path, "rb") as f:
        image_bytes = f.read()

    ext_lower = ref_dict["image_path"].rsplit(".", 1)[-1].lower()
    mime = "image/png" if ext_lower == "png" else "image/webp" if ext_lower == "webp" else "image/jpeg"

    from google.genai import types

    # Try each model in order until one succeeds
    last_err = None
    for model_name in GEMINI_MODELS:
        try:
            current_app.logger.info("Trying Gemini model: %s", model_name)
            response = client.models.generate_content(
                model=model_name,
                contents=[
                    prompt,
                    types.Part.from_bytes(data=image_bytes, mime_type=mime)
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.2
                )
            )

            # Strip any accidental markdown code fences
            raw = response.text.strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[-1]
                if raw.endswith("```"):
                    raw = raw[:-3].strip()

            parsed = json.loads(raw)
            return jsonify({
                "success": True,
                "data": parsed,
                "ref_id": ref_id,
                "image_url": url_for("static", filename=ref_dict["image_path"]),
                "model_used": model_name
            })
        except Exception as e:
            last_err = e
            current_app.logger.warning("Model %s failed: %s", model_name, str(e)[:200])
            continue

    # All models failed
    return jsonify({
        "success": False,
        "error": f"All Gemini models are currently unavailable. Last error: {last_err}"
    }), 503


# ── Apply (import) detected parts ─────────────────────────────────────────────

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

    max_order = db.execute(
        "SELECT COALESCE(MAX(sort_order), -1) as m FROM parts WHERE project_id = ?",
        (project_id,)
    ).fetchone()["m"]

    valid_cats = {"wig", "garment", "armor", "prop", "footwear", "accessory", "makeup", "electronics", "other"}

    added_count = 0
    for idx, item in enumerate(parts_list):
        name = item.get("name", "").strip()
        if not name:
            continue

        cat = item.get("category", "other").lower()
        if cat not in valid_cats:
            cat = "other"

        cur_order = max_order + 1 + idx

        db.execute(
            "INSERT INTO parts (project_id, name, category, sort_order) VALUES (?, ?, ?, ?)",
            (project_id, name, cat, cur_order)
        )
        part_id = db.execute("SELECT last_insert_rowid() as id").fetchone()["id"]
        added_count += 1

        # Build task description from sizing guide + crafting tip
        sizing_guide = item.get("sizing_guide", "")
        crafting_tip = item.get("crafting_tip", "")
        task_desc_lines = []
        if sizing_guide:
            task_desc_lines.append(f"📏 Sizing Guide: {sizing_guide}")
        if crafting_tip:
            task_desc_lines.append(f"✂️ Crafting Tip: {crafting_tip}")

        # For props with blueprints, append step-by-step build plan
        blueprint = item.get("blueprint")
        if cat == "prop" and blueprint and isinstance(blueprint, dict):
            bp_lines = ["\n🔧 PROP BLUEPRINT"]
            if blueprint.get("total_length_cm"):
                bp_lines.append(f"  Total length: {blueprint['total_length_cm']} cm")
            if blueprint.get("core_material"):
                bp_lines.append(f"  Core: {blueprint['core_material']}")
            steps = blueprint.get("build_steps", [])
            if steps:
                bp_lines.append("  Build steps:")
                for i, step in enumerate(steps, 1):
                    bp_lines.append(f"    {i}. {step}")
            if blueprint.get("con_compliance"):
                bp_lines.append(f"  ⚠️ Con compliance: {blueprint['con_compliance']}")
            task_desc_lines.append("\n".join(bp_lines))

        task_desc = "\n\n".join(task_desc_lines) if task_desc_lines else None

        db.execute(
            """INSERT INTO tasks (project_id, part_id, title, description, priority, status)
               VALUES (?, ?, ?, ?, 'medium', 'todo')""",
            (project_id, part_id, f"Pattern & Build {name}", task_desc)
        )

        # Add suggested materials to BOM (up to 3)
        suggested_mats = item.get("suggested_materials", [])
        for mat_name in suggested_mats[:3]:
            if isinstance(mat_name, str) and mat_name.strip():
                mat_cat = (
                    "fabric" if cat == "garment"
                    else "foam" if cat == "armor"
                    else "wig" if cat == "wig"
                    else "other"
                )
                db.execute(
                    """INSERT INTO materials (project_id, part_id, item_name, category, quantity, unit, price_est, in_stash)
                       VALUES (?, ?, ?, ?, 1.0, 'pcs', 0.0, 0)""",
                    (project_id, part_id, mat_name.strip(), mat_cat)
                )

        # For props with blueprints, add core material to BOM too
        if cat == "prop" and blueprint and blueprint.get("core_material"):
            db.execute(
                """INSERT INTO materials (project_id, part_id, item_name, category, quantity, unit, price_est, in_stash)
                   VALUES (?, ?, ?, 'other', 1.0, 'pcs', 0.0, 0)""",
                (project_id, part_id, blueprint["core_material"])
            )

    db.commit()
    return jsonify({
        "success": True,
        "added_count": added_count,
        "redirect_url": url_for("projects.view", project_id=project_id)
    })
