"""
Тест для проверки парсинга sitemap ГТРК Саха
Проверяем почему не находится статья от 11 сентября 2024
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.scrapy_parser import ScrapyParser
from datetime import datetime, timedelta
import requests

def test_sakha_sitemap():
    """Тестирует sitemap ГТРК Саха"""
    
    print("=" * 60)
    print("ТЕСТ SITEMAP ГТРК САХА")
    print("=" * 60)
    
    # Создаем парсер
    parser = ScrapyParser()
    
    # Сайт ГТРК Саха
    site_url = "https://gtrksakha.ru"
    
    print(f"\n[>] Проверяем сайт: {site_url}")
    
    # 1. Находим sitemap
    print("\n1. Поиск sitemap...")
    sitemap_data = parser.find_sitemap(site_url)
    
    if sitemap_data:
        sitemap_url, xml_content = sitemap_data
        print(f"[OK] Sitemap найден: {sitemap_url}")
        print(f"   Размер: {len(xml_content)} символов")
        
        # 2. Парсим URL БЕЗ фильтрации по датам
        print("\n2. Парсинг всех URL из sitemap (без фильтра дат)...")
        all_articles = parser.parse_sitemap_urls(xml_content)
        print(f"[OK] Всего URL в sitemap: {len(all_articles)}")
        
        # Показываем примеры URL
        if all_articles:
            print("\n   Примеры URL (первые 10):")
            for i, article in enumerate(all_articles[:10], 1):
                date_str = article['date'].strftime('%Y-%m-%d') if article['date'] else 'без даты'
                print(f"   {i}. {date_str}: {article['url'][:80]}...")
            
            # Ищем статьи за сентябрь 2024
            print("\n3. Фильтруем статьи за сентябрь 2024...")
            sept_2024_articles = []
            for article in all_articles:
                if article['date']:
                    if article['date'].year == 2024 and article['date'].month == 9:
                        sept_2024_articles.append(article)
            
            print(f"[OK] Найдено статей за сентябрь 2024: {len(sept_2024_articles)}")
            
            if sept_2024_articles:
                print("\n   Статьи за сентябрь 2024:")
                for article in sept_2024_articles[:20]:
                    date_str = article['date'].strftime('%Y-%m-%d')
                    print(f"   - {date_str}: {article['url'][:70]}...")
                
                # Ищем конкретную статью про конгресс
                print("\n4. Ищем статью про конгресс здравоохранения...")
                keywords = ["конгресс", "здравоохранение", "национальное"]
                
                for article in sept_2024_articles:
                    # Проверяем URL на ключевые слова
                    url_lower = article['url'].lower()
                    if any(kw in url_lower for kw in keywords):
                        print(f"[!] Возможная статья: {article['url']}")
                        
                        # Пробуем загрузить и проверить
                        try:
                            resp = requests.get(article['url'], timeout=5, verify=False)
                            if resp.status_code == 200:
                                text_lower = resp.text.lower()
                                if "конгресс" in text_lower and "здравоохранение" in text_lower:
                                    print(f"[OK] НАЙДЕНА СТАТЬЯ ПРО КОНГРЕСС!")
                                    print(f"   URL: {article['url']}")
                                    print(f"   Дата: {article['date']}")
                                    
                                    # Извлекаем заголовок
                                    from bs4 import BeautifulSoup
                                    soup = BeautifulSoup(resp.text, 'html.parser')
                                    title = soup.find('h1')
                                    if title:
                                        print(f"   Заголовок: {title.text.strip()}")
                        except:
                            pass
        else:
            print("[WARNING] Sitemap пустой!")
        
        # 5. Тестируем поиск за правильный период
        print("\n5. Тестируем поиск за период (7-14 сентября 2024)...")
        date_from = datetime(2024, 9, 7)
        date_to = datetime(2024, 9, 14)
        
        filtered_articles = parser.parse_sitemap_urls(xml_content, date_from, date_to)
        print(f"[OK] Найдено статей за 7-14 сентября 2024: {len(filtered_articles)}")
        
        if filtered_articles:
            print("\n   Статьи за этот период:")
            for article in filtered_articles[:10]:
                date_str = article['date'].strftime('%Y-%m-%d') if article['date'] else 'без даты'
                print(f"   - {date_str}: {article['url'][:70]}...")
    else:
        print("[ERROR] Sitemap не найден")
    
    print("\n" + "=" * 60)
    print("ТЕСТ ЗАВЕРШЕН")
    print("=" * 60)

if __name__ == "__main__":
    print("\n>>> ТЕСТ SITEMAP ГТРК САХА\n")
    test_sakha_sitemap()