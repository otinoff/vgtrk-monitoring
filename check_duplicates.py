#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import pandas as pd

def check_database():
    """Проверка базы данных на дубликаты и анализ"""
    
    conn = sqlite3.connect('data/vgtrk_monitoring.db')
    
    # Основная статистика
    df = pd.read_sql_query('SELECT * FROM filials', conn)
    print("=== СТАТИСТИКА БАЗЫ ДАННЫХ ===")
    print(f"Всего записей: {len(df)}")
    print(f"Максимальный ID: {df['id'].max()}")
    print(f"Минимальный ID: {df['id'].min()}")
    
    # Поиск дубликатов по названию
    duplicates_by_name = df.groupby('name').size()
    duplicates_name = duplicates_by_name[duplicates_by_name > 1]
    
    print(f"\n=== ДУБЛИКАТЫ ПО НАЗВАНИЮ ===")
    print(f"Найдено дубликатов: {len(duplicates_name)}")
    if len(duplicates_name) > 0:
        for name, count in duplicates_name.items():
            print(f"  '{name}': {count} раз")
    
    # Поиск дубликатов по названию + региону
    duplicates_by_name_region = df.groupby(['name', 'region']).size()
    duplicates_name_region = duplicates_by_name_region[duplicates_by_name_region > 1]
    
    print(f"\n=== ПОЛНЫЕ ДУБЛИКАТЫ (название + регион) ===")
    print(f"Найдено полных дубликатов: {len(duplicates_name_region)}")
    if len(duplicates_name_region) > 0:
        for (name, region), count in duplicates_name_region.items():
            print(f"  '{name}' ({region}): {count} раз")
    
    # Последние записи
    print(f"\n=== ПОСЛЕДНИЕ 10 ЗАПИСЕЙ ===")
    last_records = df.nlargest(10, 'id')[['id', 'name', 'region']]
    for _, row in last_records.iterrows():
        print(f"ID {row['id']}: {row['name']} ({row['region']})")
    
    # Записи с высокими ID
    high_id_records = df[df['id'] > 85]
    print(f"\n=== ЗАПИСИ С ID > 85 ===")
    print(f"Найдено записей: {len(high_id_records)}")
    for _, row in high_id_records.iterrows():
        print(f"ID {row['id']}: {row['name']} ({row['region']})")
    
    conn.close()
    
    return len(duplicates_name), len(duplicates_name_region)

if __name__ == "__main__":
    check_database()