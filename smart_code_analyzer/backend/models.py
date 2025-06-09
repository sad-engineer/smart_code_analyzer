#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------------------------------------------------
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class FileContent(BaseModel):
    """
    Модель для представления содержимого файла, отправляемого на анализ.

    Атрибуты:
        filename (str): Имя файла. Должно быть не менее 1 и не более 255 символов, поддерживаются только определённые
        расширения.
        content (str): Содержимое файла для анализа. Не может быть пустым.
        relative_path (Optional[str]): Относительный путь к файлу внутри архива/директории.
    """

    filename: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    relative_path: Optional[str] = Field(None, description="Относительный путь к файлу внутри архива/директории")

    @classmethod
    @field_validator('filename')
    def validate_filename(cls, v):
        if not v.endswith(('.py',)):
            raise ValueError('Неподдерживаемый тип файла')
        return v


class PackageAnalysisRequest(BaseModel):
    """
    Модель запроса для пакетного анализа нескольких файлов.

    Атрибуты:
        files (List[FileContent]): Список файлов для анализа. Должен содержать хотя бы один файл с уникальным именем.
    """

    files: List[FileContent] = Field(..., min_items=1)

    @classmethod
    @field_validator('files')
    def validate_unique_paths(cls, v):
        # Используем relative_path если есть, иначе filename
        paths = [getattr(f, 'relative_path', f.filename) for f in v]
        if len(paths) != len(set(paths)):
            raise ValueError('Пути файлов должны быть уникальными')
        return v


class AnalysisResponse(BaseModel):
    """
    Модель ответа для обычного анализа кода (не ИИ).

    Атрибуты:
        status (str): Статус анализа (completed, pending, error).
        data (dict): Результаты анализа в виде словаря.
        html (Optional[str]): HTML-представление результатов анализа (если есть).
    """

    status: str = Field(..., pattern='^(completed|pending|error)$')
    data: dict
    html: Optional[str] = None


class AIAnalysisResponse(BaseModel):
    """
    Модель ответа для ИИ-анализа кода.

    Атрибуты:
        filename (str): Имя анализируемого файла.
        code_style (dict): Оценка и рекомендации по стилю кода.
        solid_principles (dict): Оценка соответствия принципам SOLID.
        potential_issues (List[Dict[str, str]]): Список найденных потенциальных проблем с подробностями.
        recommendations (List[str]): Список рекомендаций по улучшению кода.
        overall_score (float): Общая оценка качества кода (от 0 до 100).
    """

    filename: str
    code_style: dict
    solid_principles: dict
    potential_issues: List[Dict[str, str]]
    recommendations: List[str]
    overall_score: float = Field(..., ge=0, le=100)


class ErrorResponse(BaseModel):
    """
    Модель для структурированного ответа с ошибкой.

    Атрибуты:
        error (str): Краткое описание ошибки.
        details (Optional[dict]): Дополнительные сведения об ошибке (если есть).
    """

    error: str
    details: Optional[dict] = None


class AIAnalysisResult(BaseModel):
    """
    Результат анализа кода с помощью ИИ (Pydantic-модель).

    Атрибуты:
        filename (str): Имя анализируемого файла.
        code_style (dict): Оценка и рекомендации по стилю кода.
        solid_principles (dict): Оценка соответствия принципам SOLID.
        potential_issues (List[Dict[str, str]]): Список найденных потенциальных проблем с подробностями.
        recommendations (List[str]): Список рекомендаций по улучшению кода.
        overall_score (float): Общая оценка качества кода (от 0 до 1).
    """

    filename: str
    code_style: Dict[str, str]
    solid_principles: Dict[str, str]
    potential_issues: List[Dict[str, str]]
    recommendations: List[str]
    overall_score: float = Field(..., ge=0.0, le=1.0)
