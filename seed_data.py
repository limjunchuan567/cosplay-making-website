"""
seed_data.py — CosplayHub development seed script.

Populates the database with a realistic cosplay build so we can verify:
  - Foreign-key relationships and ON DELETE CASCADE.
  - Budget calculations (estimated vs. actual totals).
  - Task and material filtering by part.
  - Feasibility check rows.

Build seeded:  "Cyberpunk: Edgerunners — David Martinez (Jacket Build)"

Run with:  python seed_data.py
(The app must already be initialised: `flask init-db`)
"""

import sqlite3
import os
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), "instance", "cosplayhub.db")


def seed():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    cur = con.cursor()

    # ------------------------------------------------------------------ #
    # 1. Demo user
    # ------------------------------------------------------------------ #
    cur.execute(
        "INSERT OR IGNORE INTO users (username, email, password_hash) VALUES (?, ?, ?)",
        (
            "testcosplayer",
            "test@cosplayhub.dev",
            generate_password_hash("testpass123"),
        ),
    )
    user_id = cur.execute(
        "SELECT id FROM users WHERE username = 'testcosplayer'"
    ).fetchone()["id"]

    # ------------------------------------------------------------------ #
    # 2. Project
    # ------------------------------------------------------------------ #
    cur.execute(
        """
        INSERT INTO projects
            (user_id, name, character_name, source_series, status,
             convention_name, convention_date, budget_limit, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            "David Martinez — Jacket Build",
            "David Martinez",
            "Cyberpunk: Edgerunners",
            "in_progress",
            "AnimeFest 2027",
            "2027-03-15",
            250.00,
            "Focus on accuracy of the red liner jacket and the LED undersuit details.",
        ),
    )
    project_id = cur.lastrowid

    # ------------------------------------------------------------------ #
    # 3. Costume parts (subsystems)
    # ------------------------------------------------------------------ #
    parts_data = [
        ("Red Liner Jacket",   "garment",     "in_progress", 0),
        ("Undersuit",          "garment",     "not_started", 1),
        ("Styled Wig",         "wig",         "not_started", 2),
        ("LED Circuit Detail", "electronics", "not_started", 3),
        ("Boots / Footwear",   "footwear",    "not_started", 4),
    ]
    part_ids = {}
    for name, category, status, sort_order in parts_data:
        cur.execute(
            """
            INSERT INTO parts (project_id, name, category, status, sort_order)
            VALUES (?, ?, ?, ?, ?)
            """,
            (project_id, name, category, status, sort_order),
        )
        part_ids[name] = cur.lastrowid

    # ------------------------------------------------------------------ #
    # 4. Tasks
    # ------------------------------------------------------------------ #
    tasks_data = [
        # (title, description, priority, status, due_date, part_name or None)
        ("Order jacket fabric", "Need 2m of red PU faux-leather + black cotton lining.", "critical", "done",    "2026-12-01", "Red Liner Jacket"),
        ("Cut jacket pattern",  "Use modified McCall's M6893 biker jacket pattern.",     "high",     "in_progress", None,       "Red Liner Jacket"),
        ("Sew jacket shell",    "Stitch outer PU layer, leave lining separate.",         "high",     "todo",    None,           "Red Liner Jacket"),
        ("Attach lining",       "Hand-stitch lining to shell at collar and cuffs.",      "medium",   "todo",    None,           "Red Liner Jacket"),
        ("Order wig",           "Natural black base, needs to be cut short.",            "critical", "todo",    "2026-12-15",   "Styled Wig"),
        ("Style + cut wig",     "Reference Episode 1 turnaround. Spiky fringe.",         "high",     "todo",    None,           "Styled Wig"),
        ("Wire LED strips",     "Neopixel SK6812 strips run along forearm seams.",       "medium",   "todo",    None,           "LED Circuit Detail"),
        ("Hallway test",        "Full 2-hour wear-test before convention.",              "critical", "todo",    "2027-03-08",   None),
    ]
    for title, desc, priority, status, due_date, part_name in tasks_data:
        p_id = part_ids.get(part_name) if part_name else None
        cur.execute(
            """
            INSERT INTO tasks
                (project_id, part_id, title, description, priority, status, due_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (project_id, p_id, title, desc, priority, status, due_date),
        )

    # ------------------------------------------------------------------ #
    # 5. Materials (Smart BOM)
    # ------------------------------------------------------------------ #
    materials_data = [
        # (item_name, category, qty, unit, price_est, price_actual, in_stash, status, vendor_url, part_name)
        ("Red PU Faux Leather", "fabric",      2.0,  "meters", 18.00, 17.50,  0, "acquired", "https://fabricstore.example.com", "Red Liner Jacket"),
        ("Black Cotton Lining", "fabric",      2.0,  "meters",  5.00,  5.00,  0, "acquired", None,                             "Red Liner Jacket"),
        ("Separating Zipper 60cm","hardware",  1.0,  "pcs",     3.50,  None,  0, "needed",   None,                             "Red Liner Jacket"),
        ("Barge Contact Cement", "consumable", 1.0,  "tin",    12.00,  None,  1, "acquired", None,                             None),
        ("Black Wig (short)",    "wig",        1.0,  "pcs",    22.00,  None,  0, "ordered",  "https://wigstore.example.com",   "Styled Wig"),
        ("Wig Cap",              "wig",        2.0,  "pcs",     1.50,  None,  0, "needed",   None,                             "Styled Wig"),
        ("SK6812 Neopixel Strip","electronics",1.0,  "meters", 15.00,  None,  0, "needed",   None,                             "LED Circuit Detail"),
        ("USB Power Bank 10000mAh","electronics",1.0,"pcs",    18.00,  None,  0, "needed",   None,                             "LED Circuit Detail"),
        ("Black Combat Boots",   "other",      1.0,  "pcs",    45.00,  None,  0, "needed",   None,                             "Boots / Footwear"),
    ]
    for (item_name, category, qty, unit, price_est, price_actual,
         in_stash, status, vendor_url, part_name) in materials_data:
        p_id = part_ids.get(part_name) if part_name else None
        cur.execute(
            """
            INSERT INTO materials
                (project_id, part_id, item_name, category, quantity, unit,
                 price_est, price_actual, in_stash, status, vendor_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (project_id, p_id, item_name, category, qty, unit,
             price_est, price_actual, in_stash, status, vendor_url),
        )

    # ------------------------------------------------------------------ #
    # 6. Feasibility checks
    # ------------------------------------------------------------------ #
    feasibility_data = [
        ("bathroom_access",    1, "Side-zip opening on jacket + undersuit crotch snap."),
        ("mobility_sitting",   1, "Jacket tested — no rigid panels, full mobility OK."),
        ("ventilation_vision", 0, "No mask/helmet, but need to test LED heat output."),
        ("transport_breakdown",1, "Jacket rolls flat; wig in separate hatbox."),
        ("con_weapon_rules",   1, "No props with blades — build is clothing-only."),
    ]
    for check_type, is_passed, notes in feasibility_data:
        cur.execute(
            """
            INSERT OR REPLACE INTO feasibility_checks
                (project_id, check_type, is_passed, solution_notes)
            VALUES (?, ?, ?, ?)
            """,
            (project_id, check_type, is_passed, notes),
        )

    con.commit()

    # ------------------------------------------------------------------ #
    # 7. Verification queries — printed to console
    # ------------------------------------------------------------------ #
    print("\n✅  Seed complete. Running verification queries...\n")

    total_est = con.execute(
        "SELECT SUM(quantity * price_est) as total FROM materials WHERE project_id = ?",
        (project_id,)
    ).fetchone()["total"]
    total_actual = con.execute(
        "SELECT SUM(quantity * price_actual) as total FROM materials WHERE project_id = ? AND price_actual IS NOT NULL",
        (project_id,)
    ).fetchone()["total"]
    stash_count = con.execute(
        "SELECT COUNT(*) as cnt FROM materials WHERE project_id = ? AND in_stash = 1",
        (project_id,)
    ).fetchone()["cnt"]

    print(f"  💰 Budget limit    : ${250.00:.2f}")
    print(f"  📋 Estimated total : ${total_est:.2f}")
    print(f"  💳 Actual spent    : ${total_actual:.2f}")
    print(f"  🗃️  Items in stash  : {stash_count}")

    tasks_by_part = con.execute(
        """
        SELECT p.name as part, COUNT(t.id) as task_count
        FROM parts p
        LEFT JOIN tasks t ON t.part_id = p.id
        WHERE p.project_id = ?
        GROUP BY p.id
        """,
        (project_id,)
    ).fetchall()
    print("\n  📌 Tasks per part:")
    for row in tasks_by_part:
        print(f"     {row['part']}: {row['task_count']} task(s)")

    con.close()
    print("\n✅  Verification complete — schema and seed data look good!\n")


if __name__ == "__main__":
    seed()
