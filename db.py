"""
db.py — CosplayHub database connection manager.

Wraps SQLite with:
  - Per-request connection lifecycle via Flask's application context (g).
  - Row factory so columns are accessible by name (row['column']).
  - Foreign-key enforcement on every connection.
  - init_db() helper to execute schema.sql against a fresh database.
"""

import sqlite3
import click
import os
from flask import current_app, g


def get_db():
    """
    Return (or open) the SQLite connection for the current request context.
    The connection is stored on Flask's 'g' object so it is reused within
    the same request and automatically closed when the request ends.
    """
    if "db" not in g:
        g.db = sqlite3.connect(
            current_app.config["DATABASE"],
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        # Row factory: lets us access columns by name (row["id"]) instead of index.
        g.db.row_factory = sqlite3.Row
        # Enforce foreign-key constraints (SQLite disables them by default).
        g.db.execute("PRAGMA foreign_keys = ON")

    return g.db


def close_db(e=None):
    """
    Close the database connection at the end of the request.
    Registered with app.teardown_appcontext() in init_app().
    """
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """
    Execute schema.sql against the configured database.
    Creates all tables if they do not already exist.
    """
    db = get_db()
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path, "r", encoding="utf-8") as f:
        db.executescript(f.read())
    db.commit()


@click.command("init-db")
def init_db_command():
    """Flask CLI command: flask init-db — initialise / reset the database."""
    init_db()
    click.echo("✅  Database initialised from schema.sql")


def init_app(app):
    """
    Register database helpers with the Flask application:
      - Teardown: close_db is called after every request.
      - CLI command: 'flask init-db' is available from the terminal.
    """
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
