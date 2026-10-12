"""Registration, login, logout, and login-required protection."""

import re

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

import models

auth_bp = Blueprint("auth", __name__)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^\+?[0-9]{10,15}$")


def login_required(view):
    from functools import wraps

    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in to continue.", "warning")
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)

    return wrapped


def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return models.get_user_by_id(user_id)


def normalize_phone(value):
    cleaned = re.sub(r"[\s\-()]", "", (value or "").strip())
    return cleaned


def validate_phone(value):
    return bool(PHONE_RE.match(normalize_phone(value)))


def validate_email(value):
    return bool(EMAIL_RE.match((value or "").strip()))


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("emergency.dashboard"))

    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip()
        phone = normalize_phone(request.form.get("phone"))
        password = request.form.get("password") or ""
        confirm = request.form.get("confirm_password") or ""
        contact_name = (request.form.get("contact_name") or "").strip()
        contact_phone = normalize_phone(request.form.get("contact_phone"))
        contact_email = (request.form.get("contact_email") or "").strip()

        errors = []
        if len(name) < 2:
            errors.append("Please enter your full name.")
        if not validate_email(email):
            errors.append("Please enter a valid email address.")
        if not validate_phone(phone):
            errors.append("Enter a valid phone number (10–15 digits, optional +).")
        if len(password) < 8:
            errors.append("Password must be at least 8 characters.")
        if password != confirm:
            errors.append("Passwords do not match.")
        if len(contact_name) < 2:
            errors.append("Please enter an emergency contact name.")
        if not validate_phone(contact_phone):
            errors.append("Enter a valid emergency contact phone number.")
        if contact_email and not validate_email(contact_email):
            errors.append("Emergency contact email is invalid.")
        if models.get_user_by_email(email):
            errors.append("An account with this email already exists.")

        if errors:
            for message in errors:
                flash(message, "danger")
            return render_template("register.html")

        try:
            user_id = models.create_user(
                name=name,
                email=email,
                phone=phone,
                password_hash=generate_password_hash(password, method="pbkdf2:sha256"),
            )
            models.add_contact(user_id, contact_name, contact_phone, contact_email)
        except Exception:
            flash("Could not create the account because of a database error.", "danger")
            return render_template("register.html")

        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("emergency.dashboard"))

    if request.method == "POST":
        email = (request.form.get("email") or "").strip()
        password = request.form.get("password") or ""
        user = models.get_user_by_email(email)
        if not user or not check_password_hash(user["password_hash"], password):
            flash("Invalid email or password.", "danger")
            return render_template("login.html")

        session.clear()
        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        flash(f"Welcome back, {user['name']}.", "success")
        return redirect(url_for("emergency.dashboard"))

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
