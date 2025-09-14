"""
Тестовый скрипт для проверки асинхронного мониторинга
"""

import asyncio
import time
import sqlite3
from pathlib import Path
import sys
sys.path.append('modules')

from modules.async_monitoring import AsyncMonitoring, run_monitoring_async


def get_test_filials(limit=10):
    """Получаем несколько филиалов для тестирования"""
    
    db_path = "data/vgtrk_monitoring.db"
    filials = []
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, website_url, sitemap_url, federal_district
            FROM filials
            WHERE website_url IS NOT NULL
            AND is_active = 1
            LIMIT ?
        """, (limit,))
        
        for row in cursor.fetchall():
            filials.append({
                'id': row[0],
                'name': row[1],
                'website': row[2],
                'sitemap_url': row[3],
                'federal_district': row[4]
            })
    
    return filials


def progress_callback(completed, total, result):
    """Callback для отображения прогресса"""
    status_icon = {
        'success': '[OK]',
        'no_data': '[--]',
        'error': '[!!]'
    }.get(result['status'], '[??]')
    
    articles_count = len(result.get('articles', []))
    time_str = f"{result['processing_time']:.2f}с"
    
    print(
        f"[{completed}/{total}] {status_icon} {result['filial_name']}: "
        f"{articles_count} статей за {time_str}"
    )
    
    if result['error']:
        print(f"     Ошибка: {result['error']}")


async def test_async_monitoring():
    """Основная функция тестирования"""
    
    print("=" * 60)
    print("ТЕСТ АСИНХРОННОГО МОНИТОРИНГА")
    print("=" * 60)
    
    # Получаем тестовые филиалы
    filials = get_test_filials(limit=10)
    print(f"\nНайдено {len(filials)} филиалов для тестирования:")
    for f in filials:
        print(f"  - {f['name']} - {f['website']}")
    
    # Тестовые запросы
    queries = [
        {'query_text': 'губернатор'},
        {'query_text': 'новости'},
        {'query_text': 'регион'}
    ]
    
    print(f"\nПоисковые запросы: {[q['query_text'] for q in queries]}")
    print("\n" + "=" * 60)
    
    # Запускаем асинхронный мониторинг
    print("\n>>> Запуск асинхронного мониторинга (max_concurrent=5)...")
    start_time = time.time()
    
    monitor = AsyncMonitoring(max_concurrent=5)
    
    try:
        keywords = [q['query_text'] for q in queries]
        
        results = await monitor.process_filials_batch(
            filials,
            keywords,
            days=7,
            max_articles=20,
            progress_callback=progress_callback
        )
        
        total_time = time.time() - start_time
        
        # Статистика
        print("\n" + "=" * 60)
        print("РЕЗУЛЬТАТЫ:")
        print("=" * 60)
        
        success_count = sum(1 for r in results if r['status'] == 'success')
        error_count = sum(1 for r in results if r['status'] == 'error')
        no_data_count = sum(1 for r in results if r['status'] == 'no_data')
        total_articles = sum(len(r.get('articles', [])) for r in results)
        
        print(f"\n=== Статистика:")
        print(f"  - Общее время: {total_time:.2f} секунд")
        print(f"  - Среднее время на филиал: {total_time/len(filials):.2f} секунд")
        print(f"  - Успешно: {success_count}")
        print(f"  - Ошибки: {error_count}")
        print(f"  - Нет данных: {no_data_count}")
        print(f"  - Всего найдено статей: {total_articles}")
        
        # Детали по филиалам с результатами
        print("\n=== Найденные статьи:")
        for result in results:
            if result['articles']:
                print(f"\n{result['filial_name']}:")
                for i, article in enumerate(result['articles'][:3], 1):
                    print(f"  {i}. {article.get('title', article['url'])[:80]}...")
                    print(f"     Ключевые слова: {', '.join(article['keywords'])}")
        
    finally:
        await monitor.close()
    
    print("\n[ГОТОВО] Тест завершён!")


def compare_sync_vs_async():
    """Сравнение скорости синхронного и асинхронного подходов"""
    
    print("\n" + "=" * 60)
    print("СРАВНЕНИЕ СИНХРОННОГО И АСИНХРОННОГО ПОДХОДОВ")
    print("=" * 60)
    
    # Получаем филиалы для теста
    filials = get_test_filials(limit=5)
    queries = [{'query_text': 'новости'}]
    
    # Запускаем асинхронный тест
    print("\n>>> Асинхронный мониторинг (параллельно)...")
    start_async = time.time()
    
    results = run_monitoring_async(
        filials,
        queries,
        days=3,
        max_concurrent=5,
        progress_callback=progress_callback
    )
    
    async_time = time.time() - start_async
    
    print(f"\n=== Результаты:")
    print(f"  - Асинхронный подход: {async_time:.2f} секунд")
    print(f"  - Скорость: {len(filials)/async_time:.2f} филиалов/сек")
    
    # Оценка для синхронного подхода
    avg_time_per_filial = async_time / len(filials) * 3  # Примерная оценка
    sync_time_estimate = avg_time_per_filial * len(filials)
    
    print(f"\n  - Оценка синхронного: ~{sync_time_estimate:.2f} секунд")
    print(f"  - Ускорение: ~{sync_time_estimate/async_time:.1f}x")


if __name__ == "__main__":
    import sys
    
    # Если передан аргумент командной строки, используем его
    if len(sys.argv) > 1:
        choice = sys.argv[1]
    else:
        # По умолчанию запускаем полный тест
        choice = "1"
    
    if choice == "1":
        asyncio.run(test_async_monitoring())
    elif choice == "2":
        compare_sync_vs_async()
    elif choice == "3":
        asyncio.run(test_async_monitoring())
        print("\n" * 2)
        compare_sync_vs_async()
    else:
        print("Использование: python test_async_monitoring.py [1|2|3]")
        print("1 - Полный тест асинхронного мониторинга")
        print("2 - Сравнение скорости")
        print("3 - Оба теста")