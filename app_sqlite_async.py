"""
Расширение основного приложения с поддержкой асинхронного мониторинга
"""

import streamlit as st
import asyncio
from datetime import datetime
import time
from modules.async_monitoring import AsyncMonitoring
from modules.database import VGTRKDatabase
from modules.results_formatter import SitemapResultsFormatter
import json


async def process_monitoring_async(
    db: VGTRKDatabase,
    filials: list,
    queries: list,
    search_days: int = 7,
    max_concurrent: int = 20,
    session_id: int = None,
    progress_placeholder=None
):
    """Асинхронная обработка мониторинга"""
    
    start_time = time.time()
    monitor = AsyncMonitoring(max_concurrent=max_concurrent)
    
    try:
        # Преобразуем запросы в ключевые слова
        keywords = [q['query_text'] for q in queries]
        
        # Счётчики для статистики
        total = len(filials)
        completed = 0
        results_saved = 0
        
        # Callback для обновления прогресса
        def progress_callback(current, total_count, result):
            nonlocal completed, results_saved
            completed = current
            
            # Обновляем прогресс в Streamlit
            if progress_placeholder:
                status_icon = {
                    'success': '✅',
                    'no_data': '⚠️', 
                    'error': '❌'
                }.get(result['status'], '❓')
                
                progress_text = f"""
                **Прогресс: {completed}/{total_count}**
                
                Последний обработан: {status_icon} {result['filial_name']}
                - Статей найдено: {len(result.get('articles', []))}
                - Время обработки: {result['processing_time']:.2f}с
                """
                
                if result.get('error'):
                    progress_text += f"\n- Ошибка: {result['error']}"
                
                progress_placeholder.markdown(progress_text)
        
        # Запускаем асинхронную обработку
        results = await monitor.process_filials_batch(
            filials,
            keywords,
            days=search_days,
            max_articles=50,
            progress_callback=progress_callback
        )
        
        # Сохраняем результаты в БД
        formatter = SitemapResultsFormatter()
        
        for result in results:
            if result['status'] == 'success' and result['articles']:
                # Сохраняем результат для каждого запроса
                for query in queries:
                    query_text = query['query_text']
                    
                    # Фильтруем статьи по запросу
                    relevant_articles = [
                        article for article in result['articles']
                        if query_text.lower() in ' '.join(article.get('keywords', [])).lower()
                    ]
                    
                    if relevant_articles:
                        # Форматируем результаты
                        formatted = formatter.format_sitemap_results(
                            relevant_articles,
                            result['filial_name'],
                            query_text,
                            max_display=10
                        )
                        
                        # Сохраняем в БД
                        db_result = {
                            'filial_id': result['filial_id'],
                            'search_query_id': query['id'],
                            'url': result['website'],
                            'page_title': result['filial_name'],
                            'content': formatted['content'],
                            'gigachat_analysis': f"Найдено {len(relevant_articles)} статей (асинхронный поиск)",
                            'relevance_score': min(len(relevant_articles) / 10, 1.0),
                            'status': 'success',
                            'search_mode': 'sitemap_async',
                            'articles': formatted['articles'],
                            'metrics': {
                                'articles_found': len(relevant_articles),
                                'search_days': search_days,
                                'processing_time': result['processing_time']
                            }
                        }
                        
                        db.save_monitoring_result(result['filial_id'], db_result, session_id)
                        results_saved += 1
            
            elif result['status'] == 'error':
                # Сохраняем ошибку
                db_result = {
                    'filial_id': result['filial_id'],
                    'url': result['website'],
                    'status': 'error',
                    'error_message': result.get('error', 'Неизвестная ошибка'),
                    'search_mode': 'sitemap_async'
                }
                db.save_monitoring_result(result['filial_id'], db_result, session_id)
        
        total_time = time.time() - start_time
        
        # Финальная статистика
        success_count = sum(1 for r in results if r['status'] == 'success')
        error_count = sum(1 for r in results if r['status'] == 'error')
        no_data_count = sum(1 for r in results if r['status'] == 'no_data')
        total_articles = sum(len(r.get('articles', [])) for r in results)
        
        return {
            'total_time': total_time,
            'total_filials': total,
            'success_count': success_count,
            'error_count': error_count,
            'no_data_count': no_data_count,
            'total_articles': total_articles,
            'results_saved': results_saved,
            'avg_time_per_filial': total_time / total if total > 0 else 0
        }
        
    finally:
        await monitor.close()


def run_async_monitoring_streamlit(
    db: VGTRKDatabase,
    filials: list,
    queries: list,
    search_days: int = 7,
    max_concurrent: int = 20,
    session_id: int = None,
    progress_placeholder=None
):
    """Обёртка для запуска асинхронного мониторинга из Streamlit"""
    
    # Создаём новый event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        return loop.run_until_complete(
            process_monitoring_async(
                db, filials, queries, search_days,
                max_concurrent, session_id, progress_placeholder
            )
        )
    finally:
        loop.close()


def show_async_settings():
    """Показать настройки асинхронного режима"""
    
    with st.expander("⚙️ Настройки асинхронного режима", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            max_concurrent = st.slider(
                "Макс. параллельных соединений",
                min_value=1,
                max_value=50,
                value=20,
                help="Количество одновременных соединений. Больше = быстрее, но выше нагрузка"
            )
        
        with col2:
            timeout = st.slider(
                "Таймаут соединения (сек)",
                min_value=10,
                max_value=60,
                value=30,
                help="Максимальное время ожидания ответа от сервера"
            )
        
        st.info(
            f"💡 При {max_concurrent} параллельных соединениях, "
            f"100 филиалов будут обработаны примерно за "
            f"{100 / max_concurrent * 2:.0f}-{100 / max_concurrent * 5:.0f} секунд"
        )
        
        return max_concurrent, timeout


def compare_monitoring_modes():
    """Сравнение режимов мониторинга"""
    
    st.markdown("""
    ### 🔄 Сравнение режимов мониторинга
    
    | Параметр | Синхронный | Асинхронный |
    |----------|------------|-------------|
    | **Скорость** | 🐌 Медленно (5-10 сек/филиал) | ⚡ Быстро (0.5-2 сек/филиал) |
    | **Параллельность** | ❌ Нет (по очереди) | ✅ Да (до 50 одновременно) |
    | **Использование ресурсов** | 💚 Низкое | 🟡 Среднее |
    | **Стабильность** | ✅ Высокая | ⚠️ Зависит от сети |
    | **100 филиалов** | ~10-15 минут | ~30-60 секунд |
    
    **Рекомендации:**
    - **Асинхронный режим** - для массового мониторинга (>10 филиалов)
    - **Синхронный режим** - для отладки и небольших проверок
    """)


if __name__ == "__main__":
    st.set_page_config(
        page_title="Асинхронный мониторинг ВГТРК",
        page_icon="⚡",
        layout="wide"
    )
    
    st.title("⚡ Асинхронный мониторинг ВГТРК")
    
    # Выбор режима
    mode = st.radio(
        "Выберите режим мониторинга",
        ["🚀 Асинхронный (быстрый)", "🐌 Синхронный (последовательный)"],
        horizontal=True
    )
    
    if mode == "🚀 Асинхронный (быстрый)":
        st.success("✅ Выбран асинхронный режим - обработка до 50 филиалов одновременно!")
        max_concurrent, timeout = show_async_settings()
    else:
        st.info("ℹ️ Выбран синхронный режим - филиалы обрабатываются по очереди")
    
    # Сравнение режимов
    with st.expander("📊 Сравнение режимов", expanded=False):
        compare_monitoring_modes()