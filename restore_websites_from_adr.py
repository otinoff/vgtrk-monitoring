import sqlite3
import os
import re

def restore_websites_from_adr():
    """Восстанавливает сайты филиалов из файла adr.md"""
    
    db_path = 'data/vgtrk_monitoring.db'
    adr_path = 'doc/adr.md'
    
    if not os.path.exists(db_path):
        print(f"База данных не найдена: {db_path}")
        return
        
    if not os.path.exists(adr_path):
        print(f"Файл adr.md не найден: {adr_path}")
        return
    
    print(f"Восстанавливаем сайты из {adr_path}")
    
    # Подключаемся к базе данных
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Читаем файл adr.md
    with open(adr_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Извлекаем таблицу с сайтами
    table_pattern = r'\| (\d+) \| ГТРК «([^»]+)» \| ([^|]+) \| ([^|]+) \|'
    matches = re.findall(table_pattern, content)
    
    updated_count = 0
    added_domains_count = 0
    not_found_count = 0
    
    for match in matches:
        num, name, websites, region = match
        websites = websites.strip()
        
        if websites == '-' or not websites:
            continue
            
        # Очищаем название для поиска
        search_name = f'ГТРК "{name}"'
        
        # Ищем филиал в базе данных
        cursor.execute("SELECT id, name, website FROM filials WHERE name LIKE ?", (f'%{name}%',))
        filial = cursor.fetchone()
        
        if filial:
            filial_id, db_name, current_website = filial
            
            # Разбираем список сайтов
            site_list = [site.strip() for site in websites.split(',')]
            main_site = site_list[0].strip()
            
            # Очищаем основной сайт от лишних символов
            main_site = re.sub(r'^https?://', '', main_site)
            main_site = re.sub(r'/$', '', main_site)
            
            # Обновляем основной сайт
            if main_site and main_site != current_website:
                # Исключаем telegram и vk ссылки из основного сайта
                if not ('t.me' in main_site or 'vk.com' in main_site):
                    cursor.execute("UPDATE filials SET website = ? WHERE id = ?", (main_site, filial_id))
                    updated_count += 1
                    print(f"[OK] Обновлен сайт для {db_name}: {main_site}")
            
            # Добавляем дополнительные сайты
            for site in site_list[1:]:  # пропускаем первый (основной)
                site = site.strip()
                if site:
                    # Очищаем сайт
                    site = re.sub(r'^https?://', '', site)
                    site = re.sub(r'/$', '', site)
                    
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
                        added_domains_count += 1
                        print(f"  [+] Добавлен дополнительный сайт: {site}")
        else:
            print(f"[!] Филиал не найден в БД: ГТРК «{name}»")
            not_found_count += 1
    
    # Сохраняем изменения
    conn.commit()
    conn.close()
    
    print(f"\nРезультаты восстановления:")
    print(f"- Обновлено основных сайтов: {updated_count}")
    print(f"- Добавлено дополнительных сайтов: {added_domains_count}")
    print(f"- Филиалов не найдено в БД: {not_found_count}")
    
    # Показываем итоговую статистику
    print("\nИтоговая статистика:")
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
    
    print(f"\nТеперь у нас должно быть намного больше сайтов!")

if __name__ == "__main__":
    restore_websites_from_adr()