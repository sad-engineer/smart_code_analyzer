#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------------------------------------------------
from dataclasses import dataclass
from typing import Dict, List, Optional
from openai import AsyncOpenAI
from pathlib import Path
import os
from dotenv import load_dotenv
import httpx
import logging

# Настраиваем логирование
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Загружаем переменные окружения из .env файла
load_dotenv()


def get_proxy_url(proxy_type: str = "http") -> Optional[str]:
    """
    Формирует URL прокси для proxyapi.ru
    
    Args:
        proxy_type: Тип прокси ("http" или "socks5")
        
    Returns:
        URL прокси с аутентификацией или None, если не удалось получить настройки
    """
    proxy_api_key = os.getenv("PROXYAPI_KEY")
    if not proxy_api_key:
        logger.warning("PROXYAPI_KEY не найден в .env файле")
        return None
        
    # Формируем URL прокси в зависимости от типа
    if proxy_type == "socks5":
        proxy_url = "socks5://api.proxyapi.ru:1080"
    else:
        proxy_url = "http://api.proxyapi.ru:3128"
        
    # Добавляем аутентификацию
    return f"{proxy_url}?key={proxy_api_key}"


@dataclass
class AIAnalysisResult:
    """Результат анализа кода с помощью ИИ"""
    filename: str
    code_style: Dict[str, str]  # Анализ стиля кода
    solid_principles: Dict[str, str]  # Соответствие принципам SOLID
    potential_issues: List[Dict[str, str]]  # Потенциальные проблемы
    recommendations: List[str]  # Рекомендации по улучшению
    overall_score: float  # Общая оценка качества кода


