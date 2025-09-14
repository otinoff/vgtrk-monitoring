#!/usr/bin/env python3
"""
Универсальный скрипт для проверки и исправления структуры базы данных
Проверяет все необходимые поля и исправляет структуру
"""

import sqlite3
import os

def check_and_fix_database():
    """Проверяет и исправляет структуру базы данных"""
    
    db_path = "data/vgtrk_monitoring.db"
    
    # Создаем папку data если её нет
    os.makedirs("data", exist_ok=True)
    
    print("=" * 60)
    print("🔍 ПРОВЕРКА СТРУКТУРЫ БАЗЫ ДАННЫХ")
    print("=" * 60)
    
    # Подключаемся к базе данных
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. Проверяем существование таблицы filials
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='filials'")
        if not cursor.fetchone():
            print("❌ Таблица filials не найдена! Создаём...")
            create_filials_table(conn)
        else:
            print("✅ Таблица filials существует")
        
        # 2. Получаем текущую структуру таблицы
        cursor.execute("PRAGMA table_info(filials)")
        columns = cursor.fetchall()
        existing_columns = {col[1]: col[2] for col in columns}
        
        print("\n📊 Текущие колонки в таблице:")
        for col_name, col_type in existing_columns.items():
            print(f"  - {col_name} ({col_type})")
        
        # 3. Определяем необходимые колонки
        required_columns = {
            'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
            'name': 'TEXT',
            'federal_district': 'TEXT',
            'region': 'TEXT',
            'website': 'TEXT',  # Внимание: website, а не website_url!
            'sitemap_url': 'TEXT',
            'is_active': 'INTEGER DEFAULT 1',
            'region_code': 'TEXT'
        }
        
        # 4. Проверяем и добавляем недостающие колонки
        print("\n🔧 Проверка недостающих колонок...")
        missing_columns = []
        
        for col_name, col_type in required_columns.items():
            if col_name not in existing_columns:
                missing_columns.append((col_name, col_type))
                print(f"  ❌ Отсутствует колонка: {col_name}")
        
        if missing_columns:
            print("\n📝 Добавляем недостающие колонки...")
            for col_name, col_type in missing_columns:
                if col_name != 'id':  # id нельзя добавить через ALTER TABLE
                    try:
                        # Определяем дефолтное значение
                        default_value = ""
                        if col_type.startswith('INTEGER'):
                            default_value = " DEFAULT 0"
                            if 'is_active' in col_name:
                                default_value = " DEFAULT 1"
                        elif col_type.startswith('TEXT'):
                            default_value = " DEFAULT ''"
                        
                        sql = f"ALTER TABLE filials ADD COLUMN {col_name} {col_type.split(' ')[0]}{default_value}"
                        cursor.execute(sql)
                        conn.commit()
                        print(f"  ✅ Добавлена колонка: {col_name}")
                    except sqlite3.OperationalError as e:
                        print(f"  ⚠️ Не удалось добавить {col_name}: {e}")
        else:
            print("  ✅ Все необходимые колонки присутствуют")
        
        # 5. Проверяем наличие данных
        cursor.execute("SELECT COUNT(*) FROM filials")
        count = cursor.fetchone()[0]
        print(f"\n📈 Записей в таблице: {count}")
        
        if count == 0:
            print("  ⚠️ Таблица пуста. Возможно, нужно запустить init_database.py")
        
        # 6. Финальная проверка структуры
        print("\n✅ ФИНАЛЬНАЯ СТРУКТУРА ТАБЛИЦЫ:")
        cursor.execute("PRAGMA table_info(filials)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        print("\n" + "=" * 60)
        print("✅ ПРОВЕРКА ЗАВЕРШЕНА УСПЕШНО!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        print("\nПопытка пересоздать таблицу...")
        try:
            cursor.execute("DROP TABLE IF EXISTS filials")
            create_filials_table(conn)
            print("✅ Таблица пересоздана успешно!")
        except Exception as e2:
            print(f"❌ Не удалось пересоздать таблицу: {e2}")
    
    finally:
        conn.close()

def create_filials_table(conn):
    """Создает таблицу filials с правильной структурой"""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS filials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            federal_district TEXT,
            region TEXT,
            website TEXT,
            sitemap_url TEXT,
            is_active INTEGER DEFAULT 1,
            region_code TEXT
        )
    """)
    conn.commit()
    print("✅ Таблица filials создана с правильной структурой")

if __name__ == "__main__":
    check_and_fix_database()
    print("\n💡 Теперь запустите приложение снова!")
    print("   Если ошибки продолжаются, запустите:")
    print("   python3 init_database.py")