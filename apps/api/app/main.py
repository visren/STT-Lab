from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import ensure_dirs, settings
from .db import init_db
from .routers import audio, datasets, evaluate, finetune, models, settings as settings_router, transcribe

ensure_dirs()
init_db()

app = FastAPI(title="STT Lab API", version="0.1.0")

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(models.router)
app.include_router(transcribe.router)
app.include_router(datasets.router)
app.include_router(finetune.router)
app.include_router(evaluate.router)
app.include_router(settings_router.router)
app.include_router(audio.router)


@app.get("/api/health")
def health():
    return {"ok": True, "service": "stt-lab"}
