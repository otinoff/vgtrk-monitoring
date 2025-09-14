"""
Скрипт для добавления поля sitemap_url в таблицу filials
и обновления записи для ГТРК Саха
"""

import sqlite3
from pathlib import Path

def add_sitemap_url_field():
    """Добавляет поле sitemap_url в таблицу filials"""
    
    db_path = Path("data/vgtrk_monitoring.db")
    
    if not db_path.exists():
        print(f"[ERROR] База данных не найдена: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Проверяем, существует ли уже поле sitemap_url
        cursor.execute("PRAGMA table_info(filials)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'sitemap_url' in columns:
            print("[OK] Поле sitemap_url уже существует в таблице filials")
        else:
            # Добавляем новое поле
            cursor.execute('''
                ALTER TABLE filials
                ADD COLUMN sitemap_url TEXT
            ''')
            conn.commit()
            print("[OK] Поле sitemap_url успешно добавлено в таблицу filials")
        
        # Обновляем запись для ГТРК Саха с новым sitemap URL
        cursor.execute('''
            UPDATE filials 
            SET sitemap_url = ?, updated_at = CURRENT_TIMESTAMP
            WHERE name LIKE '%Саха%' 
               OR website = 'https://gtrksakha.ru'
               OR website = 'gtrksakha.ru'
        ''', ('https://gtrksakha.ru/sitemap2025.xml',))
        
        updated_count = cursor.rowcount
        conn.commit()
        
        if updated_count > 0:
            print(f"[OK] Обновлен sitemap URL для ГТРК Саха ({updated_count} записей)")
            
            # Проверяем результат
            cursor.execute('''
                SELECT id, name, website, sitemap_url
                FROM filials
                WHERE sitemap_url IS NOT NULL
            ''')
            
            results = cursor.fetchall()
            if results:
                print("\n[INFO] Филиалы с установленным sitemap_url:")
                for row in results:
                    print(f"   ID: {row[0]}, Название: {row[1]}")
                    print(f"   Сайт: {row[2]}")
                    print(f"   Sitemap: {row[3]}")
                    print("-" * 50)
        else:
            print("[WARNING] Не найдены записи ГТРК Саха для обновления")
            
            # Покажем все филиалы с "Саха" в названии
            cursor.execute('''
                SELECT id, name, website
                FROM filials
                WHERE name LIKE '%Саха%'
            ''')
            
            results = cursor.fetchall()
            if results:
                print("\n[SEARCH] Найденные филиалы с 'Саха' в названии:")
                for row in results:
                    print(f"   ID: {row[0]}, Название: {row[1]}, Сайт: {row[2]}")
        
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"[ERROR] Ошибка при работе с базой данных: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Неожиданная ошибка: {e}")
        return False

def main():
    """Основная функция"""
    print("[START] Добавление поля sitemap_url в базу данных...")
    print("=" * 60)
    
    success = add_sitemap_url_field()
    
    if success:
        print("\n[SUCCESS] Операция завершена успешно!")
        print("\n[INFO] Теперь вы можете:")
        print("   1. Добавлять sitemap URL для других филиалов")
        print("   2. Использовать прямые sitemap URL для поиска")
        print("   3. Избежать проблем с sitemap_index.xml")
    else:
        print("\n[ERROR] Операция завершена с ошибками")

if __name__ == "__main__":
    main()