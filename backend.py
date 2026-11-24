import os
import sqlite3
import hmac
import secrets
from datetime import datetime
from functools import wraps

from flask import (Flask, render_template, request, redirect, url_for,
                   session, flash, jsonify, abort, send_from_directory)
from werkzeug.security import generate_password_hash, check_password_hash

# ДОБАВЛЕНО: Поддержка PostgreSQL (Supabase)
try:
    import psycopg2
    import psycopg2.extras
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, template_folder=BASE_DIR, static_folder=None)
app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY", "dev-only-change-this-secret-key"
)

# ДОБАВЛЕНО: Считывание переменной окружения DATABASE_URL из Render
DATABASE_URL = os.environ.get("DATABASE_URL")
DATABASE_SQLITE = os.path.join(BASE_DIR, "Final_project.db")

PUBLIC_ASSETS = {
    "hub.css",
    "hub.js",
    "index2.css",
    "index3.js",
    "6266-190550868_medium.mp4",
}

@app.route("/static/<path:filename>")
def static(filename):
    if filename not in PUBLIC_ASSETS:
        abort(404)
    return send_from_directory(BASE_DIR, filename)

TICKET_STATUSES = ("Open", "In Progress", "Resolved")
TICKET_CATEGORIES = ("Wi-Fi & Network", "LMS / Platform", "PC / Classroom Hardware",
                     "Email / Account", "Other")


# ----------------------------------------------------------------------------
# База данных (Универсальное подключение: Supabase PostgreSQL / SQLite fallback)
# ----------------------------------------------------------------------------
# ДОБАВЛЕНО: Обёртка для совместной работы SQLite и PostgreSQL
class DBWrapper:
    def __init__(self, conn, is_pg=False):
        self.conn = conn
        self.is_pg = is_pg

    def execute(self, sql, params=()):
        cursor = self.conn.cursor()
        if self.is_pg:
            # Преобразуем синтаксис плейсхолдеров SQLite (?) в PostgreSQL (%s)
            sql_pg = sql.replace("?", "%s")
            cursor.execute(sql_pg, params)
        else:
            cursor.execute(sql, params)
        return cursor

    def commit(self):
        self.conn.commit()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.conn.rollback()
        self.conn.close()


def get_db_connection():
    # ДОБАВЛЕНО: Авто-переключение на Supabase при наличии DATABASE_URL
    if DATABASE_URL and HAS_PSYCOPG2:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.DictCursor)
        return DBWrapper(conn, is_pg=True)
    else:
        conn = sqlite3.connect(DATABASE_SQLITE)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return DBWrapper(conn, is_pg=False)


