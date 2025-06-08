#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------------------------------------------------
import asyncio
import os
from pathlib import Path

from smart_code_analyzer.backend.ai_analyzer import AIAnalyzer


async def demonstrate_analyzer():
    """Демонстрация работы анализатора кода"""
    print("Начинаем анализ кода...")

    # Проверяем наличие API ключей
    api_key = os.getenv("OPENAI_API_KEY")
    proxy_api_key = os.getenv("PROXYAPI_KEY")

    if not api_key:
        raise ValueError("OPENAI_API_KEY не найден. Укажите его в .env файле.")
    if not proxy_api_key:
        raise ValueError("PROXYAPI_KEY не найден. Укажите его в .env файле.")

    # Показываем доступные модели
    print("\nДоступные модели:")
    for model, description in AIAnalyzer.AVAILABLE_MODELS.items():
        print(f"- {model}: {description}")

    # Тестовый код для анализа
    test_code = """
    from dataclasses import dataclass
    from typing import List, Optional
    
    @dataclass
    class User:
        id: int
        name: str
        email: str
        is_active: bool = True
        
        def get_full_info(self) -> str:
            return f"{self.name} ({self.email})"
    
    class UserRepository:
        def __init__(self):
            self.users: List[User] = []
            
        def add_user(self, user: User) -> None:
            self.users.append(user)
            
        def get_user_by_id(self, user_id: int) -> Optional[User]:
            return next((u for u in self.users if u.id == user_id), None)
            
        def get_active_users(self) -> List[User]:
            return [u for u in self.users if u.is_active]
    
    class UserService:
        def __init__(self, repository: UserRepository):
            self.repository = repository
            
        def create_user(self, name: str, email: str) -> User:
            user_id = len(self.repository.users) + 1
            user = User(id=user_id, name=name, email=email)
            self.repository.add_user(user)
            return user
            
        def get_user_info(self, user_id: int) -> Optional[str]:
            user = self.repository.get_user_by_id(user_id)
            return user.get_full_info() if user else None
    """

    # Создаем временный файл с тестовым кодом
    test_file = Path("test_code.py")
    try:
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(test_code)

        # Используем контекстный менеджер для анализатора
        async with AIAnalyzer(api_key=api_key) as analyzer:
            print(f"\nИспользуем модель: {analyzer.model}")

            # Запускаем анализ
            result = await analyzer.analyze_file(test_file)

            # Выводим результаты
            print("\nРезультаты анализа:")
            print(f"Файл: {result.filename}")

            print("\nАнализ стиля кода:")
            for aspect, status in result.code_style.items():
                print(f"- {aspect}: {status}")

            print("\nСоответствие SOLID принципам:")
            for principle, status in result.solid_principles.items():
                print(f"- {principle}: {status}")

            print("\nПотенциальные проблемы:")
            for issue in result.potential_issues:
                print(f"- {issue['type']}: {issue['description']}")
                print(f"  Рекомендация: {issue['recommendation']}")

            print("\nРекомендации по улучшению:")
            for rec in result.recommendations:
                print(f"- {rec}")

            print(f"\nОбщая оценка качества кода: {result.overall_score:.2f}")

    finally:
        # Удаляем временный файл
        if test_file.exists():
            test_file.unlink()


if __name__ == "__main__":
    asyncio.run(demonstrate_analyzer())
