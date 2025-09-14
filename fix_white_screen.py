#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Автоматическое исправление проблем белого экрана в Streamlit
"""

import os
import sys
import subprocess
import time

def run_command(command, description):
    """Выполнение команды с описанием"""
    print(f"Выполняется: {description}")
    print(f"Команда: {command}")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, encoding='utf-8')
        if result.returncode == 0:
            print(f"   [OK] {description}")
            if result.stdout:
                print(f"   Вывод: {result.stdout.strip()}")
        else:
            print(f"   [ERROR] {description}")
            if result.stderr:
                print(f"   Ошибка: {result.stderr.strip()}")
        return result.returncode == 0
    except Exception as e:
        print(f"   [ERROR] Ошибка выполнения: {e}")
        return False

def fix_streamlit_issues():
    """Исправление типичных проблем Streamlit"""
    print("=== АВТОМАТИЧЕСКОЕ ИСПРАВЛЕНИЕ ПРОБЛЕМ STREAMLIT ===\n")
    
    fixes = [
        ("pip install --upgrade streamlit", "Обновление Streamlit"),
        ("pip install --upgrade st-aggrid", "Обновление st-aggrid"), 
        ("pip install --upgrade pandas", "Обновление pandas"),
        ("streamlit cache clear", "Очистка кеша Streamlit"),
    ]
    
    successful_fixes = 0
    
    for command, description in fixes:
        if run_command(command, description):
            successful_fixes += 1
        print()
        time.sleep(1)
    
    print(f"Выполнено исправлений: {successful_fixes}/{len(fixes)}")
    
    # Дополнительные рекомендации
    print("\n=== ДОПОЛНИТЕЛЬНЫЕ РЕКОМЕНДАЦИИ ===")
    
    recommendations = [
        "1. Перезапустите приложение на другом порту:",
        "   streamlit run app.py --server.port 8502",
        "",
        "2. Если проблема в браузере:",
        "   - Откройте режим инкогнито",
        "   - Очистите кеш (Ctrl+Shift+Delete)",
        "   - Попробуйте другой браузер",
        "",
        "3. Проверьте локальный адрес:",
        "   - Откройте: http://127.0.0.1:8501",
        "   - Или: http://localhost:8501",
        "",
        "4. Если используете корпоративную сеть:",
        "   - Отключите прокси/VPN",
        "   - Проверьте настройки брандмауэра",
        "",
        "5. Запуск с отладкой:",
        "   streamlit run app.py --logger.level debug",
        "   (посмотрите ошибки в консоли)"
    ]
    
    for rec in recommendations:
        print(rec)

def create_startup_script():
    """Создание скрипта для стабильного запуска"""
    print("\n=== СОЗДАНИЕ СКРИПТА ЗАПУСКА ===")
    
    startup_script = """@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8

echo Запуск Streamlit приложения...
echo Откройте браузер: http://localhost:8502

streamlit run app.py --server.port 8502 --server.headless false --browser.gatherUsageStats false --server.address localhost

pause
"""
    
    try:
        with open("start_app.bat", "w", encoding="utf-8-sig") as f:
            f.write(startup_script)
        print("[OK] Создан файл start_app.bat")
        print("     Для запуска приложения дважды кликните по start_app.bat")
    except Exception as e:
        print(f"[ERROR] Не удалось создать start_app.bat: {e}")

def main():
    print("ИНСТРУМЕНТ ИСПРАВЛЕНИЯ БЕЛОГО ЭКРАНА STREAMLIT")
    print("=" * 50)
    
    # Проверяем, что мы в правильной директории
    if not os.path.exists("app.py"):
        print("ERROR: app.py не найден в текущей директории!")
        print("Запустите этот скрипт из папки parsing_vesti42")
        return
    
    # Выполняем исправления
    fix_streamlit_issues()
    
    # Создаем скрипт запуска
    create_startup_script()
    
    print("\n=== ГОТОВО ===")
    print("Попробуйте запустить приложение:")
    print("1. Через start_app.bat (двойной клик)")
    print("2. Или командой: streamlit run app.py --server.port 8502")

if __name__ == "__main__":
    main()