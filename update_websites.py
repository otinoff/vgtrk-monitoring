#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Скрипт для обновления адресов сайтов филиалов ВГТРК в базе данных
"""

import os
import sys
import sqlite3
from pathlib import Path

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Словарь с адресами сайтов филиалов - точные названия из БД
FILIAL_WEBSITES = {
    'ГТРК "Адыгея" (из ВГТРК "Адыгея")': "adygtv.ru",
    'ГТРК "Алания"': "alaniatv.ru",
    'ГТРК "Алтай"': "vesti22.tv",
    'ГТРК "Амур"': "gtrkamur.ru",
    'ГТРК "Башкортостан"': "gtrk.tv",
    'ГТРК "Белгород"': "belgorodtv.ru",
    'ГТРК "Бира"': "biratv.ru",
    'ГТРК "Брянск"': "br-tvr.ru",
    'ГТРК "Бурятия"': "bgtrk.ru",
    'ГТРК "Вайнах"': "gtrkvainah.tv",
    'ГТРК "Владивосток"': "vestiprim.ru",
    'ГТРК "Владимир"': "vladtv.ru",
    'ГТРК "Волга"': "gtrk-volga.ru",
    'ГТРК "Волгоград-ТРВ"': "volgograd-trv.ru",
    'ГТРК "Вологда"': "вести35.рф",
    'ГТРК "Воронеж"': "vestivrn.ru",
    'ГТРК "Вятка"': "gtrk-vyatka.ru",
    'ГТРК "Горный Алтай"': "elaltay.ru",
    'ГТРК "Дагестан"': "gtrkdagestan.ru",
    'ГТРК "Дальневосточная"': "vestidv.ru",
    'ГТРК "Дон-ТР"': "dontr.ru",
    'ГТРК "Донецк"': "https://t.me/VESTIDONETSK",
    'ГТРК "Ивтелерадио" (из ГТРК "Иваново")': "ivteleradio.ru",
    'ГТРК "Ингушетия"': "ingushetiatv.ru",
    'ГТРК "Иркутск"': "vestiirk.ru",
    'ГТРК "Иртыш"': "vesti-omsk.ru",
    'ГТРК "Кабардино-Балкария"': "vestikbr.ru",
    'ГТРК "Калининград"': "vesti-kaliningrad.ru",
    'ГТРК "Калмыкия"': "vesti-kalmykia.ru",
    'ГТРК "Калуга"': "gtrk-kaluga.ru",
    'ГТРК "Камчатка"': "kamchatka.tv",
    'ГТРК "Карачаево-Черкесия"': "gtrkkchr.ru",
    'ГТРК "Карелия"': "tv-karelia.ru",
    'ГТРК "Коми Гор"': "komigor.com",
    'ГТРК "Кострома"': "gtrk-kostroma.ru",
    'ГТРК "Красноярск" (из ГТРК "Красноярский край")': "vesti-krasnoyarsk.ru",
    'ГТРК "Кубань"': "kubantv.ru",
    'ГТРК "Кузбасс"': "vesti42.ru",
    'ГТРК "Курган"': "gtrk-kurgan.ru",
    'ГТРК "Курск"': "gtrkkursk.ru",
    'ГТРК "Липецк"': "vesti-lipetsk.ru",
    'ГТРК "Лотос"': "lotosgtrk.ru",
    'ГТРК "Луганск"': "gtrklnr.ru",
    'ГТРК "Магадан" (из ГТРК "Магаданская область")': "vesti-magadan.ru",
    'ГТРК "Марий Эл"': "gtrkmariel.ru",
    'ГТРК "Мордовия"': "mordoviatv.ru",
    'ГТРК "Мурман"': "murman.tv",
    'ГТРК "Нижний Новгород"': "vestinn.ru",
    'ГТРК "Новосибирск"': "nsktv.ru",
    'ГТРК "Ока"': "gtrkoka.ru",
    'ГТРК "Орел"': "vestiorel.ru",
    'ГТРК "Оренбург"': "vestirama.ru",
    'ГТРК "Пенза"': "russia58.tv",
    'ГТРК "Пермь"': "vesti-perm.ru",
    'ГТРК "Поморье"': "pomorie.ru",
    'ГТРК "Псков"': "gtrkpskov.ru",
    'ГТРК "Регион-Тюмень"': "region-tyumen.ru",
    'ГТРК "Самара"': "tvsamara.ru",
    'ГТРК "Санкт-Петербург"': "rtr.spb.ru",
    'ГТРК "Саратов"': "gtrk-saratov.ru",
    'ГТРК "Саха"': "gtrksakha.ru",
    'ГТРК "Сахалин"': "gtrk.ru",
    'ГТРК "Севастополь" (из ГТРК "Севастополь")': "vesti92.ru",
    'ГТРК "Славия"': "vesti53.ru",
    'ГТРК "Смоленск"': "gtrksmolensk.ru",
    'ГТРК "Сочи" (из ГТРК "Вести-Сочи")': "vesti-sochi.tv",
    'ГТРК "Ставрополь"': "stavropolye.tv",
    'ГТРК "Таврида" (из ГТРК "Вести-Крым")': "vesti-k.ru",
    'ГТРК "Тамбов"': "vestitambov.ru",
    'ГТРК "Татарстан" (из ГТРК "Татарстан")': "trt-tv.ru",
    'ГТРК "Тверь"': "vesti-tver.ru",
    'ГТРК "Томск" (из ГТРК "Томская область")': "tvtomsk.ru",
    'ГТРК "Тула"': "vestitula.ru",
    'ГТРК "Тыва"': "gtrktuva.ru",
    'ГТРК "Удмуртия"': "udmtv.ru",
    'ГТРК "Урал"': "vesti-ural.ru",
    'ГТРК "Хакасия"': "вести-хакасия.рф",
    'ГТРК "Чита"': "gtrkchita.ru",
    'ГТРК "Чувашия"': "chgtrk.ru",
    'ГТРК "Чукотка" (из ГТРК "Чукотский АО")': "vk.com/vestichukotka",
    'ГТРК "Югория"': "ugoria.tv",
    'ГТРК "Южный Урал"': "cheltv.ru",
    'ГТРК "Ямал"': "vesti-yamal.ru",
    'ГТРК "Ярославия"': "vesti-yaroslavl.ru",
    'РГ ВГТРК "Россия" (ГТРФ)': "gtrf.ru",
    'РГ ВГТРК "Государственная"': "gtrf.ru"
}

# Дополнительные домены для некоторых филиалов - точные названия из БД
ADDITIONAL_DOMAINS = {
    'ГТРК "Владивосток"': ["vostok24.tv"],
    'ГТРК "Вятка"': ["tvkirov.ru"],
    'ГТРК "Калуга"': ["gtrkkaluga.ru", "гтрк-калуга.рф"],
    'ГТРК "Кузбасс"': ["kuzbassmayak.ru"],
    'ГТРК "Марий Эл"': ["гтркмарийэл.рф"],
    'ГТРК "Мурман"': ["murmantv.ru"],
    'ГТРК "Новосибирск"': ["вестинск.рф"],
    'ГТРК "Пенза"': ["russia58.ru"],
    'ГТРК "Севастополь" (из ГТРК "Севастополь")': ["вести92.рф"],
    'ГТРК "Славия"': ["vesti53.com"],
    'ГТРК "Сочи" (из ГТРК "Вести-Сочи")': ["sochivesti.ru"],
    'ГТРК "Тверь"': ["вести-тверь.рф"],
    'ГТРК "Чукотка" (из ГТРК "Чукотский АО")': ["vk.com/vesti.chukotka"]
}

def update_websites():
    """Обновление адресов сайтов в базе данных"""
    
    # Путь к базе данных
    db_path = Path(__file__).parent / "data" / "vgtrk_monitoring.db"
    
    if not db_path.exists():
        print(f"[ERROR] База данных не найдена: {db_path}")
        return
    
    # Подключение к БД
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Добавляем колонку website_url если её нет
        cursor.execute("""
            SELECT COUNT(*) FROM pragma_table_info('filials') 
            WHERE name='website_url'
        """)
        
        if cursor.fetchone()[0] == 0:
            print("[INFO] Добавляем колонку website_url в таблицу filials...")
            cursor.execute("ALTER TABLE filials ADD COLUMN website_url TEXT")
            conn.commit()
        
        # Обновляем адреса сайтов
        updated_count = 0
        not_found = []
        
        for name, website in FILIAL_WEBSITES.items():
            cursor.execute("""
                UPDATE filials 
                SET website_url = ? 
                WHERE name = ?
            """, (website, name))
            
            if cursor.rowcount > 0:
                updated_count += 1
                print(f"[OK] Обновлен сайт для {name}: {website}")
            else:
                not_found.append(name)
        
        # Добавляем дополнительные домены в отдельную таблицу
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS filial_additional_domains (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filial_id INTEGER NOT NULL,
                domain TEXT NOT NULL,
                FOREIGN KEY (filial_id) REFERENCES filials(id)
            )
        """)
        
        # Очищаем старые дополнительные домены
        cursor.execute("DELETE FROM filial_additional_domains")
        
        # Добавляем новые дополнительные домены
        for filial_name, domains in ADDITIONAL_DOMAINS.items():
            cursor.execute("SELECT id FROM filials WHERE name = ?", (filial_name,))
            result = cursor.fetchone()
            if result:
                filial_id = result[0]
                for domain in domains:
                    cursor.execute("""
                        INSERT INTO filial_additional_domains (filial_id, domain)
                        VALUES (?, ?)
                    """, (filial_id, domain))
                print(f"[OK] Добавлены дополнительные домены для {filial_name}: {', '.join(domains)}")
        
        conn.commit()
        
        # Статистика
        print("\n" + "="*60)
        print(f"[INFO] Обновлено филиалов: {updated_count}")
        
        if not_found:
            print(f"[WARNING] Не найдены в БД филиалы: {', '.join(not_found)}")
        
        # Проверяем результаты
        cursor.execute("""
            SELECT COUNT(*) FROM filials WHERE website_url IS NOT NULL
        """)
        with_websites = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM filials")
        total = cursor.fetchone()[0]
        
        print(f"[INFO] Филиалов с сайтами: {with_websites} из {total}")
        
        # Показываем филиалы без сайтов
        cursor.execute("""
            SELECT name FROM filials 
            WHERE website_url IS NULL OR website_url = ''
            ORDER BY name
        """)
        
        without_websites = cursor.fetchall()
        if without_websites:
            print("\n[WARNING] Филиалы без сайтов:")
            for row in without_websites:
                print(f"  - {row[0]}")
        
        # Обновляем модуль database.py для работы с website_url
        print("\n[INFO] Обновляем app_sqlite.py для отображения адресов сайтов...")
        
    except Exception as e:
        print(f"[ERROR] Ошибка обновления БД: {e}")
        conn.rollback()
    finally:
        conn.close()
        print("\n[INFO] Обновление завершено")

if __name__ == "__main__":
    update_websites()