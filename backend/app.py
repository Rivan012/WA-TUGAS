from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from backend.routes.webhook import router as webhook_router
from backend.routes.auth import router as auth_router
from backend.routes.groups import router as groups_router
from backend.scheduler import start_scheduler

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield


app = FastAPI(
    title="WA Task Bot",
    lifespan=lifespan
)

app.include_router(webhook_router)
app.include_router(auth_router)
app.include_router(groups_router)

# Dashboard web (login + kelola grup terdaftar) - static, dilayani dari /dashboard
if FRONTEND_DIR.exists():
    app.mount("/dashboard", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="dashboard")
