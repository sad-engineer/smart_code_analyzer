#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------------------------------------------------
import logging
from dataclasses import asdict
from typing import Any, Dict, List, Union

from code_analizer import FileBatchAnalyzer, HtmlFormatter, HtmlSummaryFormatter, LineProcessor, SummaryData
from fastapi import APIRouter, File, UploadFile

from smart_code_analyzer.backend.ai_analyzer import AIAnalyzer

router = APIRouter(prefix="/analyzer", tags=["analyzer"])

# Настраиваем класс пакетного анализа списка файлов
batch_analyzer = FileBatchAnalyzer(LineProcessor)

# Настраиваем логирование
logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.DEBUG)


@router.post("/analyze")
async def analyze_code(files: List[UploadFile] = File(...)):
    """
    Анализирует загруженный файл с кодом
    """
    logger.info(f"Загружено файлов для parsing-анализа: {len(files)}")
    results_analysis = {}
    datas_list = await batch_analyzer.analyze_files(files)
    summary_data = batch_analyzer.get_summary()

    code_formatter = HtmlFormatter()
    summary_formatter = HtmlSummaryFormatter()

    for code_data in datas_list:
        formatted_html = code_formatter.format(code_data)
        results_analysis[code_data.filename] = {
            "status": "completed",
            "data": asdict(code_data),
            "html": formatted_html,
        }

    # Добавляем summary_data в результаты
    results_analysis["summary"] = {
        "status": "completed",
        "data": summary_data,
        "html": summary_formatter.format(summary_data),
    }

    # Сохраняем результаты для последующего ИИ-анализа
    global RESULTS_CACHE
    RESULTS_CACHE = results_analysis

    logger.info(f"Parsing-анализ завершен")
    return results_analysis


@router.get("/status/{analysis_id}")
async def get_analysis_status(analysis_id: str) -> Dict[str, Any]:
    """
    Получает статус анализа по ID
    """
    return {"analysis_id": analysis_id, "status": "pending", "message": "Статус анализа будет реализован"}


@router.post("/ai-analyze")
async def ai_analyze_code(file: UploadFile = File(...)):
    """
    Анализирует файл с помощью ИИ
    """
    filename = file.filename
    logger.info(f"ИИ-анализ для файла: {filename}")

    code = RESULTS_CACHE[filename]['data']['file_content']

    if not code:
        logger.error(f"Код для файла {filename} не найден")
        return {"error": "Код не найден"}

    async with AIAnalyzer() as analyzer:
        result = await analyzer.analyze_code_text(code, filename=filename)
        if result:
            logger.info(f"ИИ-анализ файла {filename} завершен")
        else:
            logger.info(f"ИИ-анализ файла {filename} завершен с ошибкой")

    return {
        "filename": filename,
        "code_style": result.code_style,
        "solid_principles": result.solid_principles,
        "potential_issues": result.potential_issues,
        "recommendations": result.recommendations,
        "overall_score": result.overall_score,
    }
