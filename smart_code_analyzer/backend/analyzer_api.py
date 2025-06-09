#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------------------------------------------------
import logging
from dataclasses import asdict
from typing import Any, Dict, List

from code_analizer import FileBatchAnalyzer, HtmlFormatter, HtmlSummaryFormatter, LineProcessor
from fastapi import APIRouter, Body, File, UploadFile, Request, HTTPException
from fastapi.responses import JSONResponse

from smart_code_analyzer.backend.ai_analyzer import AIAnalyzer
from smart_code_analyzer.backend.models import (
    PackageAnalysisRequest,
    AnalysisResponse,
    AIAnalysisResponse,
    ErrorResponse
)

router = APIRouter(prefix="/analyzer", tags=["analyzer"])

# Настраиваем класс пакетного анализа списка файлов
batch_analyzer = FileBatchAnalyzer(LineProcessor)

# Настраиваем логирование
logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.DEBUG)


@router.post("/analyze", response_model=Dict[str, AnalysisResponse])
async def analyze_code(request: Request, files: List[UploadFile] = File(...)):
    """
    Анализирует загруженный файл с кодом
    """
    try:
        logger.info(f"Загружено файлов для parsing-анализа: {len(files)}")
        results_analysis = {}
        datas_list = await batch_analyzer.analyze_files(files)
        summary_data = batch_analyzer.get_summary()

        code_formatter = HtmlFormatter()
        summary_formatter = HtmlSummaryFormatter()

        for code_data in datas_list:
            formatted_html = code_formatter.format(code_data)
            results_analysis[code_data.filename] = AnalysisResponse(
                status="completed",
                data=asdict(code_data),
                html=formatted_html
            )

        # Добавляем summary_data в результаты
        results_analysis["summary"] = AnalysisResponse(
            status="completed",
            data=asdict(summary_data),
            html=summary_formatter.format(summary_data)
        )

        # Сохраняем результаты для последующего ИИ-анализа
        request.app.state.results_cache = results_analysis

        logger.info(f"Parsing-анализ завершен")
        return results_analysis
    except Exception as e:
        logger.error(f"Ошибка при анализе кода: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{analysis_id}", response_model=Dict[str, Any])
async def get_analysis_status(analysis_id: str) -> Dict[str, Any]:
    """
    Получает статус анализа по ID
    """
    return {"analysis_id": analysis_id, "status": "pending", "message": "Статус анализа будет реализован"}


@router.post("/ai-analyze", response_model=AIAnalysisResponse)
async def ai_analyze_code(request: Request, file: UploadFile = File(...)):
    """
    Анализирует файл с помощью ИИ
    """
    try:
        filename = file.filename
        logger.info(f"ИИ-анализ для файла: {filename}")

        results_cache = request.app.state.results_cache
        if not results_cache or filename not in results_cache:
            raise HTTPException(status_code=404, detail=f"Результаты анализа для файла {filename} не найдены")

        code = results_cache[filename].data['file_content']

        if not code:
            logger.error(f"Код для файла {filename} не найден")
            raise HTTPException(status_code=404, detail="Код не найден")

        async with AIAnalyzer() as analyzer:
            result = await analyzer.analyze_code_text(code, filename=filename)
            if not result:
                raise HTTPException(status_code=500, detail="Ошибка при ИИ-анализе")

            logger.info(f"ИИ-анализ файла {filename} завершен")
            return AIAnalysisResponse(
                filename=filename,
                code_style=result.code_style,
                solid_principles=result.solid_principles,
                potential_issues=result.potential_issues,
                recommendations=result.recommendations,
                overall_score=result.overall_score
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при ИИ-анализе: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai-analyze-package", response_model=Dict[str, Any])
async def ai_analyze_package(request: PackageAnalysisRequest):
    """
    ИИ-анализ структуры пакета (проекта)
    """
    try:
        files = [{"filename": f.filename, "content": f.content} for f in request.files]
        logger.info(f"ИИ-анализ структуры пакета {len(files)} файлов")
        
        async with AIAnalyzer() as analyzer:
            result = await analyzer.analyze_package_structure(files)
            if not result:
                raise HTTPException(status_code=500, detail="Ошибка при анализе структуры пакета")
            
            logger.info(f"ИИ-анализ структуры пакета завершен")
            return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при анализе пакета: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
