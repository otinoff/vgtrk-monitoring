#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Скрипт для проверки названий филиалов в БД
"""

import os
import sys
import sqlite3
from pathlib import Path

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_names():
    """Проверка названий филиалов в БД"""
    
    # Путь к базе данных
    db_path = Path(__file__).parent / "data" / "vgtrk_monitoring.db"
    
    if not db_path.exists():
        print(f"[ERROR] База данных не найдена: {db_path}")
        return
    
    # Подключение к БД
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Получаем все названия из БД
        cursor.execute("SELECT id, name, region FROM filials ORDER BY name")
        filials = cursor.fetchall()
        
        print("=" * 60)
        print("Филиалы в базе данных:")
        print("=" * 60)
        
        for filial in filials:
            print(f"ID: {filial[0]:3} | Название: {filial[1]:40} | Регион: {filial[2]}")
        
        print(f"\nВсего филиалов: {len(filials)}")
        
    except Exception as e:
        print(f"[ERROR] Ошибка чтения БД: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_names()