"""Dashboard, SOS workflow, contacts, and alert history."""

from datetime import datetime

from flask import (
    Blueprint,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from geopy.exc import GeocoderServiceError, GeocoderTimedOut
from geopy.geocoders import Nominatim

import models
from ai_model import (
    EMERGENCY_TYPES,
    classify_risk,
    build_feature_row,
    features_to_json,
)
from auth import current_user, login_required, validate_email, validate_phone, normalize_phone
from config import Config
from notifications import notify_contacts

emergency_bp = Blueprint("emergency", __name__)

SEVERITY_CHOICES = [
    (1, "1 — Low"),
    (2, "2 — Moderate"),
    (3, "3 — Serious"),
    (4, "4 — Severe"),
    (5, "5 — Extreme"),
]


def build_location_url(latitude, longitude):
    return (
        f"https://www.google.com/maps?q={latitude},{longitude}"
        f" | https://www.openstreetmap.org/?mlat={latitude}&mlon={longitude}#map=16/{latitude}/{longitude}"
    )


def google_maps_url(latitude, longitude):
    return f"https://www.google.com/maps?q={latitude},{longitude}"


def reverse_geocode(latitude, longitude):
    """Best-effort address lookup. SOS must not fail if this service is down."""
    try:
        geolocator = Nominatim(user_agent="ai_emergency_safety_system_student_project")
        location = geolocator.reverse(
            (latitude, longitude),
            language="en",
            timeout=8,
        )
        if location and location.address:
            return location.address
    except (GeocoderTimedOut, GeocoderServiceError, Exception):
        return None
    return None


def build_emergency_message(user, location_url, emergency_type, description, address):
    extra = f" Type: {emergency_type}."
    if description:
        extra += f" Details: {description}."
    if address:
        extra += f" Approximate address: {address}."
    return (
        f"EMERGENCY ALERT! I need immediate help. "
        f"My current location is: {location_url}.{extra} "
        f"Please contact me ({user['name']}, {user['phone']}) or emergency services immediately."
    )


@emergency_bp.route("/")
def home():
    if session.get("user_id"):
        return redirect(url_for("emergency.dashboard"))
    return redirect(url_for("auth.login"))


@emergency_bp.route("/dashboard")
@login_required
def dashboard():
    user = current_user()
    contacts = models.list_contacts(user["id"])
    alerts = models.list_alerts(user["id"], limit=8)
    last_alert = alerts[0] if alerts else None
    return render_template(
        "dashboard.html",
        user=user,
        contacts=contacts,
        alerts=alerts,
        last_alert=last_alert,
        emergency_types=EMERGENCY_TYPES,
        severity_choices=SEVERITY_CHOICES,
        sms_configured=Config.sms_configured(),
        email_configured=Config.email_configured(),
    )


@emergency_bp.route("/emergency")
@login_required
def emergency_page():
    user = current_user()
    contacts = models.list_contacts(user["id"])
    return render_template(
        "emergency.html",
        user=user,
        contacts=contacts,
        emergency_types=EMERGENCY_TYPES,
        severity_choices=SEVERITY_CHOICES,
        sms_configured=Config.sms_configured(),
        email_configured=Config.email_configured(),
    )


@emergency_bp.route("/sos", methods=["POST"])
@login_required
def sos():
    user = current_user()
    payload = request.get_json(silent=True) or request.form

    try:
        latitude = float(payload.get("latitude"))
        longitude = float(payload.get("longitude"))
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "Valid latitude and longitude are required."}), 400

    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        return jsonify({"ok": False, "error": "Location values are out of range."}), 400

    emergency_type = (payload.get("emergency_type") or "Other").strip()
    if emergency_type not in EMERGENCY_TYPES:
        emergency_type = "Other"

    description = (payload.get("description") or "").strip()[:400]
    try:
        user_severity = int(payload.get("user_severity") or 3)
    except (TypeError, ValueError):
        user_severity = 3
    user_severity = min(5, max(1, user_severity))

    contacts = models.list_contacts(user["id"])
    location_url = google_maps_url(latitude, longitude)
    osm_url = (
        f"https://www.openstreetmap.org/?mlat={latitude}&mlon={longitude}"
        f"#map=16/{latitude}/{longitude}"
    )
    combined_url = f"{location_url} | {osm_url}"
    address = reverse_geocode(latitude, longitude)
    message = build_emergency_message(
        user, location_url, emergency_type, description, address
    )

    now = datetime.now()
    sos_attempts = models.count_recent_alerts(user["id"], hours=24) + 1
    previous_frequency = models.count_alerts(user["id"])
    response_status = 0  # pending at the moment the alert is created

    features = build_feature_row(
        emergency_type=emergency_type,
        sos_attempts=sos_attempts,
        hour_of_day=now.hour,
        previous_frequency=previous_frequency,
        response_status=response_status,
        user_severity=user_severity,
    )
    risk_level, explanation = classify_risk(features)

    try:
        sms_status, email_status = notify_contacts(contacts, message, user["name"])
        alert_id = models.create_alert(
            user_id=user["id"],
            emergency_type=emergency_type,
            description=description,
            latitude=latitude,
            longitude=longitude,
            location_url=combined_url,
            risk_level=risk_level,
            sms_status=sms_status,
            email_status=email_status,
        )
        feature_json = features_to_json(features, explanation)
        models.create_model_log(
            alert_id=alert_id,
            user_id=user["id"],
            emergency_type=emergency_type,
            sos_attempts=sos_attempts,
            hour_of_day=now.hour,
            previous_frequency=previous_frequency,
            response_status=response_status,
            user_severity=user_severity,
            predicted_risk=risk_level,
            feature_json=feature_json,
        )
        models.create_emergency_event(
            alert_id=alert_id,
            user_id=user["id"],
            emergency_type=emergency_type,
            sos_attempts=sos_attempts,
            hour_of_day=now.hour,
            previous_frequency=previous_frequency,
            response_status=response_status,
            user_severity=user_severity,
            predicted_risk=risk_level,
            notes=feature_json,
        )
    except Exception:
        return jsonify(
            {
                "ok": False,
                "error": "The alert could not be saved because of a database error.",
            }
        ), 500

    demo_sms = (not Config.sms_configured()) or ("Demo Mode" in sms_status)
    demo_email = (not Config.email_configured()) or ("Demo Mode" in email_status)

    return jsonify(
        {
            "ok": True,
            "alert_id": alert_id,
            "risk_level": risk_level,
            "sms_status": sms_status,
            "email_status": email_status,
            "location_url": location_url,
            "osm_url": osm_url,
            "address": address,
            "message": message,
            "demo_sms": demo_sms,
            "demo_email": demo_email,
            "ai_disclaimer": explanation.get("disclaimer"),
            "created_at": now.strftime("%Y-%m-%d %H:%M:%S"),
        }
    )


