"""
Emergency Risk Classification (demonstration / assistance feature).

This module trains a Random Forest on a small labeled demo dataset.
It is NOT a real-world danger predictor. Predictions are assistance only.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

from config import Config

EMERGENCY_TYPES = [
    "Medical Emergency",
    "Accident",
    "Personal Safety",
    "Fire",
    "Harassment",
    "Other",
]

RISK_LEVELS = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

FEATURE_COLUMNS = [
    "emergency_type_code",
    "sos_attempts",
    "hour_of_day",
    "previous_frequency",
    "response_status",
    "user_severity",
]


def emergency_type_code(emergency_type):
    try:
        return EMERGENCY_TYPES.index(emergency_type)
    except ValueError:
        return EMERGENCY_TYPES.index("Other")


def _label_demo_row(row):
    """
    Transparent labeling rules used only to create the demo dataset.
    Students can read these rules and compare them with model predictions.
    """
    score = 0
    etype = row["emergency_type"]
    severity = int(row["user_severity"])
    attempts = int(row["sos_attempts"])
    hour = int(row["hour_of_day"])
    frequency = int(row["previous_frequency"])
    response = int(row["response_status"])

    if etype in {"Fire", "Medical Emergency"}:
        score += 3
    elif etype in {"Accident", "Harassment", "Personal Safety"}:
        score += 2
    else:
        score += 1

    score += severity
    if attempts >= 3:
        score += 3
    elif attempts == 2:
        score += 1

    if hour >= 22 or hour <= 5:
        score += 2

    if frequency >= 5:
        score += 2
    elif frequency >= 2:
        score += 1

    # 0 = pending, 1 = acknowledged, 2 = resolved
    if response == 0:
        score += 1

    if score >= 12:
        return "CRITICAL"
    if score >= 9:
        return "HIGH"
    if score >= 6:
        return "MEDIUM"
    return "LOW"


def generate_demo_dataset(path: Path, n_samples=360, seed=42):
    """Create a clearly labeled demonstration CSV if it does not exist."""
    rng = np.random.default_rng(seed)
    rows = []
    for _ in range(n_samples):
        emergency_type = EMERGENCY_TYPES[int(rng.integers(0, len(EMERGENCY_TYPES)))]
        row = {
            "emergency_type": emergency_type,
            "sos_attempts": int(rng.integers(1, 8)),
            "hour_of_day": int(rng.integers(0, 24)),
            "previous_frequency": int(rng.integers(0, 12)),
            "response_status": int(rng.integers(0, 3)),
            "user_severity": int(rng.integers(1, 6)),
        }
        row["risk_level"] = _label_demo_row(row)
        rows.append(row)

    path.parent.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(rows)
    frame.to_csv(path, index=False)
    return frame


def _prepare_features(frame: pd.DataFrame):
    data = frame.copy()
    data["emergency_type_code"] = data["emergency_type"].map(emergency_type_code)
    X = data[FEATURE_COLUMNS]
    y = data["risk_level"]
    return X, y


def train_and_save_model(dataset_path=None, model_path=None):
    dataset_path = Path(dataset_path or Config.DATASET_PATH)
    model_path = Path(model_path or Config.MODEL_PATH)

    if not dataset_path.exists():
        generate_demo_dataset(dataset_path)
    frame = pd.read_csv(dataset_path)
    X, y = _prepare_features(frame)

    encoder = LabelEncoder()
    y_encoded = encoder.fit_transform(y)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y_encoded,
        test_size=0.25,
        random_state=42,
        stratify=y_encoded,
    )

    classifier = RandomForestClassifier(
        n_estimators=120,
        max_depth=8,
        random_state=42,
        class_weight="balanced",
    )
    classifier.fit(X_train, y_train)
    accuracy = float(classifier.score(X_test, y_test))

    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "classifier": classifier,
            "label_encoder": encoder,
            "feature_columns": FEATURE_COLUMNS,
            "accuracy": accuracy,
            "note": (
                "Demonstration model trained on synthetic labeled data. "
                "Not a real-world danger predictor."
            ),
        },
        model_path,
    )
    return accuracy


_CACHED_BUNDLE = None


def load_model():
    global _CACHED_BUNDLE
    if _CACHED_BUNDLE is not None:
        return _CACHED_BUNDLE

    model_path = Config.MODEL_PATH
    if not model_path.exists():
        train_and_save_model()

    _CACHED_BUNDLE = joblib.load(model_path)
    return _CACHED_BUNDLE


def ensure_model():
    Config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    Config.MODEL_DIR.mkdir(parents=True, exist_ok=True)
    if not Config.DATASET_PATH.exists():
        generate_demo_dataset(Config.DATASET_PATH)
    if not Config.MODEL_PATH.exists():
        train_and_save_model()
    load_model()


def build_feature_row(
    emergency_type,
    sos_attempts,
    hour_of_day,
    previous_frequency,
    response_status,
    user_severity,
):
    return {
        "emergency_type_code": emergency_type_code(emergency_type),
        "sos_attempts": int(sos_attempts),
        "hour_of_day": int(hour_of_day),
        "previous_frequency": int(previous_frequency),
        "response_status": int(response_status),
        "user_severity": int(user_severity),
    }


def classify_risk(features: dict):
    """
    Return (risk_level, explanation_dict).
    Falls back to a readable rule if the model file cannot be loaded.
    """
    try:
        bundle = load_model()
        classifier = bundle["classifier"]
        encoder = bundle["label_encoder"]
        columns = bundle["feature_columns"]
        row = pd.DataFrame([features], columns=columns)
        predicted = classifier.predict(row)[0]
        risk = encoder.inverse_transform([predicted])[0]
        probabilities = classifier.predict_proba(row)[0]
        class_probs = {
            encoder.inverse_transform([i])[0]: round(float(probabilities[i]), 3)
            for i in range(len(encoder.classes_))
        }
        importances = {
            columns[i]: round(float(classifier.feature_importances_[i]), 3)
            for i in range(len(columns))
        }
        explanation = {
            "mode": "random_forest",
            "probabilities": class_probs,
            "feature_importances": importances,
            "disclaimer": (
                "Assistance / risk-classification only. "
                "This demo model cannot reliably predict real-world danger."
            ),
        }
        return str(risk), explanation
    except Exception as error:
        risk = _fallback_risk(features)
        explanation = {
            "mode": "fallback_rules",
            "error": str(error),
            "disclaimer": (
                "Assistance / risk-classification only. "
                "Model file unavailable; a simple rule was used instead."
            ),
        }
        return risk, explanation


def _fallback_risk(features: dict):
    severity = int(features.get("user_severity") or 1)
    attempts = int(features.get("sos_attempts") or 1)
    hour = int(features.get("hour_of_day") or datetime.now().hour)
    type_code = int(features.get("emergency_type_code") or 5)
    score = severity + attempts
    if type_code in {0, 3}:
        score += 3
    if hour >= 22 or hour <= 5:
        score += 2
    if score >= 10:
        return "CRITICAL"
    if score >= 7:
        return "HIGH"
    if score >= 4:
        return "MEDIUM"
    return "LOW"


def features_to_json(features, explanation):
    payload = {"features": features, "explanation": explanation}
    return json.dumps(payload)