def add_column_if_missing(db, table, column, definition):
    if not db.is_pg:
        columns = [row["name"] for row in db.execute(f"PRAGMA table_info({table})").fetchall()]
        if column not in columns:
            db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def init_db():
    """Создаёт таблицы при необходимости и авто-регистрирует админа."""
    with get_db_connection() as db:
        if db.is_pg:
            # Таблицы для Supabase (PostgreSQL)
            db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    login VARCHAR(255) NOT NULL UNIQUE,
                    password VARCHAR(255) NOT NULL,
                    role VARCHAR(50) NOT NULL DEFAULT 'student',
                    full_name VARCHAR(255)
                )
            """)
            db.execute("""
                CREATE TABLE IF NOT EXISTS tickets (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    description TEXT NOT NULL,
                    status VARCHAR(50) NOT NULL DEFAULT 'Open',
                    user_id INTEGER REFERENCES users(id),
                    requester_name VARCHAR(255),
                    group_name VARCHAR(255),
                    category VARCHAR(255),
                    created_at VARCHAR(50)
                )
            """)
        else:
            # Таблицы для локального SQLite
            db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    login TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'student',
                    full_name TEXT
                )
            """)
            db.execute("""
                CREATE TABLE IF NOT EXISTS tickets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'Open',
                    user_id INTEGER,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            add_column_if_missing(db, "users", "full_name", "TEXT")
            add_column_if_missing(db, "tickets", "requester_name", "TEXT")
            add_column_if_missing(db, "tickets", "group_name", "TEXT")
            add_column_if_missing(db, "tickets", "category", "TEXT")
            add_column_if_missing(db, "tickets", "created_at", "TEXT")

        # АВТОМАТИЧЕСКОЕ СОЗДАНИЕ АККАУНТА АДМИНИСТРАТОРА
        ADMIN_LOGIN = "darkhan"
        ADMIN_PASSWORD = "123"
        ADMIN_FULL_NAME = "Darkhan (Admin)"
        
        cur = db.execute("SELECT 1 FROM users WHERE lower(login) = ?", (ADMIN_LOGIN,))
        admin_exists = cur.fetchone()
        if not admin_exists:
            password_hash = generate_password_hash(ADMIN_PASSWORD)
            db.execute(
                "INSERT INTO users (login, password, role, full_name) VALUES (?, ?, 'admin', ?)",
                (ADMIN_LOGIN, password_hash, ADMIN_FULL_NAME)
            )

        db.commit()


def ticket_to_dict(row):
    return {
        "id": row["id"],
        "name": row["requester_name"] or "",
        "group": row["group_name"] or "",
        "category": row["category"] or "Other",
        "title": row["title"],
        "desc": row["description"],
        "status": row["status"],
        "date": row["created_at"] or "",
        "user_id": row["user_id"],
    }


# ----------------------------------------------------------------------------
# Вспомогательное: сессия, CSRF, декораторы
# ----------------------------------------------------------------------------
def get_csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(16)
    return session["csrf_token"]


@app.context_processor
def inject_csrf():
    return {"csrf_token": get_csrf_token}


@app.before_request
def check_csrf():
    if request.method == "POST":
        sent = request.form.get("csrf_token") or request.headers.get("X-CSRF-Token", "")
        expected = session.get("csrf_token", "")
        if not expected or not hmac.compare_digest(sent, expected):
            if request.path.startswith("/api/"):
                return jsonify(error="Invalid CSRF token. Reload the page."), 400
            flash("Your session expired. Please try again.")
            return redirect(request.referrer or url_for("login"))


def current_user():
    if "user_id" not in session:
        return None
    with get_db_connection() as db:
        cur = db.execute(
            "SELECT id, login, role, full_name FROM users WHERE id = ?",
            (session["user_id"],)
        )
        return cur.fetchone()


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            if request.path.startswith("/api/"):
                return jsonify(error="Not authenticated"), 401
            flash("Please log in to access the dashboard.")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped_view


# ----------------------------------------------------------------------------
# Страницы: регистрация / вход / выход
# ----------------------------------------------------------------------------
@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("hub"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        login = request.form.get("login", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        role = request.form.get("role", "student")

        if not full_name or not login or not password:
            flash("Please fill in all required fields.")
            return redirect(url_for("register"))
        if len(password) < 8:
            flash("Password must contain at least 8 characters.")
            return redirect(url_for("register"))
        if password != confirm_password:
            flash("Passwords do not match.")
            return redirect(url_for("register"))
        if role not in ("student", "teacher"):
            role = "student"

        password_hash = generate_password_hash(password)

        try:
            with get_db_connection() as db:
                cur = db.execute("SELECT 1 FROM users WHERE lower(login) = ?", (login,))
                if cur.fetchone():
                    flash("This login is already registered. Choose another one.")
                    return redirect(url_for("register"))
                db.execute(
                    "INSERT INTO users (login, password, role, full_name) VALUES (?, ?, ?, ?)",
                    (login, password_hash, role, full_name)
                )
                db.commit()
        except Exception:
            flash("An error occurred during registration. Please try again.")
            return redirect(url_for("register"))

        flash("Account created successfully. You can now log in.")
        return redirect(url_for("login"))

    return render_template("registration.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        login_value = request.form.get("login", "").strip().lower()
        password = request.form.get("password", "")

        with get_db_connection() as db:
            cur = db.execute(
                "SELECT id, login, password, role, full_name FROM users WHERE lower(login) = ?",
                (login_value,)
            )
            user = cur.fetchone()

        if user is None:
            flash("Incorrect login or password.")
            return redirect(url_for("login"))

        stored_password = user["password"]
        try:
            password_is_valid = check_password_hash(stored_password, password)
        except (ValueError, TypeError):
            password_is_valid = False

        if not password_is_valid and hmac.compare_digest(stored_password.encode(), password.encode()):
            password_is_valid = True
            with get_db_connection() as db:
                db.execute(
                    "UPDATE users SET password = ? WHERE id = ?",
                    (generate_password_hash(password), user["id"])
                )
                db.commit()

        if not password_is_valid:
            flash("Incorrect login or password.")
            return redirect(url_for("login"))

        session.clear()
        session["user_id"] = user["id"]
        return redirect(url_for("hub"))

    if "user_id" in session:
        return redirect(url_for("hub"))
    return render_template("login.html")


@app.route("/hub")
@login_required
def hub():
    user = current_user()
    if user is None:
        session.clear()
        return redirect(url_for("login"))
    return render_template("hub.html", user=user)


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("You have logged out.")
    return redirect(url_for("login"))


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        flash("If this account exists, recovery instructions have been sent. "
              "You can also visit the IT department (Room 304).")
        return redirect(url_for("forgot_password"))
    return render_template("forget.html")


# ----------------------------------------------------------------------------
# API заявок (tickets)
# ----------------------------------------------------------------------------
@app.route("/api/tickets", methods=["GET"])
@login_required
def api_tickets_list():
    user = current_user()
    with get_db_connection() as db:
        if user["role"] == "admin":
            cur = db.execute("SELECT * FROM tickets ORDER BY id DESC")
        else:
            cur = db.execute("SELECT * FROM tickets WHERE user_id = ? ORDER BY id DESC", (user["id"],))
        rows = cur.fetchall()
    return jsonify([ticket_to_dict(r) for r in rows])


@app.route("/api/tickets", methods=["POST"])
@login_required
def api_tickets_create():
    user = current_user()
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    group = str(data.get("group", "")).strip()
    category = str(data.get("category", "")).strip()
    description = str(data.get("desc", "")).strip()

    if not name or not group or not description:
        return jsonify(error="Please fill in all fields."), 400
    if category not in TICKET_CATEGORIES:
        category = "Other"
    if len(description) > 2000 or len(name) > 100 or len(group) > 50:
        return jsonify(error="Text is too long."), 400

    title = f"{category}: {description[:50]}"
    created_at = datetime.now().strftime("%d.%m.%Y")

    with get_db_connection() as db:
        # ДОБАВЛЕНО: Разное получение ID нового тикета для PostgreSQL (RETURNING id) и SQLite (lastrowid)
        if db.is_pg:
            cur = db.execute(
                "INSERT INTO tickets (title, description, status, user_id, requester_name, "
                "group_name, category, created_at) VALUES (?, ?, 'Open', ?, ?, ?, ?, ?) RETURNING id",
                (title, description, user["id"], name, group, category, created_at)
            )
            new_id = cur.fetchone()[0]
        else:
            cur = db.execute(
                "INSERT INTO tickets (title, description, status, user_id, requester_name, "
                "group_name, category, created_at) VALUES (?, ?, 'Open', ?, ?, ?, ?, ?)",
                (title, description, user["id"], name, group, category, created_at)
            )
            new_id = cur.lastrowid
        db.commit()

        cur_row = db.execute("SELECT * FROM tickets WHERE id = ?", (new_id,))
        row = cur_row.fetchone()
    return jsonify(ticket_to_dict(row)), 201


@app.route("/api/tickets/<int:ticket_id>/status", methods=["POST"])
@login_required
def api_ticket_status(ticket_id):
    user = current_user()
    if user["role"] != "admin":
        return jsonify(error="Only administrators can change ticket status."), 403
    data = request.get_json(silent=True) or {}
    status = data.get("status")
    if status not in TICKET_STATUSES:
        return jsonify(error="Unknown status."), 400

    with get_db_connection() as db:
        cur = db.execute("UPDATE tickets SET status = ? WHERE id = ?", (status, ticket_id))
        db.commit()
        if cur.rowcount == 0:
            return jsonify(error="Ticket not found."), 404
        cur_row = db.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
        row = cur_row.fetchone()
    return jsonify(ticket_to_dict(row))


@app.route("/api/stats")
@login_required
def api_stats():
    with get_db_connection() as db:
        cur_tot = db.execute("SELECT COUNT(*) FROM tickets")
        total = cur_tot.fetchone()[0]
        cur_res = db.execute("SELECT COUNT(*) FROM tickets WHERE status = 'Resolved'")
        resolved = cur_res.fetchone()[0]
        open_ = total - resolved
    return jsonify(total=total, resolved=resolved, open=open_)


init_db()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "5000")),
        debug=os.environ.get("FLASK_DEBUG", "0") == "1"
    )
