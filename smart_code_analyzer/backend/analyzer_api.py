#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------------------------------------------------
from typing import Any, Dict, List

from fastapi import APIRouter, File, UploadFile

router = APIRouter(prefix="/analyzer", tags=["analyzer"])


@router.post("/analyze")
async def analyze_code(files: List[UploadFile] = File(...)):
    """
    Анализирует загруженный файл с кодом
    """
    results_analysis = {}
    for file in files:
        content = await file.read()
        code = content.decode()

        print(f"Анализируем файл: {code}")

        # TODO: Добавить интеграцию с code-analizer

        results_analysis[file.filename] = {"status": "pending", "message": "Анализ кода будет реализован"}
    return results_analysis


@router.get("/status/{analysis_id}")
async def get_analysis_status(analysis_id: str) -> Dict[str, Any]:
    """
    Получает статус анализа по ID
    """
    return {"analysis_id": analysis_id, "status": "pending", "message": "Статус анализа будет реализован"}
