# 🧠 AI Project Memory: CosplayHub

> **Context for Future AI Chats:** Read this file first. It contains the complete project vision, user profile, tech stack, architectural history, what has been implemented, and what is planned next.

---

## 1. Project Vision & User Profile

- **Project Name:** CosplayHub (rebuilt from an earlier static prototype named *CraftCon*).
- **Core Vision:** A web-based "Cosplay Command Center" to help cosplayers plan, track, and budget their builds. It focuses heavily on the **pre-production phase** (before buying materials or cutting foam): visual references, AI-assisted costume deconstruction, anatomical parts breakdown, material & budget tracking (Smart BOM), task breakdown with prop blueprints, convention countdowns, body measurements, 3D anatomical mannequins, and wearability checks.
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
- **Auth & Security:** **Werkzeug** (`generate_password_hash`, `check_password_hash`), Flask server-side sessions, `@login_required` decorator. Includes `DEV_BYPASS_AUTH=True` option in `app.py` for frictionless local development with auto-injected `devuser`.
- **AI Vision Engine:** Google Gemini SDK (`google-genai` >= 3.6.0) utilizing `gemini-3.5-flash` with graceful fallback handling for 503 capacity spikes. Structured JSON prompt engineering for deconstructing character turnarounds into tailored craftable parts and prop blueprints.
- **3D Graphics & Mannequins:** **Three.js (r170)** and **mannequin.js** loaded via ESM `<script type="importmap">`. Features articulated artist dummy models with OrbitControls, directional lighting, and parametric body scaling.
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
1. **360° Deconstruction & Visual References:** Breaking characters into anatomical subsystems (Wig, Garment, Armor, Props, Footwear, Makeup, Electronics).
2. **AI-Assisted Tailoring & Blueprints:** Extracting concrete pattern dimensions based on cosplayer measurements, plus step-by-step assembly guides and safety compliance rules for weapons/props.
3. **3D Fitting & Mannequin Visualization:** Visualizing anatomical zones and costume pieces directly on a scaled virtual body frame before cutting patterns.
4. **Reality Checks:** Answering critical wearability questions before building (bathroom protocol, mobility & sitting, sensory/ventilation, transport/packability, con weapons compliance).
5. **Smart BOM & Stash Buster:** Tracking raw materials, hardware, adhesives, and consumables with an "In My Stash" toggle to prevent re-buying owned supplies.
6. **Reverse Timeline:** Counting backwards from Con Day 0 with a mandatory **"Hallway Test" at Con Day -7** (full 2-hour wear test at home).
7. **Body Measurements & Proportional Sizing:** Fitting garments to sewing patterns and Asian vendor charts (Taobao/Miccostumes/DokiDoki run 1–2 sizes smaller).

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
  - Clean anatomical **mannequin.js 3D Body Frame**: Parametrically scaled to user measurements via `/measurements/api/mannequin`.
- [x] **Visual Reference Board & Gemini Vision AI Costume Deconstruction:**
  - `references.py`: Character turnaround and detail art upload (`references_board` table).
  - **Gemini Vision AI Integration:** Deconstructs outfit into discrete parts with tailored dimensions based on user's exact body profile.
  - **Prop Blueprints & Task Notes:** For props/weapons, AI generates structural core recommendation (e.g. PVC pipe, fiberglass rod), step-by-step build instructions, and con weapons compliance notes.
  - **One-Click Batch Import:** Seamlessly imports detected parts, creates tasks with sizing/build guides, and populates suggested materials into the Smart BOM.
  - **Fault-Tolerant Error Handling:** Top-level JSON error wrapping with fallback models to handle temporary Google API rate/capacity spikes.
- [x] **3D Costume Fit Preview & Fitting Room (In Projects):**
  - Integrated directly into `templates/projects/view.html` beneath character references.
  - Enables cosplayers to test different costumes on their 3D mannequin model per-project.
  - **Costume Toggle:** Switch between "Body Frame" (neutral articulated wood dummy) and "Costume Fit" (translucent color-coded overlays per anatomical zone).
  - **Dynamic Legend:** Automatically identifies and colors zones based on parts currently in the project (Wig = Purple, Garment = Teal, Armor = Steel Blue, Prop = Gold, Footwear = Coral, etc.).
- [x] **Expandable Task Blueprints:**
  - `templates/projects/view.html`: Tasks with build notes and AI blueprints render an inline expandable accordion (`▶ Build notes & blueprint`).

---

## 5. What to Focus on Next (Roadmap)

1. **Module 5E: Pre-Flight Feasibility Checklist**
   - Interactive checklist on the project page for bathroom access, mobility, ventilation, transport breakdown, and prop check rules (`feasibility_checks` table).
2. **Proportional Caliper & Prop Scaler Tool**
   - Input character reference image height vs. user height to calculate weapon/prop lengths in real-world centimeters.
3. **3D Model Inspector / Bounding Box Scaler**
   - Parse uploaded `.obj` / `.stl` / `.glb` files to calculate 3D print scaling percentages against user head/shoulder measurements.
4. **Costume Part Detail View & Progress Gallery**
   - Dedicated detail page per costume part with sub-tasks, progress photos, and tailored sizing cheat sheet.
