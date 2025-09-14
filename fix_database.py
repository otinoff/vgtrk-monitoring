#!/usr/bin/env python3
"""
Скрипт для исправления структуры базы данных
Добавляет недостающую колонку sitemap_url в таблицу filials
"""

import sqlite3
import os

def fix_database():
    """Добавляет колонку sitemap_url если её нет"""
    
    db_path = "data/vgtrk_monitoring.db"
    
    # Создаем папку data если её нет
    os.makedirs("data", exist_ok=True)
    
    # Подключаемся к базе данных
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Проверяем, есть ли колонка sitemap_url
        cursor.execute("PRAGMA table_info(filials)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'sitemap_url' not in column_names:
            print("🔧 Добавляем колонку sitemap_url...")
            cursor.execute("ALTER TABLE filials ADD COLUMN sitemap_url TEXT")
            conn.commit()
            print("✅ Колонка sitemap_url добавлена успешно!")
        else:
            print("✅ Колонка sitemap_url уже существует")
        
        # Проверяем структуру таблицы
        cursor.execute("PRAGMA table_info(filials)")
        columns = cursor.fetchall()
        
        print("\n📊 Текущая структура таблицы filials:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    fix_database()