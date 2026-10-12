from typing import Any, Dict, List, Optional

from .database import Incident


def serialize_incident(record: Incident) -> Dict[str, Any]:
    return {
        "id": record.id,
        "incident_type": record.incident_type,
        "severity": record.severity,
        "confidence": round(record.confidence, 2) if record.confidence is not None else 0.0,
        "people_count": record.people_count,
        "face_count": record.face_count,
        "details": record.details,
        "image_path": record.image_path,
        "created_at": record.created_at.isoformat() if record.created_at else None,
    }


def serialize_incidents(records: List[Incident]) -> List[Dict[str, Any]]:
    return [serialize_incident(record) for record in records]


def summary_payload(total: int, critical: int, high: int, medium: int, safe: bool) -> Dict[str, Any]:
    return {
        "total_incidents": total,
        "critical": critical,
        "high": high,
        "medium": medium,
        "safe": safe,
    }
