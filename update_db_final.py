#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Финальное обновление БД:
1. Добавление поля region_code (автомобильный код региона)
2. Добавление недостающих сайтов
"""

import os
import sys
import sqlite3
from pathlib import Path

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Коды регионов России (автомобильные)
REGION_CODES = {
    "Республика Адыгея": 1,
    "Республика Башкортостан": 2,
    "Республика Бурятия": 3,
    "Республика Алтай": 4,
    "Республика Дагестан": 5,
    "Республика Ингушетия": 6,
    "Кабардино-Балкарская Республика": 7,
    "Республика Калмыкия": 8,
    "Карачаево-Черкесская Республика": 9,
    "Республика Карелия": 10,
    "Республика Коми": 11,
    "Республика Марий Эл": 12,
    "Республика Мордовия": 13,
    "Республика Саха (Якутия)": 14,
    "Республика Северная Осетия - Алания": 15,
    "Республика Татарстан": 16,
    "Республика Тыва": 17,
    "Удмуртская Республика": 18,
    "Республика Хакасия": 19,
    "Чеченская Республика": 20,
    "Чувашская Республика": 21,
    "Алтайский край": 22,
    "Краснодарский край": 23,
    "Красноярский край": 24,
    "Приморский край": 25,
    "Ставропольский край": 26,
    "Хабаровский край": 27,
    "Амурская область": 28,
    "Архангельская область": 29,
    "Астраханская область": 30,
    "Белгородская область": 31,
    "Брянская область": 32,
    "Владимирская область": 33,
    "Волгоградская область": 34,
    "Вологодская область": 35,
    "Воронежская область": 36,
    "Ивановская область": 37,
    "Иркутская область": 38,
    "Калининградская область": 39,
    "Калужская область": 40,
    "Камчатский край": 41,
    "Кемеровская область": 42,  # Кузбасс
    "Кировская область": 43,
    "Костромская область": 44,
    "Курганская область": 45,
    "Курская область": 46,
    "Ленинградская область": 47,
    "Липецкая область": 48,
    "Магаданская область": 49,
    "Московская область": 50,
    "Мурманская область": 51,
    "Нижегородская область": 52,
    "Новгородская область": 53,
    "Новосибирская область": 54,
    "Омская область": 55,
    "Оренбургская область": 56,
    "Орловская область": 57,
    "Пензенская область": 58,
    "Пермский край": 59,
    "Псковская область": 60,
    "Ростовская область": 61,
    "Рязанская область": 62,
    "Самарская область": 63,
    "Саратовская область": 64,
    "Сахалинская область": 65,
    "Свердловская область": 66,
    "Смоленская область": 67,
    "Тамбовская область": 68,
    "Тверская область": 69,
    "Томская область": 70,
    "Тульская область": 71,
    "Тюменская область": 72,
    "Ульяновская область": 73,
    "Челябинская область": 74,
    "Забайкальский край": 75,
    "Ярославская область": 76,
    "Москва": 77,
    "Санкт-Петербург": 78,
    "Еврейская автономная область": 79,
    "Республика Крым": 82,
    "Ненецкий АО": 83,
    "Ханты-Мансийский АО": 86,
    "Чукотский автономный округ": 87,
    "Ямало-Ненецкий АО": 89,
    "Севастополь": 92,
    # Новые территории
    "Донецкая область": 93,
    "Луганская область": 94,
    "Запорожская область": 95,
    "Херсонская область": 96,
}

# Недостающие сайты (из анализа)
MISSING_WEBSITES = {
    27: "adygtv.ru",  # ГТРК "Адыгея"
    18: None,  # ГТРК "Ивтелерадио" - уже есть как ivteleradio.ru
    5: None,  # ГТРК "Владивосток" - уже есть
    70: None,  # ГТРК "Заречный" - нет информации
    52: None,  # ГТРК "Коми-Пермяцкий" - нет информации
    84: None,  # ГТРК "Красноярский" - уже есть как vesti-krasnoyarsk.ru
    71: None,  # ГТРК "Кристалл" - нет информации
    88: None,  # ГТРК "Магадан" - уже есть как vesti-magadan.ru
    64: None,  # ГТРК "Новосибирск" - уже есть как nsktv.ru
    72: None,  # ГТРК "Норильск" - нет информации
    87: None,  # ГТРК "Москва" - нет информации
    35: "stavropolye.tv",  # ГТРК "Ставрополь"
    42: "stavropolye.tv",  # ГТРК "Ставрополье" (дубль)
    31: "vesti-k.ru",  # ГТРК "Таврида"
    73: None,  # ГТРК "Теодор" - нет информации
    55: "tyva.ru",  # ГТРК "Тыва" - исправить на gtrktuva.ru
    78: None,  # ГТРК "Томск" - уже есть как tvtomsk.ru
    74: None,  # ГТРК "Урбах" - нет информации
    91: None,  # ГТРК "Чукотка" - уже есть VK
    33: "gtrf.ru",  # РГ ВГТРК "Россия" (ГТРФ)
    43: "gtrf.ru",  # РГ ВГТРК "Государственная" (дубль)
}

def update_database():
    """Финальное обновление базы данных"""
    
    # Путь к базе данных
    db_path = Path(__file__).parent / "data" / "vgtrk_monitoring.db"
    
    if not db_path.exists():
        print(f"[ERROR] База данных не найдена: {db_path}")
        return
    
    # Подключение к БД
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. Добавляем поле region_code если его нет
        cursor.execute("""
            SELECT COUNT(*) FROM pragma_table_info('filials') 
            WHERE name='region_code'
        """)
        
        if cursor.fetchone()[0] == 0:
            print("[INFO] Добавляем поле region_code в таблицу filials...")
            cursor.execute("ALTER TABLE filials ADD COLUMN region_code INTEGER")
            conn.commit()
            print("[OK] Поле region_code добавлено")
        
        # 2. Обновляем коды регионов
        print("\n[INFO] Обновляем коды регионов...")
        updated_codes = 0
        
        cursor.execute("SELECT id, name, region FROM filials")
        filials = cursor.fetchall()
        
        for filial_id, name, region in filials:
            # Ищем код региона
            region_code = None
            
            # Сначала проверяем точное совпадение
            region_code = REGION_CODES.get(region)
            
            # Если не нашли, ищем частичное совпадение
            if not region_code:
                for reg_name, code in REGION_CODES.items():
                    if reg_name.lower() in region.lower() or region.lower() in reg_name.lower():
                        region_code = code
                        break
            
            # Особые случаи
            if "Кузбасс" in name or "Кемеровская" in region:
                region_code = 42
            elif "Новосибирск" in name or "Новосибирская" in region:
                region_code = 54
            
            if region_code:
                cursor.execute("""
                    UPDATE filials 
                    SET region_code = ? 
                    WHERE id = ?
                """, (region_code, filial_id))
                updated_codes += 1
                print(f"  [{region_code:02d}] {name}")
        
        conn.commit()
        print(f"\n[OK] Обновлено кодов регионов: {updated_codes}")
        
        # 3. Обновляем недостающие сайты
        print("\n[INFO] Обновляем недостающие сайты...")
        updated_sites = 0
        
        for filial_id, website in MISSING_WEBSITES.items():
            if website:
                cursor.execute("""
                    UPDATE filials 
                    SET website_url = ? 
                    WHERE id = ? AND (website_url IS NULL OR website_url = '')
                """, (website, filial_id))
                
                if cursor.rowcount > 0:
                    cursor.execute("SELECT name FROM filials WHERE id = ?", (filial_id,))
                    name = cursor.fetchone()[0]
                    print(f"  [OK] {name}: {website}")
                    updated_sites += 1
        
        conn.commit()
        print(f"\n[OK] Обновлено сайтов: {updated_sites}")
        
        # 4. Статистика
        print("\n" + "=" * 60)
        print("ИТОГОВАЯ СТАТИСТИКА")
        print("=" * 60)
        
        cursor.execute("SELECT COUNT(*) FROM filials")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM filials WHERE website_url IS NOT NULL AND website_url != ''")
        with_sites = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM filials WHERE region_code IS NOT NULL")
        with_codes = cursor.fetchone()[0]
        
        print(f"Всего филиалов: {total}")
        print(f"С сайтами: {with_sites} ({with_sites*100//total}%)")
        print(f"С кодами регионов: {with_codes} ({with_codes*100//total}%)")
        
        # Показываем филиалы без сайтов
        cursor.execute("""
            SELECT id, name, region, region_code 
            FROM filials 
            WHERE website_url IS NULL OR website_url = ''
            ORDER BY name
        """)
        
        without_sites = cursor.fetchall()
        if without_sites:
            print(f"\n[WARNING] Филиалы без сайтов ({len(without_sites)}):")
            for filial_id, name, region, code in without_sites:
                code_str = f"[{code:02d}]" if code else "[--]"
                print(f"  {code_str} ID:{filial_id:3} - {name} ({region})")
        
    except Exception as e:
        print(f"[ERROR] Ошибка обновления БД: {e}")
        conn.rollback()
    finally:
        conn.close()
        print("\n[INFO] Обновление завершено")

if __name__ == "__main__":
    update_database()