from contextlib import asynccontextmanager
from fastapi import FastAPI

from backend.routes.webhook import router
from backend.scheduler import start_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield


app = FastAPI(
    title="WA Task Bot",
    lifespan=lifespan
)

app.include_router(router)