"""
Тестовый скрипт для проверки модуля scrapy_parser.py
Проверяет парсинг sitemap и поиск статей за период
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.scrapy_parser import ScrapyParser
from datetime import datetime, timedelta

def test_sitemap_search():
    """Тестирует поиск через sitemap"""
    
    print("=" * 60)
    print("ТЕСТ ПОИСКА ЧЕРЕЗ SITEMAP")
    print("=" * 60)
    
    # Создаем парсер
    parser = ScrapyParser()
    
    # Тестовый сайт
    test_site = "https://vesti42.ru"
    
    # Ключевые слова для поиска
    keywords = [
        "губернатор",
        "здравоохранение",
        "медицина",
        "больница",
        "поликлиника"
    ]
    
    print(f"\n[>] Тестируем сайт: {test_site}")
    print(f"[>] Ключевые слова: {', '.join(keywords)}")
    print(f"[>] Период: последние 7 дней\n")
    
    # 1. Проверяем наличие sitemap
    print("1. Поиск sitemap...")
    sitemap_data = parser.find_sitemap(test_site)
    
    if sitemap_data:
        sitemap_url, xml_content = sitemap_data
        print(f"[OK] Sitemap найден: {sitemap_url}")
        print(f"   Размер: {len(xml_content)} символов")
        
        # 2. Парсинг URL из sitemap
        print("\n2. Парсинг URL из sitemap...")
        date_to = datetime.now()
        date_from = date_to - timedelta(days=7)
        
        articles = parser.parse_sitemap_urls(xml_content, date_from, date_to)
        print(f"[OK] Найдено URL за последнюю неделю: {len(articles)}")
        
        if articles:
            # Показываем примеры URL
            print("\n   Примеры найденных URL:")
            for article in articles[:5]:
                date_str = article['date'].strftime('%d.%m.%Y') if article['date'] else 'без даты'
                print(f"   - {date_str}: {article['url'][:80]}...")
        
        # 3. Поиск по ключевым словам (тестируем на небольшом количестве)
        print("\n3. Поиск по ключевым словам (проверяем первые 10 статей)...")
        
        found_articles = []
        for i, article in enumerate(articles[:10], 1):
            print(f"   Проверяем {i}/10: {article['url'][:50]}...", end="")
            result = parser.search_in_article(article['url'], keywords)
            if result:
                found_articles.append(result)
                print(" [+] Найдено!")
            else:
                print(" [-]")
        
        print(f"\n[OK] Найдено релевантных статей: {len(found_articles)}")
        
        # 4. Показываем результаты
        if found_articles:
            print("\n4. Найденные статьи:")
            for i, article in enumerate(found_articles, 1):
                print(f"\n   {i}. {article['title']}")
                print(f"      URL: {article['url']}")
                print(f"      Ключевые слова: {', '.join(article['keywords'])}")
                if article.get('snippet'):
                    print(f"      Фрагмент: {article['snippet'][:150]}...")
        
        # 5. Тестируем полный поиск
        print("\n5. Тестируем полный поиск через метод search_with_sitemap...")
        results = parser.search_with_sitemap(
            test_site, 
            keywords, 
            days=3,  # За 3 дня
            max_articles=20  # Максимум 20 статей
        )
        
        print(f"[OK] Полный поиск завершен: найдено {len(results)} статей")
        
        # 6. Тестируем форматирование результатов
        print("\n6. Форматирование результатов (простой вывод):")
        if results:
            formatted = parser.get_results_simple(results[:3])  # Показываем первые 3
            print(formatted)
        
    else:
        print("[ERROR] Sitemap не найден")
        
        # Альтернативный тест на другом сайте
        print("\n[>] Пробуем альтернативный сайт...")
        alt_site = "https://vesti-yamal.ru"
        print(f"   Тестируем: {alt_site}")
        
        sitemap_data = parser.find_sitemap(alt_site)
        if sitemap_data:
            print(f"[OK] Sitemap найден для {alt_site}")
        else:
            print(f"[ERROR] Sitemap не найден и для {alt_site}")
    
    print("\n" + "=" * 60)
    print("ТЕСТ ЗАВЕРШЕН")
    print("=" * 60)


def test_date_filtering():
    """Тестирует фильтрацию по датам"""
    
    print("\n" + "=" * 60)
    print("ТЕСТ ФИЛЬТРАЦИИ ПО ДАТАМ")
    print("=" * 60)
    
    parser = ScrapyParser()
    
    # Тестовый XML с разными датами
    test_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        <url>
            <loc>https://example.com/news/1</loc>
            <lastmod>2024-09-10T10:00:00+07:00</lastmod>
        </url>
        <url>
            <loc>https://example.com/news/2</loc>
            <lastmod>2024-09-05T10:00:00+07:00</lastmod>
        </url>
        <url>
            <loc>https://example.com/news/3</loc>
            <lastmod>2024-08-01T10:00:00+07:00</lastmod>
        </url>
    </urlset>
    """
    
    # Тест 1: За последнюю неделю
    date_to = datetime(2024, 9, 13)
    date_from = date_to - timedelta(days=7)
    
    print(f"\n[>] Фильтр: {date_from.date()} - {date_to.date()}")
    articles = parser.parse_sitemap_urls(test_xml, date_from, date_to)
    print(f"[OK] Найдено статей: {len(articles)}")
    for article in articles:
        print(f"   - {article['date'].date()}: {article['url']}")
    
    # Тест 2: За месяц
    date_from = date_to - timedelta(days=30)
    print(f"\n[>] Фильтр: {date_from.date()} - {date_to.date()}")
    articles = parser.parse_sitemap_urls(test_xml, date_from, date_to)
    print(f"[OK] Найдено статей: {len(articles)}")
    
    # Тест 3: Без фильтра
    print(f"\n[>] Без фильтра дат")
    articles = parser.parse_sitemap_urls(test_xml)
    print(f"[OK] Найдено статей: {len(articles)}")


