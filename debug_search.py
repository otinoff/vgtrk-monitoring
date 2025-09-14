#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Отладочный скрипт для проверки поиска статей
"""

import sqlite3
import asyncio
import aiohttp
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
from urllib.parse import urlparse
import re
import sys
import io

# Устанавливаем правильную кодировку для вывода
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

async def fetch_sitemap(session, url):
    """Загрузка и парсинг sitemap"""
    try:
        async with session.get(url, timeout=10) as response:
            if response.status == 200:
                content = await response.text()
                return content
    except Exception as e:
        print(f"Ошибка загрузки sitemap {url}: {e}")
    return None

def parse_sitemap(xml_content):
    """Парсинг sitemap и извлечение URL статей"""
    articles = []
    try:
        # Убираем namespace для упрощения парсинга
        xml_content = re.sub(r'xmlns="[^"]+"', '', xml_content)
        xml_content = re.sub(r'xmlns:news="[^"]+"', '', xml_content)
        
        root = ET.fromstring(xml_content)
        
        for url_elem in root.findall('.//url'):
            loc = url_elem.find('loc')
            if loc is not None and loc.text:
                articles.append(loc.text)
                
    except Exception as e:
        print(f"Ошибка парсинга XML: {e}")
    
    return articles
async def parse_sitemap_with_index(session, xml_content, depth=0):
    """Парсинг sitemap с поддержкой sitemap_index"""
    articles = []
    
    # Ограничиваем глубину рекурсии
    if depth > 2:
        return articles
    
    try:
        # Убираем namespace для упрощения парсинга
        clean_content = re.sub(r'xmlns[^=]*=\"[^\"]*\"', '', xml_content)
        
        # Проверяем, является ли это sitemap_index
        if '<sitemapindex' in clean_content or 'sitemapindex>' in clean_content:
            print(f"[INFO] {'  ' * depth}Обнаружен sitemap_index")
            root = ET.fromstring(clean_content)
            
            # Извлекаем URL'ы вложенных sitemap
            sitemap_urls = []
            for sitemap_elem in root.findall('.//sitemap'):
                loc = sitemap_elem.find('loc')
                if loc is not None and loc.text:
                    sitemap_urls.append(loc.text)
            
            print(f"[INFO] {'  ' * depth}Найдено {len(sitemap_urls)} вложенных sitemap файлов")
            
            # Загружаем первые несколько для теста
            for i, sitemap_url in enumerate(sitemap_urls[:3], 1):
                print(f"[INFO] {'  ' * depth}Загружаем вложенный sitemap {i}/{min(3, len(sitemap_urls))}: {sitemap_url}")
                try:
                    sub_content = await fetch_sitemap(session, sitemap_url)
                    if sub_content:
                        sub_articles = await parse_sitemap_with_index(session, sub_content, depth + 1)
                        articles.extend(sub_articles)
                        if len(articles) >= 100:  # Ограничиваем для теста
                            break
                except Exception as e:
                    print(f"[ERROR] {'  ' * depth}Ошибка загрузки вложенного sitemap: {e}")
        else:
            # Обычный sitemap
            root = ET.fromstring(clean_content)
            
            for url_elem in root.findall('.//url'):
                loc = url_elem.find('loc')
                if loc is not None and loc.text:
                    articles.append(loc.text)
                    
    except Exception as e:
        print(f"[ERROR] {'  ' * depth}Ошибка парсинга XML: {e}")
    
    return articles


def check_keyword_in_url(url, keywords):
    """Проверка наличия ключевых слов в URL"""
    url_lower = url.lower()
    for keyword in keywords:
        if keyword.lower() in url_lower:
            return True, keyword
    return False, None

async def test_filial(filial_name, website_url, sitemap_url, keywords):
    """Тестирование поиска для одного филиала"""
    print(f"\n{'='*60}")
    print(f"Тестируем филиал: {filial_name}")
    print(f"Сайт: {website_url}")
    print(f"Sitemap: {sitemap_url}")
    print(f"Ключевые слова: {', '.join(keywords)}")
    print('-'*60)
    
    if not sitemap_url:
        print("[ERROR] Sitemap URL не задан")
        return
    
    async with aiohttp.ClientSession() as session:
        # Загружаем sitemap
        print(f"Загружаем sitemap...")
        xml_content = await fetch_sitemap(session, sitemap_url)
        
        if not xml_content:
            print("[ERROR] Не удалось загрузить sitemap")
            return
            
        print(f"[OK] Sitemap загружен, размер: {len(xml_content)} байт")
        
        # Парсим sitemap с поддержкой index
        articles = await parse_sitemap_with_index(session, xml_content)
        print(f"[INFO] Всего найдено URL: {len(articles)}")
        
        if articles:
            # Показываем первые 5 URL
            print("\nПримеры URL из sitemap:")
            for i, url in enumerate(articles[:5], 1):
                print(f"  {i}. {url}")
            
            # Ищем совпадения с ключевыми словами
            matches = []
            for url in articles:
                found, keyword = check_keyword_in_url(url, keywords)
                if found:
                    matches.append((url, keyword))
            
            if matches:
                print(f"\n[OK] Найдено совпадений: {len(matches)}")
                print("\nПримеры найденных статей:")
                for i, (url, keyword) in enumerate(matches[:5], 1):
                    print(f"  {i}. Ключевое слово '{keyword}' в URL:")
                    print(f"     {url}")
            else:
                print(f"\n[WARNING] Совпадений с ключевыми словами не найдено!")
                print("\nПроверим наличие ключевых слов в URL...")
                for keyword in keywords:
                    keyword_lower = keyword.lower()
                    found_any = False
                    for url in articles[:100]:  # Проверяем первые 100 URL
                        if keyword_lower in url.lower():
                            print(f"  [OK] Слово '{keyword}' найдено в: {url}")
                            found_any = True
                            break
                    if not found_any:
                        print(f"  [X] Слово '{keyword}' не найдено в первых 100 URL")

async def main():
    """Основная функция"""
    # Подключаемся к БД
    conn = sqlite3.connect('data/vgtrk_monitoring.db')
    cursor = conn.cursor()
    
    # Тестовые ключевые слова - используем те же, что в приложении
    # А также добавляем слова, которые точно находятся (конгресс)
    keywords = ["конгресс", "здравоохранение", "сахалин", "власт", "губернатор", "правительств", "выбор", "бурят"]
    
    print("="*60)
    print("ОТЛАДКА ПОИСКА СТАТЕЙ В SITEMAP")
    print("="*60)
    print(f"\nИспользуемые ключевые слова для теста:")
    print(f"  {', '.join(keywords)}")
    
    # Получаем несколько филиалов для теста
    cursor.execute("""
        SELECT name, website_url, sitemap_url 
        FROM filials 
        WHERE sitemap_url IS NOT NULL AND sitemap_url != ''
        ORDER BY name
        LIMIT 3
    """)
    
    filials = cursor.fetchall()
    
    if not filials:
        print("\n[ERROR] Не найдено филиалов с заполненным sitemap_url")
        
        # Покажем, что есть в БД
        cursor.execute("SELECT COUNT(*) FROM filials")
        total = cursor.fetchone()[0]
        print(f"\nВсего филиалов в БД: {total}")
        
        cursor.execute("SELECT COUNT(*) FROM filials WHERE sitemap_url IS NOT NULL AND sitemap_url != ''")
        with_sitemap = cursor.fetchone()[0]
        print(f"Филиалов с sitemap: {with_sitemap}")
        
        # Покажем примеры
        cursor.execute("SELECT name, website_url FROM filials LIMIT 5")
        print("\nПримеры филиалов:")
        for name, url in cursor.fetchall():
            print(f"  - {name}: {url}")
    else:
        print(f"\nБудем тестировать {len(filials)} филиала(ов)")
        
        # Тестируем каждый филиал
        for name, website_url, sitemap_url in filials:
            await test_filial(name, website_url, sitemap_url, keywords)
    
    # Специально проверим Бурятию, если она есть
    print("\n" + "="*60)
    print("Поиск филиала Бурятия...")
    cursor.execute("""
        SELECT name, website_url, sitemap_url 
        FROM filials 
        WHERE LOWER(name) LIKE '%бурят%' OR LOWER(name) LIKE '%buriat%'
    """)
    
    buryatia = cursor.fetchone()
    if buryatia:
        name, website_url, sitemap_url = buryatia
        await test_filial(name, website_url, sitemap_url, keywords)
    else:
        print("[ERROR] Филиал Бурятия не найден в БД")
        
        # Попробуем найти любой филиал с Бурят в названии
        cursor.execute("""
            SELECT name FROM filials WHERE name LIKE '%урят%'
        """)
        similar = cursor.fetchall()
        if similar:
            print("\nВозможно, вы имели в виду:")
            for (name,) in similar:
                print(f"  - {name}")
    
    conn.close()
    
    print("\n" + "="*60)
    print("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())