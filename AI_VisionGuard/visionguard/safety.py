from __future__ import annotations

from typing import Any, Dict, List


def classify_safety(metrics: Dict[str, Any]) -> str:
    risk_score = 0
    if metrics.get("fall_detected"):
        risk_score += 35
    if metrics.get("drowsiness_detected"):
        risk_score += 25
    if metrics.get("unsafe_activity_detected"):
        risk_score += 30
    if metrics.get("person_count", 0) >= 3:
        risk_score += 10
    if metrics.get("face_count", 0) == 0 and metrics.get("person_count", 0) > 0:
        risk_score += 5

    if risk_score >= 60:
        return "CRITICAL"
    if risk_score >= 40:
        return "HIGH"
    if risk_score >= 20:
        return "MEDIUM"
    return "SAFE"


def incident_type(metrics: Dict[str, Any]) -> str:
    if metrics.get("fall_detected"):
        return "fall_detection"
    if metrics.get("drowsiness_detected"):
        return "drowsiness"
    if metrics.get("unsafe_activity_detected"):
        return "unsafe_activity"
    if metrics.get("face_count", 0) > 0:
        return "face_monitoring"
    return "environment_monitoring"


def build_summary(metrics: Dict[str, Any], recent: List[Dict[str, Any]]) -> Dict[str, Any]:
    severity_map = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0}
    for item in recent:
        severity = item.get("severity", "SAFE")
        if severity in severity_map:
            severity_map[severity] += 1

    return {
        "project_name": "AI VisionGuard",
        "status": classify_safety(metrics),
        "people_count": metrics.get("person_count", 0),
        "face_count": metrics.get("face_count", 0),
        "drowsiness": bool(metrics.get("drowsiness_detected")),
        "fall_detected": bool(metrics.get("fall_detected")),
        "unsafe_activity": bool(metrics.get("unsafe_activity_detected")),
        "critical_count": severity_map["CRITICAL"],
        "high_count": severity_map["HIGH"],
        "medium_count": severity_map["MEDIUM"],
        "safe": classify_safety(metrics) == "SAFE",
    }
