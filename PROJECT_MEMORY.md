# 🧠 AI Project Memory: CosplayHub

> **Context for Future AI Chats:** Read this file first. It contains the complete project vision, user profile, tech stack, architectural history, what has been implemented, and what is planned next.

---

## 1. Project Vision & User Profile

- **Project Name:** CosplayHub (rebuilt from an earlier static prototype named *CraftCon*).
- **Core Vision:** A web-based "Cosplay Command Center" to help cosplayers plan, track, and budget their builds. It focuses heavily on the **pre-production phase** (before buying materials or cutting foam): anatomical parts deconstruction, material & budget tracking, task breakdown, convention countdowns, body measurements, and wearability checks.
- **User Profile:**
  - **Coder Background:** Knows C, Python, HTML, CSS, Java, SQL.
  - **Learning Goals:** Willing to learn modern web dev concepts; not limited to existing knowledge; introduce standard tools when necessary.
  - **Development Mode:** Scenario A (writing real, production-ready code).
  - **Git Workflow:** The user instructed: **"from now on, git push for me"**. Always make clean git commits and push to `origin main` using the authenticated remote URL.
  - **GitHub Repository:** [https://github.com/limjunchuan567/cosplay-making-website](https://github.com/limjunchuan567/cosplay-making-website)

---

## 2. Tech Stack & Design Rules

- **Backend:** Python 3.12 with **Flask** (application factory pattern in `app.py`, Blueprints).
- **Database:** **SQLite** with raw SQL (`sqlite3.Row` factory, `PRAGMA foreign_keys = ON`, `schema.sql`).
- **Auth & Security:** **Werkzeug** (`generate_password_hash`, `check_password_hash`), Flask server-side sessions, `@login_required` decorator.
- **Frontend:** Semantic HTML5, Custom Dark Mode CSS3 (CSS variables), Vanilla JavaScript, Jinja2 template inheritance (`base.html`).
- **Design Tokens (Dark Mode):**
  - Background: `#121212` (`--bg-primary`)
  - Cards & Surfaces: `#1e1e1e` (`--bg-surface`, hover: `#262626`)
  - Primary Accent: `#bb86fc` (Cyber Purple)
  - Secondary Accent: `#03dac6` (Electric Teal)
  - Text: `#f5f5f7` (Primary), `#a0a0a5` (Secondary), `#6e6e73` (Muted)
  - Borders: `#2d2d2d` (`--border-subtle`)

---

## 3. Senior Cosplayer Pre-Production Framework (Discussed Principles)

Cosplay planning follows a strict pre-production sequence:
1. **360° Deconstruction:** Breaking characters into anatomical subsystems (Wig, Garment, Armor, Props, Footwear, Makeup, Electronics).
2. **Reality Checks:** Answering the 5 critical wearability questions before building:
   - *Bathroom Protocol:* Can you use the restroom unassisted?
   - *Mobility & Sitting:* Can you sit down without cracking armor?
   - *Sensory/Ventilation:* Can you breathe, hear, and see without visor fogging?
   - *Transport & Packability:* Does the weapon break down to fit in a suitcase?
   - *Convention Weapons Rules:* Orange tips, blunted edges, dimension limits.
3. **Smart BOM & Stash Buster:** Tracking raw materials, hardware, adhesives, and consumables with an "In My Stash" toggle to prevent re-buying owned supplies.
4. **Reverse Timeline:** Counting backwards from Con Day 0 with a mandatory **"Hallway Test" at Con Day -7** (full 2-hour wear test at home).
5. **Body Measurements & Proportional Sizing:** Fitting garments to sewing patterns and Asian vendor charts (Taobao/Miccostumes/DokiDoki run 1–2 sizes smaller).

---

## 4. What Has Been Built (Completed Milestones)

- [x] **Level 1 — Relational Data Model & DB Engine:**
  - `schema.sql`: 7 relational tables (`users`, `projects`, `parts`, `tasks`, `materials`, `references_board`, `feasibility_checks`, `user_measurements`) with foreign keys, indexes, and `ON DELETE CASCADE`.
  - `db.py`: SQLite connection lifecycle (`get_db`, `close_db`, `flask init-db` CLI command).
  - `seed_data.py`: Realistic David Martinez (*Cyberpunk: Edgerunners*) test build.
- [x] **Level 2 — Authentication Engine:**
  - `auth.py`: Blueprint for registration, login, logout, password hashing, and session management.
  - `templates/auth/login.html` and `register.html`: Full dark mode auth views with flash alerts.
  - `@login_required` decorator and `g.user` injection on every request.
- [x] **Level 3 & 4 — Dark Mode UI & Project CRUD:**
  - `templates/base.html`: Master layout with sticky navbar, flash messages, user badge, and footer.
  - `static/css/style.css` & `components.css`: Complete Dark Mode design system.
  - `projects.py`: CRUD operations (New, View, Edit, Delete with cascade).
  - `templates/index.html`: Dashboard showing project cards, stats bar, budget progress bars, and countdown badges.
  - `templates/projects/view.html`: Project Command Center page.
- [x] **Level 5 — Pre-Production Modules:**
  - **Costume Parts (`parts.py`):** Add parts, cycle status (Not Started ➔ In Progress ➔ Done), delete.
  - **Tasks (`tasks.py`):** Add tasks linked to parts, priority dots, due dates, checkbox toggle.
  - **Smart BOM (`materials.py`):** Add materials, unit/quantity, estimated vs. actual cost, vendor URLs, "In Stash" toggle, auto-calculated footer totals.
  - **Convention Countdown:** Automatic countdown banner turning urgent (red) under 14 days.
- [x] **Body Measurements Profile & Sizing Intelligence:**
  - `measurements.py` & `templates/measurements/index.html`: Complete anatomical profile (Height, Head/Neck for wigs/helmets, Torso, Arms/Gauntlets, Legs/Footwear).
  - Dynamic JavaScript unit switcher (`cm` ↔ `inches`).
  - **CosplayHub Sizing Intelligence Algorithm:** Automatically estimates US/Western sizes, Asian vendor sizes (Taobao/DokiDoki/Miccostumes), and wig/helmet fit.

---

## 5. What to Focus on Next (Roadmap)

1. **Module 5D: Visual Reference Board & Moodboard**
   - Image file upload or image URL dropping per project/part (`references_board` table).
   - Character turnaround angles (front, side, back) and color palette swatches.
2. **Module 5E: Pre-Flight Feasibility Checklist**
   - Interactive checklist on the project page for bathroom access, mobility, ventilation, transport breakdown, and prop check rules (`feasibility_checks` table).
3. **Proportional Caliper & Prop Scaler Tool**
   - Input character reference image height vs. user height to calculate weapon/prop lengths in real-world centimeters.
4. **3D Model Inspector / Bounding Box Scaler**
   - Parse uploaded `.obj` / `.stl` / `.glb` files to calculate 3D print scaling percentages against user head/shoulder measurements.