def test_keyword_search():
    """Тестирует поиск по ключевым словам в HTML"""
    
    print("\n" + "=" * 60)
    print("ТЕСТ ПОИСКА КЛЮЧЕВЫХ СЛОВ")
    print("=" * 60)
    
    parser = ScrapyParser()
    
    # Тестовый HTML
    test_html = """
    <html>
        <head><title>Губернатор провел совещание по здравоохранению</title></head>
        <body>
            <article>
                <h1>Губернатор обсудил развитие медицины</h1>
                <p>Сегодня губернатор региона провел важное совещание, 
                посвященное вопросам здравоохранения и развития медицинских учреждений.</p>
                <p>На встрече обсуждались планы строительства новой больницы 
                и модернизации существующих поликлиник.</p>
            </article>
        </body>
    </html>
    """
    
    # Мокаем requests для теста
    import unittest.mock as mock
    
    keywords = ["губернатор", "здравоохранение", "больница"]
    
    with mock.patch('requests.get') as mock_get:
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.text = test_html
        mock_get.return_value = mock_response
        
        result = parser.search_in_article("https://test.com/news/1", keywords)
        
        if result:
            print("[OK] Статья найдена!")
            print(f"   Заголовок: {result['title']}")
            print(f"   Найденные ключевые слова: {', '.join(result['keywords'])}")
            print(f"   Фрагмент: {result['snippet']}")
        else:
            print("[ERROR] Статья не найдена")


if __name__ == "__main__":
    print("\n>>> ЗАПУСК ТЕСТОВ МОДУЛЯ SCRAPY_PARSER\n")
    
    # Запускаем тесты
    try:
        # Тест фильтрации дат
        test_date_filtering()
        
        # Тест поиска ключевых слов
        test_keyword_search()
        
        # Основной тест с реальным сайтом
        test_sitemap_search()
        
        print("\n[OK] ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ УСПЕШНО!")
        
    except Exception as e:
        print(f"\n[ERROR] ОШИБКА В ТЕСТАХ: {e}")
        import traceback
        traceback.print_exc()