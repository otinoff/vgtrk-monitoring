import streamlit as st
import pandas as pd
import time
from datetime import datetime
import json
import os

# Добавляем путь к модулям
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

from modules.google_sheets import GoogleSheetsManager
from modules.site_parser import SiteParser
from modules.gigachat_client import GigaChatClient
from config.settings import GIGACHAT_API_KEY, GIGACHAT_CLIENT_ID

# Настройка страницы
st.set_page_config(
    page_title="Парсинг сайтов через Google Sheets",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Инициализация состояния сессии
if 'parsing_results' not in st.session_state:
    st.session_state.parsing_results = []
if 'current_status' not in st.session_state:
    st.session_state.current_status = "Готов к работе"
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'logs' not in st.session_state:
    st.session_state.logs = []

def log_message(message: str, level: str = "info"):
    """Функция для логирования сообщений"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = {
        'timestamp': timestamp,
        'message': message,
        'level': level
    }
    st.session_state.logs.append(log_entry)
    
    # Выводим в соответствующий виджет Streamlit
    if level == "error":
        st.error(f"[{timestamp}] {message}")
    elif level == "warning":
        st.warning(f"[{timestamp}] {message}")
    elif level == "success":
        st.success(f"[{timestamp}] {message}")
    else:
        st.info(f"[{timestamp}] {message}")

def main():
    st.title("🤖 Админка парсинга сайтов")
    st.markdown("---")
    
    # Боковая панель
    with st.sidebar:
        st.header("⚙️ Настройки")
        
        # URL Google таблицы
        spreadsheet_url = st.text_input(
            "URL Google таблицы",
            placeholder="https://docs.google.com/spreadsheets/d/...",
            help="Вставьте URL таблицы с сайтами"
        )
        
        # Настройки GigaChat
        st.subheader("🤖 GigaChat")
        gigachat_model = st.selectbox(
            "Модель", 
            ["GigaChat", "GigaChat-Pro"],
            index=0
        )
        
        temperature = st.slider(
            "Температура", 
            0.1, 1.0, 0.7, 0.1,
            help="Контролирует креативность ответов"
        )
        
        # Диапазон обработки
        st.subheader("📊 Диапазон обработки")
        start_row = st.number_input(
            "От строки", 
            min_value=1, 
            value=1,
            help="С какой строки начать обработку"
        )
        
        end_row = st.number_input(
            "До строки", 
            min_value=start_row, 
            value=100,
            help="По какую строку обрабатывать"
        )
        
        # Кнопки управления
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            start_button = st.button(
                "🚀 Начать парсинг",
                type="primary",
                disabled=st.session_state.processing,
                use_container_width=True
            )
        
        with col2:
            stop_button = st.button(
                "⏹️ Остановить",
                disabled=not st.session_state.processing,
                use_container_width=True
            )
    
    # Основная область
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📋 Статус обработки")
        
        # Индикатор прогресса
        if st.session_state.processing:
            progress_bar = st.progress(0)
            status_text = st.empty()
            status_text.info(f"🔄 {st.session_state.current_status}")
        
        # Кнопки управления
        if start_button and spreadsheet_url:
            st.session_state.processing = True
            st.session_state.current_status = "Запуск обработки..."
            st.rerun()
            
        if stop_button:
            st.session_state.processing = False
            st.session_state.current_status = "Обработка остановлена"
            st.rerun()
        
        # Обработка данных
        if st.session_state.processing and spreadsheet_url:
            process_sites(
                spreadsheet_url, 
                gigachat_model, 
                temperature, 
                start_row, 
                end_row
            )
    
    with col2:
        st.subheader("📈 Статистика")
        
        # Метрики
        total_processed = len([r for r in st.session_state.parsing_results if r.get('status') == 'completed'])
        total_errors = len([r for r in st.session_state.parsing_results if r.get('status') == 'error'])
        
        st.metric("Обработано сайтов", total_processed)
        st.metric("Ошибок", total_errors)
        
        # Текущий статус
        st.info(f"🔄 {st.session_state.current_status}")
    
    # Логи
    st.markdown("---")
    st.subheader("📝 Логи выполнения")
    
    # Отображение логов
    log_container = st.container()
    with log_container:
        for log in st.session_state.logs[-50:]:  # Показываем последние 50 записей
            if log['level'] == "error":
                st.error(f"[{log['timestamp']}] {log['message']}")
            elif log['level'] == "warning":
                st.warning(f"[{log['timestamp']}] {log['message']}")
            elif log['level'] == "success":
                st.success(f"[{log['timestamp']}] {log['message']}")
            else:
                st.info(f"[{log['timestamp']}] {log['message']}")
    
    # Автоскролл к последним логам
    st.markdown("<script>window.scrollTo(0, document.body.scrollHeight);</script>", unsafe_allow_html=True)

def process_sites(spreadsheet_url: str, model: str, temperature: float, start_row: int, end_row: int):
    """Обработка сайтов из Google таблицы"""
    try:
        log_message("Начало обработки сайтов", "info")
        
        # Инициализация компонентов
        sheets_manager = GoogleSheetsManager("config/credentials.json")
        site_parser = SiteParser()
        gigachat_client = GigaChatClient(GIGACHAT_API_KEY, GIGACHAT_CLIENT_ID, model, temperature)
        
        # Подключение к Google Sheets
        log_message("Подключение к Google Sheets...", "info")
        sheet_data = sheets_manager.read_sites_sheet(spreadsheet_url, start_row, end_row)
        
        if not sheet_data:
            log_message("Не удалось получить данные из Google Sheets", "error")
            st.session_state.processing = False
            return
        
        total_sites = len(sheet_data)
        log_message(f"Получено {total_sites} сайтов для обработки", "success")
        
        # Обработка каждого сайта
        for idx, site_info in enumerate(sheet_data):
            if not st.session_state.processing:
                log_message("Обработка остановлена пользователем", "warning")
                break
            
            site_url = site_info.get('url')
            site_theme = site_info.get('theme', 'Не указана')
            row_index = site_info.get('row_index')
            
            log_message(f"Обработка сайта {idx+1}/{total_sites}: {site_url}", "info")
            st.session_state.current_status = f"Обработка сайта {idx+1}/{total_sites}: {site_url}"
            
            try:
                # Парсинг сайта
                parsed_content = site_parser.parse_site(site_url)
                
                if parsed_content:
                    # Анализ контента с помощью GigaChat
                    analysis_result = gigachat_client.analyze_content(parsed_content, site_theme)
                    
                    # Сохранение результата
                    result = {
                        'url': site_url,
                        'theme': site_theme,
                        'content': parsed_content[:500] + "..." if len(parsed_content) > 500 else parsed_content,
                        'analysis': analysis_result,
                        'status': 'completed',
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    st.session_state.parsing_results.append(result)
                    log_message(f"Сайт {site_url} успешно обработан", "success")
                    
                    # Запись результата в Google Sheets
                    sheets_manager.write_analysis_result(spreadsheet_url, row_index, analysis_result, "Данные получены")
                else:
                    # Ошибка парсинга
                    result = {
                        'url': site_url,
                        'theme': site_theme,
                        'content': '',
                        'analysis': 'Не удалось получить контент сайта',
                        'status': 'error',
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    st.session_state.parsing_results.append(result)
                    log_message(f"Ошибка парсинга сайта {site_url}", "error")
                    
                    # Запись результата в Google Sheets
                    sheets_manager.write_analysis_result(spreadsheet_url, row_index, "Не удалось получить контент", "Данные не получены")
                
                # Обновление прогресса
                progress = (idx + 1) / total_sites
                st.progress(progress)
                
            except Exception as e:
                log_message(f"Ошибка обработки сайта {site_url}: {str(e)}", "error")
                st.session_state.current_status = f"Ошибка: {str(e)}"
                
                # Запись ошибки в Google Sheets
                sheets_manager.write_analysis_result(spreadsheet_url, row_index, f"Ошибка: {str(e)}", "Ошибка обработки")
                
                continue
        
        # Завершение обработки
        st.session_state.processing = False
        st.session_state.current_status = "Обработка завершена"
        log_message("Обработка всех сайтов завершена", "success")
        
    except Exception as e:
        log_message(f"Критическая ошибка: {str(e)}", "error")
        st.session_state.processing = False
        st.session_state.current_status = f"Критическая ошибка: {str(e)}"

if __name__ == "__main__":
    main()