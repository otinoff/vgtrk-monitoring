"""
Тестирование поиска через прямой sitemap URL
для ГТРК Саха (https://gtrksakha.ru/sitemap2025.xml)
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import sqlite3

# Добавляем текущую директорию в path
sys.path.append(str(Path(__file__).parent))

from modules.scrapy_parser import ScrapyParser
from modules.advanced_logger import AdvancedLogger, LogLevel
from modules.database import VGTRKDatabase

def test_direct_sitemap():
    """Тестирует поиск через прямой sitemap URL"""
    
    # Инициализация компонентов
    logger = AdvancedLogger(LogLevel.INFO)
    parser = ScrapyParser(logger)
    db = VGTRKDatabase()
    
    print("\n" + "="*70)
    print("[TEST] Тестирование поиска через прямой sitemap URL")
    print("="*70)
    
    # Получаем информацию о ГТРК Саха из базы
    try:
        with db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT id, name, website, sitemap_url 
                FROM filials 
                WHERE sitemap_url IS NOT NULL 
                LIMIT 1
            """)
            filial = cursor.fetchone()
            
            if filial:
                filial_id = filial[0]
                filial_name = filial[1]
                website = filial[2] or "https://gtrksakha.ru"
                sitemap_url = filial[3]
                
                print(f"\n[INFO] Тестируем филиал: {filial_name}")
                print(f"       Сайт: {website}")
                print(f"       Sitemap: {sitemap_url}")
            else:
                print("[ERROR] Не найдены филиалы с установленным sitemap_url")
                return
                
    except Exception as e:
        print(f"[ERROR] Ошибка при чтении из базы данных: {e}")
        return
    
    # Тестовые ключевые слова
    keywords = [
        "Якутия",
        "Саха",
        "Айсен Николаев",
        "развитие",
        "проект"
    ]
    
    print(f"\n[INFO] Ключевые слова для поиска: {', '.join(keywords)}")
    print(f"[INFO] Период поиска: последние 7 дней\n")
    
    # Выполняем поиск с прямым sitemap URL
    try:
        results = parser.search_with_sitemap(
            site_url=website,
            keywords=keywords,
            days=7,
            max_articles=50,
            sitemap_url=sitemap_url  # Используем прямой URL
        )
        
        print(f"\n[RESULT] Найдено статей: {len(results)}")
        
        if results:
            print("\n[INFO] Первые 5 найденных статей:")
            print("-" * 70)
            
            for i, article in enumerate(results[:5], 1):
                date_str = article['date'].strftime('%d.%m.%Y') if article.get('date') else 'Дата неизвестна'
                print(f"\n{i}. {article['title']}")
                print(f"   Дата: {date_str}")
                print(f"   URL: {article['url']}")
                print(f"   Ключевые слова: {', '.join(article['keywords'])}")
                if article.get('snippet'):
                    print(f"   Фрагмент: {article['snippet'][:150]}...")
            
            # Сохраняем результаты в базу данных
            print(f"\n[INFO] Сохраняем результаты в базу данных...")
            saved_count = 0
            
            for article in results[:10]:  # Сохраняем только первые 10
                try:
                    result_data = {
                        'url': article['url'],
                        'page_title': article['title'],
                        'content': article.get('content', '')[:1000],
                        'status': 'success',
                        'relevance_score': len(article['keywords']) / len(keywords) * 100
                    }
                    
                    db.save_monitoring_result(filial_id, result_data)
                    saved_count += 1
                    
                except Exception as e:
                    print(f"[WARNING] Ошибка при сохранении результата: {e}")
            
            print(f"[INFO] Сохранено {saved_count} результатов в базу данных")
            
        else:
            print("\n[WARNING] Статьи с указанными ключевыми словами не найдены")
            
    except Exception as e:
        print(f"\n[ERROR] Ошибка при выполнении поиска: {e}")
        logger.log("ERROR", f"Ошибка поиска: {e}")
    
    print("\n" + "="*70)
    print("[INFO] Тест завершен")
    print("="*70)

def test_sitemap_parsing():
    """Дополнительный тест - проверка парсинга sitemap напрямую"""
    
    print("\n\n[TEST] Проверка парсинга sitemap напрямую")
    print("="*70)
    
    logger = AdvancedLogger(LogLevel.INFO)
    parser = ScrapyParser(logger)
    
    sitemap_url = "https://gtrksakha.ru/sitemap2025.xml"
    
    try:
        # Загружаем sitemap
        print(f"[INFO] Загружаем sitemap: {sitemap_url}")
        sitemap_data = parser.find_sitemap("https://gtrksakha.ru", sitemap_url)
        
        if sitemap_data:
            _, xml_content = sitemap_data
            print("[OK] Sitemap успешно загружен")
            
            # Парсим URL из sitemap
            date_to = datetime.now()
            date_from = date_to - timedelta(days=7)
            
            articles = parser.parse_sitemap_urls(xml_content, date_from, date_to)
            print(f"\n[INFO] Найдено URL в sitemap за последние 7 дней: {len(articles)}")
            
            if articles:
                print("\n[INFO] Примеры URL из sitemap:")
                for article in articles[:5]:
                    date_str = article['date'].strftime('%d.%m.%Y') if article.get('date') else 'Без даты'
                    print(f"   - {date_str}: {article['url']}")
        else:
            print("[ERROR] Не удалось загрузить sitemap")
            
    except Exception as e:
        print(f"[ERROR] Ошибка при парсинге sitemap: {e}")

def main():
    """Основная функция"""
    # Тест 1: Проверка парсинга sitemap
    test_sitemap_parsing()
    
    # Тест 2: Полный поиск с ключевыми словами
    test_direct_sitemap()

if __name__ == "__main__":
    main()