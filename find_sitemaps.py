#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для автоматического поиска sitemap на сайтах филиалов ВГТРК
и заполнения поля sitemap_url в базе данных.

Автор: SnowWhiteAI
Дата: 2025-09-13
"""

import sys
import os
import io

# Устанавливаем кодировку для Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import requests
import sqlite3
import re
from datetime import datetime
from typing import Optional, List, Tuple
from urllib.parse import urljoin, urlparse

# Добавляем путь к модулям
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

# Настройки
DB_PATH = "data/vgtrk_monitoring.db"
TIMEOUT = 10  # Таймаут для запросов в секундах

# Стандартные пути для поиска sitemap
SITEMAP_PATHS = [
    "/sitemap.xml",
    "/sitemap_index.xml", 
    "/sitemap2025.xml",  # Как у Якутии
    "/sitemap2024.xml",  # На случай если есть за прошлый год
    "/news-sitemap.xml",
    "/post-sitemap.xml",
    "/yandex-turbo-sitemap.xml",
    "/sitemap/sitemap.xml",
    "/sitemaps/sitemap.xml"
]


class SitemapFinder:
    """Класс для поиска sitemap на сайтах"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.results = []
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def find_sitemap_in_robots(self, base_url: str) -> Optional[str]:
        """
        Ищет sitemap в robots.txt
        
        Args:
            base_url: Базовый URL сайта
            
        Returns:
            URL sitemap или None
        """
        try:
            robots_url = urljoin(base_url, '/robots.txt')
            print(f"  Проверяем robots.txt: {robots_url}")
            
            response = self.session.get(robots_url, timeout=TIMEOUT, verify=False)
            if response.status_code == 200:
                # Ищем строки с Sitemap:
                for line in response.text.split('\n'):
                    if 'sitemap:' in line.lower():
                        # Извлекаем URL после Sitemap:
                        sitemap_url = line.split(':', 1)[1].strip()
                        print(f"  [OK] Найден в robots.txt: {sitemap_url}")
                        
                        # Проверяем, что sitemap действительно существует
                        try:
                            check_response = self.session.get(sitemap_url, timeout=TIMEOUT, verify=False)
                            if check_response.status_code == 200 and 'xml' in check_response.text[:100].lower():
                                return sitemap_url
                        except:
                            pass
        except Exception as e:
            print(f"  [WARN] Ошибка при проверке robots.txt: {e}")
        
        return None
    
    def check_standard_paths(self, base_url: str) -> Optional[str]:
        """
        Проверяет стандартные пути для sitemap
        
        Args:
            base_url: Базовый URL сайта
            
        Returns:
            URL sitemap или None
        """
        for path in SITEMAP_PATHS:
            try:
                sitemap_url = urljoin(base_url, path)
                print(f"  Проверяем: {sitemap_url}")
                
                response = self.session.get(sitemap_url, timeout=TIMEOUT, verify=False)
                if response.status_code == 200:
                    # Проверяем, что это действительно XML
                    if 'xml' in response.text[:100].lower() or '<urlset' in response.text[:500]:
                        print(f"  [OK] Найден: {sitemap_url}")
                        return sitemap_url
            except Exception as e:
                continue
        
        return None
    
    def process_filial(self, filial: dict) -> Tuple[int, str, Optional[str], str]:
        """
        Обрабатывает один филиал
        
        Args:
            filial: Словарь с данными филиала
            
        Returns:
            Кортеж (id, name, sitemap_url, status)
        """
        filial_id = filial['id']
        name = filial['name']
        website = filial.get('website_url') or filial.get('website')
        
        print(f"\n[SCAN] Обрабатываем: {name}")
        
        if not website:
            print(f"  [X] Нет сайта")
            return (filial_id, name, None, "Нет сайта")
        
        # Добавляем протокол если нет
        if not website.startswith(('http://', 'https://')):
            website = f"https://{website}"
        
        print(f"  Сайт: {website}")
        
        # Если уже есть sitemap_url, пропускаем
        if filial.get('sitemap_url'):
            print(f"  [INFO] Уже есть sitemap: {filial['sitemap_url']}")
            return (filial_id, name, filial['sitemap_url'], "Уже есть")
        
        # 1. Сначала проверяем robots.txt
        sitemap_url = self.find_sitemap_in_robots(website)
        
        # 2. Если не нашли, проверяем стандартные пути
        if not sitemap_url:
            sitemap_url = self.check_standard_paths(website)
        
        if sitemap_url:
            return (filial_id, name, sitemap_url, "Найден")
        else:
            print(f"  [X] Sitemap не найден")
            return (filial_id, name, None, "Не найден")
    
    def get_filials_from_db(self) -> List[dict]:
        """
        Получает список филиалов из БД
        
        Returns:
            Список филиалов
        """
        filials = []
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, name, website_url, sitemap_url, federal_district, region
                    FROM filials
                    WHERE is_active = 1
                    ORDER BY federal_district, name
                """)
                
                for row in cursor.fetchall():
                    filials.append({
                        'id': row[0],
                        'name': row[1],
                        'website_url': row[2],
                        'sitemap_url': row[3],
                        'federal_district': row[4],
                        'region': row[5]
                    })
        except Exception as e:
            print(f"[ERROR] Ошибка при чтении БД: {e}")
        
        return filials
    
    def update_sitemap_in_db(self, filial_id: int, sitemap_url: str):
        """
        Обновляет sitemap_url в БД
        
        Args:
            filial_id: ID филиала
            sitemap_url: URL sitemap
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE filials
                    SET sitemap_url = ?
                    WHERE id = ?
                """, (sitemap_url, filial_id))
                conn.commit()
                print(f"  [SAVED] Сохранено в БД")
        except Exception as e:
            print(f"  [ERROR] Ошибка при сохранении в БД: {e}")
    
    def run(self, auto_save: bool = False):
        """
        Запускает процесс поиска sitemap
        
        Args:
            auto_save: Автоматически сохранять найденные sitemap в БД
        """
        print("=" * 60)
        print("ПОИСК SITEMAP ДЛЯ ФИЛИАЛОВ ВГТРК")
        print("=" * 60)
        
        # Получаем филиалы из БД
        filials = self.get_filials_from_db()
        print(f"\n[STAT] Найдено филиалов: {len(filials)}")
        
        # Статистика
        stats = {
            'total': len(filials),
            'found': 0,
            'not_found': 0,
            'no_website': 0,
            'already_has': 0,
            'errors': 0
        }
        
        # Обрабатываем каждый филиал
        for i, filial in enumerate(filials, 1):
            print(f"\n[{i}/{len(filials)}]", end="")
            
            try:
                filial_id, name, sitemap_url, status = self.process_filial(filial)
                
                # Сохраняем результат
                self.results.append({
                    'id': filial_id,
                    'name': name,
                    'sitemap_url': sitemap_url,
                    'status': status
                })
                
                # Обновляем статистику
                if status == "Найден":
                    stats['found'] += 1
                    if auto_save:
                        self.update_sitemap_in_db(filial_id, sitemap_url)
                elif status == "Не найден":
                    stats['not_found'] += 1
                elif status == "Нет сайта":
                    stats['no_website'] += 1
                elif status == "Уже есть":
                    stats['already_has'] += 1
                    
            except Exception as e:
                print(f"  [ERROR] Ошибка: {e}")
                stats['errors'] += 1
        
        # Выводим итоговую статистику
        self.print_summary(stats)
        
        # Предлагаем сохранить результаты
        if not auto_save and stats['found'] > 0:
            self.offer_to_save()
    
    def print_summary(self, stats: dict):
        """Выводит итоговую статистику"""
        print("\n")
        print("=" * 60)
        print("ИТОГОВАЯ СТАТИСТИКА")
        print("=" * 60)
        print(f"Всего филиалов:     {stats['total']}")
        print(f"[OK] Найдено sitemap:  {stats['found']}")
        print(f"[X] Не найдено:       {stats['not_found']}")
        print(f"[*] Уже есть в БД:    {stats['already_has']}")
        print(f"[-] Нет сайта:        {stats['no_website']}")
        print(f"[!] Ошибки:          {stats['errors']}")
        print("=" * 60)
        
        # Выводим найденные sitemap
        if stats['found'] > 0:
            print("\n[OK] НАЙДЕННЫЕ SITEMAP:")
            print("-" * 60)
            for result in self.results:
                if result['status'] == "Найден":
                    print(f"{result['name']}")
                    print(f"  -> {result['sitemap_url']}")
    
    def offer_to_save(self):
        """Предлагает сохранить найденные sitemap в БД"""
        print("\n" + "=" * 60)
        answer = input("Сохранить найденные sitemap в базу данных? (y/n): ")
        
        if answer.lower() in ['y', 'yes', 'да', 'д']:
            saved_count = 0
            for result in self.results:
                if result['status'] == "Найден":
                    self.update_sitemap_in_db(result['id'], result['sitemap_url'])
                    saved_count += 1
            
            print(f"\n[OK] Сохранено {saved_count} записей в БД")
        else:
            print("\n[CANCELLED] Отменено. Данные не сохранены.")


def main():
    """Главная функция"""
    # Отключаем предупреждения о SSL
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # Проверяем наличие БД
    if not os.path.exists(DB_PATH):
        print(f"[ERROR] База данных не найдена: {DB_PATH}")
        return
    
    # Создаем объект поиска
    finder = SitemapFinder(DB_PATH)
    
    # Проверяем аргументы командной строки
    auto_save = '--auto' in sys.argv or '-a' in sys.argv
    
    if auto_save:
        print("[AUTO] Режим автосохранения включен")
    
    # Запускаем поиск
    try:
        finder.run(auto_save=auto_save)
    except KeyboardInterrupt:
        print("\n\n[CANCELLED] Прервано пользователем")
    except Exception as e:
        print(f"\n[CRITICAL ERROR] Критическая ошибка: {e}")


if __name__ == "__main__":
    main()