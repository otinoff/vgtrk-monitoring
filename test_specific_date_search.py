#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест поиска по конкретной дате (11 сентября)
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

from datetime import datetime, date
from modules.scrapy_parser import ScrapyParser
from modules.advanced_logger import get_logger

# Создаем парсер
logger = get_logger()
parser = ScrapyParser(logger=logger)

# Параметры поиска
site_url = "https://gtrksakha.ru"
sitemap_url = "https://gtrksakha.ru/sitemap2025.xml"
keywords = ["Конгресс", "конгресс", "здравоохранение"]

# Конкретная дата - 11 сентября 2025
search_date = date(2025, 9, 11)

print("="*60)
print("Тест поиска по конкретной дате")
print("="*60)
print(f"Сайт: {site_url}")
print(f"Дата поиска: {search_date.strftime('%d.%m.%Y')}")
print(f"Ключевые слова: {', '.join(keywords)}")
print("="*60)

# Поиск через новый метод
results = parser.search_with_sitemap_date(
    site_url,
    keywords,
    search_date=search_date,
    max_articles=150,
    sitemap_url=sitemap_url
)

print(f"\nРезультаты поиска:")
print(f"Найдено статей: {len(results) if results else 0}")

if results:
    print("\nНайденные статьи:")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result['title']}")
        print(f"   URL: {result['url']}")
        print(f"   Дата: {result.get('date', 'не указана')}")
        print(f"   Ключевые слова: {result['keywords']}")
        
        # Проверяем, есть ли статья про Конгресс
        if "конгресс" in result['title'].lower():
            print("   [V] ЭТО СТАТЬЯ ПРО КОНГРЕСС!")
else:
    print("\n[X] Статьи не найдены")

# Дополнительно - проверим сколько всего статей за 11 сентября
print("\n" + "="*60)
print("Анализ всех статей за 11 сентября")
print("="*60)

# Загружаем sitemap для анализа
sitemap_data = parser.find_sitemap(site_url, sitemap_url)
if sitemap_data:
    _, xml_content = sitemap_data
    
    # Парсим для конкретной даты
    from datetime import time
    date_from = datetime.combine(search_date, time.min)
    date_to = datetime.combine(search_date, time.max)
    
    all_articles = parser.parse_sitemap_urls(xml_content, date_from, date_to)
    print(f"Всего статей за {search_date.strftime('%d.%m.%Y')}: {len(all_articles)}")
    
    # Показываем все URL за эту дату
    if len(all_articles) <= 10:
        print("\nВсе статьи за эту дату:")
        for i, article in enumerate(all_articles, 1):
            print(f"{i}. {article['url']}")
    else:
        print(f"\nПервые 5 статей из {len(all_articles)}:")
        for i, article in enumerate(all_articles[:5], 1):
            print(f"{i}. {article['url']}")