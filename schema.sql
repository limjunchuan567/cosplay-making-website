-- ============================================================
-- CosplayHub — SQLite Database Schema
-- Pre-production command centre for cosplay builds
-- ============================================================

PRAGMA foreign_keys = ON;

-- ------------------------------------------------------------
-- TABLE: users
-- Stores account credentials. Passwords are stored as
-- Werkzeug-generated hashes, never plain-text.
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT    NOT NULL UNIQUE,
    email         TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL,
    created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- ------------------------------------------------------------
-- TABLE: projects
-- Root entity for a single cosplay build.
-- status: 'planning' | 'in_progress' | 'completed' | 'on_hold'
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS projects (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id          INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name             TEXT    NOT NULL,
    character_name   TEXT,
    source_series    TEXT,
    status           TEXT    NOT NULL DEFAULT 'planning'
                             CHECK(status IN ('planning','in_progress','completed','on_hold')),
    convention_name  TEXT,
    convention_date  TEXT,                    -- ISO-8601 date string: YYYY-MM-DD
    budget_limit     REAL    NOT NULL DEFAULT 0.0,
    notes            TEXT,
    created_at       TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at       TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- Index so we can quickly look up all projects owned by a user.
CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id);

-- ------------------------------------------------------------
-- TABLE: parts
-- Anatomical subsystems of the costume
-- (e.g. "EVA Chest Armour", "Styled Wig", "Buster Sword").
-- category: 'wig' | 'garment' | 'armor' | 'prop' |
--           'footwear' | 'accessory' | 'makeup' | 'electronics'
-- status:   'not_started' | 'in_progress' | 'completed'
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS parts (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name       TEXT    NOT NULL,
    category   TEXT    NOT NULL DEFAULT 'other'
                       CHECK(category IN (
                           'wig','garment','armor','prop',
                           'footwear','accessory','makeup','electronics','other'
                       )),
    status     TEXT    NOT NULL DEFAULT 'not_started'
                       CHECK(status IN ('not_started','in_progress','completed')),
    sort_order INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_parts_project_id ON parts(project_id);

-- ------------------------------------------------------------
-- TABLE: tasks
-- Granular actionable steps, optionally linked to a part.
-- If part_id IS NULL the task belongs to the project overall.
-- priority: 'low' | 'medium' | 'high' | 'critical'
-- status:   'todo' | 'in_progress' | 'done'
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tasks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id  INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    part_id     INTEGER          REFERENCES parts(id)    ON DELETE CASCADE,
    title       TEXT    NOT NULL,
    description TEXT,
    priority    TEXT    NOT NULL DEFAULT 'medium'
                        CHECK(priority IN ('low','medium','high','critical')),
    status      TEXT    NOT NULL DEFAULT 'todo'
                        CHECK(status IN ('todo','in_progress','done')),
    due_date    TEXT,                          -- ISO-8601 date string: YYYY-MM-DD
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_tasks_project_id ON tasks(project_id);
CREATE INDEX IF NOT EXISTS idx_tasks_part_id    ON tasks(part_id);

-- ------------------------------------------------------------
-- TABLE: materials  (Smart Bill of Materials / BOM)
-- Items to purchase or already owned ("in stash").
-- If part_id IS NULL the material belongs to the project overall.
-- category: 'fabric' | 'foam' | 'hardware' | 'paint' |
--           'wig' | 'consumable' | 'electronics' | 'other'
-- status:   'needed' | 'ordered' | 'acquired'
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS materials (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id   INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    part_id      INTEGER          REFERENCES parts(id)    ON DELETE SET NULL,
    item_name    TEXT    NOT NULL,
    category     TEXT    NOT NULL DEFAULT 'other'
                         CHECK(category IN (
                             'fabric','foam','hardware','paint',
                             'wig','consumable','electronics','other'
                         )),
    quantity     REAL    NOT NULL DEFAULT 1.0,
    unit         TEXT    NOT NULL DEFAULT 'pcs',   -- 'pcs','meters','sheets','ml','grams'
    price_est    REAL    NOT NULL DEFAULT 0.0,     -- estimated cost per unit
    price_actual REAL,                             -- actual cost per unit (NULL until purchased)
    in_stash     INTEGER NOT NULL DEFAULT 0        -- 1 = already owned, 0 = need to buy
                         CHECK(in_stash IN (0, 1)),
    status       TEXT    NOT NULL DEFAULT 'needed'
                         CHECK(status IN ('needed','ordered','acquired')),
    vendor_url   TEXT,
    notes        TEXT,
    created_at   TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_materials_project_id ON materials(project_id);
CREATE INDEX IF NOT EXISTS idx_materials_part_id    ON materials(part_id);

-- ------------------------------------------------------------
-- TABLE: references_board  (Visual Moodboard & References)
-- Images, turnarounds, colour swatches, and prop blueprints.
-- If part_id IS NULL the reference belongs to the whole project.
-- category: 'turnaround' | 'detail' | 'color_palette' |
--           'prop_blueprint' | 'inspiration'
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS references_board (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id  INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    part_id     INTEGER          REFERENCES parts(id)    ON DELETE SET NULL,
    image_path  TEXT    NOT NULL,              -- relative path under static/uploads/
    caption     TEXT,
    category    TEXT    NOT NULL DEFAULT 'inspiration'
                        CHECK(category IN (
                            'turnaround','detail','color_palette',
                            'prop_blueprint','inspiration'
                        )),
    sort_order  INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_ref_project_id ON references_board(project_id);

-- ------------------------------------------------------------
-- TABLE: feasibility_checks  (Pre-flight Wearability Reality Check)
-- One row per check per project.
-- check_type: see CHECK constraint below.
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS feasibility_checks (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id     INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    check_type     TEXT    NOT NULL
                           CHECK(check_type IN (
                               'bathroom_access',
                               'mobility_sitting',
                               'ventilation_vision',
                               'transport_breakdown',
                               'con_weapon_rules'
                           )),
    is_passed      INTEGER NOT NULL DEFAULT 0  -- 0 = not checked / fail, 1 = pass
                           CHECK(is_passed IN (0, 1)),
    solution_notes TEXT,
    updated_at     TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE(project_id, check_type)             -- one row per check per project
);

CREATE INDEX IF NOT EXISTS idx_feasibility_project_id ON feasibility_checks(project_id);


-- ------------------------------------------------------------
-- TABLE: user_measurements
-- Anatomical body measurements profile for fitting & scaling.
-- ------------------------------------------------------------
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
    preferred_unit          TEXT NOT NULL DEFAULT 'cm' CHECK(preferred_unit IN ('cm', 'in')),
    notes                   TEXT,
    updated_at              TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_measurements_user_id ON user_measurements(user_id);
