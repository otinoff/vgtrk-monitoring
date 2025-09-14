"""
Модуль для отображения результатов мониторинга в виде карточек
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from typing import List, Dict

def show_monitoring_results_cards(results: List[Dict], filials: List[Dict], queries: List[Dict]):
    """
    Отображает результаты мониторинга в виде карточек филиалов
    
    Args:
        results: Список результатов из БД
        filials: Список проверенных филиалов
        queries: Список поисковых запросов
    """
    
    st.header("📊 Результаты мониторинга")
    
    # Группируем результаты по филиалам
    results_by_filial = {}
    for result in results:
        filial_id = result.get('filial_id')
        if filial_id not in results_by_filial:
            results_by_filial[filial_id] = []
        results_by_filial[filial_id].append(result)
    
    # Создаем словарь филиалов для быстрого доступа
    filials_dict = {f['id']: f for f in filials}
    
    # Статистика
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Всего филиалов", len(filials))
    with col2:
        found_count = len([f for f in filials if f['id'] in results_by_filial and 
                          any(r['status'] == 'success' for r in results_by_filial[f['id']])])
        st.metric("Найдено упоминаний", found_count, f"{found_count/len(filials)*100:.0f}%")
    with col3:
        not_found = len(filials) - found_count
        st.metric("Не найдено", not_found)
    with col4:
        # Суммируем количество найденных статей из метрик
        total_articles = 0
        for r in results:
            if r.get('status') == 'success':
                metrics = r.get('metrics')
                if isinstance(metrics, dict) and 'articles_found' in metrics:
                    total_articles += metrics.get('articles_found', 0)
        st.metric("Всего статей", total_articles)
    
    st.markdown("---")
    
    # Фильтры
    col_filter1, col_filter2, col_filter3 = st.columns(3)
    with col_filter1:
        filter_status = st.selectbox(
            "Показать",
            ["Все", "Только с результатами", "Только без результатов"],
            help="Фильтр по наличию результатов"
        )
    with col_filter2:
        selected_query = st.selectbox(
            "Ключевое слово",
            ["Все"] + [q['query_text'] for q in queries],
            help="Фильтр по ключевому слову"
        )
    with col_filter3:
        sort_by = st.selectbox(
            "Сортировка",
            ["По алфавиту", "По количеству статей", "По округам"],
            help="Порядок отображения карточек"
        )
    
    st.markdown("---")
    
    # Подготавливаем список филиалов для отображения
    display_filials = []
    for filial in filials:
        filial_results = results_by_filial.get(filial['id'], [])
        success_results = [r for r in filial_results if r['status'] == 'success']
        
        # Применяем фильтры
        if filter_status == "Только с результатами" and not success_results:
            continue
        elif filter_status == "Только без результатов" and success_results:
            continue
        
        if selected_query != "Все":
            filtered_results = [r for r in success_results 
                              if any(q['query_text'] == selected_query for q in queries if q['id'] == r.get('search_query_id'))]
            if not filtered_results and filter_status == "Только с результатами":
                continue
            success_results = filtered_results
        
        # Подсчитываем общее количество статей
        articles_count = 0
        all_filial_results = filial_results  # Используем все результаты, не только success
        
        for r in all_filial_results:
            if r.get('search_mode') in ['sitemap', 'sitemap_no_ai']:
                metrics = r.get('metrics')
                if isinstance(metrics, dict) and 'articles_found' in metrics:
                    articles_count += metrics.get('articles_found', 0)
        
        display_filials.append({
            'filial': filial,
            'results': filial_results,  # Передаем все результаты
            'articles_count': articles_count,
            'has_results': bool(success_results)
        })
    
    # Сортировка
    if sort_by == "По алфавиту":
        display_filials.sort(key=lambda x: x['filial']['name'])
    elif sort_by == "По количеству статей":
        display_filials.sort(key=lambda x: x['articles_count'], reverse=True)
    elif sort_by == "По округам":
        display_filials.sort(key=lambda x: (x['filial'].get('federal_district', ''), x['filial']['name']))
    
    # Отображаем карточки
    # Создаем колонки для карточек (по 3 в ряд)
    for i in range(0, len(display_filials), 3):
        cols = st.columns(3)
        for j in range(3):
            if i + j < len(display_filials):
                with cols[j]:
                    display_filial_card(display_filials[i + j], queries)


def display_filial_card(filial_data: Dict, queries: List[Dict]):
    """
    Отображает карточку одного филиала
    """
    filial = filial_data['filial']
    results = filial_data['results']
    has_results = filial_data['has_results']
    articles_count = filial_data['articles_count']
    
    # Определяем цвет карточки
    if has_results:
        card_color = "#d4edda"  # Светло-зеленый
        border_color = "#28a745"  # Зеленый
        icon = "✅"
    else:
        card_color = "#f8d7da"  # Светло-красный
        border_color = "#dc3545"  # Красный
        icon = "❌"
    
    # Стилизованная карточка
    card_html = f"""
    <div style="
        background-color: {card_color};
        border: 2px solid {border_color};
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 20px;
        min-height: 200px;
    ">
        <h4 style="margin: 0 0 10px 0; color: #333;">
            {icon} {filial['name']}
        </h4>
        <p style="margin: 5px 0; font-size: 0.9em; color: #666;">
            {filial.get('federal_district', 'Округ не указан')} | {filial.get('region', 'Регион не указан')}
        </p>
    """
    
    if filial.get('website_url') or filial.get('website'):
        website = filial.get('website_url') or filial.get('website')
        if not website.startswith('http'):
            website = f"https://{website}"
        card_html += f'<p style="margin: 5px 0; font-size: 0.85em;"><a href="{website}" target="_blank">🌐 {website}</a></p>'
    
    # Группируем по ключевым словам (всегда, независимо от articles_count)
    results_by_keyword = {}
    for result in results:
        query_id = result.get('search_query_id')
        query_text = next((q['query_text'] for q in queries if q['id'] == query_id), 'Неизвестно')
        if query_text not in results_by_keyword:
            results_by_keyword[query_text] = []
        results_by_keyword[query_text].append(result)
    
    if articles_count > 0:
        card_html += f'<p style="margin: 10px 0; font-weight: bold; color: #28a745;">Найдено статей: {articles_count}</p>'
        
        card_html += '<div style="margin-top: 10px;">'
        for keyword, keyword_results in results_by_keyword.items():
            # Собираем все статьи для этого ключевого слова
            all_articles = []
            
            for res in keyword_results:
                if res.get('search_mode') in ['sitemap', 'sitemap_no_ai'] and res.get('articles'):
                    all_articles.extend(res.get('articles', []))
            
            card_html += f'<p style="margin: 8px 0; font-weight: bold; color: #555;">📌 {keyword}:</p>'
            
            if all_articles:
                # Показываем первые 2 статьи прямо в карточке
                card_html += '<div style="margin-left: 20px; font-size: 0.85em;">'
                for i, article in enumerate(all_articles[:2], 1):
                    title = article.get('title', 'Без названия')
                    url = article.get('url', '#')
                    date = article.get('date', '')
                    snippet = article.get('snippet', '')
                    
                    # Форматируем дату если это datetime объект
                    if hasattr(date, 'strftime'):
                        date_str = date.strftime('%d.%m.%Y')
                    else:
                        date_str = str(date) if date else 'Дата не указана'
                    
                    # Не ограничиваем длину заголовка - показываем полностью
                    card_html += f'''
                    <div style="margin: 8px 0; background-color: #f8f9fa; padding: 8px; border-radius: 5px;">
                        <div style="margin-bottom: 4px;">
                            {i}. <a href="{url}" target="_blank" style="color: #0066cc; text-decoration: none; font-weight: bold;">
                                {title}
                            </a>
                        </div>
                        <div style="color: #999; font-size: 0.9em; margin-bottom: 4px;">
                            📅 {date_str}
                        </div>
                    '''
                    
                    # Убираем показ snippet по просьбе пользователя
                    
                    card_html += '</div>'
                
                if len(all_articles) > 2:
                    card_html += f'<p style="margin: 4px 0; color: #666; font-style: italic;">... и еще {len(all_articles) - 2} статей</p>'
                card_html += '</div>'
            else:
                # Если статей нет, проверяем метрики
                total_articles = 0
                for res in keyword_results:
                    if res.get('search_mode') in ['sitemap', 'sitemap_no_ai']:
                        metrics = res.get('metrics')
                        if isinstance(metrics, dict) and 'articles_found' in metrics:
                            total_articles += metrics.get('articles_found', 0)
                
                if total_articles > 0:
                    card_html += f'<p style="margin: 5px 0 10px 20px; font-size: 0.85em; color: #28a745;">✓ Найдено статей: {total_articles}</p>'
                else:
                    # Убираем показ анализа GigaChat по просьбе пользователя
                    card_html += f'<p style="margin: 5px 0 10px 20px; font-size: 0.85em; color: #dc3545;">✗ Статей не найдено</p>'
        
        card_html += '</div>'
    else:
        # Если articles_count = 0, но есть результаты, показываем их
        if results_by_keyword:
            card_html += '<div style="margin-top: 10px;">'
            for keyword, keyword_results in results_by_keyword.items():
                card_html += f'<p style="margin: 8px 0; font-weight: bold; color: #555;">📌 {keyword}:</p>'
                
                # Убираем показ анализа GigaChat по просьбе пользователя
                card_html += f'<p style="margin: 5px 0 10px 20px; font-size: 0.85em; color: #dc3545;">✗ Статей не найдено</p>'
            card_html += '</div>'
        else:
            card_html += '<p style="margin: 10px 0; color: #666; font-style: italic;">Упоминаний не найдено</p>'
    
    card_html += '</div>'
    
    st.markdown(card_html, unsafe_allow_html=True)
    
    # Если есть результаты с деталями статей, добавляем кнопку для деталей
    has_articles_details = any(
        res.get('articles')
        for results_list in results_by_keyword.values()
        for res in results_list
        if res.get('search_mode') in ['sitemap', 'sitemap_no_ai']
    ) if results_by_keyword else False
    
    if has_articles_details:
        if st.button(f"📋 Показать все статьи", key=f"details_{filial['id']}", use_container_width=True):
            with st.expander(f"📰 Найденные статьи - {filial['name']}", expanded=True):
                for keyword, keyword_results in results_by_keyword.items():
                    st.markdown(f"### 🔍 Ключевое слово: **{keyword}**")
                    
                    total_articles_for_keyword = 0
                    all_articles_for_keyword = []
                    
                    # Собираем все статьи для этого ключевого слова
                    for res in keyword_results:
                        if res.get('search_mode') in ['sitemap', 'sitemap_no_ai']:
                            articles = res.get('articles', [])
                            if articles:
                                all_articles_for_keyword.extend(articles)
                                total_articles_for_keyword += len(articles)
                            else:
                                # Если нет сохраненных статей, но есть количество
                                count = res.get('metrics', {}).get('articles_found', 0)
                                if count > 0:
                                    total_articles_for_keyword += count
                    
                    if all_articles_for_keyword:
                        st.write(f"📊 **Найдено статей:** {len(all_articles_for_keyword)}")
                        
                        # Отображаем каждую статью
                        for i, article in enumerate(all_articles_for_keyword, 1):
                            col1, col2 = st.columns([4, 1])
                            
                            with col1:
                                # Заголовок статьи как ссылка
                                article_title = article.get('title', 'Без названия')
                                article_url = article.get('url', '#')
                                st.markdown(f"**{i}.** [{article_title}]({article_url})")
                            
                            with col2:
                                # Дата публикации
                                article_date = article.get('date', 'Дата не указана')
                                # Форматируем дату если это datetime объект
                                if hasattr(article_date, 'strftime'):
                                    date_str = article_date.strftime('%d.%m.%Y')
                                else:
                                    date_str = str(article_date) if article_date else 'Дата не указана'
                                st.caption(f"📅 {date_str}")
                            
                            # Убираем показ snippet по просьбе пользователя
                            
                            # Разделитель между статьями
                            if i < len(all_articles_for_keyword):
                                st.divider()
                    
                    elif total_articles_for_keyword > 0:
                        # Если есть количество статей, но нет деталей
                        st.info(f"📊 Найдено статей: {total_articles_for_keyword} (детали не сохранены)")
                    else:
                        # Проверяем, есть ли анализ GigaChat
                        # Убираем показ анализа GigaChat по просьбе пользователя
                        st.warning(f"❌ Статей по запросу '{keyword}' не найдено")
                    
                    st.markdown("---")


def show_results_summary(results: List[Dict], filials: List[Dict], queries: List[Dict]):
    """
    Показывает сводную статистику по результатам
    """
    with st.expander("📊 Сводная статистика", expanded=False):
        # Создаем DataFrame для анализа
        data = []
        for filial in filials:
            filial_results = [r for r in results if r['filial_id'] == filial['id']]
            for query in queries:
                query_results = [r for r in filial_results if r.get('search_query_id') == query['id']]
                success_results = [r for r in query_results if r['status'] == 'success']
                articles_count = 0
                for r in success_results:
                    metrics = r.get('metrics')
                    if isinstance(metrics, dict) and 'articles_found' in metrics:
                        articles_count += metrics.get('articles_found', 0)
                
                data.append({
                    'Филиал': filial['name'],
                    'Округ': filial.get('federal_district', 'Не указан'),
                    'Ключевое слово': query['query_text'],
                    'Найдено': '✅' if success_results else '❌',
                    'Количество статей': articles_count
                })
        
        df = pd.DataFrame(data)
        
        # Сводная таблица
        pivot = df.pivot_table(
            index='Филиал',
            columns='Ключевое слово',
            values='Количество статей',
            aggfunc='sum',
            fill_value=0
        )
        
        st.dataframe(pivot, use_container_width=True)
        
        # Кнопка экспорта
        if st.button("📥 Экспорт в Excel", key="export_summary"):
            # Здесь можно добавить функционал экспорта
            st.info("Функция экспорта будет добавлена")


class ResultsCardsDisplay:
    """
    Класс для отображения результатов мониторинга в виде карточек
    """
    
    def __init__(self, results: List[Dict]):
        """
        Инициализация
        
        Args:
            results: Список результатов мониторинга из БД
        """
        self.results = results
        self._prepare_data()
    
    def _prepare_data(self):
        """Подготовка данных для отображения"""
        # Получаем уникальные филиалы и поисковые запросы
        self.filials = {}
        self.queries = {}
        
        for result in self.results:
            # Собираем информацию о филиалах
            filial_id = result.get('filial_id')
            if filial_id and filial_id not in self.filials:
                self.filials[filial_id] = {
                    'id': filial_id,
                    'name': result.get('filial_name', 'Неизвестный филиал'),
                    'federal_district': result.get('federal_district', 'Не указан'),
                    'region': result.get('region', 'Не указан'),
                    'website': result.get('url', '')
                }
            
            # Собираем информацию о поисковых запросах
            query_id = result.get('search_query_id')
            if query_id and query_id not in self.queries:
                self.queries[query_id] = {
                    'id': query_id,
                    'query_text': result.get('query_text', 'Неизвестный запрос')
                }
    
    def display_cards(self):
        """Отображает карточки филиалов с результатами"""
        # Преобразуем словари в списки
        filials_list = list(self.filials.values())
        queries_list = list(self.queries.values())
        
        # Используем существующую функцию для отображения
        show_monitoring_results_cards(self.results, filials_list, queries_list)