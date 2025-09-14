#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Проверка конкретной статьи про Конгресс
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

import requests
from datetime import datetime, timedelta
from modules.scrapy_parser import ScrapyParser
from modules.advanced_logger import get_logger

# URL статьи про Конгресс
article_url = "https://gtrksakha.ru/news/2025/09/11/kongress-nacionalnoe-zdravoohranenie-projdet-v-nacionalnom-centre-rossiya/"

print("="*60)
print("Проверка конкретной статьи")
print("="*60)
print(f"URL: {article_url}")
print()

# Создаем парсер
logger = get_logger()
parser = ScrapyParser(logger=logger)

# 1. Проверяем, есть ли эта статья в sitemap
print("1. Проверяем наличие статьи в sitemap...")
sitemap_url = "https://gtrksakha.ru/sitemap2025.xml"
sitemap_data = parser.find_sitemap("https://gtrksakha.ru", sitemap_url)

if sitemap_data:
    _, xml_content = sitemap_data
    
    # Проверяем без фильтра дат
    print("\nПоиск в sitemap БЕЗ фильтра дат:")
    all_articles = parser.parse_sitemap_urls(xml_content)
    
    congress_in_sitemap = False
    for article in all_articles:
        if article_url in article['url']:
            congress_in_sitemap = True
            print(f"[OK] Статья НАЙДЕНА в sitemap!")
            print(f"   URL: {article['url']}")
            print(f"   Дата: {article['date']}")
            break
    
    if not congress_in_sitemap:
        print("[X] Статья НЕ найдена в sitemap")
        # Проверим, может URL другой
        for article in all_articles:
            if "kongress" in article['url'].lower():
                print(f"\nНайдена похожая статья: {article['url']}")
    
    # Проверяем с фильтром дат
    print("\n2. Проверяем с фильтром дат (3 дня)...")
    date_to = datetime.now()
    date_from = date_to - timedelta(days=3)
    
    print(f"Период поиска: {date_from.strftime('%Y-%m-%d %H:%M')} - {date_to.strftime('%Y-%m-%d %H:%M')}")
    
    filtered_articles = parser.parse_sitemap_urls(xml_content, date_from, date_to)
    print(f"Найдено статей за период: {len(filtered_articles)}")
    
    congress_in_filtered = False
    for article in filtered_articles:
        if article_url in article['url']:
            congress_in_filtered = True
            print(f"[OK] Статья есть в отфильтрованном списке")
            break
    
    if not congress_in_filtered:
        print("[X] Статья НЕ попала в отфильтрованный список")
        # Проверим дату 11 сентября
        sep_11_start = datetime(2025, 9, 11, 0, 0, 0)
        sep_11_end = datetime(2025, 9, 11, 23, 59, 59)
        print(f"\n11 сентября начало дня: {sep_11_start}")
        print(f"Попадает в диапазон поиска: {date_from <= sep_11_start <= date_to}")

# 3. Пробуем загрузить статью напрямую
print("\n3. Загружаем статью напрямую...")
keywords = ["Конгресс", "конгресс", "здравоохранение"]
article_data = parser.search_in_article(article_url, keywords)

if article_data:
    print("[OK] Статья успешно загружена и проанализирована:")
    print(f"   Заголовок: {article_data['title']}")
    print(f"   Найденные ключевые слова: {article_data['keywords']}")
    print(f"   Фрагмент: {article_data['snippet'][:200]}...")
else:
    print("[X] Не удалось загрузить или найти ключевые слова в статье")

# 4. Проверяем полный поиск за больший период
print("\n4. Проверяем поиск за 7 дней...")
results_7days = parser.search_with_sitemap(
    "https://gtrksakha.ru",
    keywords,
    days=7,
    max_articles=150,
    sitemap_url=sitemap_url
)

congress_found = False
for result in results_7days:
    if "kongress" in result['url'].lower() or "конгресс" in result['title'].lower():
        congress_found = True
        print(f"\n[OK] Статья найдена при поиске за 7 дней:")
        print(f"   Заголовок: {result['title']}")
        print(f"   URL: {result['url']}")
        print(f"   Дата: {result.get('date', 'не указана')}")
        print(f"   Ключевые слова: {result['keywords']}")