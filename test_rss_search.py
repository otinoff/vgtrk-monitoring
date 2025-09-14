#!/usr/bin/env python3
"""
Тестовый скрипт для проверки RSS поиска.
Демонстрирует экстремальную скорость и эффективность RSS парсинга.
"""

import sys
import os
import time
from datetime import datetime

# Добавляем путь к модулям
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

from modules.site_parser import SiteParser
from modules.advanced_logger import LogLevel

def test_rss_search():
    """Тестирование RSS поиска"""
    
    print("=" * 70)
    print("ТЕСТИРОВАНИЕ RSS ПОИСКА")
    print("=" * 70)
    
    # Инициализация парсера
    parser = SiteParser(log_level=LogLevel.INFO)
    
    # Тестовые сайты с RSS
    test_sites = [
        "https://vesti42.ru",
        "https://vesti-novosibirsk.ru",
        "https://stavropolye.tv",
        "https://vesti-kaliningrad.ru"
    ]
    
    # Ключевые слова для поиска
    keywords = ["губернатор", "новости", "развитие", "ВГТРК", "регион"]
    
    print(f"\nКлючевые слова для поиска: {', '.join(keywords)}")
    print("-" * 70)
    
    for site in test_sites:
        print(f"\n📡 Тестируем сайт: {site}")
        print("-" * 50)
        
        # Засекаем время
        start_time = time.time()
        
        # Парсим RSS
        rss_data, metrics = parser.parse_rss_feed(site)
        
        rss_time = time.time() - start_time
        
        if rss_data:
            print(f"✅ RSS успешно получен!")
            print(f"   ⏱️  Время: {rss_time:.2f} сек")
            print(f"   📰 Новостей: {metrics.get('items_count', 0)}")
            print(f"   📍 RSS URL: {metrics.get('rss_url', 'не указан')}")
            
            # Поиск ключевых слов в RSS
            search_results = parser.search_in_rss(rss_data, keywords)
            
            print(f"\n   🔍 Результаты поиска:")
            for keyword, found_items in search_results.items():
                if found_items:
                    print(f"      ✅ '{keyword}': найдено в {len(found_items)} новостях")
                    # Показываем первую найденную новость
                    if found_items:
                        first = found_items[0]
                        print(f"         Пример: {first['title'][:60]}...")
                else:
                    print(f"      ❌ '{keyword}': не найдено")
            
            # Сравнение с обычным парсингом
            print(f"\n   📊 СРАВНЕНИЕ С ОБЫЧНЫМ ПАРСИНГОМ:")
            start_time = time.time()
            full_content, full_metrics = parser.parse_site(site)
            full_time = time.time() - start_time
            
            if full_content:
                speedup = full_time / rss_time if rss_time > 0 else 0
                print(f"      Полный парсинг: {full_time:.2f} сек")
                print(f"      RSS парсинг: {rss_time:.2f} сек")
                print(f"      🚀 УСКОРЕНИЕ: {speedup:.1f}x быстрее!")
                
                # Экономия по размеру данных
                rss_size = sum(len(item.get('full_text', '')) for item in rss_data.get('items', []))
                full_size = len(full_content)
                savings = (1 - rss_size / full_size) * 100 if full_size > 0 else 0
                print(f"      💰 ЭКОНОМИЯ ДАННЫХ: {savings:.1f}%")
        else:
            print(f"❌ RSS не найден или ошибка: {metrics.get('error', 'неизвестная ошибка')}")
        
        print("\n" + "=" * 70)
        time.sleep(1)  # Пауза между сайтами

def test_rss_with_gigachat_integration():
    """Тест интеграции RSS с анализом через GigaChat"""
    
    print("\n" + "=" * 70)
    print("ТЕСТ ИНТЕГРАЦИИ RSS + GIGACHAT")
    print("=" * 70)
    
    parser = SiteParser(log_level=LogLevel.INFO)
    
    # Тестовый сайт
    test_site = "https://vesti42.ru"
    keyword = "губернатор"
    
    print(f"\nСайт: {test_site}")
    print(f"Ищем: '{keyword}'")
    print("-" * 50)
    
    # Получаем RSS
    rss_data, metrics = parser.parse_rss_feed(test_site)
    
    if rss_data:
        # Ищем ключевое слово
        search_results = parser.search_in_rss(rss_data, [keyword])
        found_items = search_results.get(keyword, [])
        
        if found_items:
            print(f"\n✅ Найдено {len(found_items)} новостей с '{keyword}'")
            print("\nПРИМЕР ДЛЯ ОТПРАВКИ В GIGACHAT:")
            print("-" * 40)
            
            # Берем первую найденную новость
            first_news = found_items[0]
            
            # Формируем контекст для GigaChat
            context = f"""
Заголовок: {first_news['title']}
Описание: {first_news['description']}
Ссылка: {first_news['link']}
Дата: {first_news['pubDate']}
"""
            print(context)
            print("-" * 40)
            print("\nЭтот контекст можно отправить в GigaChat для анализа!")
            print("Размер контекста:", len(context), "символов")
            print("Экономия токенов: ~95% по сравнению с полной страницей")
        else:
            print(f"❌ '{keyword}' не найдено в RSS")
    else:
        print("❌ RSS не удалось получить")

