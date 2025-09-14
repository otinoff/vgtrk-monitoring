"""
Тестовый скрипт для проверки отображения карточек с результатами
"""

import streamlit as st
from app_sqlite_results_cards import ResultsCardsDisplay
from datetime import datetime

# Создаем тестовые данные
test_results = [
    # ГТРК Саха с найденными статьями
    {
        'filial_id': 1,
        'filial_name': 'ГТРК "Саха"',
        'federal_district': 'ДФО',
        'region': 'Республика Саха (Якутия)',
        'url': 'https://gtrksakha.ru',
        'search_query_id': 1,
        'query_text': 'Конгресс',
        'status': 'success',
        'search_mode': 'sitemap_no_ai',
        'metrics': {'articles_found': 2},
        'articles': [
            {
                'title': 'В Якутске пройдет международный медицинский конгресс',
                'url': 'https://gtrksakha.ru/news/v-yakutske-proydet-kongress',
                'date': '12.09.2025',
                'snippet': 'Международный медицинский конгресс соберет ведущих специалистов из разных стран...'
            },
            {
                'title': 'Итоги конгресса по развитию здравоохранения',
                'url': 'https://gtrksakha.ru/news/itogi-kongressa',
                'date': '11.09.2025',
                'snippet': 'Подведены итоги крупнейшего конгресса по вопросам развития системы здравоохранения...'
            }
        ]
    },
    # ГТРК Саха - не найдено по другому запросу
    {
        'filial_id': 1,
        'filial_name': 'ГТРК "Саха"',
        'federal_district': 'ДФО',
        'region': 'Республика Саха (Якутия)',
        'url': 'https://gtrksakha.ru',
        'search_query_id': 2,
        'query_text': '4-й Национальный конгресс «Национальное здравоохранение 2025»',
        'status': 'no_data',
        'search_mode': 'sitemap',
        'gigachat_analysis': 'В представленном тексте отсутствуют прямые упоминания о «4-м Национальном конгрессе»',
        'metrics': {'articles_found': 0},
        'articles': []
    },
    # ГТРК Алтай - найдено
    {
        'filial_id': 2,
        'filial_name': 'ГТРК "Алтай"',
        'federal_district': 'СФО',
        'region': 'Алтайский край',
        'url': 'https://vesti22.tv',
        'search_query_id': 1,
        'query_text': 'Конгресс',
        'status': 'success',
        'search_mode': 'sitemap_no_ai',
        'metrics': {'articles_found': 3},
        'articles': [
            {
                'title': 'Алтайские врачи примут участие в национальном конгрессе',
                'url': 'https://vesti22.tv/news/altayskie-vrachi-kongress',
                'date': '13.09.2025',
                'snippet': 'Делегация алтайских медиков отправится на национальный конгресс...'
            },
            {
                'title': 'Подготовка к медицинскому конгрессу идет полным ходом',
                'url': 'https://vesti22.tv/news/podgotovka-k-kongressu',
                'date': '10.09.2025',
                'snippet': 'В регионе активно готовятся к участию в крупнейшем медицинском форуме...'
            },
            {
                'title': 'Конгресс соберет лучших специалистов страны',
                'url': 'https://vesti22.tv/news/kongress-spetsialisty',
                'date': '09.09.2025',
                'snippet': 'На конгрессе будут обсуждаться актуальные вопросы развития медицины...'
            }
        ]
    },
    # ГТРК Кострома - не найдено
    {
        'filial_id': 3,
        'filial_name': 'ГТРК "Кострома"',
        'federal_district': 'ЦФО',
        'region': 'Костромская область',
        'url': 'https://gtrkkostroma.ru',
        'search_query_id': 1,
        'query_text': 'Конгресс',
        'status': 'no_data',
        'search_mode': 'sitemap',
        'metrics': {'articles_found': 0},
        'articles': []
    }
]

# Настройка страницы
st.set_page_config(
    page_title="Тест отображения карточек",
    page_icon="🎴",
    layout="wide"
)

st.title("🎴 Тестирование отображения карточек результатов")
st.markdown("---")

# Создаем и отображаем карточки
cards_display = ResultsCardsDisplay(test_results)
cards_display.display_cards()