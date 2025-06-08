#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------------------------------------------------
import asyncio
import os
from pathlib import Path
from smart_code_analyzer.backend.ai_analyzer import AIAnalyzer

async def test_ai_analyzer():
    # Получаем API ключ из переменной окружения
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Ошибка: Не найден OPENAI_API_KEY в переменных окружения")
        return

    # Создаем анализатор
    analyzer = AIAnalyzer(api_key)
    
    # Тестовый код для анализа
    test_code = """
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class UserData:
    name: str
    age: int
    email: str
    created_at: datetime

class UserRepository(ABC):
    @abstractmethod
    def save(self, user: UserData) -> None:
        pass
    
    @abstractmethod
    def get_by_id(self, user_id: int) -> Optional[UserData]:
        pass
    
    @abstractmethod
    def get_all(self) -> List[UserData]:
        pass

class DatabaseUserRepository(UserRepository):
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self._users: Dict[int, UserData] = {}
        self._next_id = 1
    
    def save(self, user: UserData) -> None:
        user_id = self._next_id
        self._users[user_id] = user
        self._next_id += 1
    
    def get_by_id(self, user_id: int) -> Optional[UserData]:
        return self._users.get(user_id)
    
    def get_all(self) -> List[UserData]:
        return list(self._users.values())
    """
    
    # Создаем временный файл
    test_file = Path("test_code.py")
    try:
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(test_code)
        
        print("Начинаем анализ кода...")
        
        # Анализируем файл
        result = await analyzer.analyze_file(test_file)
        
        # Выводим результаты
        print("\n=== Результаты анализа ===")
        print(f"Файл: {result.filename}")
        
        print("\n=== Анализ стиля кода ===")
        for key, value in result.code_style.items():
            print(f"{key}: {value}")
        
        print("\n=== SOLID принципы ===")
        for principle, status in result.solid_principles.items():
            print(f"{principle}: {status}")
        
        print("\n=== Потенциальные проблемы ===")
        for issue in result.potential_issues:
            print(f"\nТип: {issue.get('type', 'Не указан')}")
            print(f"Описание: {issue.get('description', 'Не указано')}")
            print(f"Строка: {issue.get('line', 'Не указана')}")
            print(f"Рекомендация: {issue.get('recommendation', 'Не указана')}")
        
        print("\n=== Рекомендации ===")
        for i, rec in enumerate(result.recommendations, 1):
            print(f"{i}. {rec}")
        
        print(f"\nОбщая оценка: {result.overall_score:.2f}")
        
    finally:
        # Удаляем временный файл
        if test_file.exists():
            os.remove(test_file)

if __name__ == "__main__":
    asyncio.run(test_ai_analyzer()) 