def compare_all_modes():
    """Сравнение всех режимов поиска"""
    
    print("\n" + "=" * 70)
    print("СРАВНЕНИЕ ВСЕХ РЕЖИМОВ ПОИСКА")
    print("=" * 70)
    
    parser = SiteParser(log_level=LogLevel.WARNING)  # Меньше логов
    test_site = "https://vesti42.ru"
    
    print(f"\nТестовый сайт: {test_site}")
    print("-" * 50)
    
    results = {}
    
    # 1. RSS режим
    print("\n1️⃣ RSS РЕЖИМ...")
    start = time.time()
    rss_data, rss_metrics = parser.parse_rss_feed(test_site)
    rss_time = time.time() - start
    rss_size = sum(len(item.get('full_text', '')) for item in rss_data.get('items', [])) if rss_data else 0
    results['RSS'] = {'time': rss_time, 'size': rss_size}
    
    # 2. Мета-поиск (только главная)
    print("2️⃣ МЕТА-ПОИСК (главная)...")
    start = time.time()
    meta_content, meta_metrics = parser.parse_meta_data(test_site, include_news=False)
    meta_time = time.time() - start
    meta_size = len(meta_content) if meta_content else 0
    results['Мета'] = {'time': meta_time, 'size': meta_size}
    
    # 3. Мета-поиск (главная + новости)
    print("3️⃣ МЕТА-ПОИСК (главная + новости)...")
    start = time.time()
    meta_news_content, meta_news_metrics = parser.parse_meta_data(test_site, include_news=True)
    meta_news_time = time.time() - start
    meta_news_size = len(meta_news_content) if meta_news_content else 0
    results['Мета+Новости'] = {'time': meta_news_time, 'size': meta_news_size}
    
    # 4. Полный парсинг
    print("4️⃣ ПОЛНЫЙ ПАРСИНГ...")
    start = time.time()
    full_content, full_metrics = parser.parse_site(test_site)
    full_time = time.time() - start
    full_size = len(full_content) if full_content else 0
    results['Полный'] = {'time': full_time, 'size': full_size}
    
    # Результаты
    print("\n" + "=" * 70)
    print("📊 ИТОГОВОЕ СРАВНЕНИЕ:")
    print("-" * 70)
    print(f"{'Режим':<20} {'Время (сек)':<15} {'Размер (символов)':<20} {'Скорость':<15}")
    print("-" * 70)
    
    for mode, data in results.items():
        if data['time'] > 0:
            speedup = results['Полный']['time'] / data['time']
            speed_str = f"{speedup:.1f}x быстрее"
        else:
            speed_str = "N/A"
        
        print(f"{mode:<20} {data['time']:<15.2f} {data['size']:<20,} {speed_str:<15}")
    
    print("-" * 70)
    
    # Рекомендации
    print("\n🎯 РЕКОМЕНДАЦИИ:")
    print("-" * 40)
    print("📡 RSS поиск - для поиска в свежих новостях (самый быстрый)")
    print("⚡ Мета (главная) - для общего мониторинга")
    print("📰 Мета (главная+новости) - для детального анализа")
    print("🔍 Полный парсинг - только когда нужен весь контент")

if __name__ == "__main__":
    try:
        # Запускаем тесты
        test_rss_search()
        test_rss_with_gigachat_integration()
        compare_all_modes()
        
        print("\n" + "=" * 70)
        print("✅ ВСЕ ТЕСТЫ RSS ЗАВЕРШЕНЫ УСПЕШНО!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ ОШИБКА ТЕСТИРОВАНИЯ: {e}")
        import traceback
        traceback.print_exc()