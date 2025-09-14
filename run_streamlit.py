#!/usr/bin/env python3
"""
Скрипт для запуска правильной версии Streamlit приложения
"""

import os
import sys
import subprocess

def main():
    """Определяет и запускает нужную версию приложения"""
    
    # Проверяем наличие файлов
    if os.path.exists("app_sqlite.py"):
        print("[INFO] Запускаем app_sqlite.py (версия с SQLite)")
        app_file = "app_sqlite.py"
    elif os.path.exists("app.py"):
        print("[INFO] Запускаем app.py (версия с Google Sheets)")
        app_file = "app.py"
    else:
        print("[ERROR] Не найден файл приложения!")
        sys.exit(1)
    
    # Запускаем Streamlit
    cmd = [sys.executable, "-m", "streamlit", "run", app_file]
    
    print(f"[CMD] {' '.join(cmd)}")
    subprocess.run(cmd)

if __name__ == "__main__":
    main()