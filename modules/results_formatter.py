"""
Модуль для форматирования результатов поиска через Sitemap
"""

import streamlit as st
from typing import List, Dict
from datetime import datetime

class SitemapResultsFormatter:
    """Форматирует результаты поиска из Sitemap для отображения"""
    
    @staticmethod
    def format_sitemap_results(sitemap_results: List[Dict], filial_name: str, 
                             keyword: str, max_display: int = 10) -> Dict:
        """
        Форматирует результаты поиска из sitemap для сохранения в БД
        
        Args:
            sitemap_results: Список найденных статей
            filial_name: Название филиала
            keyword: Ключевое слово поиска
            max_display: Максимальное количество статей для отображения
            
        Returns:
            Словарь с отформатированными данными
        """
        if not sitemap_results:
            return {
                'content': f"Поиск по '{keyword}' не дал результатов",
                'articles': [],
                'total_count': 0
            }
        
        # Фильтруем статьи по конкретному ключевому слову
        relevant_articles = [
            article for article in sitemap_results
            if keyword.lower() in ' '.join(article.get('keywords', [])).lower()
        ]
        
        if not relevant_articles:
            return {
                'content': f"Статей с упоминанием '{keyword}' не найдено",
                'articles': [],
                'total_count': 0
            }
        
        # Сортируем по дате (новые первыми)
        relevant_articles.sort(key=lambda x: x.get('date') or datetime.min, reverse=True)
        
        # Форматируем для отображения
        formatted_articles = []
        for i, article in enumerate(relevant_articles[:max_display]):
            date_str = article['date'].strftime('%d.%m.%Y') if article.get('date') else 'Дата не указана'
            
            formatted_articles.append({
                'title': article['title'],
                'url': article['url'],
                'date': date_str,
                'keywords_found': article.get('keywords', []),
                'snippet': article.get('snippet', '')
            })
        
        # Формируем текстовое описание для БД
        content = f"Найдено {len(relevant_articles)} статей с упоминанием '{keyword}'"
        if len(relevant_articles) > max_display:
            content += f" (показаны первые {max_display})"
        
        return {
            'content': content,
            'articles': formatted_articles,
            'total_count': len(relevant_articles)
        }
    
    @staticmethod
    def display_articles_in_expander(articles: List[Dict], filial_name: str, keyword: str):
        """
        Отображает статьи в экспандере Streamlit
        
        Args:
            articles: Список отформатированных статей
            filial_name: Название филиала
            keyword: Ключевое слово
        """
        if not articles:
            st.info(f"Статей с упоминанием '{keyword}' не найдено")
            return
        
        for i, article in enumerate(articles, 1):
            # Заголовок с номером
            st.markdown(f"**{i}. [{article['title']}]({article['url']})**")
            
            # Метаинформация
            col1, col2 = st.columns([1, 3])
            with col1:
                st.caption(f"📅 {article['date']}")
            with col2:
                if article['keywords_found']:
                    keywords_str = ", ".join(article['keywords_found'])
                    st.caption(f"🔍 Найдено: {keywords_str}")
            
            # Фрагмент текста
            if article['snippet']:
                st.text(article['snippet'][:300] + "..." if len(article['snippet']) > 300 else article['snippet'])
            
            # Разделитель
            if i < len(articles):
                st.markdown("---")
    
    @staticmethod
    def create_articles_dataframe(articles: List[Dict]):
        """
        Создает DataFrame из списка статей для экспорта
        
        Args:
            articles: Список статей
            
        Returns:
            pandas.DataFrame
        """
        import pandas as pd
        
        data = []
        for article in articles:
            data.append({
                'Заголовок': article['title'],
                'URL': article['url'],
                'Дата': article['date'],
                'Ключевые слова': ', '.join(article.get('keywords_found', [])),
                'Фрагмент': article.get('snippet', '')[:200]
            })
        
        return pd.DataFrame(data)
    
    @staticmethod
    def format_for_gigachat(articles: List[Dict], filial_name: str, keyword: str) -> str:
        """
        Форматирует статьи для анализа в GigaChat
        
        Args:
            articles: Список статей
            filial_name: Название филиала
            keyword: Ключевое слово
            
        Returns:
            Текст для отправки в GigaChat
        """
        if not articles:
            return f"Статей с упоминанием '{keyword}' на сайте {filial_name} не найдено."
        
        text = f"Анализ статей с сайта {filial_name} по запросу '{keyword}':\n\n"
        text += f"Найдено статей: {len(articles)}\n\n"
        
        for i, article in enumerate(articles[:5], 1):  # Берем первые 5 для анализа
            text += f"{i}. {article['date']} - {article['title']}\n"
            if article.get('snippet'):
                text += f"   Фрагмент: {article['snippet'][:150]}...\n"
            text += "\n"
        
        if len(articles) > 5:
            text += f"... и еще {len(articles) - 5} статей\n"
        
        return text