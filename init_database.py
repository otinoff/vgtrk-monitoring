#!/usr/bin/env python3
"""
Скрипт для инициализации базы данных SQLite и импорта данных филиалов ВГТРК
"""

import sys
import os
from pathlib import Path

# Добавляем путь к модулям
sys.path.append(os.path.dirname(__file__))

from modules.database import VGTRKDatabase
import pandas as pd


def init_vgtrk_database():
    """Инициализация базы данных и импорт начальных данных"""
    
    print("=" * 60)
    print("🚀 Инициализация базы данных системы мониторинга ВГТРК")
    print("=" * 60)
    
    # Создаем экземпляр базы данных
    db = VGTRKDatabase("data/vgtrk_monitoring.db")
    print("✅ База данных создана: data/vgtrk_monitoring.db")
    
    # Импортируем филиалы из CSV
    csv_path = Path("../ГТРК/vgtrk_filials_final.csv")
    if not csv_path.exists():
        # Пробуем альтернативный путь
        csv_path = Path("ГТРК/vgtrk_filials_final.csv")
    
    if csv_path.exists():
        print(f"\n📂 Импорт филиалов из {csv_path}")
        count = db.import_filials_from_csv(str(csv_path), clear_existing=True)
        print(f"✅ Импортировано {count} филиалов")
        
        # Показываем статистику по округам
        stats = db.get_statistics()
        print("\n📊 Распределение филиалов по федеральным округам:")
        for district, count in sorted(stats['by_district'].items()):
            print(f"   {district}: {count} филиалов")
        print(f"   ИТОГО: {stats['filials']['total']} филиалов")
    else:
        print(f"⚠️ Файл {csv_path} не найден!")
        print("Создаем тестовые данные...")
        create_test_data(db)
    
    # Добавляем стандартные поисковые запросы
    print("\n📝 Добавление стандартных поисковых запросов...")
    add_default_search_queries(db)
    
    # Создаем дополнительные индексы для оптимизации
    print("\n🔧 Оптимизация базы данных...")
    optimize_database(db)
    
    print("\n✅ Инициализация завершена успешно!")
    print("\n📋 Структура базы данных:")
    print("   - filials: Филиалы ВГТРК")
    print("   - search_queries: Поисковые запросы для мониторинга")
    print("   - monitoring_results: Результаты парсинга и анализа")
    print("   - monitoring_logs: Системные логи")
    
    return db


