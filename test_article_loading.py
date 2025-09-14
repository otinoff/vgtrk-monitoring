#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест загрузки конкретной статьи про Конгресс
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

import requests
from bs4 import BeautifulSoup
from modules.scrapy_parser import ScrapyParser
from modules.advanced_logger import get_logger

# URL статьи
article_url = "https://gtrksakha.ru/news/2025/09/11/kongress-nacionalnoe-zdravoohranenie-projdet-v-nacionalnom-centre-rossiya/"

print("="*60)
print("Тест загрузки статьи")
print("="*60)
print(f"URL: {article_url}")
print()

# Создаем парсер
logger = get_logger()
parser = ScrapyParser(logger=logger)

# 1. Пробуем загрузить через search_in_article
print("1. Загрузка через search_in_article...")
keywords = ["Конгресс", "конгресс", "здравоохранение"]
result = parser.search_in_article(article_url, keywords)

if result:
    print("[OK] Статья загружена успешно!")
    print(f"Заголовок: {result['title']}")
    print(f"Найденные ключевые слова: {result['keywords']}")
    print(f"Фрагмент: {result['snippet'][:200] if result.get('snippet') else 'нет'}")
else:
    print("[X] Статья НЕ загрузилась или ключевые слова не найдены")

# 2. Пробуем загрузить напрямую
print("\n2. Прямая загрузка через requests...")
try:
    response = requests.get(article_url, timeout=10, verify=False)
    print(f"Статус код: {response.status_code}")
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Ищем заголовок
        h1 = soup.find('h1')
        print(f"H1 заголовок: {h1.get_text(strip=True) if h1 else 'не найден'}")
        
        # Ищем контент
        content_found = False
        content_selectors = [
            ('article', None),
            ('div', {'class': 'content'}),
            ('div', {'class': 'article'}),
            ('div', {'class': 'post'}),
            ('div', {'class': 'entry-content'}),
            ('div', {'class': 'single-content'}),
            ('div', {'class': 'post-content'}),
        ]
        
        for tag, attrs in content_selectors:
            elements = soup.find_all(tag, attrs)
            if elements:
                print(f"\nНайден контент в <{tag}> с атрибутами {attrs}:")
                for elem in elements[:1]:  # Берем первый элемент
                    text = elem.get_text(strip=True)[:500]
                    print(f"Превью текста: {text}...")
                    
                    # Проверяем наличие ключевых слов
                    print("\nПроверка ключевых слов:")
                    for keyword in keywords:
                        if keyword.lower() in text.lower():
                            print(f"  [OK] '{keyword}' найдено!")
                        else:
                            print(f"  [X] '{keyword}' НЕ найдено")
                    
                    content_found = True
                    break
            
            if content_found:
                break
        
        if not content_found:
            # Попробуем найти все параграфы
            paragraphs = soup.find_all('p')
            if paragraphs:
                print("\nНайдены параграфы:")
                all_text = ' '.join([p.get_text(strip=True) for p in paragraphs])
                print(f"Всего параграфов: {len(paragraphs)}")
                print(f"Общий текст (первые 500 символов): {all_text[:500]}...")
                
                print("\nПроверка ключевых слов в параграфах:")
                for keyword in keywords:
                    if keyword.lower() in all_text.lower():
                        print(f"  [OK] '{keyword}' найдено!")
                    else:
                        print(f"  [X] '{keyword}' НЕ найдено")
        
    else:
        print(f"[X] Ошибка загрузки: статус код {response.status_code}")
        
except Exception as e:
    print(f"[X] Ошибка при загрузке: {str(e)}")

# 3. Отладка парсера
print("\n" + "="*60)
print("3. Отладка search_in_article")
print("="*60)

# Загружаем страницу вручную и смотрим, что видит парсер
try:
    response = requests.get(article_url, timeout=5, verify=False)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Как парсер ищет заголовок
        title = None
        for tag in ['h1', 'title']:
            elem = soup.find(tag)
            if elem:
                title = elem.get_text(strip=True)
                print(f"Найден заголовок в <{tag}>: {title}")
                break
        
        # Как парсер ищет контент
        content = ""
        content_tags = soup.find_all(['article', 'main', 'div'], 
                                    class_=parser._get_content_class_pattern())
        
        print(f"\nНайдено элементов с классами content|article|post|text|body: {len(content_tags)}")
        
        if content_tags:
            for tag in content_tags:
                paragraphs = tag.find_all('p')
                if paragraphs:
                    content = ' '.join([p.get_text(strip=True) for p in paragraphs])
                    print(f"Найден контент в <{tag.name} class='{tag.get('class')}'>")
                    print(f"Параграфов: {len(paragraphs)}")
                    break
        
        # Если контент не найден, берем все параграфы
        if not content:
            paragraphs = soup.find_all('p')
            content = ' '.join([p.get_text(strip=True) for p in paragraphs[:20]])
            print(f"\nКонтент не найден в специальных тегах, взяты все параграфы: {len(paragraphs)}")
        
        # Проверяем ключевые слова
        full_text = f"{title or ''} {content}".lower()
        print(f"\nПолный текст для поиска: {len(full_text)} символов")
        
        for keyword in keywords:
            if keyword.lower() in full_text:
                print(f"[OK] '{keyword}' найдено в полном тексте")
            else:
                print(f"[X] '{keyword}' НЕ найдено в полном тексте")
                
except Exception as e:
    print(f"Ошибка при отладке: {str(e)}")

def _get_content_class_pattern():
    """Вспомогательная функция для получения паттерна классов"""
    import re
    return re.compile(r'content|article|post|text|body')

parser._get_content_class_pattern = _get_content_class_pattern