class AIAnalyzer:
    """Класс для анализа кода с помощью ИИ"""
    
    # Доступные модели
    AVAILABLE_MODELS = {
        "gpt-4.1": "GPT-4.1 (самая мощная модель, 1M контекст)",
        "gpt-4.1-mini": "GPT-4.1 Mini (быстрая версия с высокими лимитами)",
        "codex-mini-latest": "Codex Mini (специализированная модель для кода)",
        "gpt-4o": "GPT-4o (базовая модель, 128K контекст)",
        "gpt-4o-mini": "GPT-4o Mini (быстрая базовая модель)"
    }
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Инициализация анализатора
        
        Args:
            api_key: API ключ для OpenAI (если не указан, берется из .env)
            model: Модель для анализа (если не указана, берется из .env или используется gpt-4.1)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("API ключ не найден. Укажите его в .env файле или передайте в конструктор.")
        
        # Получаем модель из параметра или .env
        self.model = model or os.getenv("AI_MODEL", "gpt-4.1")
        
        # Проверяем корректность модели
        if self.model not in self.AVAILABLE_MODELS:
            raise ValueError(f"Неподдерживаемая модель. Доступные модели: {', '.join(self.AVAILABLE_MODELS.keys())}")
        
        # Получаем ключ ProxyAPI
        proxy_api_key = os.getenv("PROXYAPI_KEY")
        if not proxy_api_key:
            raise ValueError("PROXYAPI_KEY не найден. Укажите его в .env файле.")
        
        # Настройка HTTP клиента
        transport = httpx.AsyncHTTPTransport(
            verify=False,  # Отключаем проверку SSL
            retries=3  # Количество попыток переподключения
        )
        
        self.http_client = httpx.AsyncClient(
            transport=transport,
            timeout=60.0,  # Увеличиваем таймаут
            follow_redirects=True  # Разрешаем следовать по редиректам
        )
        
        self.client = AsyncOpenAI(
            api_key=proxy_api_key,  # Используем ключ ProxyAPI
            http_client=self.http_client,
            base_url="https://api.proxyapi.ru/openai/v1"  # Используем базовый URL ProxyAPI
        )
    
    async def close(self):
        """Закрытие HTTP клиента"""
        await self.http_client.aclose()
    
    async def __aenter__(self):
        """Поддержка контекстного менеджера"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Закрытие при выходе из контекстного менеджера"""
        await self.close()
    
    async def analyze_file(self, file_path: Path) -> AIAnalysisResult:
        """
        Анализ одного файла
        
        Args:
            file_path: Путь к файлу для анализа
            
        Returns:
            AIAnalysisResult: Результат анализа
            
        Raises:
            FileNotFoundError: Если файл не найден
            ValueError: Если файл пустой или не является Python файлом
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Файл {file_path} не найден")
            
        if file_path.suffix != '.py':
            raise ValueError("Поддерживаются только Python файлы")
            
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read().strip()
            
        if not code:
            raise ValueError("Файл пуст")
            
        try:
            # Анализ стиля кода
            style_analysis = await self._analyze_code_style(code)
            
            # Проверка SOLID принципов
            solid_analysis = await self._check_solid_principles(code)
            
            # Поиск потенциальных проблем
            issues = await self._find_potential_issues(code)
            
            # Генерация рекомендаций
            recommendations = await self._generate_recommendations(code)
            
            # Расчет общей оценки
            overall_score = self._calculate_overall_score(style_analysis, solid_analysis, issues)
            
            return AIAnalysisResult(
                filename=file_path.name,
                code_style=style_analysis,
                solid_principles=solid_analysis,
                potential_issues=issues,
                recommendations=recommendations,
                overall_score=overall_score
            )
        except Exception as e:
            raise RuntimeError(f"Ошибка при анализе файла {file_path}: {str(e)}")
    
    async def _analyze_code_style(self, code: str) -> Dict[str, str]:
        """Анализ стиля кода"""
        prompt = f"""
        Проанализируй стиль следующего кода и дай рекомендации по улучшению.
        Ответ должен быть в формате JSON:
        {{
            "formatting": "оценка и рекомендации",
            "naming": "оценка и рекомендации",
            "documentation": "оценка и рекомендации",
            "structure": "оценка и рекомендации"
        }}

        Код для анализа:
        {code}
        """
        
        response = await self._get_ai_response(prompt)
        return self._parse_style_analysis(response)
    
    async def _check_solid_principles(self, code: str) -> Dict[str, str]:
        """Проверка соответствия принципам SOLID"""
        prompt = f"""
        Проверь соответствие следующего кода принципам SOLID.
        Ответ должен быть в формате JSON:
        {{
            "SRP": "оценка и объяснение",
            "OCP": "оценка и объяснение",
            "LSP": "оценка и объяснение",
            "ISP": "оценка и объяснение",
            "DIP": "оценка и объяснение"
        }}

        Код для анализа:
        {code}
        """
        
        response = await self._get_ai_response(prompt)
        return self._parse_solid_analysis(response)
    
    async def _find_potential_issues(self, code: str) -> List[Dict[str, str]]:
        """Поиск потенциальных проблем в коде"""
        prompt = f"""
        Найди потенциальные проблемы в следующем коде.
        Ответ должен быть в формате JSON массив объектов:
        [
            {{
                "type": "тип проблемы",
                "description": "описание проблемы",
                "line": "строка кода",
                "recommendation": "рекомендация по исправлению"
            }}
        ]

        Код для анализа:
        {code}
        """
        
        response = await self._get_ai_response(prompt)
        return self._parse_issues(response)
    
    async def _generate_recommendations(self, code: str) -> List[str]:
        """Генерация рекомендаций по улучшению кода"""
        prompt = f"""
        Дай рекомендации по улучшению следующего кода.
        Ответ должен быть в формате JSON массив строк:
        [
            "рекомендация 1",
            "рекомендация 2",
            ...
        ]

        Код для анализа:
        {code}
        """
        
        response = await self._get_ai_response(prompt)
        return self._parse_recommendations(response)
    
    async def _get_ai_response(self, prompt: str) -> str:
        """Получение ответа от ИИ"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,  # Используем выбранную модель
                messages=[
                    {"role": "system", "content": "Ты - эксперт по анализу кода. Твоя задача - анализировать код и давать конкретные рекомендации. Всегда отвечай в формате JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"Ошибка при получении ответа от ИИ: {str(e)}")
    
    def _parse_style_analysis(self, response: str) -> Dict[str, str]:
        """Парсинг анализа стиля кода"""
        try:
            import json
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                "formatting": "Ошибка парсинга ответа",
                "naming": "Ошибка парсинга ответа",
                "documentation": "Ошибка парсинга ответа",
                "structure": "Ошибка парсинга ответа"
            }
    
    def _parse_solid_analysis(self, response: str) -> Dict[str, str]:
        """Парсинг анализа SOLID принципов"""
        try:
            import json
            # Очищаем ответ от возможных лишних символов
            cleaned_response = response.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()
            
            result = json.loads(cleaned_response)
            
            # Проверяем наличие всех необходимых ключей
            required_keys = ["SRP", "OCP", "LSP", "ISP", "DIP"]
            for key in required_keys:
                if key not in result:
                    result[key] = "Ошибка: отсутствует в ответе"
            
            return result
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга SOLID анализа: {str(e)}")
            logger.error(f"Ответ модели: {response}")
            return {
                "SRP": "Ошибка парсинга ответа",
                "OCP": "Ошибка парсинга ответа",
                "LSP": "Ошибка парсинга ответа",
                "ISP": "Ошибка парсинга ответа",
                "DIP": "Ошибка парсинга ответа"
            }
    
    def _parse_issues(self, response: str) -> List[Dict[str, str]]:
        """Парсинг найденных проблем"""
        try:
            import json
            # Очищаем ответ от возможных лишних символов
            cleaned_response = response.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()
            
            issues = json.loads(cleaned_response)
            
            # Проверяем структуру каждой проблемы
            valid_issues = []
            for issue in issues:
                if isinstance(issue, dict):
                    # Добавляем отсутствующие поля с дефолтными значениями
                    valid_issue = {
                        "type": issue.get("type", "Неизвестная проблема"),
                        "description": issue.get("description", "Нет описания"),
                        "line": issue.get("line", "Не указана"),
                        "recommendation": issue.get("recommendation", "Нет рекомендации")
                    }
                    valid_issues.append(valid_issue)
            
            return valid_issues
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга проблем: {str(e)}")
            logger.error(f"Ответ модели: {response}")
            return [{
                "type": "Ошибка парсинга",
                "description": "Не удалось разобрать ответ ИИ",
                "line": "Неизвестно",
                "recommendation": "Проверьте формат ответа модели"
            }]
    
    def _parse_recommendations(self, response: str) -> List[str]:
        """Парсинг рекомендаций"""
        try:
            import json
            # Очищаем ответ от возможных лишних символов
            cleaned_response = response.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()
            
            recommendations = json.loads(cleaned_response)
            
            # Проверяем, что это список строк
            if isinstance(recommendations, list):
                return [str(rec) for rec in recommendations if rec]
            else:
                logger.error(f"Неверный формат рекомендаций: {recommendations}")
                return ["Ошибка: рекомендации должны быть списком строк"]
                
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга рекомендаций: {str(e)}")
            logger.error(f"Ответ модели: {response}")
            return ["Ошибка парсинга ответа"]
    
    def _calculate_overall_score(self, style_analysis: Dict[str, str], 
                               solid_analysis: Dict[str, str], 
                               issues: List[Dict[str, str]]) -> float:
        """Расчет общей оценки качества кода"""
        # Базовая оценка
        score = 1.0
        
        # Штраф за проблемы
        score -= len(issues) * 0.1
        
        # Проверка SOLID принципов
        for principle, status in solid_analysis.items():
            if "не соответствует" in status.lower():
                score -= 0.1
        
        # Проверка стиля кода
        for aspect, status in style_analysis.items():
            if "плохо" in status.lower() or "отсутствует" in status.lower():
                score -= 0.05
        
        # Ограничиваем оценку от 0 до 1
        return max(0.0, min(1.0, score))