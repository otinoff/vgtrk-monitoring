"""
Модуль для поиска sitemap на сайтах филиалов ВГТРК
"""

import requests
from urllib.parse import urlparse, urljoin
import xml.etree.ElementTree as ET
import sqlite3
from typing import Optional
import re

def find_sitemap_for_filial(website_url: str, timeout: int = 5) -> Optional[str]:
    """
    Ищет sitemap для указанного сайта
    
    Args:
        website_url: URL сайта
        timeout: Таймаут для запросов
        
    Returns:
        URL найденного sitemap или None
    """
    if not website_url:
        return None
        
    # Нормализуем URL
    if not website_url.startswith(('http://', 'https://')):
        website_url = f'https://{website_url}'
    
    # Убираем завершающий слеш
    base_url = website_url.rstrip('/')
    
    # Список возможных путей к sitemap
    sitemap_paths = [
        '/sitemap.xml',
        '/sitemap_index.xml',
        '/sitemap2025.xml',
        '/sitemap2024.xml',
        '/news-sitemap.xml',
        '/post-sitemap.xml',
        '/page-sitemap.xml',
        '/wp-sitemap.xml',
        '/yoast-sitemap.xml',
        '/sitemap'
    ]
    
    # Сначала проверяем robots.txt
    try:
        robots_url = f"{base_url}/robots.txt"
        response = requests.get(robots_url, timeout=timeout, verify=False)
        if response.status_code == 200:
            # Ищем sitemap в robots.txt
            for line in response.text.splitlines():
                if line.lower().startswith('sitemap:'):
                    sitemap_url = line.split(':', 1)[1].strip()
                    # Проверяем доступность
                    try:
                        check_response = requests.head(sitemap_url, timeout=timeout, verify=False)
                        if check_response.status_code == 200:
                            # Возвращаем относительный путь или полный URL
                            if sitemap_url.startswith(base_url):
                                return sitemap_url.replace(base_url, '')
                            return sitemap_url
                    except:
                        pass
    except:
        pass
    
    # Проверяем стандартные пути
    for path in sitemap_paths:
        try:
            sitemap_url = f"{base_url}{path}"
            response = requests.head(sitemap_url, timeout=timeout, verify=False)
            
            if response.status_code == 200:
                # Проверяем, что это действительно XML
                check_response = requests.get(sitemap_url, timeout=timeout, verify=False, stream=True)
                content = check_response.raw.read(1000).decode('utf-8', errors='ignore')
                if '<?xml' in content or '<urlset' in content or '<sitemapindex' in content:
                    return path  # Возвращаем относительный путь
        except:
            continue
    
    return None

def save_sitemap_to_db(filial_id: int, sitemap_url: str, db_path: str = "data/vgtrk_monitoring.db"):
    """
    Сохраняет URL sitemap в базу данных
    
    Args:
        filial_id: ID филиала
        sitemap_url: URL sitemap (относительный или полный)
        db_path: Путь к базе данных
    """
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE filials 
            SET sitemap_url = ? 
            WHERE id = ?
        """, (sitemap_url, filial_id))
        conn.commit()

def batch_find_sitemaps(filials: list, db_path: str = "data/vgtrk_monitoring.db", max_count: int = 10):
    """
    Ищет sitemap для списка филиалов
    
    Args:
        filials: Список филиалов (словарей с id и website)
        db_path: Путь к базе данных
        max_count: Максимальное количество филиалов для обработки
        
    Returns:
        Количество найденных sitemap
    """
    found_count = 0
    
    for filial in filials[:max_count]:
        website = filial.get('website')
        if website and not filial.get('sitemap_url'):
            sitemap_url = find_sitemap_for_filial(website)
            if sitemap_url:
                save_sitemap_to_db(filial['id'], sitemap_url, db_path)
                found_count += 1
                print(f"✅ {filial['name']}: найден {sitemap_url}")
            else:
                print(f"❌ {filial['name']}: sitemap не найден")
    
    return found_count