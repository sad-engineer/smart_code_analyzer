#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------------------------------------------------
from pathlib import Path
from typing import List

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.requests import Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import ValidationError
from pydantic_settings import BaseSettings

from smart_code_analyzer.backend.analyzer_api import router as analyzer_router
from smart_code_analyzer.backend.models import ErrorResponse

app = FastAPI(
    title="Smart Code Analyzer",
    description="""
    Smart Code Analyzer — сервис для анализа исходного кода и архитектуры проектов с помощью статических методов и 
    искусственного интеллекта.

    **Возможности:**
    - Анализ отдельных файлов и целых пакетов
    - Проверка стиля, SOLID, поиск проблем
    - ИИ-анализ структуры проекта
    """,
    version="0.0.13",
)


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
    ]
    ALLOWED_METHODS: List[str] = ["GET", "POST"]
    ALLOWED_HEADERS: List[str] = ["Content-Type", "Authorization"]

    class Config:
        env_file = ".env"


settings = Settings()

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=settings.ALLOWED_METHODS,
    allow_headers=settings.ALLOWED_HEADERS,
)

# Подключаем статические файлы
BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "frontend" / "templates"
STATIC_DIR = BASE_DIR / "frontend" / "static"

# Создаем директории, если они не существуют
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
STATIC_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Настраиваем шаблоны
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Подключаем роутеры
app.include_router(analyzer_router)

# Интеграция Prometheus для метрик
Instrumentator().instrument(app).expose(app)


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """Обработчик ошибок валидации Pydantic"""
    return JSONResponse(
        status_code=422, content=ErrorResponse(error="Ошибка валидации данных", details={"errors": exc.errors()}).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Общий обработчик ошибок"""
    return JSONResponse(
        status_code=500, content=ErrorResponse(error="Внутренняя ошибка сервера", details={"message": str(exc)}).dict()
    )


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Отображает главную страницу с формой загрузки."""
    return templates.TemplateResponse("index.html", {"request": request})


def start():
    uvicorn.run("smart_code_analyzer.backend.main:app", host="127.0.0.1", port=8000, reload=True)


if __name__ == "__main__":
    start()

#     poetry run uvicorn smart_code_analyzer.backend.main:app --reload --host 0.0.0.0 --port 8000
#       http://localhost:8000
#       http://localhost:8000/docs
#       http://localhost:8000/redoc
#       http://localhost:8000/metrics

# ENVIRONMENT=production
# ALLOWED_ORIGINS=["https://your-production-domain.com"]
# Добавить тесты
# Добавить мониторинг и метрики
# Добавьте Prometheus и (по желанию) Grafana для визуализации.
