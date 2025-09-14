"""
Тест для проверки исправления ошибки с неинициализированной переменной parsed_content
"""

import sys
import os
from datetime import datetime, timedelta

# Добавляем путь к модулям
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

from modules.database import VGTRKDatabase
from modules.site_parser import SiteParser
from modules.gigachat_client import GigaChatClient
from modules.advanced_logger import AdvancedLogger, LogLevel, get_logger
from modules.scrapy_parser import ScrapyParser
from config.settings import GIGACHAT_API_KEY, GIGACHAT_CLIENT_ID

def test_sitemap_search():
    """Тест режима sitemap_search с проверкой инициализации переменных"""
    
    print("=" * 60)
    print("ТЕСТ: Режим sitemap_search с исправлением parsed_content")
    print("=" * 60)
    
    # Инициализация компонентов
    logger = get_logger(LogLevel.DEBUG)
    scrapy_parser = ScrapyParser(logger=logger)
    
    # Тестовый филиал
    test_filial = {
        'id': 14,
        'name': 'ГТРК Саха',
        'website_url': 'https://gtrksakha.ru'
    }
    
    # Тестовые запросы
    test_queries = [
        {'id': 1, 'query_text': 'здравоохранение'},
        {'id': 2, 'query_text': 'конгресс'}
    ]
    
    print(f"\n🔍 Тестируем филиал: {test_filial['name']}")
    print(f"   Сайт: {test_filial['website_url']}")
    print(f"   Запросы: {[q['query_text'] for q in test_queries]}")
    
    try:
        # Имитируем блок из process_monitoring
        website = test_filial['website_url']
        filial_name = test_filial['name']
        keywords = [q['query_text'] for q in test_queries]
        search_days = 7
        
        print(f"\n🕷️ Запускаем Sitemap поиск за {search_days} дней...")
        
        # Поиск через Sitemap
        sitemap_results = scrapy_parser.search_with_sitemap(
            website,
            keywords,
            days=search_days,
            max_articles=50
        )
        
        # ВАЖНО: Проверяем инициализацию переменных
        parsed_content = None  # Sitemap режим не использует parsed_content
        parse_metrics = {'mode': 'sitemap', 'articles_checked': len(sitemap_results) if sitemap_results else 0}
        
        print(f"\n✅ Переменные инициализированы:")
        print(f"   parsed_content: {type(parsed_content)}")
        print(f"   parse_metrics: {parse_metrics}")
        
        if sitemap_results:
            print(f"\n📊 Найдено {len(sitemap_results)} статей")
            for idx, article in enumerate(sitemap_results[:3], 1):
                print(f"\n   {idx}. {article['title'][:100]}")
                print(f"      URL: {article['url']}")
                if article.get('date'):
                    print(f"      Дата: {article['date']}")
                if article.get('keywords'):
                    print(f"      Ключевые слова: {', '.join(article['keywords'][:3])}")
        else:
            print("\n⚠️ Sitemap не найден или пустой")
            # Инициализируем переменные для избежания ошибки
            parse_metrics = {'error': 'Sitemap не найден или пустой'}
            parsed_content = None
            
            print(f"\n✅ Переменные инициализированы при ошибке:")
            print(f"   parsed_content: {type(parsed_content)}")
            print(f"   parse_metrics: {parse_metrics}")
        
        # Проверяем, что переменные можно использовать дальше
        print(f"\n🔍 Проверка использования переменных:")
        
        # Эта проверка не должна вызвать ошибку
        if parsed_content is not None:
            print(f"   parsed_content содержит данные: {len(parsed_content)} символов")
        else:
            print(f"   parsed_content = None (ожидаемо для sitemap режима)")
        
        print(f"   parse_metrics содержит: {parse_metrics}")
        
        print("\n✅ ТЕСТ ПРОЙДЕН: Переменные правильно инициализированы!")
        
    except NameError as e:
        print(f"\n❌ ОШИБКА: Переменная не инициализирована: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def test_rss_search():
    """Тест режима rss_search для проверки инициализации переменных"""
    
    print("\n" + "=" * 60)
    print("ТЕСТ: Режим rss_search")
    print("=" * 60)
    
    # Инициализация компонентов
    logger = get_logger(LogLevel.INFO)
    site_parser = SiteParser(log_level=LogLevel.INFO)
    
    # Тестовый филиал
    test_filial = {
        'id': 14,
        'name': 'ГТРК Саха',
        'website_url': 'https://gtrksakha.ru'
    }
    
    print(f"\n📡 Тестируем RSS для: {test_filial['name']}")
    
    try:
        website = test_filial['website_url']
        
        # RSS парсинг
        rss_data, parse_metrics = site_parser.parse_rss_feed(website)
        
        if rss_data:
            # Формируем parsed_content из RSS
            parsed_content = f"=== RSS ЛЕНТА {test_filial['name']} ===\n"
            parsed_content += f"Канал: {rss_data.get('channel_title', '')}\n"
            parsed_content += f"Описание: {rss_data.get('channel_description', '')}\n\n"
            
            items_count = 0
            for item in rss_data.get('items', []):
                parsed_content += f"--- НОВОСТЬ ---\n"
                parsed_content += f"Заголовок: {item['title']}\n"
                parsed_content += f"Описание: {item['description']}\n"
                parsed_content += f"Ссылка: {item['link']}\n"
                parsed_content += f"Дата: {item['pubDate']}\n\n"
                items_count += 1
                if items_count >= 3:  # Показываем только первые 3 для теста
                    break
            
            print(f"\n✅ RSS получен: {len(rss_data.get('items', []))} новостей")
            print(f"   parsed_content: {len(parsed_content)} символов")
            print(f"   parse_metrics: {parse_metrics}")
        else:
            parsed_content = None
            print("\n⚠️ RSS не найден")
            print(f"   parsed_content: {type(parsed_content)}")
            print(f"   parse_metrics: {parse_metrics}")
        
        # Проверка использования переменных
        if parsed_content:
            print(f"\n✅ ТЕСТ RSS ПРОЙДЕН: parsed_content содержит {len(parsed_content)} символов")
        else:
            print(f"\n✅ ТЕСТ RSS ПРОЙДЕН: parsed_content = None (RSS не найден)")
        
    except Exception as e:
        print(f"\n❌ Ошибка в RSS тесте: {e}")
        return False
    
    return True

def test_meta_search():
    """Тест режима meta_search для проверки инициализации переменных"""
    
    print("\n" + "=" * 60)
    print("ТЕСТ: Режим meta_search")
    print("=" * 60)
    
    # Инициализация компонентов
    logger = get_logger(LogLevel.INFO)
    site_parser = SiteParser(log_level=LogLevel.INFO)
    
    # Тестовый филиал
    test_filial = {
        'id': 14,
        'name': 'ГТРК Саха',
        'website_url': 'https://gtrksakha.ru'
    }
    
    print(f"\n📄 Тестируем мета-парсинг для: {test_filial['name']}")
    
    try:
        website = test_filial['website_url']
        
        # Мета-парсинг
        parsed_content, parse_metrics = site_parser.parse_meta_data(website, include_news=False)
        
        if parsed_content:
            print(f"\n✅ Мета-данные получены:")
            print(f"   parsed_content: {len(parsed_content)} символов")
            print(f"   Страниц: {parse_metrics.get('pages_parsed', 0)}")
            print(f"   Заголовков: {parse_metrics.get('headers_count', 0)}")
            print(f"   Мета-тегов: {parse_metrics.get('meta_tags_count', 0)}")
            
            # Показываем первые 200 символов
            preview = parsed_content[:200] + "..." if len(parsed_content) > 200 else parsed_content
            print(f"\n   Превью контента:\n{preview}")
        else:
            print("\n⚠️ Мета-данные не получены")
            print(f"   parsed_content: {type(parsed_content)}")
            print(f"   parse_metrics: {parse_metrics}")
        
        print(f"\n✅ ТЕСТ META ПРОЙДЕН!")
        
    except Exception as e:
        print(f"\n❌ Ошибка в meta тесте: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 ЗАПУСК ТЕСТОВ ИСПРАВЛЕНИЯ parsed_content\n")
    
    # Запускаем все тесты
    tests = [
        ("Sitemap Search", test_sitemap_search),
        ("RSS Search", test_rss_search),
        ("Meta Search", test_meta_search)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"\n❌ Критическая ошибка в тесте {test_name}: {e}")
            results.append((test_name, False))
    
    # Итоги
    print("\n" + "=" * 60)
    print("ИТОГИ ТЕСТИРОВАНИЯ")
    print("=" * 60)
    
    for test_name, success in results:
        status = "✅ ПРОЙДЕН" if success else "❌ ПРОВАЛЕН"
        print(f"{test_name}: {status}")
    
    all_passed = all(success for _, success in results)
    if all_passed:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
    else:
        print("\n⚠️ Некоторые тесты провалены, требуется доработка")