@emergency_bp.route("/history")
@login_required
def history():
    user = current_user()
    alerts = models.list_alerts(user["id"], limit=200)
    return render_template("history.html", user=user, alerts=alerts)


@emergency_bp.route("/contacts")
@login_required
def contacts():
    user = current_user()
    items = models.list_contacts(user["id"])
    return render_template("contacts.html", user=user, contacts=items)


@emergency_bp.route("/contacts/add", methods=["POST"])
@login_required
def add_contact():
    user = current_user()
    name = (request.form.get("name") or "").strip()
    phone = normalize_phone(request.form.get("phone"))
    email = (request.form.get("email") or "").strip()

    if len(name) < 2:
        flash("Contact name is required.", "danger")
    elif not validate_phone(phone):
        flash("Enter a valid contact phone number (10–15 digits).", "danger")
    elif email and not validate_email(email):
        flash("Contact email is invalid.", "danger")
    else:
        try:
            models.add_contact(user["id"], name, phone, email)
            flash("Emergency contact added.", "success")
        except Exception:
            flash("Could not add the contact because of a database error.", "danger")
    return redirect(url_for("emergency.contacts"))


@emergency_bp.route("/contacts/<int:contact_id>/edit", methods=["POST"])
@login_required
def edit_contact(contact_id):
    user = current_user()
    existing = models.get_contact(user["id"], contact_id)
    if not existing:
        flash("Contact not found.", "danger")
        return redirect(url_for("emergency.contacts"))

    name = (request.form.get("name") or "").strip()
    phone = normalize_phone(request.form.get("phone"))
    email = (request.form.get("email") or "").strip()

    if len(name) < 2:
        flash("Contact name is required.", "danger")
    elif not validate_phone(phone):
        flash("Enter a valid contact phone number (10–15 digits).", "danger")
    elif email and not validate_email(email):
        flash("Contact email is invalid.", "danger")
    else:
        try:
            models.update_contact(user["id"], contact_id, name, phone, email)
            flash("Emergency contact updated.", "success")
        except Exception:
            flash("Could not update the contact because of a database error.", "danger")
    return redirect(url_for("emergency.contacts"))


@emergency_bp.route("/contacts/<int:contact_id>/delete", methods=["POST"])
@login_required
def delete_contact(contact_id):
    user = current_user()
    existing = models.get_contact(user["id"], contact_id)
    if not existing:
        flash("Contact not found.", "danger")
    else:
        try:
            models.delete_contact(user["id"], contact_id)
            flash("Emergency contact deleted.", "success")
        except Exception:
            flash("Could not delete the contact because of a database error.", "danger")
    return redirect(url_for("emergency.contacts"))
