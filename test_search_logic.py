#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест логики поиска ключевых слов в Sitemap режиме
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

from modules.scrapy_parser import ScrapyParser
from modules.advanced_logger import get_logger

# Создаем логгер
logger = get_logger()

# URL сайта и sitemap
site_url = "https://gtrksakha.ru"
sitemap_url = "https://gtrksakha.ru/sitemap2025.xml"

# Ключевые слова - как в основном приложении (все вместе)
all_keywords = ["Конгресс", "конгресс", "здравоохранение"]

# Создаем парсер
parser = ScrapyParser(logger=logger)

print("="*60)
print("Тест логики поиска как в основном приложении")
print("="*60)
print(f"Сайт: {site_url}")
print(f"Sitemap: {sitemap_url}")
print(f"Все ключевые слова: {all_keywords}")
print(f"Период: 3 дня")
print("="*60)

# Поиск через Sitemap (как в основном приложении)
sitemap_results = parser.search_with_sitemap(
    site_url,
    all_keywords,  # Передаем все ключевые слова сразу
    days=3,
    max_articles=50,
    sitemap_url=sitemap_url
)

print(f"\nНайдено статей всего: {len(sitemap_results) if sitemap_results else 0}")

if sitemap_results:
    # Теперь фильтруем по каждому ключевому слову отдельно (как в app_sqlite.py)
    for keyword in all_keywords:
        print(f"\n--- Фильтрация по '{keyword}' ---")
        
        # Точно такая же логика как в app_sqlite.py (строки 698-701)
        relevant_articles = [
            article for article in sitemap_results
            if keyword.lower() in ' '.join(article.get('keywords', [])).lower()
        ]
        
        print(f"Найдено статей с '{keyword}': {len(relevant_articles)}")
        
        if relevant_articles:
            for idx, article in enumerate(relevant_articles[:3], 1):
                print(f"\n{idx}. {article['title']}")
                print(f"   URL: {article['url']}")
                print(f"   Найденные ключевые слова в статье: {article.get('keywords', [])}")
                
    # Проверим статью про Конгресс конкретно
    print("\n" + "="*60)
    print("Проверка конкретной статьи про Конгресс")
    print("="*60)
    
    congress_articles = [
        article for article in sitemap_results
        if "конгресс" in article['title'].lower()
    ]
    
    if congress_articles:
        print(f"Найдено статей с 'конгресс' в заголовке: {len(congress_articles)}")
        for article in congress_articles:
            print(f"\nЗаголовок: {article['title']}")
            print(f"URL: {article['url']}")
            print(f"Ключевые слова найденные парсером: {article.get('keywords', [])}")
            
            # Проверяем логику фильтрации
            print("\nПроверка фильтрации:")
            keywords_str = ' '.join(article.get('keywords', [])).lower()
            print(f"Строка из ключевых слов: '{keywords_str}'")
            
            for kw in all_keywords:
                in_keywords = kw.lower() in keywords_str
                in_title = kw.lower() in article['title'].lower()
                print(f"  '{kw}' в keywords: {in_keywords}")
                print(f"  '{kw}' в title: {in_title}")