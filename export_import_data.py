#!/usr/bin/env python3
"""
Скрипт для экспорта и импорта данных между средами разработки и продакшна
"""

import sys
import os
import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Any

# Добавляем путь к модулям
sys.path.append(os.path.dirname(__file__))

from modules.database import VGTRKDatabase


def export_data(db_path: str, export_file: str):
    """
    Экспорт данных из базы данных в JSON файл
    
    Args:
        db_path: Путь к базе данных
        export_file: Путь к файлу для экспорта
    """
    print(f"📤 Экспорт данных из {db_path}")
    
    # Подключаемся к базе данных
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    try:
        export_data = {}
        
        # Экспортируем филиалы
        cursor = conn.execute('SELECT * FROM filials ORDER BY federal_district, name')
        filials = [dict(row) for row in cursor.fetchall()]
        export_data['filials'] = filials
        print(f"   ✅ Экспортировано {len(filials)} филиалов")
        
        # Экспортируем поисковые запросы
        cursor = conn.execute('SELECT * FROM search_queries ORDER BY priority DESC, query_text')
        queries = [dict(row) for row in cursor.fetchall()]
        export_data['search_queries'] = queries
        print(f"   ✅ Экспортировано {len(queries)} поисковых запросов")
        
        # Экспортируем сессии мониторинга (только последние 50)
        cursor = conn.execute('SELECT * FROM monitoring_sessions ORDER BY started_at DESC LIMIT 50')
        sessions = [dict(row) for row in cursor.fetchall()]
        export_data['monitoring_sessions'] = sessions
        print(f"   ✅ Экспортировано {len(sessions)} сессий мониторинга")
        
        # Сохраняем в файл
        with open(export_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"   📁 Данные сохранены в {export_file}")
        print(f"   💾 Размер файла: {os.path.getsize(export_file) / 1024:.1f} КБ")
        
    except Exception as e:
        print(f"❌ Ошибка при экспорте: {e}")
        raise
    finally:
        conn.close()


def import_data(db_path: str, import_file: str, clear_existing: bool = False):
    """
    Импорт данных из JSON файла в базу данных
    
    Args:
        db_path: Путь к базе данных
        import_file: Путь к файлу для импорта
        clear_existing: Очистить существующие данные перед импортом
    """
    print(f"📥 Импорт данных в {db_path} из {import_file}")
    
    # Читаем данные из файла
    with open(import_file, 'r', encoding='utf-8') as f:
        import_data = json.load(f)
    
    # Подключаемся к базе данных
    conn = sqlite3.connect(db_path)
    
    try:
        # Начинаем транзакцию
        conn.execute('BEGIN TRANSACTION')
        
        if clear_existing:
            print("   🧹 Очистка существующих данных...")
            conn.execute('DELETE FROM monitoring_results')
            conn.execute('DELETE FROM monitoring_sessions')
            conn.execute('DELETE FROM search_queries')
            conn.execute('DELETE FROM filials')
            conn.commit()
            print("   ✅ База данных очищена")
        
        # Импортируем филиалы
        if 'filials' in import_data:
            filials = import_data['filials']
            print(f"   📥 Импорт {len(filials)} филиалов...")
            
            for filial in filials:
                # Удаляем поля, которые не должны импортироваться
                filial_data = {k: v for k, v in filial.items() 
                              if k in ['name', 'region', 'city', 'website', 'federal_district', 
                                      'all_sites', 'is_active', 'sitemap_url']}
                
                # Добавляем недостающие поля со значениями по умолчанию
                if 'is_active' not in filial_data:
                    filial_data['is_active'] = 1
                if 'sitemap_url' not in filial_data:
                    filial_data['sitemap_url'] = None
                
                # Создаем список полей и значений
                fields = list(filial_data.keys())
                placeholders = ', '.join(['?' for _ in fields])
                values = [filial_data[field] for field in fields]
                
                # Формируем SQL запрос
                sql = f'''
                    INSERT OR REPLACE INTO filials ({', '.join(fields)})
                    VALUES ({placeholders})
                '''
                
                conn.execute(sql, values)
            
            conn.commit()
            print(f"   ✅ Импортировано {len(filials)} филиалов")
        
        # Импортируем поисковые запросы
        if 'search_queries' in import_data:
            queries = import_data['search_queries']
            print(f"   📥 Импорт {len(queries)} поисковых запросов...")
            
            for query in queries:
                # Удаляем поля, которые не должны импортироваться
                query_data = {k: v for k, v in query.items() 
                             if k in ['query_text', 'category', 'description', 'priority', 'is_active']}
                
                # Добавляем недостающие поля со значениями по умолчанию
                if 'is_active' not in query_data:
                    query_data['is_active'] = 1
                if 'priority' not in query_data:
                    query_data['priority'] = 1
                
                # Создаем список полей и значений
                fields = list(query_data.keys())
                placeholders = ', '.join(['?' for _ in fields])
                values = [query_data[field] for field in fields]
                
                # Формируем SQL запрос
                sql = f'''
                    INSERT OR REPLACE INTO search_queries ({', '.join(fields)})
                    VALUES ({placeholders})
                '''
                
                conn.execute(sql, values)
            
            conn.commit()
            print(f"   ✅ Импортировано {len(queries)} поисковых запросов")
        
        # Импортируем сессии мониторинга
        if 'monitoring_sessions' in import_data:
            sessions = import_data['monitoring_sessions']
            print(f"   📥 Импорт {len(sessions)} сессий мониторинга...")
            
            for session in sessions:
                # Удаляем поля, которые не должны импортироваться
                session_data = {k: v for k, v in session.items() 
                               if k in ['session_name', 'search_mode', 'search_period', 'search_date', 
                                       'filials_count', 'queries_count', 'results_count', 'status', 
                                       'started_at', 'completed_at', 'duration_seconds', 'error_message']}
                
                # Добавляем недостающие поля со значениями по умолчанию
                if 'status' not in session_data:
                    session_data['status'] = 'completed'
                if 'filials_count' not in session_data:
                    session_data['filials_count'] = 0
                if 'queries_count' not in session_data:
                    session_data['queries_count'] = 0
                if 'results_count' not in session_data:
                    session_data['results_count'] = 0
                
                # Создаем список полей и значений
                fields = list(session_data.keys())
                placeholders = ', '.join(['?' for _ in fields])
                values = [session_data[field] for field in fields]
                
                # Формируем SQL запрос
                sql = f'''
                    INSERT OR IGNORE INTO monitoring_sessions ({', '.join(fields)})
                    VALUES ({placeholders})
                '''
                
                conn.execute(sql, values)
            
            conn.commit()
            print(f"   ✅ Импортировано {len(sessions)} сессий мониторинга")
        
        print("✅ Импорт завершен успешно!")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Ошибка при импорте: {e}")
        raise
    finally:
        conn.close()


