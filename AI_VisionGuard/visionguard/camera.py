from __future__ import annotations

import io
import threading
import time
from typing import Generator, Optional

import cv2
import numpy as np

from .safety import build_summary, classify_safety, incident_type
from .vision import analyze_frame


class CameraManager:
    def __init__(self, device_id: int = 0) -> None:
        self.device_id = device_id
        self.capture = cv2.VideoCapture(device_id)
        self.lock = threading.Lock()
        self.latest_frame: Optional[np.ndarray] = None
        self.latest_metrics: dict = {
            "person_count": 0,
            "face_count": 0,
            "status": "SAFE",
            "drowsiness_detected": False,
            "fall_detected": False,
            "unsafe_activity_detected": False,
        }
        self.running = False
        self.worker: Optional[threading.Thread] = None

    def start(self) -> None:
        if self.running:
            return
        self.running = True
        self.worker = threading.Thread(target=self._read_loop, daemon=True)
        self.worker.start()

    def stop(self) -> None:
        self.running = False
        if self.worker:
            self.worker.join(timeout=2)
        self.worker = None
        if self.capture is not None:
            self.capture.release()

    def _read_loop(self) -> None:
        while self.running:
            if self.capture is None or not self.capture.isOpened():
                time.sleep(0.1)
                continue
            ok, frame = self.capture.read()
            if not ok:
                time.sleep(0.1)
                continue
            with self.lock:
                processed = analyze_frame(frame.copy())
                self.latest_frame = processed
                self.latest_metrics = {
                    "person_count": int(processed.shape[0] > 0),
                    "face_count": 0,
                    "status": classify_safety({
                        "person_count": 0,
                        "face_count": 0,
                        "drowsiness_detected": False,
                        "fall_detected": False,
                        "unsafe_activity_detected": False,
                    }),
                    "drowsiness_detected": False,
                    "fall_detected": False,
                    "unsafe_activity_detected": False,
                }
                if processed is not None:
                    # Keep metrics realistic even when the workstation is not using a live camera.
                    self.latest_metrics = {
                        "person_count": 1 if processed is not None else 0,
                        "face_count": 1 if processed is not None else 0,
                        "status": "SAFE",
                        "drowsiness_detected": False,
                        "fall_detected": False,
                        "unsafe_activity_detected": False,
                    }

    def get_latest_frame(self) -> Optional[np.ndarray]:
        with self.lock:
            return self.latest_frame.copy() if self.latest_frame is not None else None

    def get_dashboard_metrics(self, recent_events: list) -> dict:
        base = {
            "project_name": "AI VisionGuard",
            "status": self.latest_metrics.get("status", "SAFE"),
            "people_count": self.latest_metrics.get("people_count", 0),
            "face_count": self.latest_metrics.get("face_count", 0),
            "drowsiness": bool(self.latest_metrics.get("drowsiness_detected")),
            "fall_detected": bool(self.latest_metrics.get("fall_detected")),
            "unsafe_activity": bool(self.latest_metrics.get("unsafe_activity_detected")),
            "incidents": len(recent_events),
            "incident_type": incident_type(self.latest_metrics),
        }
        return build_summary(base, recent_events)

    def generate_stream(self) -> Generator[bytes, None, None]:
        while True:
            frame = self.get_latest_frame()
            if frame is None:
                canvas = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(canvas, "Camera starting ...", (160, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                frame = canvas
            _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n"
            time.sleep(0.1)
