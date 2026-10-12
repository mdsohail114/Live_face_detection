from __future__ import annotations

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .camera import CameraManager
from .config import settings
from .database import init_db
from .routes import router


def create_app() -> FastAPI:
    app = FastAPI(title=settings.PROJECT_NAME, version="1.0.0")
    app.state.camera = CameraManager()
    app.state.camera.start()

    app.mount("/static", StaticFiles(directory=str(settings.STATIC_DIR)), name="static")
    app.mount("/media", StaticFiles(directory=str(settings.MEDIA_DIR), check_dir=False), name="media")

    templates = Jinja2Templates(directory=str(settings.TEMPLATES_DIR))
    app.state.templates = templates

    init_db()
    app.include_router(router)

    @app.get("/health")
    async def healthcheck() -> dict:
        return {"status": "ok", "project": settings.PROJECT_NAME}

    return app
