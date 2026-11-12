"""
auth.py — CosplayHub Authentication Blueprint (Level 2).

Provides:
  - User registration with validation and password hashing (Werkzeug).
  - User login with credential verification and session management.
  - User logout (session cleanup).
  - g.user population for every request via before_app_request.
  - @login_required decorator to protect private routes.
"""

import functools
from flask import (
    Blueprint,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash
from db import get_db

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.before_app_request
def load_logged_in_user():
    """
    Runs before every request. If a user_id is stored in the session,
    loads the user's record from SQLite and attaches it to Flask's 'g' object.
    Accessible in templates as 'g.user'.
    """
    user_id = session.get("user_id")

    if user_id is None:
        g.user = None
    else:
        db = get_db()
        g.user = db.execute(
            "SELECT id, username, email, created_at FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()


def login_required(view):
    """
    Decorator for views that require user authentication.
    Redirects unauthenticated users to the login page.
    """
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("auth.login", next=request.path))
        return view(**kwargs)

    return wrapped_view


@bp.route("/register", methods=("GET", "POST"))
def register():
    """Handle new user registration."""
    # If already logged in, redirect to dashboard or home
    if g.user:
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        error = None
        db = get_db()

        # Validation rules
        if not username:
            error = "Username is required."
        elif len(username) < 3:
            error = "Username must be at least 3 characters."
        elif not email:
            error = "Email is required."
        elif "@" not in email or "." not in email:
            error = "Please enter a valid email address."
        elif not password:
            error = "Password is required."
        elif len(password) < 6:
            error = "Password must be at least 6 characters."
        elif password != confirm_password:
            error = "Passwords do not match."
        elif db.execute(
            "SELECT id FROM users WHERE username = ?", (username,)
        ).fetchone():
            error = f"Username '{username}' is already taken."
        elif db.execute(
            "SELECT id FROM users WHERE email = ?", (email,)
        ).fetchone():
            error = f"Email '{email}' is already registered."

        if error is None:
            # Secure password hashing with Werkzeug (scrypt / pbkdf2)
            password_hash = generate_password_hash(password)
            db.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                (username, email, password_hash),
            )
            db.commit()

            flash("Registration successful! You can now log in.", "success")
            return redirect(url_for("auth.login"))

        flash(error, "error")

    return render_template("auth/register.html")


@bp.route("/login", methods=("GET", "POST"))
def login():
    """Handle user login and session creation."""
    if g.user:
        return redirect(url_for("index"))

    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()
        password = request.form.get("password", "")

        error = None
        db = get_db()

        # Allow logging in with either username or email
        user = db.execute(
            "SELECT * FROM users WHERE username = ? OR email = ?",
            (identifier, identifier.lower()),
        ).fetchone()

        if user is None:
            error = "Incorrect username/email or password."
        elif not check_password_hash(user["password_hash"], password):
            error = "Incorrect username/email or password."

        if error is None:
            # Clear old session data and set new credentials
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]

            flash(f"Welcome back, {user['username']}! 🧵", "success")

            next_url = request.args.get("next")
            if next_url and next_url.startswith("/"):
                return redirect(next_url)
            return redirect(url_for("index"))

        flash(error, "error")

    return render_template("auth/login.html")


@bp.route("/logout")
def logout():
    """Clear the session and log the user out."""
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
