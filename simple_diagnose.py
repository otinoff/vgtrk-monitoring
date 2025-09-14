#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Простая диагностика Streamlit приложения
Без использования Unicode символов для совместимости с Windows
"""

import sys
import os
import importlib
import sqlite3

def main():
    print("=== ДИАГНОСТИКА STREAMLIT ПРИЛОЖЕНИЯ ===")
    
    # 1. Проверка Python
    print(f"\n1. Python версия: {sys.version}")
    if sys.version_info >= (3, 8):
        print("   [OK] Версия Python подходящая")
    else:
        print("   [ERROR] Требуется Python 3.8+")
    
    # 2. Проверка зависимостей
    print("\n2. Проверка зависимостей:")
    packages = ['streamlit', 'pandas', 'st_aggrid', 'requests']
    
    for package in packages:
        try:
            module = importlib.import_module(package)
            version = getattr(module, '__version__', 'unknown')
            print(f"   [OK] {package}: {version}")
        except ImportError:
            print(f"   [ERROR] {package}: НЕ УСТАНОВЛЕН")
    
    # 3. Проверка структуры файлов
    print("\n3. Проверка файлов:")
    files_to_check = [
        "app.py",
        "data/vgtrk_monitoring.db", 
        "modules/filials_table_editor.py"
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"   [OK] {file_path} ({size} байт)")
        else:
            print(f"   [ERROR] {file_path} - НЕ НАЙДЕН")
    
    # 4. Проверка базы данных
    print("\n4. Проверка базы данных:")
    try:
        conn = sqlite3.connect("data/vgtrk_monitoring.db")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM filials")
        count = cursor.fetchone()[0]
        print(f"   [OK] База данных работает, записей: {count}")
        conn.close()
    except Exception as e:
        print(f"   [ERROR] Проблема с БД: {e}")
    
    # 5. Рекомендации по устранению белого экрана
    print("\n=== ПРИЧИНЫ БЕЛОГО ЭКРАНА И РЕШЕНИЯ ===")
    
    solutions = [
        "1. ПРОБЛЕМА С ПОРТАМИ:",
        "   - Попробуйте другой порт: streamlit run app.py --server.port 8502",
        "   - Проверьте, свободен ли порт: netstat -an | findstr 8501",
        "",
        "2. ПРОБЛЕМА С БРАУЗЕРОМ:",
        "   - Очистите кеш браузера (Ctrl+Shift+R)",
        "   - Попробуйте режим инкогнито",
        "   - Попробуйте другой браузер (Chrome, Firefox, Edge)",
        "",
        "3. ПРОБЛЕМА С СЕТЬЮ:",
        "   - Отключите VPN и прокси",
        "   - Проверьте брандмауэр Windows",
        "   - Попробуйте локальный адрес: http://127.0.0.1:8501",
        "",
        "4. ПРОБЛЕМА С STREAMLIT:",
        "   - Переустановите: pip uninstall streamlit && pip install streamlit",
        "   - Очистите кеш: streamlit cache clear",
        "   - Обновите: pip install --upgrade streamlit",
        "",
        "5. ПРОБЛЕМА С КОДИРОВКОЙ:",
        "   - Установите переменную среды: set PYTHONIOENCODING=utf-8",
        "   - Запустите в CMD, а не PowerShell",
        "",
        "6. ПРОБЛЕМА С ЗАВИСИМОСТЯМИ:",
        "   - Переустановите st-aggrid: pip install --upgrade st-aggrid",
        "   - Проверьте версии: pip list | findstr streamlit",
        "",
        "7. РЕЖИМ ОТЛАДКИ:",
        "   - Запустите с отладкой: streamlit run app.py --logger.level debug",
        "   - Посмотрите логи в терминале"
    ]
    
    for solution in solutions:
        print(solution)
    
    print("\n=== КОМАНДЫ ДЛЯ БЫСТРОГО ИСПРАВЛЕНИЯ ===")
    print("pip install --upgrade streamlit st-aggrid pandas")
    print("streamlit cache clear")  
    print("streamlit run app.py --server.port 8502 --server.headless false")

if __name__ == "__main__":
    main()