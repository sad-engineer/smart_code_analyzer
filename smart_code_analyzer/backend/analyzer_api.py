#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------------------------------------------------
from dataclasses import asdict
from typing import Any, Dict, List

from code_analizer import FileBatchAnalyzer, HtmlFormatter, HtmlSummaryFormatter, LineProcessor
from fastapi import APIRouter, File, UploadFile, Form
from smart_code_analyzer.backend.ai_analyzer import AIAnalyzer, AIAnalysisResult

router = APIRouter(prefix="/analyzer", tags=["analyzer"])

batch_analyzer = FileBatchAnalyzer(LineProcessor)


@router.post("/analyze")
async def analyze_code(files: List[UploadFile] = File(...)):
    """
    Анализирует загруженный файл с кодом
    """
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
    import tempfile
    from pathlib import Path

    # Сохраняем файл во временную папку
    with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as tmp:
        tmp.write(await file.read())
        tmp_path = Path(tmp.name)

    async with AIAnalyzer() as analyzer:
        result: AIAnalysisResult = await analyzer.analyze_file(tmp_path)

    # Удаляем временный файл
    tmp_path.unlink(missing_ok=True)

    return {
        "filename": result.filename,
        "code_style": result.code_style,
        "solid_principles": result.solid_principles,
        "potential_issues": result.potential_issues,
        "recommendations": result.recommendations,
        "overall_score": result.overall_score,
    }
