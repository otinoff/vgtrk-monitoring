#!/usr/bin/env python3
"""
Простой тестовый скрипт для проверки подключения к Google Sheets
"""

import sys
import os

# Добавляем путь к модулям
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

from modules.google_sheets import GoogleSheetsManager

def test_connection():
    """Тест подключения к Google Sheets"""
    
    print("🚀 Тест подключения к Google Sheets...")
    
    try:
        # Инициализация менеджера Google Sheets
        sheets_manager = GoogleSheetsManager("config/credentials.json")
        print("✅ Авторизация в Google Sheets успешна")
        
        # URL таблицы
        spreadsheet_url = "https://docs.google.com/spreadsheets/d/1am372lsoSiwOFNQwcCzXIWn1gXvad9ZZRLtElQOjXfg/edit?gid=319026814#gid=319026814"
        
        # Попытка чтения данных
        print("📝 Попытка чтения данных из таблицы...")
        sites_data = sheets_manager.read_sites_sheet(spreadsheet_url, 1, 5)
        
        print(f"✅ Успешно прочитано {len(sites_data)} строк из таблицы")
        
        # Показываем данные
        print("\n📋 Данные из таблицы:")
        for i, site in enumerate(sites_data, start=1):
            print(f"  {i}. {site['url']} - {site['theme']}")
            
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_connection()
    
    if success:
        print("\n🎉 Тест пройден успешно!")
    else:
        print("\n❌ Тест не пройден!")