def create_test_data(db: VGTRKDatabase):
    """Создание тестовых данных если CSV файл не найден"""
    test_filials = [
        {
            'name': 'ГТРК "Новосибирск"',
            'region': 'Новосибирская область',
            'city': 'Новосибирск',
            'website': 'nsktv.ru',
            'federal_district': 'СФО'
        },
        {
            'name': 'ГТРК "Кузбасс"',
            'region': 'Кемеровская область',
            'city': 'Кемерово',
            'website': 'vesti42.ru',
            'federal_district': 'СФО'
        },
        {
            'name': 'ГТРК "Иртыш"',
            'region': 'Омская область',
            'city': 'Омск',
            'website': 'vesti-omsk.ru',
            'federal_district': 'СФО'
        }
    ]
    
    with db.get_connection() as conn:
        for filial in test_filials:
            conn.execute('''
                INSERT OR REPLACE INTO filials 
                (name, region, city, website, federal_district)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                filial['name'],
                filial['region'],
                filial['city'],
                filial['website'],
                filial['federal_district']
            ))
        conn.commit()
    
    print(f"✅ Добавлено {len(test_filials)} тестовых филиалов")


def add_default_search_queries(db: VGTRKDatabase):
    """Добавление стандартных поисковых запросов для мониторинга"""
    
    queries = [
        # Обязательный контент
        {
            'query': 'ВГТРК',
            'category': 'обязательный',
            'description': 'Упоминание головной компании',
            'priority': 10
        },
        {
            'query': 'лицензия СМИ',
            'category': 'обязательный',
            'description': 'Наличие информации о лицензии',
            'priority': 9
        },
        {
            'query': 'контакты редакции',
            'category': 'обязательный',
            'description': 'Контактная информация',
            'priority': 8
        },
        
        # Федеральные темы
        {
            'query': 'указ президента',
            'category': 'федеральные',
            'description': 'Освещение указов президента',
            'priority': 7
        },
        {
            'query': 'правительство России',
            'category': 'федеральные',
            'description': 'Новости правительства',
            'priority': 7
        },
        {
            'query': 'национальные проекты',
            'category': 'федеральные',
            'description': 'Освещение нацпроектов',
            'priority': 6
        },
        
        # Региональные темы
        {
            'query': 'губернатор',
            'category': 'региональные',
            'description': 'Деятельность губернатора',
            'priority': 5
        },
        {
            'query': 'местные новости',
            'category': 'региональные',
            'description': 'Региональные события',
            'priority': 5
        },
        {
            'query': 'социальные проекты',
            'category': 'региональные',
            'description': 'Социальные инициативы региона',
            'priority': 4
        }
    ]
    
    added = 0
    for q in queries:
        query_id = db.add_search_query(
            q['query'],
            q['category'],
            q['description'],
            q['priority']
        )
        if query_id:
            added += 1
    
    print(f"✅ Добавлено {added} поисковых запросов")
    
    # Показываем категории
    all_queries = db.get_search_queries()
    categories = {}
    for q in all_queries:
        cat = q.get('category', 'без категории')
        categories[cat] = categories.get(cat, 0) + 1
    
    print("\n   Категории запросов:")
    for cat, count in categories.items():
        print(f"   - {cat}: {count} запросов")


def optimize_database(db: VGTRKDatabase):
    """Оптимизация базы данных"""
    with db.get_connection() as conn:
        # Включаем оптимизации SQLite
        conn.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging для лучшей производительности
        conn.execute("PRAGMA synchronous=NORMAL")  # Баланс между скоростью и надежностью
        conn.execute("PRAGMA cache_size=10000")  # Увеличиваем кэш
        conn.execute("PRAGMA temp_store=MEMORY")  # Временные таблицы в памяти
        
        # Анализируем таблицы для оптимизации запросов
        conn.execute("ANALYZE")
        conn.commit()
    
    print("✅ База данных оптимизирована")


def show_database_info(db: VGTRKDatabase):
    """Показать информацию о базе данных"""
    print("\n" + "=" * 60)
    print("📊 ИНФОРМАЦИЯ О БАЗЕ ДАННЫХ")
    print("=" * 60)
    
    stats = db.get_statistics()
    
    print(f"\n📍 Филиалы:")
    print(f"   Всего: {stats['filials']['total']}")
    print(f"   Активных: {stats['filials']['active']}")
    
    print(f"\n🌍 По федеральным округам:")
    for district, count in sorted(stats['by_district'].items()):
        bar = "█" * (count // 2)  # Простая визуализация
        print(f"   {district:4} | {bar} {count}")
    
    # Поисковые запросы
    queries = db.get_search_queries()
    print(f"\n🔍 Поисковых запросов: {len(queries)}")
    
    # Размер базы данных
    db_path = Path("data/vgtrk_monitoring.db")
    if db_path.exists():
        size_mb = db_path.stat().st_size / (1024 * 1024)
        print(f"\n💾 Размер базы данных: {size_mb:.2f} МБ")


if __name__ == "__main__":
    # Запускаем инициализацию
    db = init_vgtrk_database()
    
    # Показываем информацию о базе
    show_database_info(db)
    
    # Тестовый запрос
    print("\n🧪 Тестовый запрос - филиалы СФО:")
    sfo_filials = db.get_filials_by_district("СФО")
    for i, filial in enumerate(sfo_filials[:5], 1):  # Показываем первые 5
        print(f"   {i}. {filial['name']} - {filial.get('website', 'нет сайта')}")
    
    if len(sfo_filials) > 5:
        print(f"   ... и еще {len(sfo_filials) - 5} филиалов")
    
    print("\n✨ База данных готова к использованию!")
    print("📝 Запустите 'streamlit run app.py' для начала работы")