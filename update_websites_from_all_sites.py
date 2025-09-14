import sqlite3
import csv
import os

def update_websites_from_all_sites():
    """Обновляет информацию о сайтах филиалов из файла vgtrk_all_sites.csv"""
    
    db_path = 'data/vgtrk_monitoring.db'
    csv_path = '../ГТРК/vgtrk_all_sites.csv'
    
    if not os.path.exists(db_path):
        print(f"База данных не найдена: {db_path}")
        return
        
    if not os.path.exists(csv_path):
        print(f"CSV файл не найден: {csv_path}")
        return
    
    print(f"Обновляем сайты филиалов из {csv_path}")
    
    # Подключаемся к базе данных
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Читаем CSV файл
    updated_count = 0
    added_sites_count = 0
    
    with open(csv_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        
        for row in reader:
            name = row['Название'].strip('"')
            main_site = row['Сайт'].strip() if row['Сайт'] else ''
            all_sites = row['Все_сайты'].strip() if row['Все_сайты'] else ''
            
            # Ищем филиал в базе данных
            cursor.execute("SELECT id, name, website FROM filials WHERE name = ?", (name,))
            filial = cursor.fetchone()
            
            if filial:
                filial_id, db_name, current_website = filial
                
                # Определяем, какой сайт использовать как основной
                new_website = main_site if main_site else ''
                
                # Если основного сайта нет, но есть дополнительные сайты, берем первый
                if not new_website and all_sites:
                    # Берем первый сайт из списка дополнительных
                    first_site = all_sites.split(';')[0].strip()
                    if first_site and not first_site.startswith('smotrim.ru'):
                        new_website = first_site
                    elif first_site:
                        new_website = first_site
                
                # Обновляем основной сайт если нужно
                if new_website and new_website != current_website:
                    cursor.execute("UPDATE filials SET website = ? WHERE id = ?", (new_website, filial_id))
                    updated_count += 1
                    print(f"Обновлен сайт для {db_name}: {new_website}")
                
                # Добавляем дополнительные сайты в отдельную таблицу, если они есть
                if all_sites:
                    sites_list = [site.strip() for site in all_sites.split(';')]
                    for site in sites_list:
                        if site and site != new_website:
                            # Проверяем, есть ли уже такой дополнительный сайт
                            cursor.execute("""
                                SELECT COUNT(*) FROM filial_additional_domains 
                                WHERE filial_id = ? AND domain = ?
                            """, (filial_id, site))
                            
                            if cursor.fetchone()[0] == 0:
                                cursor.execute("""
                                    INSERT INTO filial_additional_domains (filial_id, domain) 
                                    VALUES (?, ?)
                                """, (filial_id, site))
                                added_sites_count += 1
                                print(f"  Добавлен дополнительный сайт: {site}")
            else:
                print(f"Филиал не найден в БД: {name}")
    
    # Сохраняем изменения
    conn.commit()
    conn.close()
    
    print(f"\nОбновление завершено:")
    print(f"- Обновлено основных сайтов: {updated_count}")
    print(f"- Добавлено дополнительных сайтов: {added_sites_count}")
    
    # Показываем статистику после обновления
    print("\nСтатистика после обновления:")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM filials WHERE website IS NOT NULL AND website != ''")
    with_sites = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM filials WHERE website IS NULL OR website = ''")
    without_sites = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM filial_additional_domains")
    additional_domains = cursor.fetchone()[0]
    
    print(f"- Филиалов с основными сайтами: {with_sites}")
    print(f"- Филиалов без основных сайтов: {without_sites}")
    print(f"- Всего дополнительных доменов: {additional_domains}")
    
    conn.close()

if __name__ == "__main__":
    update_websites_from_all_sites()