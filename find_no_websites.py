#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Скрипт для поиска филиалов без сайтов
"""

import os
import sys
import sqlite3
from pathlib import Path

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def find_no_websites():
    """Поиск филиалов без сайтов"""
    
    # Путь к базе данных
    db_path = Path(__file__).parent / "data" / "vgtrk_monitoring.db"
    
    if not db_path.exists():
        print(f"[ERROR] База данных не найдена: {db_path}")
        return
    
    # Подключение к БД
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Получаем филиалы без сайтов
        cursor.execute("""
            SELECT id, name, region, federal_district
            FROM filials 
            WHERE website_url IS NULL OR website_url = ''
            ORDER BY name
        """)
        no_website = cursor.fetchall()
        
        print("=" * 80)
        print("ФИЛИАЛЫ БЕЗ САЙТОВ")
        print("=" * 80)
        
        if no_website:
            for idx, (filial_id, name, region, district) in enumerate(no_website, 1):
                print(f"\n{idx}. ID:{filial_id} - {name}")
                print(f"   Регион: {region}")
                print(f"   Округ: {district}")
                
                # Особые случаи
                if "Адыгея" in name:
                    print("   >>> ЕСТЬ САЙТ: adygtv.ru")
                elif "Кузбасс" in name:
                    print("   >>> ЕСТЬ САЙТ: vesti42.ru (основной), kuzbassmayak.ru (дополнительный)")
                elif "Донецк" in name:
                    print("   >>> Telegram канал: https://t.me/VESTIDONETSK")
                elif "Луганск" in name:
                    print("   >>> ЕСТЬ САЙТ: gtrklnr.ru")
            
            print(f"\n\nВСЕГО БЕЗ САЙТОВ: {len(no_website)} филиалов")
        else:
            print("\nВсе филиалы имеют сайты!")
        
    except Exception as e:
        print(f"[ERROR] Ошибка поиска: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    find_no_websites()