#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Диагностика проблем Streamlit приложения
Проверка основных компонентов и зависимостей
"""

import sys
import os
import importlib
import sqlite3
from pathlib import Path

def check_python_version():
    """Проверка версии Python"""
    print("=== ПРОВЕРКА PYTHON ===")
    print(f"Версия Python: {sys.version}")
    print(f"Исполняемый файл: {sys.executable}")
    
    if sys.version_info < (3, 8):
        print("⚠️  ВНИМАНИЕ: Streamlit требует Python 3.8+")
    else:
        print("✅ Версия Python подходящая")
    return True

def check_dependencies():
    """Проверка установленных зависимостей"""
    print("\n=== ПРОВЕРКА ЗАВИСИМОСТЕЙ ===")
    
    required_packages = [
        'streamlit',
        'pandas', 
        'sqlite3',
        'st_aggrid',
        'requests',
        'pathlib'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'sqlite3':
                import sqlite3
                print(f"✅ {package}: встроенный модуль")
            elif package == 'pathlib':
                from pathlib import Path
                print(f"✅ {package}: встроенный модуль")
            else:
                module = importlib.import_module(package)
                if hasattr(module, '__version__'):
                    print(f"✅ {package}: {module.__version__}")
                else:
                    print(f"✅ {package}: установлен")
        except ImportError:
            print(f"❌ {package}: НЕ УСТАНОВЛЕН")
            missing_packages.append(package)
    
    return len(missing_packages) == 0

def check_database():
    """Проверка базы данных"""
    print("\n=== ПРОВЕРКА БАЗЫ ДАННЫХ ===")
    
    db_path = "data/vgtrk_monitoring.db"
    
    if not os.path.exists(db_path):
        print(f"❌ База данных не найдена: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Проверяем таблицы
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"✅ База данных найдена: {db_path}")
        print(f"Таблицы: {[table[0] for table in tables]}")
        
        # Проверяем основную таблицу
        cursor.execute("SELECT COUNT(*) FROM filials")
        count = cursor.fetchone()[0]
        print(f"Записей в таблице filials: {count}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при работе с БД: {e}")
        return False

def check_app_structure():
    """Проверка структуры приложения"""
    print("\n=== ПРОВЕРКА СТРУКТУРЫ ПРИЛОЖЕНИЯ ===")
    
    required_files = [
        "app.py",
        "data/vgtrk_monitoring.db",
        "modules/filials_table_editor.py",
        "modules/__init__.py"
    ]
    
    missing_files = []
    
    for file_path in required_files:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"✅ {file_path} ({size} байт)")
        else:
            print(f"❌ {file_path} - НЕ НАЙДЕН")
            missing_files.append(file_path)
    
    return len(missing_files) == 0

def check_streamlit_config():
    """Проверка конфигурации Streamlit"""
    print("\n=== ПРОВЕРКА КОНФИГУРАЦИИ STREAMLIT ===")
    
    # Проверяем файл конфигурации
    config_locations = [
        os.path.expanduser("~/.streamlit/config.toml"),
        ".streamlit/config.toml",
        "config.toml"
    ]
    
    config_found = False
    for config_path in config_locations:
        if os.path.exists(config_path):
            print(f"✅ Конфигурация найдена: {config_path}")
            config_found = True
            break
    
    if not config_found:
        print("ℹ️  Файл конфигурации не найден (используются настройки по умолчанию)")
    
    return True

def check_app_syntax():
    """Проверка синтаксиса основного файла приложения"""
    print("\n=== ПРОВЕРКА СИНТАКСИСА APP.PY ===")
    
    try:
        with open("app.py", 'r', encoding='utf-8') as f:
            code = f.read()
        
        compile(code, "app.py", "exec")
        print("✅ Синтаксис app.py корректен")
        return True
        
    except SyntaxError as e:
        print(f"❌ Синтаксическая ошибка в app.py: {e}")
        return False
    except Exception as e:
        print(f"❌ Ошибка при проверке app.py: {e}")
        return False

def generate_recommendations():
    """Генерация рекомендаций для решения проблем"""
    print("\n=== РЕКОМЕНДАЦИИ ПО УСТРАНЕНИЮ ПРОБЛЕМ ===")
    
    recommendations = [
        "1. Попробуйте запустить: streamlit run app.py --server.port 8501 --server.headless true",
        "2. Очистите кеш браузера (Ctrl+Shift+Delete)",
        "3. Проверьте другой браузер (Chrome, Firefox, Edge)",
        "4. Отключите блокировщики рекламы и расширения браузера",
        "5. Проверьте, не блокирует ли брандмауэр порт 8501",
        "6. Переустановите зависимости: pip install --upgrade streamlit st-aggrid",
        "7. Очистите кеш Streamlit: streamlit cache clear",
        "8. Перезапустите приложение полностью"
    ]
    
    for rec in recommendations:
        print(rec)

def main():
    """Основная функция диагностики"""
    print("ДИАГНОСТИКА STREAMLIT ПРИЛОЖЕНИЯ")
    print("=" * 50)
    
    all_checks = [
        check_python_version(),
        check_dependencies(),
        check_database(),
        check_app_structure(),
        check_streamlit_config(),
        check_app_syntax()
    ]
    
    print("\n=== ИТОГОВЫЙ ОТЧЕТ ===")
    passed_checks = sum(all_checks)
    total_checks = len(all_checks)
    
    print(f"Прошло проверок: {passed_checks}/{total_checks}")
    
    if passed_checks == total_checks:
        print("OK: Все проверки пройдены! Приложение должно работать корректно.")
    else:
        print("ERROR: Обнаружены проблемы. См. детали выше.")
    
    generate_recommendations()

if __name__ == "__main__":
    main()