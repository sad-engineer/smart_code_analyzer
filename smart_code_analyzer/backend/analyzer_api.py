#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------------------------------------------------
from typing import Any, Dict, List
from dataclasses import asdict

from fastapi import APIRouter, File, UploadFile

router = APIRouter(prefix="/analyzer", tags=["analyzer"])

from code_analizer.core.code_text_analyzer import CodeTextAnalyzer
from code_analizer.core.file_batch_analyzer import FileBatchAnalyzer
from code_analizer.core.line_processor import LineProcessor

batch_analyzer = FileBatchAnalyzer(LineProcessor)


@router.post("/analyze")
async def analyze_code(files: List[UploadFile] = File(...)):
    """
    Анализирует загруженный файл с кодом
    """
    results_analysis = {}
    datas_list = await batch_analyzer.analyze_files(files)
    #datas_list =  <coroutine object FileBatchAnalyzer.analyze_files at 0x0000018455DE18C0>

    print(datas_list)
    for code_data in datas_list:
        results_analysis[code_data.filename] = {
            "status": "pending",
            "data": asdict(code_data),
        }
    print(results_analysis)
    return results_analysis



@router.get("/status/{analysis_id}")
async def get_analysis_status(analysis_id: str) -> Dict[str, Any]:
    """
    Получает статус анализа по ID
    """
    return {"analysis_id": analysis_id, "status": "pending", "message": "Статус анализа будет реализован"}