def show_database_info(db_path: str):
    """
    Показать информацию о базе данных
    
    Args:
        db_path: Путь к базе данных
    """
    print(f"📊 Информация о базе данных: {db_path}")
    
    # Подключаемся к базе данных
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    try:
        # Общая информация
        cursor = conn.execute('SELECT COUNT(*) as total FROM filials')
        filials_count = cursor.fetchone()[0]
        print(f"   🏢 Филиалов: {filials_count}")
        
        cursor = conn.execute('SELECT COUNT(*) as total FROM search_queries')
        queries_count = cursor.fetchone()[0]
        print(f"   🔍 Поисковых запросов: {queries_count}")
        
        cursor = conn.execute('SELECT COUNT(*) as total FROM monitoring_sessions')
        sessions_count = cursor.fetchone()[0]
        print(f"   📊 Сессий мониторинга: {sessions_count}")
        
        # Распределение по округам
        print("\n   🌍 Распределение по федеральным округам:")
        cursor = conn.execute('''
            SELECT federal_district, COUNT(*) as count 
            FROM filials 
            GROUP BY federal_district 
            ORDER BY count DESC
        ''')
        for row in cursor.fetchall():
            print(f"      {row[0]}: {row[1]} филиалов")
        
        # Размер файла
        if os.path.exists(db_path):
            size_mb = os.path.getsize(db_path) / (1024 * 1024)
            print(f"\n   💾 Размер базы данных: {size_mb:.2f} МБ")
        
    except Exception as e:
        print(f"❌ Ошибка при получении информации: {e}")
    finally:
        conn.close()


def main():
    """Основная функция"""
    print("=" * 60)
    print("🔄 СКРИПТ ЭКСПОРТА/ИМПОРТА ДАННЫХ")
    print("=" * 60)
    
    if len(sys.argv) < 2:
        print("Использование:")
        print(" python export_import_data.py export [db_path] [export_file]")
        print("  python export_import_data.py import [db_path] [import_file]")
        print("  python export_import_data.py info [db_path]")
        return
    
    command = sys.argv[1]
    
    if command == "export":
        if len(sys.argv) < 4:
            print("❌ Недостаточно аргументов для экспорта")
            print("Использование: python export_import_data.py export [db_path] [export_file]")
            return
        
        db_path = sys.argv[2]
        export_file = sys.argv[3]
        export_data(db_path, export_file)
        
    elif command == "import":
        if len(sys.argv) < 4:
            print("❌ Недостаточно аргументов для импорта")
            print("Использование: python export_import_data.py import [db_path] [import_file]")
            return
        
        db_path = sys.argv[2]
        import_file = sys.argv[3]
        import_data(db_path, import_file)
        
    elif command == "info":
        if len(sys.argv) < 3:
            print("❌ Недостаточно аргументов для получения информации")
            print("Использование: python export_import_data.py info [db_path]")
            return
        
        db_path = sys.argv[2]
        show_database_info(db_path)
        
    else:
        print(f"❌ Неизвестная команда: {command}")
        print("Доступные команды: export, import, info")


if __name__ == "__main__":
    main()