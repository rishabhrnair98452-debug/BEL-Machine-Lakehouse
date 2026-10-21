import sqlite3
from pathlib import Path
from functools import wraps

from flask import (
    Blueprint,
    request,
    redirect,
    url_for,
    session,
    flash,
    render_template,
    jsonify,
)

from werkzeug.security import generate_password_hash, check_password_hash


# ============================================================
# 1. AUTHENTICATION BLUEPRINT
# ============================================================

auth = Blueprint("auth", __name__)

DATABASE = Path(__file__).resolve().parent / "users.db"

ROLES = {
    "Admin",
    "Maintenance Engineer",
    "Operator",
    "Viewer",
}


# ============================================================
# 2. DATABASE CONNECTION
# ============================================================

def get_db():
    """Open a connection to the SQLite user database."""
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def init_auth_db():
    """Create the users table if it does not exist."""
    with get_db() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


# ============================================================
# 3. CREATE USER
# ============================================================

def create_user(username, password, role):
    """Create an account with a securely hashed password."""

    username = username.strip()

    if not username or len(username) > 80:
        raise ValueError(
            "Username must contain 1–80 characters."
        )

    if len(password) < 12:
        raise ValueError(
            "Password must contain at least 12 characters."
        )

    if role not in ROLES:
        raise ValueError("Invalid user role.")

    with get_db() as connection:
        connection.execute(
            """
            INSERT INTO users (
                username,
                password_hash,
                role
            )
            VALUES (?, ?, ?)
            """,
            (
                username,
                generate_password_hash(password),
                role,
            ),
        )


# ============================================================
# 4. VERIFY USER CREDENTIALS
# ============================================================

def verify_user(username, password):
    """Return the active user if the credentials are valid."""

    with get_db() as connection:
        user = connection.execute(
            """
            SELECT id, username, password_hash, role
            FROM users
            WHERE username = ? AND active = 1
            """,
            (username.strip(),),
        ).fetchone()

    if user and check_password_hash(
        user["password_hash"],
        password,
    ):
        return {
            "id": user["id"],
            "username": user["username"],
            "role": user["role"],
        }

    return None


# ============================================================
# 5. LOGIN REQUIRED DECORATOR
# ============================================================

def login_required(view):
    """Require the user to be logged in."""

    @wraps(view)
    def wrapped(*args, **kwargs):

        if not session.get("user_id"):

            if request.path.startswith("/api/"):
                return jsonify({
                    "error": "Authentication required"
                }), 401

            return redirect(
                url_for("auth.login")
            )

        return view(*args, **kwargs)

    return wrapped


# ============================================================
# 6. ROLE REQUIRED DECORATOR
# ============================================================

def role_required(*allowed_roles):
    """Require login and one of the permitted roles."""

    def decorator(view):

        @wraps(view)
        @login_required
        def wrapped(*args, **kwargs):

            current_role = session.get("role")

            if current_role not in allowed_roles:

                if request.path.startswith("/api/"):
                    return jsonify({
                        "error": "Insufficient permissions"
                    }), 403

                return (
                    "403 - You do not have permission "
                    "to access this page.",
                    403,
                )

            return view(*args, **kwargs)

        # IMPORTANT: Return the wrapped view function.
        return wrapped

    # Return the decorator itself.
    return decorator


# ============================================================
# 7. LOGIN ROUTE
# ============================================================

@auth.route("/login", methods=["GET", "POST"])
def login():
    """Display the login page and authenticate users."""

    if session.get("user_id"):
        return redirect(url_for("index"))

    if request.method == "POST":

        username = request.form.get(
            "username", ""
        ).strip()

        password = request.form.get(
            "password", ""
        )

        selected_role = request.form.get(
            "role", ""
        )

        user = verify_user(username, password)

        # The role stored in the database is authoritative.
        # Selecting Admin in the form does not grant Admin access.
        if user and user["role"] == selected_role:

            session.clear()

            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]

            return redirect(url_for("index"))

        flash(
            "Invalid username, password, or account category.",
            "error",
        )

    return render_template("login.html")


# ============================================================
# 8. LOGOUT ROUTE
# ============================================================

@auth.route("/logout", methods=["POST"])
def logout():
    """Log out the current user."""

    session.clear()

    return redirect(url_for("auth.login"))