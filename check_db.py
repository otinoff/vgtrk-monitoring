import sqlite3
import os

# Проверяем путь к базе данных
db_path = 'data/vgtrk_monitoring.db'
if not os.path.exists(db_path):
    print(f"База данных не найдена по пути: {db_path}")
    exit(1)

print(f"Проверяем базу данных: {db_path}")
print(f"Размер файла: {os.path.getsize(db_path)} байт")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Получаем список таблиц
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"Таблицы в БД: {[table[0] for table in tables]}")
    
    # Проверяем количество филиалов
    cursor.execute("SELECT COUNT(*) FROM filials;")
    filials_count = cursor.fetchone()[0]
    print(f"Количество филиалов: {filials_count}")
    
    # Проверяем филиалы без сайтов
    cursor.execute("SELECT COUNT(*) FROM filials WHERE website IS NULL OR website = '';")
    empty_websites = cursor.fetchone()[0]
    print(f"Филиалов без сайтов: {empty_websites}")
    
    # Проверяем филиалы с сайтами
    cursor.execute("SELECT COUNT(*) FROM filials WHERE website IS NOT NULL AND website != '';")
    with_websites = cursor.fetchone()[0]
    print(f"Филиалов с сайтами: {with_websites}")
    
    # Показываем примеры филиалов
    cursor.execute("SELECT name, website FROM filials WHERE website IS NOT NULL AND website != '' LIMIT 10;")
    samples = cursor.fetchall()
    print("\nПримеры филиалов с сайтами:")
    for i, (name, website) in enumerate(samples, 1):
        print(f"  {i}. {name}: {website}")
    
    # Проверяем другие таблицы
    for table_name in ['search_queries', 'monitoring_results', 'monitoring_logs']:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            print(f"Записей в таблице {table_name}: {count}")
        except sqlite3.OperationalError:
            print(f"Таблица {table_name} не существует")
    
    conn.close()
    
except Exception as e:
    print(f"Ошибка при работе с БД: {e}")