# AI VisionGuard

AI VisionGuard is a real-time AI safety monitoring dashboard built with Python, FastAPI, OpenCV, MediaPipe, and SQLite. It is designed as a professional portfolio project for AI and computer vision roles.

## Features

- Real-time webcam feed with live dashboard
- Person detection and face detection
- Pose and hand tracking support via MediaPipe
- Safety scoring with configurable alert rules
- Incident recording in SQLite
- Triggered incident capture and recent history
- Professional analytics dashboard with Chart.js
- Docker and docker-compose support for deployment

## Stack

- Python
- FastAPI
- Uvicorn
- OpenCV
- MediaPipe
- Ultralytics (optional YOLO integration)
- SQLAlchemy
- SQLite
- scikit-learn
- pandas
- numpy
- Chart.js
- pytest

## Run locally

```bash
cd AI_VisionGuard
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Then open:

http://127.0.0.1:8000

## Docker

```bash
docker compose up --build
```

## Testing

```bash
pytest -q
```
