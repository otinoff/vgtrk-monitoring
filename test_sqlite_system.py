#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы системы с SQLite
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Добавляем путь к модулям
sys.path.append(os.path.dirname(__file__))

from modules.database import VGTRKDatabase
import pandas as pd

def test_database_operations():
    """Тестирование основных операций с базой данных"""
    
    print("=" * 60)
    print("ТЕСТИРОВАНИЕ СИСТЕМЫ МОНИТОРИНГА ВГТРК")
    print("=" * 60)
    
    # 1. Тест создания/подключения к БД
    print("\n[1] Тест подключения к базе данных...")
    try:
        db = VGTRKDatabase("data/vgtrk_monitoring.db")
        print("   [OK] Подключение успешно")
    except Exception as e:
        print(f"   [ERROR] Ошибка подключения: {e}")
        return False
    
    # 2. Тест импорта филиалов
    print("\n[2] Тест импорта филиалов из CSV...")
    csv_path = Path("../ГТРК/vgtrk_filials_final.csv")
    if not csv_path.exists():
        csv_path = Path("ГТРК/vgtrk_filials_final.csv")
    
    if csv_path.exists():
        try:
            count = db.import_filials_from_csv(str(csv_path), clear_existing=True)
            print(f"   [OK] Импортировано {count} филиалов")
        except Exception as e:
            print(f"   [ERROR] Ошибка импорта: {e}")
            return False
    else:
        print(f"   [WARNING] CSV файл не найден: {csv_path}")
        # Создаем тестовые данные
        create_test_filials(db)
    
    # 3. Тест получения филиалов
    print("\n[3] Тест получения списка филиалов...")
    try:
        all_filials = db.get_all_filials()
        print(f"   [OK] Получено {len(all_filials)} филиалов")
        
        # Показываем первые 3
        for i, filial in enumerate(all_filials[:3], 1):
            print(f"      {i}. {filial['name']} ({filial['federal_district']})")
    except Exception as e:
        print(f"   [ERROR] Ошибка получения филиалов: {e}")
        return False
    
    # 4. Тест фильтрации по округу
    print("\n[4] Тест фильтрации по федеральному округу...")
    try:
        sfo_filials = db.get_filials_by_district("СФО")
        print(f"   [OK] Найдено филиалов в СФО: {len(sfo_filials)}")
        
        # Показываем первые 3
        for i, filial in enumerate(sfo_filials[:3], 1):
            print(f"      {i}. {filial['name']} - {filial.get('website', 'нет сайта')}")
    except Exception as e:
        print(f"   [ERROR] Ошибка фильтрации: {e}")
    
    # 5. Тест добавления поисковых запросов
    print("\n[5] Тест добавления поисковых запросов...")
    try:
        test_queries = [
            ("ВГТРК", "обязательный", "Упоминание головной компании", 10),
            ("губернатор", "региональные", "Деятельность губернатора", 7),
            ("местные новости", "региональные", "Региональные события", 5),
            ("выборы", "федеральные", "Освещение выборов", 8)
        ]
        
        added = 0
        for query, category, description, priority in test_queries:
            query_id = db.add_search_query(query, category, description, priority)
            if query_id:
                added += 1
        
        print(f"   [OK] Добавлено {added} поисковых запросов")
        
        # Получаем и показываем запросы
        all_queries = db.get_search_queries()
        print(f"   Всего запросов в БД: {len(all_queries)}")
    except Exception as e:
        print(f"   [ERROR] Ошибка добавления запросов: {e}")
    
    # 6. Тест сохранения результатов мониторинга
    print("\n[6] Тест сохранения результатов мониторинга...")
    try:
        # Берем первый филиал для теста
        test_filial = all_filials[0] if all_filials else None
        
        if test_filial:
            test_result = {
                'search_query_id': 1,
                'url': test_filial.get('website', 'test.ru'),
                'page_title': 'Тестовая страница',
                'content': 'Это тестовый контент для проверки системы мониторинга ВГТРК',
                'gigachat_analysis': 'Тестовый анализ: контент соответствует запросу',
                'relevance_score': 0.85,
                'status': 'success'
            }
            
            result_id = db.save_monitoring_result(test_filial['id'], test_result)
            print(f"   [OK] Результат сохранен с ID: {result_id}")
        else:
            print("   [WARNING] Нет филиалов для тестирования")
    except Exception as e:
        print(f"   [ERROR] Ошибка сохранения результата: {e}")
    
    # 7. Тест получения статистики
    print("\n[7] Тест получения статистики...")
    try:
        stats = db.get_statistics()
        print(f"   [OK] Статистика получена:")
        print(f"      • Всего филиалов: {stats['filials']['total']}")
        print(f"      • Активных филиалов: {stats['filials']['active']}")
        print(f"      • Результатов сегодня: {stats['today']['total']}")
        
        if stats['by_district']:
            print("      • По округам:")
            for district, count in sorted(stats['by_district'].items())[:3]:
                print(f"        - {district}: {count}")
    except Exception as e:
        print(f"   [ERROR] Ошибка получения статистики: {e}")
    
    # 8. Тест экспорта в Excel
    print("\n[8] Тест экспорта в Excel...")
    try:
        export_dir = Path("exports")
        export_dir.mkdir(exist_ok=True)
        
        export_path = f"exports/test_export_{datetime.now():%Y%m%d_%H%M%S}.xlsx"
        result_path = db.export_to_excel(export_path, include_results=True)
        
        if Path(result_path).exists():
            size_kb = Path(result_path).stat().st_size / 1024
            print(f"   [OK] Экспортировано в {result_path} ({size_kb:.1f} КБ)")
        else:
            print(f"   [ERROR] Файл экспорта не создан")
    except Exception as e:
        print(f"   [ERROR] Ошибка экспорта: {e}")
    
    # 9. Тест логирования
    print("\n[9] Тест системы логирования...")
    try:
        db.add_log(None, 'system_test', 'success', 'Тестирование системы завершено успешно')
        
        logs = db.get_logs(limit=5)
        print(f"   [OK] Добавлена запись в лог. Последние записи: {len(logs)}")
    except Exception as e:
        print(f"   [ERROR] Ошибка логирования: {e}")
    
    # 10. Проверка размера БД
    print("\n[10] Информация о базе данных...")
    db_path = Path("data/vgtrk_monitoring.db")
    if db_path.exists():
        size_kb = db_path.stat().st_size / 1024
        print(f"   Размер БД: {size_kb:.1f} КБ")
        print(f"   Путь: {db_path.absolute()}")
    
    print("\n" + "=" * 60)
    print("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
    print("=" * 60)
    
    return True

def create_test_filials(db: VGTRKDatabase):
    """Создание тестовых филиалов если CSV не найден"""
    print("   Создание тестовых данных...")
    
    test_data = [
        ('ГТРК "Новосибирск"', 'Новосибирская область', 'Новосибирск', 'nsktv.ru', 'СФО'),
        ('ГТРК "Кузбасс"', 'Кемеровская область', 'Кемерово', 'vesti42.ru', 'СФО'),
        ('ГТРК "Иртыш"', 'Омская область', 'Омск', 'vesti-omsk.ru', 'СФО'),
        ('ГТРК "Томск"', 'Томская область', 'Томск', 'tvtomsk.ru', 'СФО'),
        ('ГТРК "Красноярск"', 'Красноярский край', 'Красноярск', 'vesti-krasnoyarsk.ru', 'СФО')
    ]
    
    count = 0
    with db.get_connection() as conn:
        for name, region, city, website, district in test_data:
            conn.execute('''
                INSERT OR REPLACE INTO filials 
                (name, region, city, website, federal_district)
                VALUES (?, ?, ?, ?, ?)
            ''', (name, region, city, website, district))
            count += 1
        conn.commit()
    
    print(f"   [OK] Создано {count} тестовых филиалов")

def test_streamlit_compatibility():
    """Проверка совместимости со Streamlit"""
    print("\nПроверка совместимости со Streamlit...")
    
    try:
        import streamlit
        print(f"   [OK] Streamlit установлен (версия {streamlit.__version__})")
    except ImportError:
        print("   [ERROR] Streamlit не установлен. Выполните: pip install streamlit")
        return False
    
    try:
        import pandas
        print(f"   [OK] Pandas установлен (версия {pandas.__version__})")
    except ImportError:
        print("   [ERROR] Pandas не установлен. Выполните: pip install pandas")
        return False
    
    try:
        import openpyxl
        print(f"   [OK] Openpyxl установлен (для экспорта в Excel)")
    except ImportError:
        print("   [WARNING] Openpyxl не установлен. Для экспорта в Excel выполните: pip install openpyxl")
    
    return True

if __name__ == "__main__":
    print("\nЗапуск тестирования системы мониторинга ВГТРК с SQLite\n")
    
    # Тестируем операции с БД
    if test_database_operations():
        # Проверяем совместимость
        test_streamlit_compatibility()
        
        print("\nСледующие шаги:")
        print("   1. Запустите: python init_database.py")
        print("   2. Затем: streamlit run app_sqlite.py")
        print("   3. Откройте в браузере: http://localhost:8501")
        print("\nСистема готова к использованию!")
    else:
        print("\n[ERROR] Тестирование выявило ошибки. Проверьте настройки.")