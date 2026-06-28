import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import init_db
from app.routers import admin, articles, auth, digest, feeds, onboarding, opml, settings as settings_router, topics
from app.scheduler import shutdown_scheduler, start_scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Path(settings.database_url.split("///")[-1]).parent.mkdir(parents=True, exist_ok=True)
    await init_db()
    start_scheduler()
    logger.info("News Router API started")
    yield
    shutdown_scheduler()


app = FastAPI(title="News Router API", version="1.0.0", lifespan=lifespan)


@app.exception_handler(Exception)
async def unhandled_exception(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1|192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(feeds.router, prefix="/api")
app.include_router(topics.router, prefix="/api")
app.include_router(articles.router, prefix="/api")
app.include_router(digest.router, prefix="/api")
app.include_router(settings_router.router, prefix="/api")
app.include_router(onboarding.router, prefix="/api")
app.include_router(opml.router, prefix="/api")
app.include_router(admin.router, prefix="/api")


@app.get("/api/health")
async def health():
    warnings: list[str] = []
    if settings.secret_key == "change-me-in-production-use-openssl-rand":
        warnings.append("SECRET_KEY is still the default — set a strong value in production")
    return {"status": "ok", "poll_api_version": 2, "warnings": warnings}
