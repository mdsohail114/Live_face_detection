from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from sqlalchemy.orm import Session

from .config import settings
from .database import Incident, SessionLocal, get_db
from .models import serialize_incidents, summary_payload
from .safety import classify_safety, incident_type

router = APIRouter()


@router.get("/")
async def dashboard() -> HTMLResponse:
    template_path = Path(__file__).resolve().parent.parent / "templates" / "index.html"
    html = template_path.read_text(encoding="utf-8")
    html = html.replace("{{ project_name }}", settings.PROJECT_NAME)
    return HTMLResponse(content=html)


@router.get("/api/system-status")
async def system_status(request: Request, db: Session = Depends(get_db)):
    camera = request.app.state.camera
    recent = db.query(Incident).order_by(Incident.created_at.desc()).limit(10).all()
    metrics = {
        "person_count": max(0, camera.latest_metrics.get("person_count", 0)),
        "face_count": max(0, camera.latest_metrics.get("face_count", 0)),
        "status": camera.latest_metrics.get("status", "SAFE"),
        "drowsiness_detected": bool(camera.latest_metrics.get("drowsiness_detected", False)),
        "fall_detected": bool(camera.latest_metrics.get("fall_detected", False)),
        "unsafe_activity_detected": bool(camera.latest_metrics.get("unsafe_activity_detected", False)),
    }
    severity_summary = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0}
    for item in recent:
        if item.severity in severity_summary:
            severity_summary[item.severity] += 1

    return {
        "project_name": settings.PROJECT_NAME,
        "status": classify_safety(metrics),
        "people_count": metrics["person_count"],
        "face_count": metrics["face_count"],
        "danger_level": classify_safety(metrics),
        "drowsiness": metrics["drowsiness_detected"],
        "fall_detected": metrics["fall_detected"],
        "unsafe_activity": metrics["unsafe_activity_detected"],
        "incident_type": incident_type(metrics),
        "recent_incidents": serialize_incidents(recent),
        "summary": {
            "critical": severity_summary["CRITICAL"],
            "high": severity_summary["HIGH"],
            "medium": severity_summary["MEDIUM"],
            "safe": classify_safety(metrics) == "SAFE",
        },
    }


@router.get("/api/incident-history")
async def incident_history(db: Session = Depends(get_db)):
    recent = db.query(Incident).order_by(Incident.created_at.desc()).limit(20).all()
    return {"incidents": serialize_incidents(recent)}


@router.post("/api/trigger-incident")
async def trigger_incident(request: Request, db: Session = Depends(get_db)):
    payload = await request.json()
    incident_type_name = payload.get("incident_type") or "safety_monitoring"
    severity = payload.get("severity") or "MEDIUM"
    confidence = float(payload.get("confidence", 0.0) or 0.0)
    details = payload.get("details") or "Manual incident trigger from dashboard"
    people_count = int(payload.get("people_count", 0) or 0)
    face_count = int(payload.get("face_count", 0) or 0)

    record = Incident(
        incident_type=incident_type_name,
        severity=severity,
        confidence=confidence,
        people_count=people_count,
        face_count=face_count,
        details=details,
        created_at=datetime.now(timezone.utc),
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return {"status": "created", "incident_id": record.id, "severity": severity}


@router.get("/video_feed")
async def video_feed(request: Request):
    camera = request.app.state.camera
    return StreamingResponse(camera.generate_stream(), media_type="multipart/x-mixed-replace; boundary=frame")


@router.get("/api/summary")
async def summary(request: Request, db: Session = Depends(get_db)):
    camera = request.app.state.camera
    recent = db.query(Incident).order_by(Incident.created_at.desc()).limit(10).all()
    metrics = {
        "person_count": camera.latest_metrics.get("person_count", 0),
        "face_count": camera.latest_metrics.get("face_count", 0),
        "drowsiness_detected": camera.latest_metrics.get("drowsiness_detected", False),
        "fall_detected": camera.latest_metrics.get("fall_detected", False),
        "unsafe_activity_detected": camera.latest_metrics.get("unsafe_activity_detected", False),
    }
    return {
        "status": classify_safety(metrics),
        "incident_type": incident_type(metrics),
        "summary": summary_payload(total=len(recent), critical=0, high=0, medium=0, safe=classify_safety(metrics) == "SAFE"),
    }
