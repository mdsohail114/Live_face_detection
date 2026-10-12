"""SQLite connection helpers and schema creation."""

import sqlite3
from datetime import datetime, timezone

from flask import g

from config import Config


SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    phone TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS emergency_contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    phone TEXT NOT NULL,
    email TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS emergency_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    emergency_type TEXT NOT NULL,
    description TEXT,
    latitude REAL,
    longitude REAL,
    location_url TEXT,
    risk_level TEXT,
    sms_status TEXT,
    email_status TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS emergency_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_id INTEGER,
    user_id INTEGER NOT NULL,
    emergency_type TEXT,
    sos_attempts INTEGER,
    hour_of_day INTEGER,
    previous_frequency INTEGER,
    response_status INTEGER,
    user_severity INTEGER,
    predicted_risk TEXT,
    notes TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (alert_id) REFERENCES emergency_alerts(id) ON DELETE SET NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS model_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_id INTEGER,
    user_id INTEGER NOT NULL,
    emergency_type TEXT,
    sos_attempts INTEGER,
    hour_of_day INTEGER,
    previous_frequency INTEGER,
    response_status INTEGER,
    user_severity INTEGER,
    predicted_risk TEXT,
    feature_json TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (alert_id) REFERENCES emergency_alerts(id) ON DELETE SET NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
"""


def utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def get_db():
    """Return a request-scoped SQLite connection with foreign keys enabled."""
    if "db" not in g:
        Config.INSTANCE_DIR.mkdir(parents=True, exist_ok=True)
        Config.DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(Config.DATABASE_PATH)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        g.db = connection
    return g.db


def close_db(_error=None):
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()


def init_db():
    """Create tables if they do not already exist."""
    Config.INSTANCE_DIR.mkdir(parents=True, exist_ok=True)
    Config.DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(Config.DATABASE_PATH)
    try:
        connection.executescript(SCHEMA_SQL)
        connection.commit()
    finally:
        connection.close()
