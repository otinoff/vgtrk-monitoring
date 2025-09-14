#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестовый скрипт для проверки поиска конкретной статьи
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

from modules.scrapy_parser import ScrapyParser
from modules.advanced_logger import get_logger, LogLevel
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup

def test_article_search():
    """Тестируем поиск статьи про Конгресс"""
    
    # URL статьи
    article_url = "https://gtrksakha.ru/news/2025/09/11/kongress-nacionalnoe-zdravoohranenie-projdet-v-nacionalnom-centre-rossiya/"
    
    # Загружаем страницу
    print(f"Загружаем статью: {article_url}")
    response = requests.get(article_url, timeout=10, verify=False)
    
    if response.status_code != 200:
        print(f"Ошибка загрузки: {response.status_code}")
        return
        
    # Парсим страницу
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Ищем заголовок
    title = None
    h1 = soup.find('h1')
    if h1:
        title = h1.get_text(strip=True)
        print(f"\nЗаголовок H1: {title}")
    
    title_tag = soup.find('title')
    if title_tag:
        print(f"Title тег: {title_tag.get_text(strip=True)}")
    
    # Ищем контент
    content = ""
    article_tag = soup.find('article')
    if article_tag:
        paragraphs = article_tag.find_all('p')
        content = ' '.join([p.get_text(strip=True) for p in paragraphs])
        print(f"\nКонтент статьи (первые 500 символов):\n{content[:500]}...")
    
    # Проверяем поиск ключевых слов
    full_text = f"{title or ''} {content}".lower()
    print(f"\nДлина полного текста: {len(full_text)} символов")
    
    # Тестируем разные варианты поиска
    test_keywords = [
        "Конгресс",
        "конгресс", 
        "Национальное здравоохранение",
        "здравоохранение",
        "Россия"
    ]
    
    print("\nПоиск ключевых слов:")
    for keyword in test_keywords:
        found = keyword.lower() in full_text
        print(f"- '{keyword}': {'НАЙДЕНО' if found else 'НЕ НАЙДЕНО'}")
        
        if found:
            # Показываем контекст
            pos = full_text.find(keyword.lower())
            start = max(0, pos - 50)
            end = min(len(full_text), pos + 50 + len(keyword))
            context = full_text[start:end]
            print(f"  Контекст: ...{context}...")

def test_sitemap_search():
    """Тестируем поиск через Sitemap"""
    logger = get_logger(LogLevel.INFO)
    parser = ScrapyParser(logger=logger)
    
    # Параметры поиска
    site_url = "https://gtrksakha.ru"
    sitemap_url = "https://gtrksakha.ru/sitemap2025.xml"
    keywords = ["Конгресс", "конгресс", "здравоохранение"]
    days = 3
    
    print(f"\n{'='*60}")
    print(f"Тестируем поиск через Sitemap")
    print(f"Сайт: {site_url}")
    print(f"Sitemap: {sitemap_url}")
    print(f"Ключевые слова: {keywords}")
    print(f"Период: {days} дней")
    print(f"{'='*60}\n")
    
    # Запускаем поиск
    results = parser.search_with_sitemap(
        site_url=site_url,
        keywords=keywords,
        days=days,
        max_articles=50,
        sitemap_url=sitemap_url
    )
    
    print(f"\nНайдено статей: {len(results)}")
    
    if results:
        print("\nНайденные статьи:")
        for i, article in enumerate(results, 1):
            date_str = article['date'].strftime('%d.%m.%Y') if article.get('date') else 'Дата неизвестна'
            print(f"\n{i}. {article['title']}")
            print(f"   Дата: {date_str}")
            print(f"   URL: {article['url']}")
            print(f"   Ключевые слова: {', '.join(article['keywords'])}")

def check_date_filter():
    """Проверяем фильтр дат"""
    print(f"\n{'='*60}")
    print("Проверка фильтра дат")
    print(f"{'='*60}\n")
    
    # Текущее время
    now = datetime.now()
    print(f"Текущее время: {now}")
    
    # Для 3 дней
    days = 3
    date_from = now - timedelta(days=days)
    print(f"\nПоиск за {days} дней:")
    print(f"От: {date_from} (включительно)")
    print(f"До: {now} (включительно)")
    
    # Проверяем, попадает ли статья от 11 сентября
    article_date = datetime(2025, 9, 11)
    print(f"\nДата статьи: {article_date}")
    print(f"Попадает в диапазон: {date_from <= article_date <= now}")

if __name__ == "__main__":
    # 1. Проверяем конкретную статью
    test_article_search()
    
    # 2. Проверяем фильтр дат
    check_date_filter()
    
    # 3. Проверяем поиск через Sitemap
    test_sitemap_search()