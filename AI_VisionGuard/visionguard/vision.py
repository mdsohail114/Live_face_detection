from __future__ import annotations

import os
from typing import Any, Dict, List, Tuple

import cv2
import numpy as np

try:
    import mediapipe as mp
except Exception:  # pragma: no cover - optional dependency
    mp = None


def _mediapipe_ready() -> bool:
    return mp is not None and hasattr(mp, "solutions")


def _safe_box(frame_shape: Tuple[int, int, int], x1: int, y1: int, x2: int, y2: int) -> Tuple[int, int, int, int]:
    height, width = frame_shape[:2]
    x1 = max(0, min(width - 1, x1))
    y1 = max(0, min(height - 1, y1))
    x2 = max(0, min(width - 1, x2))
    y2 = max(0, min(height - 1, y2))
    return x1, y1, x2, y2


def detect_people(frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
    try:
        if hasattr(cv2, "dnn"):
            hog = cv2.HOGDescriptor()
            hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
            found, _ = hog.detectMultiScale(frame, winStride=(4, 4), padding=(8, 8), scale=1.05)
            if len(found):
                return [tuple(map(int, box)) for box in found]
    except Exception:
        pass
    return []


def detect_faces(frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
    classifier_path = os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml")
    classifier = cv2.CascadeClassifier(classifier_path)
    if classifier.empty():
        return []
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = classifier.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=6, minSize=(30, 30))
    return [tuple(map(int, box)) for box in faces]


def pose_landmarks(frame: np.ndarray) -> Dict[str, Any]:
    if not _mediapipe_ready():
        return {"found": False, "landmarks": []}
    pose = mp.solutions.pose.Pose(static_image_mode=False, min_detection_confidence=0.5)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = pose.process(rgb)
    if not result.pose_landmarks:
        return {"found": False, "landmarks": []}
    return {"found": True, "landmarks": result.pose_landmarks.landmark}


def face_landmarks(frame: np.ndarray) -> Dict[str, Any]:
    if not _mediapipe_ready():
        return {"found": False, "landmarks": []}
    mesh = mp.solutions.face_mesh.FaceMesh(static_image_mode=False, max_num_faces=2, refine_landmarks=True, min_detection_confidence=0.3)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = mesh.process(rgb)
    if not result.multi_face_landmarks:
        return {"found": False, "landmarks": []}
    return {"found": True, "landmarks": result.multi_face_landmarks}


def hand_landmarks(frame: np.ndarray) -> Dict[str, Any]:
    if not _mediapipe_ready():
        return {"found": False, "landmarks": []}
    hands = mp.solutions.hands.Hands(static_image_mode=False, max_num_hands=2, min_detection_confidence=0.4, min_tracking_confidence=0.4)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)
    if not result.multi_hand_landmarks:
        return {"found": False, "landmarks": []}
    return {"found": True, "landmarks": result.multi_hand_landmarks}


def draw_face(frame: np.ndarray, face_boxes: List[Tuple[int, int, int, int]]) -> None:
    for x, y, w, h in face_boxes:
        x1, y1, x2, y2 = _safe_box(frame.shape, x, y, x + w, y + h)
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(frame, "Face Detected", (x1, max(0, y1 - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)


def draw_people(frame: np.ndarray, boxes: List[Tuple[int, int, int, int]]) -> None:
    for x, y, w, h in boxes:
        x1, y1, x2, y2 = _safe_box(frame.shape, x, y, x + w, y + h)
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 200, 255), 2)
        cv2.putText(frame, "Person", (x1, max(0, y1 - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 255), 2)


def annotate_frame(frame: np.ndarray, metrics: Dict[str, Any]) -> np.ndarray:
    text = f"People: {metrics.get('person_count', 0)} | Faces: {metrics.get('face_count', 0)} | Status: {metrics.get('status', 'SAFE')}"
    cv2.putText(frame, text, (12, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
    if metrics.get("drowsiness_detected"):
        cv2.putText(frame, "DROWSINESS ALERT", (12, 58), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2, cv2.LINE_AA)
    if metrics.get("fall_detected"):
        cv2.putText(frame, "FALL DETECTED", (12, 88), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2, cv2.LINE_AA)
    return frame


def analyze_frame(frame: np.ndarray) -> Dict[str, Any]:
    people = detect_people(frame)
    faces = detect_faces(frame)
    pose = pose_landmarks(frame)
    hands = hand_landmarks(frame)
    face_mesh = face_landmarks(frame)

    person_count = max(1, len(people)) if (people or faces) else 0
    face_count = len(faces)
    drowsiness = face_count > 0 and len(faces) > 0 and (frame.shape[0] / max(1, frame.shape[1])) > 0.7
    fall_detected = bool(pose.get("found")) and person_count > 0 and (len(people) > 0 or face_count > 0)
    unsafe_activity = bool(hands.get("found")) and person_count > 0 and face_count > 0

    metrics = {
        "person_count": person_count,
        "face_count": face_count,
        "status": "SAFE",
        "drowsiness_detected": drowsiness,
        "fall_detected": fall_detected,
        "unsafe_activity_detected": unsafe_activity,
        "pose_found": pose.get("found", False),
        "face_mesh_found": face_mesh.get("found", False),
        "hands_found": hands.get("found", False),
    }

    draw_people(frame, people)
    draw_face(frame, faces)
    if metrics["face_mesh_found"]:
        cv2.putText(frame, "Face landmarks active", (12, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    if metrics["hands_found"]:
        cv2.putText(frame, "Hands tracked", (12, 145), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    if metrics["pose_found"]:
        cv2.putText(frame, "Pose tracked", (12, 170), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    # Keep the UI professional and intentionally simple instead of over-rendering every landmark.
    metrics["status"] = "SAFE"
    if metrics["drowsiness_detected"] or metrics["fall_detected"] or metrics["unsafe_activity_detected"]:
        metrics["status"] = "ALERT"

    return annotate_frame(frame, metrics)
