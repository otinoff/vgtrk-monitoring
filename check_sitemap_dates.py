"""
Проверка дат в sitemap файле ГТРК Саха
"""

import requests
from xml.etree import ElementTree as ET
from datetime import datetime
from collections import Counter
import warnings

# Отключаем предупреждения SSL
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

def check_sitemap_dates():
    """Анализирует даты в sitemap файле"""
    
    sitemap_url = "https://gtrksakha.ru/sitemap2025.xml"
    
    print(f"[INFO] Загружаем sitemap: {sitemap_url}")
    
    try:
        response = requests.get(sitemap_url, timeout=10, verify=False)
        if response.status_code == 200:
            print("[OK] Sitemap успешно загружен")
            
            # Парсим XML
            root = ET.fromstring(response.text.encode('utf-8'))
            
            # Namespace для sitemap
            namespaces = {
                's': 'http://www.sitemaps.org/schemas/sitemap/0.9'
            }
            
            # Собираем статистику по датам
            dates = []
            total_urls = 0
            
            for url_elem in root.findall('s:url', namespaces):
                total_urls += 1
                lastmod = url_elem.find('s:lastmod', namespaces)
                
                if lastmod is not None:
                    try:
                        # Парсим дату
                        date_str = lastmod.text.split('T')[0]
                        article_date = datetime.strptime(date_str, '%Y-%m-%d')
                        dates.append(article_date)
                    except:
                        pass
            
            print(f"\n[STATS] Общее количество URL в sitemap: {total_urls}")
            
            if dates:
                # Сортируем даты
                dates.sort()
                
                print(f"[INFO] URL с датами: {len(dates)}")
                print(f"[INFO] Самая ранняя дата: {dates[0].strftime('%d.%m.%Y')}")
                print(f"[INFO] Самая поздняя дата: {dates[-1].strftime('%d.%m.%Y')}")
                
                # Статистика по месяцам
                months_counter = Counter()
                for date in dates:
                    month_key = date.strftime('%Y-%m')
                    months_counter[month_key] += 1
                
                print("\n[STATS] Распределение по месяцам:")
                for month, count in sorted(months_counter.items(), reverse=True)[:12]:
                    print(f"   {month}: {count} статей")
                
                # Последние 10 дат
                print("\n[INFO] Последние 10 дат в sitemap:")
                for date in dates[-10:]:
                    print(f"   - {date.strftime('%d.%m.%Y')}")
                    
                # Проверяем, есть ли статьи за последнюю неделю
                today = datetime.now()
                week_ago = today.replace(hour=0, minute=0, second=0, microsecond=0)
                week_ago = week_ago.replace(day=week_ago.day - 7 if week_ago.day > 7 else 1)
                
                recent_articles = [d for d in dates if d >= week_ago]
                print(f"\n[INFO] Статей за последние 7 дней: {len(recent_articles)}")
                
                if recent_articles:
                    print("[INFO] Даты последних статей:")
                    for date in recent_articles:
                        print(f"   - {date.strftime('%d.%m.%Y')}")
                        
            else:
                print("[WARNING] В sitemap не найдены даты статей")
                
            # Проверяем несколько примеров URL
            print("\n[INFO] Примеры URL из sitemap (первые 5):")
            urls_count = 0
            for url_elem in root.findall('s:url', namespaces)[:5]:
                loc = url_elem.find('s:loc', namespaces)
                lastmod = url_elem.find('s:lastmod', namespaces)
                
                if loc is not None:
                    url = loc.text
                    date_str = lastmod.text if lastmod is not None else "Без даты"
                    print(f"   - {date_str}: {url}")
                    urls_count += 1
                    
                if urls_count >= 5:
                    break
                    
        else:
            print(f"[ERROR] Не удалось загрузить sitemap: статус {response.status_code}")
            
    except Exception as e:
        print(f"[ERROR] Ошибка при анализе sitemap: {e}")

def main():
    """Основная функция"""
    print("="*70)
    print("[АНАЛИЗ] Проверка дат в sitemap ГТРК Саха")
    print("="*70)
    
    check_sitemap_dates()
    
    print("\n" + "="*70)
    print("[INFO] Анализ завершен")
    print("="*70)

if __name__ == "__main__":
    main()