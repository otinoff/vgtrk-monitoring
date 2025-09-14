#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Проверка порядка статей в sitemap и позиции статьи про Конгресс
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

from datetime import datetime, timedelta
from modules.scrapy_parser import ScrapyParser
from modules.advanced_logger import get_logger

# Создаем парсер
logger = get_logger()
parser = ScrapyParser(logger=logger)

# Параметры поиска
site_url = "https://gtrksakha.ru"
sitemap_url = "https://gtrksakha.ru/sitemap2025.xml"
congress_url = "https://gtrksakha.ru/news/2025/09/11/kongress-nacionalnoe-zdravoohranenie-projdet-v-nacionalnom-centre-rossiya/"

print("="*60)
print("Анализ порядка статей в sitemap")
print("="*60)

# Загружаем sitemap
sitemap_data = parser.find_sitemap(site_url, sitemap_url)
if sitemap_data:
    _, xml_content = sitemap_data
    
    # Парсим URL с фильтром по датам (4 дня)
    date_to = datetime.now()
    date_from = date_to - timedelta(days=4)
    
    print(f"Период поиска: {date_from.strftime('%Y-%m-%d')} - {date_to.strftime('%Y-%m-%d')}")
    
    articles = parser.parse_sitemap_urls(xml_content, date_from, date_to)
    print(f"\nВсего найдено статей за период: {len(articles)}")
    
    # Ищем позицию статьи про Конгресс
    congress_position = None
    for i, article in enumerate(articles):
        if article['url'] == congress_url:
            congress_position = i + 1
            print(f"\n[OK] Статья про Конгресс найдена на позиции: {congress_position}")
            print(f"URL: {article['url']}")
            print(f"Дата: {article.get('date', 'не указана')}")
            break
    
    if congress_position is None:
        print("\n[X] Статья про Конгресс НЕ найдена в списке!")
    else:
        if congress_position > 50:
            print(f"\n⚠️ ВНИМАНИЕ: Статья находится на позиции {congress_position}, но проверяются только первые 50!")
            print("Это объясняет, почему статья не была найдена при поиске.")
    
    # Показываем первые 10 и последние 10 статей
    print("\n" + "="*60)
    print("Первые 10 статей:")
    print("="*60)
    for i, article in enumerate(articles[:10]):
        date_str = article['date'].strftime('%Y-%m-%d %H:%M') if article.get('date') else 'нет даты'
        print(f"{i+1}. [{date_str}] {article['url']}")
    
    if len(articles) > 20:
        print("\n...")
        print(f"\nПоследние 10 статей (из {len(articles)}):")
        print("="*60)
        start_idx = len(articles) - 10
        for i, article in enumerate(articles[-10:], start=start_idx+1):
            date_str = article['date'].strftime('%Y-%m-%d %H:%M') if article.get('date') else 'нет даты'
            print(f"{i}. [{date_str}] {article['url']}")
    
    # Анализ распределения по датам
    print("\n" + "="*60)
    print("Распределение статей по датам:")
    print("="*60)
    date_counts = {}
    for article in articles:
        if article.get('date'):
            date_key = article['date'].strftime('%Y-%m-%d')
            date_counts[date_key] = date_counts.get(date_key, 0) + 1
    
    for date_key in sorted(date_counts.keys(), reverse=True):
        print(f"{date_key}: {date_counts[date_key]} статей")