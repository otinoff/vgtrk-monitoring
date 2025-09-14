#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Автоматическое исправление HTTP2_PROTOCOL_ERROR в Streamlit
Создание безопасной конфигурации и запуск приложения
"""

import os
import subprocess
import sys

def create_safe_config():
    """Создание безопасной конфигурации Streamlit"""
    print("Создание безопасной конфигурации Streamlit...")
    
    # Создаем директорию конфигурации
    config_dir = ".streamlit"
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
        print(f"   Создана директория: {config_dir}")
    
    # Конфигурация для решения HTTP2 проблем
    config_content = """[server]
enableCORS = false
enableXsrfProtection = false
enableWebsocketCompression = false
port = 8502
headless = false
address = "localhost"

[browser]
gatherUsageStats = false
serverAddress = "localhost"

[global]
suppressDeprecationWarnings = true
developmentMode = false

[client]
showErrorDetails = false
"""
    
    config_path = os.path.join(config_dir, "config.toml")
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(config_content)
        print(f"   ✅ Создан файл: {config_path}")
        return True
    except Exception as e:
        print(f"   ❌ Ошибка создания конфигурации: {e}")
        return False

def create_startup_script():
    """Создание bat-файла для быстрого запуска"""
    print("Создание скрипта быстрого запуска...")
    
    bat_content = """@echo off
chcp 65001 >nul
title Streamlit App - HTTP2 Fixed
cls

echo ========================================
echo   STREAMLIT APP - HTTP2 ИСПРАВЛЕНО
echo ========================================
echo.
echo Приложение запускается с исправлениями для:
echo - HTTP2_PROTOCOL_ERROR
echo - Конфликты с расширениями браузера
echo - Проблемы с криптокошельками
echo.
echo Откроется в браузере: http://localhost:8502
echo.
echo Если не работает:
echo 1. Используйте режим инкогнито (Ctrl+Shift+N)
echo 2. Отключите расширения браузера
echo 3. Попробуйте другой браузер
echo.
echo ========================================

set PYTHONIOENCODING=utf-8
set PYTHONLEGACYWINDOWSSTDIO=utf-8

streamlit run app.py --server.port 8502 --server.headless false --browser.gatherUsageStats false --server.enableCORS false --server.enableXsrfProtection false

echo.
echo Приложение завершено. Нажмите любую клавишу для выхода.
pause >nul
"""
    
    try:
        with open("start_app_http2_fix.bat", "w", encoding="utf-8-sig") as f:
            f.write(bat_content)
        print("   ✅ Создан файл: start_app_http2_fix.bat")
        return True
    except Exception as e:
        print(f"   ❌ Ошибка создания bat-файла: {e}")
        return False

def check_dependencies():
    """Проверка наличия необходимых зависимостей"""
    print("Проверка зависимостей...")
    
    try:
        import streamlit
        print(f"   ✅ Streamlit: {streamlit.__version__}")
    except ImportError:
        print("   ❌ Streamlit не установлен")
        return False
    
    if not os.path.exists("app.py"):
        print("   ❌ Файл app.py не найден")
        return False
    else:
        print("   ✅ Файл app.py найден")
    
    return True

def start_streamlit_safe():
    """Запуск Streamlit с безопасными настройками"""
    print("Запуск Streamlit с исправлениями HTTP2...")
    print("🌐 Приложение откроется: http://localhost:8502")
    print("💡 Если белый экран - используйте режим инкогнито!")
    print("")
    
    try:
        # Команда запуска с безопасными настройками
        cmd = [
            "streamlit", "run", "app.py",
            "--server.port", "8502",
            "--server.headless", "false", 
            "--browser.gatherUsageStats", "false",
            "--server.enableCORS", "false",
            "--server.enableXsrfProtection", "false",
            "--server.address", "localhost"
        ]
        
        print("Выполняемая команда:")
        print(" ".join(cmd))
        print("=" * 50)
        
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Приложение остановлено пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка запуска: {e}")
        print("\n🔧 Попробуйте:")
        print("1. pip install --upgrade streamlit")
        print("2. Запустите start_app_http2_fix.bat")
        print("3. Используйте режим инкогнито в браузере")

def main():
    """Основная функция"""
    print("=" * 60)
    print("🛠️  ИСПРАВЛЕНИЕ HTTP2_PROTOCOL_ERROR В STREAMLIT")
    print("=" * 60)
    print()
    
    # Проверяем, что мы в правильной директории
    if not os.path.exists("app.py"):
        print("❌ ОШИБКА: app.py не найден в текущей директории!")
        print("Запустите этот скрипт из папки parsing_vesti42")
        input("Нажмите Enter для выхода...")
        return
    
    # Проверяем зависимости
    if not check_dependencies():
        print("❌ Не все зависимости установлены!")
        input("Нажмите Enter для выхода...")
        return
    
    # Создаем безопасную конфигурацию
    config_created = create_safe_config()
    
    # Создаем скрипт запуска
    script_created = create_startup_script()
    
    print()
    if config_created and script_created:
        print("✅ Все исправления применены!")
        print()
        print("🚀 СПОСОБЫ ЗАПУСКА:")
        print("1. Автоматический: дважды кликните start_app_http2_fix.bat")
        print("2. Через этот скрипт: продолжите выполнение")
        print("3. Вручную: streamlit run app.py --server.port 8502")
        print()
        
        choice = input("Запустить приложение сейчас? (y/n): ").strip().lower()
        if choice in ['y', 'yes', 'да', 'д', '']:
            print()
            start_streamlit_safe()
        else:
            print("\n✅ Исправления готовы! Используйте start_app_http2_fix.bat для запуска")
    else:
        print("⚠️  Не все исправления удалось применить")
        print("Попробуйте запустить вручную:")
        print("streamlit run app.py --server.port 8502 --server.enableCORS false")

if __name__ == "__main__":
    main()