"""
measurements.py — Body Measurements Profile & Sizing Engine.

Enables cosplayers to record accurate anatomical measurements to:
  - Estimate standard US/EU clothing sizes
  - Calculate Asian cosplay vendor sizing (Taobao, Miccostumes, DokiDoki)
  - Scale 3D armor models, helmets, and prop templates
"""

from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from db import get_db
from auth import login_required

bp = Blueprint("measurements", __name__, url_prefix="/measurements")


def ensure_table():
    """Ensure the user_measurements table exists."""
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS user_measurements (
            id                      INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id                 INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
            height_cm               REAL,
            shoulder_width_cm       REAL,
            head_circumference_cm   REAL,
            neck_circumference_cm   REAL,
            chest_bust_cm           REAL,
            underbust_cm            REAL,
            waist_cm                REAL,
            hips_cm                 REAL,
            torso_length_cm         REAL,
            arm_length_cm           REAL,
            bicep_circumference_cm  REAL,
            wrist_circumference_cm  REAL,
            inseam_cm               REAL,
            outseam_cm              REAL,
            thigh_circumference_cm  REAL,
            calf_circumference_cm   REAL,
            shoe_size               TEXT,
            preferred_unit          TEXT NOT NULL DEFAULT 'cm',
            notes                   TEXT,
            updated_at              TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    db.commit()


def calculate_sizing_estimates(m):
    """
    Calculate commercial pattern and cosplay vendor size estimates
    based on chest, waist, and hips.
    """
    if not m:
        return None

    chest = m["chest_bust_cm"] or 0
    waist = m["waist_cm"] or 0
    hips = m["hips_cm"] or 0
    head = m["head_circumference_cm"] or 0

    if not (chest or waist or hips):
        return None

    # Estimate Western Unisex / Mens / Womens sizing
    # Based on standard chest/bust guidelines
    primary_measure = chest if chest > 0 else (waist + 15)

    if primary_measure < 84:
        us_size = "XS"
        asian_size = "S to M"
    elif primary_measure <= 92:
        us_size = "S"
        asian_size = "M to L"
    elif primary_measure <= 100:
        us_size = "M"
        asian_size = "L to XL"
    elif primary_measure <= 108:
        us_size = "L"
        asian_size = "XL to 2XL"
    elif primary_measure <= 116:
        us_size = "XL"
        asian_size = "2XL to 3XL"
    else:
        us_size = "2XL+"
        asian_size = "Custom / 3XL+"

    # Wig / Helmet estimate
    wig_fit = "Standard (55-57 cm)"
    if head > 0:
        if head < 54:
            wig_fit = "Small / Petite (<54 cm) — child/small wig cap"
        elif head <= 58:
            wig_fit = "Standard (54–58 cm) — fits standard adult wigs"
        else:
            wig_fit = "Large (>58 cm) — check wig cap stretch & add 5-10% to 3D helmet prints"

    return {
        "us_size": us_size,
        "asian_size": asian_size,
        "wig_fit": wig_fit,
        "has_data": True,
    }


@bp.route("/", methods=("GET", "POST"))
@login_required
def index():
    ensure_table()
    db = get_db()

    if request.method == "POST":
        unit = request.form.get("preferred_unit", "cm")

        def parse_val(field_name):
            val = request.form.get(field_name, "").strip()
            if not val:
                return None
            try:
                num = float(val)
                # If submitted in inches, store internally as cm
                if unit == "in":
                    return round(num * 2.54, 1)
                return round(num, 1)
            except ValueError:
                return None

        fields = {
            "height_cm": parse_val("height"),
            "shoulder_width_cm": parse_val("shoulder_width"),
            "head_circumference_cm": parse_val("head_circumference"),
            "neck_circumference_cm": parse_val("neck_circumference"),
            "chest_bust_cm": parse_val("chest_bust"),
            "underbust_cm": parse_val("underbust"),
            "waist_cm": parse_val("waist"),
            "hips_cm": parse_val("hips"),
            "torso_length_cm": parse_val("torso_length"),
            "arm_length_cm": parse_val("arm_length"),
            "bicep_circumference_cm": parse_val("bicep_circumference"),
            "wrist_circumference_cm": parse_val("wrist_circumference"),
            "inseam_cm": parse_val("inseam"),
            "outseam_cm": parse_val("outseam"),
            "thigh_circumference_cm": parse_val("thigh_circumference"),
            "calf_circumference_cm": parse_val("calf_circumference"),
            "shoe_size": request.form.get("shoe_size", "").strip() or None,
            "preferred_unit": unit,
            "notes": request.form.get("notes", "").strip() or None,
        }

        existing = db.execute(
            "SELECT id FROM user_measurements WHERE user_id = ?", (g.user["id"],)
        ).fetchone()

        if existing:
            set_clause = ", ".join(f"{k} = ?" for k in fields.keys())
            values = list(fields.values()) + [g.user["id"]]
            db.execute(
                f"UPDATE user_measurements SET {set_clause}, updated_at = datetime('now') WHERE user_id = ?",
                values,
            )
        else:
            cols = ["user_id"] + list(fields.keys())
            placeholders = ", ".join(["?"] * len(cols))
            values = [g.user["id"]] + list(fields.values())
            db.execute(
                f"INSERT INTO user_measurements ({', '.join(cols)}) VALUES ({placeholders})",
                values,
            )

        db.commit()
        flash("Body measurements saved successfully! 📏", "success")
        return redirect(url_for("measurements.index"))

    row = db.execute(
        "SELECT * FROM user_measurements WHERE user_id = ?", (g.user["id"],)
    ).fetchone()

    m = dict(row) if row else None
    sizing = calculate_sizing_estimates(m)

    return render_template("measurements/index.html", m=m, sizing=sizing)
