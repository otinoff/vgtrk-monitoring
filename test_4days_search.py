#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест поиска за 4 дня
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

from datetime import datetime, timedelta
from modules.scrapy_parser import ScrapyParser
from modules.advanced_logger import get_logger

# Создаем логгер и парсер
logger = get_logger()
parser = ScrapyParser(logger=logger)

# URL сайта и ключевые слова
site_url = "https://gtrksakha.ru"
sitemap_url = "https://gtrksakha.ru/sitemap2025.xml"
keywords = ["Конгресс", "конгресс", "здравоохранение"]

print("="*60)
print("Тест поиска с периодом 4 дня")
print("="*60)

# Вычисляем временной период
now = datetime.now()
date_from_3days = now - timedelta(days=3)
date_from_4days = now - timedelta(days=4)

print(f"Текущее время: {now.strftime('%Y-%m-%d %H:%M')}")
print(f"3 дня назад: {date_from_3days.strftime('%Y-%m-%d %H:%M')}")
print(f"4 дня назад: {date_from_4days.strftime('%Y-%m-%d %H:%M')}")
print()

# Дата статьи про Конгресс
article_date = datetime(2025, 9, 11, 17, 2)
print(f"Статья опубликована: {article_date.strftime('%Y-%m-%d %H:%M')}")

# Проверяем попадание в периоды
hours_passed = (now - article_date).total_seconds() / 3600
print(f"Прошло часов: {hours_passed:.1f}")
print(f"Попадает в 3-дневный период (72 часа): {'ДА' if date_from_3days <= article_date else 'НЕТ'}")
print(f"Попадает в 4-дневный период (96 часов): {'ДА' if date_from_4days <= article_date else 'НЕТ'}")
print()

# Поиск за 4 дня
print("Запускаем поиск за 4 дня...")
results = parser.search_with_sitemap(
    site_url,
    keywords,
    days=4,
    max_articles=50,
    sitemap_url=sitemap_url
)

print(f"\nРезультаты поиска:")
print(f"Найдено статей: {len(results) if results else 0}")

# Ищем статью про Конгресс
congress_found = False
for result in results:
    if "конгресс" in result['title'].lower():
        congress_found = True
        print(f"\n[OK] Статья про Конгресс найдена!")
        print(f"   Заголовок: {result['title']}")
        print(f"   URL: {result['url']}")
        print(f"   Дата: {result.get('date', 'не указана')}")
        print(f"   Ключевые слова: {result['keywords']}")
        break

if not congress_found:
    print("\n[X] Статья про Конгресс НЕ найдена в результатах поиска за 4 дня")