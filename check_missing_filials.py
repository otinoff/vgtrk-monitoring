#!/usr/bin/env python3
"""
Скрипт для проверки отсутствующих филиалов в базе данных
"""

import sys
import os
import pandas as pd
import sqlite3
from pathlib import Path

# Добавляем путь к модулям
sys.path.append(os.path.dirname(__file__))

from modules.database import VGTRKDatabase

def check_missing_filials():
    """Проверка какие филиалы из CSV отсутствуют в БД"""
    
    print("=" * 60)
    print("ПРОВЕРКА ИМПОРТА ФИЛИАЛОВ ВГТРК")
    print("=" * 60)
    
    # Читаем CSV файл
    csv_path = Path("../ГТРК/vgtrk_filials_final.csv")
    if not csv_path.exists():
        csv_path = Path("ГТРК/vgtrk_filials_final.csv")
    
    if not csv_path.exists():
        print(f"[ERROR] CSV файл не найден: {csv_path}")
        return
    
    # Читаем данные из CSV
    print(f"\n[1] Чтение CSV файла: {csv_path}")
    df_csv = pd.read_csv(csv_path)
    print(f"   Найдено в CSV: {len(df_csv)} филиалов")
    
    # Подключаемся к БД
    print("\n[2] Подключение к базе данных...")
    db = VGTRKDatabase("data/vgtrk_monitoring.db")
    
    # Получаем филиалы из БД
    all_filials = db.get_all_filials(active_only=False)
    print(f"   Найдено в БД: {len(all_filials)} филиалов")
    
    # Создаем списки названий для сравнения
    csv_names = set(df_csv['Название'].str.strip())
    db_names = set(f['name'] for f in all_filials)
    
    # Находим отсутствующие
    missing_in_db = csv_names - db_names
    extra_in_db = db_names - csv_names
    
    if missing_in_db:
        print(f"\n[!] ОТСУТСТВУЮТ В БД ({len(missing_in_db)} филиалов):")
        for i, name in enumerate(sorted(missing_in_db), 1):
            # Находим полную информацию из CSV
            row = df_csv[df_csv['Название'] == name].iloc[0]
            print(f"   {i}. {name}")
            print(f"      Регион: {row['Регион']}")
            print(f"      Город: {row['Город']}")
            print(f"      Округ: {row['Округ']}")
            print(f"      Сайт: {row.get('Сайт', 'нет')}")
    else:
        print("\n[OK] Все филиалы из CSV есть в БД")
    
    if extra_in_db:
        print(f"\n[!] ЛИШНИЕ В БД (есть в БД, но нет в CSV):")
        for i, name in enumerate(sorted(extra_in_db), 1):
            print(f"   {i}. {name}")
    
    # Проверяем конкретно ГТРК "Вятка"
    print("\n[3] Проверка ГТРК 'Вятка'...")
    vyatka_csv = df_csv[df_csv['Название'].str.contains('Вятка', na=False)]
    if not vyatka_csv.empty:
        print(f"   В CSV: {vyatka_csv.iloc[0]['Название']}")
        vyatka_db = [f for f in all_filials if 'Вятка' in f['name']]
        if vyatka_db:
            print(f"   В БД: {vyatka_db[0]['name']}")
        else:
            print("   В БД: НЕ НАЙДЕНО!")
    
    # Статистика по округам
    print("\n[4] Статистика по федеральным округам:")
    print("\n   Округ | CSV | БД  | Разница")
    print("   " + "-" * 30)
    
    csv_by_district = df_csv.groupby('Округ').size()
    db_by_district = {}
    for filial in all_filials:
        district = filial['federal_district']
        db_by_district[district] = db_by_district.get(district, 0) + 1
    
    all_districts = set(csv_by_district.index) | set(db_by_district.keys())
    
    for district in sorted(all_districts):
        csv_count = csv_by_district.get(district, 0)
        db_count = db_by_district.get(district, 0)
        diff = db_count - csv_count
        diff_str = f"+{diff}" if diff > 0 else str(diff) if diff < 0 else "OK"
        print(f"   {district:20} | {csv_count:3} | {db_count:3} | {diff_str}")
    
    print("\n" + "=" * 60)
    
    # Если есть отсутствующие, предлагаем исправить
    if missing_in_db:
        print("\n[?] Хотите добавить отсутствующие филиалы в БД? (y/n): ", end="")
        answer = input().strip().lower()
        if answer == 'y':
            fix_missing_filials(db, df_csv, missing_in_db)

def fix_missing_filials(db, df_csv, missing_names):
    """Добавление отсутствующих филиалов в БД"""
    print("\n[5] Добавление отсутствующих филиалов...")
    
    added = 0
    with db.get_connection() as conn:
        for name in missing_names:
            row = df_csv[df_csv['Название'] == name].iloc[0]
            try:
                conn.execute('''
                    INSERT INTO filials (name, region, city, website, federal_district)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    row['Название'].strip(),
                    row['Регион'] if pd.notna(row['Регион']) else '',
                    row['Город'] if pd.notna(row['Город']) else '',
                    row['Сайт'] if pd.notna(row.get('Сайт')) else None,
                    row['Округ']
                ))
                added += 1
                print(f"   [OK] Добавлен: {name}")
            except Exception as e:
                print(f"   [ERROR] Ошибка при добавлении {name}: {e}")
        
        conn.commit()
    
    print(f"\n[OK] Добавлено {added} филиалов")
    
    # Проверяем результат
    all_filials = db.get_all_filials(active_only=False)
    print(f"Теперь в БД: {len(all_filials)} филиалов")

def show_detailed_comparison():
    """Детальное сравнение данных CSV и БД"""
    
    # Читаем CSV
    csv_path = Path("ГТРК/vgtrk_filials_final.csv")
    df_csv = pd.read_csv(csv_path)
    
    # Подключаемся к БД
    db = VGTRKDatabase("data/vgtrk_monitoring.db")
    all_filials = db.get_all_filials(active_only=False)
    
    # Создаем DataFrame из БД для удобного сравнения
    df_db = pd.DataFrame(all_filials)
    
    print("\n[6] Детальное сравнение (первые 10 записей):")
    print("\nCSV файл:")
    print(df_csv[['Название', 'Округ']].head(10))
    
    print("\nБаза данных:")
    if not df_db.empty:
        print(df_db[['name', 'federal_district']].head(10))

if __name__ == "__main__":
    check_missing_filials()
    
    # Показываем итоговую статистику
    print("\n[INFO] Для полной синхронизации запустите:")
    print("   python init_database.py")
    print("\n[INFO] Для запуска приложения:")
    print("   streamlit run app_sqlite.py")