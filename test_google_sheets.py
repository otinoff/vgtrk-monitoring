#!/usr/bin/env python3
"""
Тестовый скрипт для проверки подключения к Google Sheets и заполнения таблицы данными
"""

import sys
import os
import time

# Добавляем путь к модулям
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

from modules.google_sheets import GoogleSheetsManager

def test_google_sheets_connection():
    """Тест подключения к Google Sheets и заполнения таблицы"""
    
    print("🚀 Начало теста подключения к Google Sheets...")
    
    # Инициализация менеджера Google Sheets
    try:
        sheets_manager = GoogleSheetsManager("config/credentials.json")
        print("✅ Авторизация в Google Sheets успешна")
    except Exception as e:
        print(f"❌ Ошибка авторизации: {e}")
        return False
    
    # URL тестовой таблицы (замените на вашу таблицу)
    test_spreadsheet_url = "https://docs.google.com/spreadsheets/d/1am372lsoSiwOFNQwcCzXIWn1gXvad9ZZRLtElQOjXfg/edit?gid=319026814#gid=319026814"
    
    try:
        # Создание листа для результатов
        print("📝 Создание листа для результатов...")
        sheets_manager.create_results_sheet(test_spreadsheet_url)
        print("✅ Лист для результатов создан")
        
        # Запись тестовых данных
        print("📝 Запись тестовых данных...")
        test_data = [
            ("https://example.com", "Тестовый сайт 1", "Данные получены", "Это тестовый анализ для первого сайта"),
            ("https://test.com", "Тестовый сайт 2", "Данные получены", "Это тестовый анализ для второго сайта"),
            ("https://demo.com", "Тестовый сайт 3", "Ошибка обработки", "Не удалось получить контент сайта")
        ]
        
        for i, (url, theme, status, analysis) in enumerate(test_data, start=2):  # Начинаем с строки 2
            sheets_manager.write_analysis_result(test_spreadsheet_url, i, analysis, status)
            print(f"✅ Записаны данные для {url}")
            time.sleep(1)  # Небольшая задержка между запросами
        
        print("✅ Тестовые данные успешно записаны в таблицу")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при работе с таблицей: {e}")
        return False

def main():
    """Основная функция тестового скрипта"""
    print("=" * 50)
    print("Тест подключения к Google Sheets")
    print("=" * 50)
    
    success = test_google_sheets_connection()
    
    if success:
        print("\n🎉 Тест пройден успешно!")
        print("✅ Подключение к Google Sheets работает корректно")
        print("✅ Запись данных в таблицу возможна")
    else:
        print("\n❌ Тест не пройден!")
        print("⚠️  Проверьте настройки подключения и доступ к таблице")
    
    print("=" * 50)

if __name__ == "__main__":
    main()