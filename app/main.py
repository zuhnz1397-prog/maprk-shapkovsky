from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api import api_router
from app.database import init_db
from app.config import settings, BASE_DIR


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Инициализация БД при старте
    await init_db()
    yield

app = FastAPI(
    title="Карта РК Шпаковского МО",
    description="API для управления реестром рекламных конструкций",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS — разрешаем фронтенду обращаться к API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # В продакшне заменить на конкретный домен
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем API роуты
app.include_router(api_router)

# Статические файлы (загруженные фото/схемы)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# Фронтенд — если есть папка dist (после сборки React)
frontend_dist = BASE_DIR / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "maprk-shapkovsky"}
