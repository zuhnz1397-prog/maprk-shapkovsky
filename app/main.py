from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.api import api_router
from app.config import settings, BASE_DIR


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="Карта РК Шпаковского МО",
    description="API для управления реестром рекламных конструкций",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

frontend_dist = BASE_DIR / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "maprk-shapkovsky"}


@app.get("/api/debug")
def debug_db():
    try:
        from app.database import SessionLocal
        from app.models.rk import RK
        db = SessionLocal()
        count = db.query(RK).count()
        db.close()
        return {"status": "ok", "rk_count": count}
    except Exception as e:
        import traceback
        return {"status": "error", "error": str(e), "trace": traceback.format_exc()}