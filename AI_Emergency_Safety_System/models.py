"""Data-access functions using parameterized SQL queries."""

from database import get_db, utc_now


def _row_to_dict(row):
    if row is None:
        return None
    return dict(row)


def create_user(name, email, phone, password_hash):
    db = get_db()
    cursor = db.execute(
        """
        INSERT INTO users (name, email, phone, password_hash, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (name, email.lower().strip(), phone, password_hash, utc_now()),
    )
    db.commit()
    return cursor.lastrowid


def get_user_by_email(email):
    db = get_db()
    row = db.execute(
        "SELECT * FROM users WHERE email = ?",
        (email.lower().strip(),),
    ).fetchone()
    return _row_to_dict(row)


def get_user_by_id(user_id):
    db = get_db()
    row = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return _row_to_dict(row)


def list_contacts(user_id):
    db = get_db()
    rows = db.execute(
        """
        SELECT * FROM emergency_contacts
        WHERE user_id = ?
        ORDER BY name COLLATE NOCASE
        """,
        (user_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def get_contact(user_id, contact_id):
    db = get_db()
    row = db.execute(
        "SELECT * FROM emergency_contacts WHERE id = ? AND user_id = ?",
        (contact_id, user_id),
    ).fetchone()
    return _row_to_dict(row)


def add_contact(user_id, name, phone, email):
    db = get_db()
    cursor = db.execute(
        """
        INSERT INTO emergency_contacts (user_id, name, phone, email)
        VALUES (?, ?, ?, ?)
        """,
        (user_id, name, phone, email or None),
    )
    db.commit()
    return cursor.lastrowid


def update_contact(user_id, contact_id, name, phone, email):
    db = get_db()
    db.execute(
        """
        UPDATE emergency_contacts
        SET name = ?, phone = ?, email = ?
        WHERE id = ? AND user_id = ?
        """,
        (name, phone, email or None, contact_id, user_id),
    )
    db.commit()


def delete_contact(user_id, contact_id):
    db = get_db()
    db.execute(
        "DELETE FROM emergency_contacts WHERE id = ? AND user_id = ?",
        (contact_id, user_id),
    )
    db.commit()


def create_alert(
    user_id,
    emergency_type,
    description,
    latitude,
    longitude,
    location_url,
    risk_level,
    sms_status,
    email_status,
):
    db = get_db()
    cursor = db.execute(
        """
        INSERT INTO emergency_alerts (
            user_id, emergency_type, description, latitude, longitude,
            location_url, risk_level, sms_status, email_status, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            emergency_type,
            description,
            latitude,
            longitude,
            location_url,
            risk_level,
            sms_status,
            email_status,
            utc_now(),
        ),
    )
    db.commit()
    return cursor.lastrowid


def list_alerts(user_id, limit=50):
    db = get_db()
    rows = db.execute(
        """
        SELECT * FROM emergency_alerts
        WHERE user_id = ?
        ORDER BY datetime(created_at) DESC, id DESC
        LIMIT ?
        """,
        (user_id, limit),
    ).fetchall()
    return [dict(row) for row in rows]


def get_alert(user_id, alert_id):
    db = get_db()
    row = db.execute(
        "SELECT * FROM emergency_alerts WHERE id = ? AND user_id = ?",
        (alert_id, user_id),
    ).fetchone()
    return _row_to_dict(row)


def count_alerts(user_id):
    db = get_db()
    row = db.execute(
        "SELECT COUNT(*) AS total FROM emergency_alerts WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    return int(row["total"]) if row else 0


def count_recent_alerts(user_id, hours=24):
    """Count SOS alerts created in the last N hours (used as SOS-attempt feature)."""
    db = get_db()
    row = db.execute(
        """
        SELECT COUNT(*) AS total
        FROM emergency_alerts
        WHERE user_id = ?
          AND datetime(created_at) >= datetime('now', ?)
        """,
        (user_id, f"-{int(hours)} hours"),
    ).fetchone()
    return int(row["total"]) if row else 0


def create_model_log(
    alert_id,
    user_id,
    emergency_type,
    sos_attempts,
    hour_of_day,
    previous_frequency,
    response_status,
    user_severity,
    predicted_risk,
    feature_json,
):
    db = get_db()
    cursor = db.execute(
        """
        INSERT INTO model_logs (
            alert_id, user_id, emergency_type, sos_attempts, hour_of_day,
            previous_frequency, response_status, user_severity,
            predicted_risk, feature_json, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            alert_id,
            user_id,
            emergency_type,
            sos_attempts,
            hour_of_day,
            previous_frequency,
            response_status,
            user_severity,
            predicted_risk,
            feature_json,
            utc_now(),
        ),
    )
    db.commit()
    return cursor.lastrowid


def create_emergency_event(
    alert_id,
    user_id,
    emergency_type,
    sos_attempts,
    hour_of_day,
    previous_frequency,
    response_status,
    user_severity,
    predicted_risk,
    notes,
):
    """Store the feature snapshot used by the risk classifier."""
    db = get_db()
    cursor = db.execute(
        """
        INSERT INTO emergency_events (
            alert_id, user_id, emergency_type, sos_attempts, hour_of_day,
            previous_frequency, response_status, user_severity,
            predicted_risk, notes, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            alert_id,
            user_id,
            emergency_type,
            sos_attempts,
            hour_of_day,
            previous_frequency,
            response_status,
            user_severity,
            predicted_risk,
            notes,
            utc_now(),
        ),
    )
    db.commit()
    return cursor.lastrowid
