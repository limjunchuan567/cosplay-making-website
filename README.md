# CosplayHub 🧵

A personal **Cosplay Command Centre** web app built with Flask + SQLite.  
Plan, track, and budget your cosplay builds from idea to convention floor.

## Features (Planned)
- 🔐 Secure account registration & login (Werkzeug password hashing)
- 📂 Project dashboard with status overview
- 🧩 Costume parts tree (Head → Torso → Arms → Legs → Props)
- ✅ Task breakdown per part with priority levels
- 💰 Smart Bill of Materials with estimated vs. actual spend tracking
- 🗃️ "In My Stash" toggle to avoid duplicate purchases
- 🗓️ Convention countdown + automatic Hallway-Test milestone
- 🖼️ Visual reference board & colour palette per project
- ✈️ Pre-flight feasibility checklist (bathroom access, transport, con weapon rules)

## Tech Stack
| Layer    | Technology                              |
|----------|-----------------------------------------|
| Backend  | Python 3.12 · Flask 3                   |
| Database | SQLite (via Python `sqlite3`)           |
| Auth     | Werkzeug password hashing · Flask sessions |
| Frontend | HTML5 · CSS3 (Dark Mode design system) |

## Project Structure
```
cosplayhub/
├── app.py              # Flask application factory
├── db.py               # SQLite connection manager + CLI helpers
├── schema.sql          # Full relational database schema
├── seed_data.py        # Dev seed: David Martinez build (Edgerunners)
├── requirements.txt    # Python dependencies
├── templates/          # Jinja2 HTML templates (added in Level 3)
└── static/
    ├── css/            # Dark mode stylesheet
    ├── js/             # Vanilla JS helpers
    ├── images/         # App UI assets
    └── uploads/        # User-uploaded reference images (git-ignored)
```

## Getting Started

### 1. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 2. Initialise the database
```bash
flask --app app init-db
```

### 3. Run the development server
```bash
flask --app app run --debug
```
Then open http://127.0.0.1:5000 in your browser.

### 4. (Optional) Load sample data
```bash
python seed_data.py
```

## Development Roadmap
- [x] **Level 1** — SQLite schema + Flask app skeleton + DB manager
- [ ] **Level 2** — Auth system (register, login, sessions)
- [ ] **Level 3** — Dark Mode design system + Jinja2 base template
- [ ] **Level 4** — Project CRUD dashboard
- [ ] **Level 5** — Pre-production modules (BOM, tasks, countdown, moodboard)

## License
MIT
