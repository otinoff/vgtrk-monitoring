#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Проверка наличия конкретной статьи в sitemap
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

import requests
from xml.etree import ElementTree as ET
from datetime import datetime

# URL статьи про Конгресс
target_url = "https://gtrksakha.ru/news/2025/09/11/kongress-nacionalnoe-zdravoohranenie-projdet-v-nacionalnom-centre-rossiya/"

print("="*60)
print("Проверка наличия статьи в sitemap")
print("="*60)
print(f"Ищем URL: {target_url}")
print()

# Загружаем sitemap
sitemap_url = "https://gtrksakha.ru/sitemap2025.xml"
print(f"Проверяем sitemap: {sitemap_url}")

response = requests.get(sitemap_url, verify=False)
if response.status_code != 200:
    print(f"Ошибка загрузки sitemap: {response.status_code}")
    exit(1)

# Парсим XML
root = ET.fromstring(response.content)

# Определяем namespace
if 'xmlns="https://www.sitemaps.org' in response.text:
    ns = {'s': 'https://www.sitemaps.org/schemas/sitemap/0.9'}
else:
    ns = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

# Ищем URL
found = False
all_urls = []
september_11_urls = []

for url_elem in root.findall('s:url', ns):
    loc = url_elem.find('s:loc', ns)
    if loc is not None:
        url = loc.text
        all_urls.append(url)
        
        # Проверяем точное совпадение
        if url == target_url:
            found = True
            lastmod = url_elem.find('s:lastmod', ns)
            print(f"[OK] Статья НАЙДЕНА в sitemap!")
            print(f"URL: {url}")
            if lastmod is not None:
                print(f"Дата изменения: {lastmod.text}")
            break
        
        # Собираем все URL от 11 сентября
        if "/2025/09/11/" in url:
            september_11_urls.append(url)

if not found:
    print(f"[X] Статья НЕ найдена в sitemap")
    print(f"\nВсего URL в sitemap: {len(all_urls)}")
    print(f"\nСтатей от 11 сентября: {len(september_11_urls)}")
    
    if september_11_urls:
        print("\nСписок всех статей от 11 сентября:")
        for i, url in enumerate(september_11_urls, 1):
            print(f"{i}. {url}")
            if "kongress" in url.lower() or "конгресс" in url.lower():
                print("   ^ Похоже на нужную статью!")

# Проверим другие возможные sitemap файлы
print("\n" + "="*60)
print("Проверка других возможных sitemap файлов")
print("="*60)

other_sitemaps = [
    "https://gtrksakha.ru/sitemap.xml",
    "https://gtrksakha.ru/sitemap_index.xml",
    "https://gtrksakha.ru/sitemap2024.xml",
    "https://gtrksakha.ru/news-sitemap.xml"
]

for sitemap in other_sitemaps:
    try:
        resp = requests.get(sitemap, timeout=5, verify=False)
        if resp.status_code == 200:
            print(f"[OK] Найден: {sitemap}")
            # Можно добавить поиск статьи в этом sitemap
        else:
            print(f"[X] Не найден: {sitemap} (код {resp.status_code})")
    except Exception as e:
        print(f"[X] Ошибка: {sitemap} - {str(e)}")