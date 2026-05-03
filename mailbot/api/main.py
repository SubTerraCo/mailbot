from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from mailbot.api.routers import accounts as accounts_router
from mailbot.api.routers import labels as labels_router
from mailbot.api.routers import messages as messages_router
from mailbot.api.routers import meta as meta_router
from mailbot.api.routers import oauth_web as oauth_web_router
from mailbot.api.routers import rules as rules_router
from mailbot.settings import settings

app = FastAPI(title="Mailbot", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:8765",
        "http://localhost:8765",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(meta_router.router, prefix="/api")
app.include_router(oauth_web_router.router, prefix="/api")
app.include_router(accounts_router.router, prefix="/api")
app.include_router(labels_router.router, prefix="/api")
app.include_router(messages_router.router, prefix="/api")
app.include_router(rules_router.router, prefix="/api")

_static = settings.project_root / "frontend" / "dist"
if _static.is_dir():
    app.mount("/", StaticFiles(directory=str(_static), html=True), name="static")
