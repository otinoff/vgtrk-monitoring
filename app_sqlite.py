import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta
import json
import os
import sys
from pathlib import Path

# Добавляем путь к модулям
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

# Импортируем модули
from modules.database import VGTRKDatabase
from modules.site_parser import SiteParser
from modules.gigachat_client import GigaChatClient
from modules.advanced_logger import AdvancedLogger, LogLevel, get_logger
from modules.scrapy_parser import ScrapyParser  # Новый модуль для Sitemap парсинга
from modules.results_formatter import SitemapResultsFormatter
from app_sqlite_results_cards import ResultsCardsDisplay
from config.settings import GIGACHAT_API_KEY, GIGACHAT_CLIENT_ID

# Настройка страницы
st.set_page_config(
    page_title="Мониторинг филиалов ВГТРК",
    page_icon="📺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Инициализация базы данных
def init_database():
    """Инициализация подключения к базе данных (без кеширования для обновления методов)"""
    return VGTRKDatabase("data/vgtrk_monitoring.db")

# Инициализация состояния сессии
if 'parsing_results' not in st.session_state:
    st.session_state.parsing_results = []
if 'current_status' not in st.session_state:
    st.session_state.current_status = "Готов к работе"
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'selected_filials' not in st.session_state:
    st.session_state.selected_filials = []
if 'log_level' not in st.session_state:
    st.session_state.log_level = LogLevel.INFO
if 'logger' not in st.session_state:
    st.session_state.logger = get_logger(st.session_state.log_level)

def log_message(message: str, level: str = "INFO", details: dict = None):
    """Функция для логирования сообщений через расширенный логгер"""
    st.session_state.logger.log(level.upper(), message, details)

def main():
    st.title("📺 Система мониторинга филиалов ВГТРК")
    st.markdown("---")
    
    # Инициализация БД
    db = init_database()
    
    # Создаем вкладки
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏢 Филиалы", 
        "🔍 Мониторинг", 
        "📊 Результаты", 
        "📈 Статистика",
        "⚙️ Настройки"
    ])
    
    # Вкладка: Филиалы
    with tab1:
        show_filials_tab(db)
    
    # Вкладка: Мониторинг
    with tab2:
        show_monitoring_tab(db)
    
    # Вкладка: Результаты
    with tab3:
        show_results_tab(db)
    
    # Вкладка: Статистика
    with tab4:
        show_statistics_tab(db)
    
    # Вкладка: Настройки
    with tab5:
        show_settings_tab(db)

def show_filials_tab(db: VGTRKDatabase):
    """Вкладка управления филиалами с интерактивной таблицей"""
    
    # Импортируем новый модуль для интерактивной таблицы
    from modules.filials_table_editor import FilialsTableEditor
    
    # Создаём экземпляр редактора таблицы
    table_editor = FilialsTableEditor()
    
    # Отображаем интерактивную таблицу
    table_editor.display_interactive_table()
    
    return  # Заменяем старый код на новый модуль
    
    # Старый код ниже (оставлен для совместимости, но не выполняется)
    st.header("🏢 Управление филиалами")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.subheader("Фильтры")
        
        # Фильтр по округам
        all_filials = db.get_all_filials()
        districts = sorted(list(set(f['federal_district'] for f in all_filials if f.get('federal_district'))))
        districts.insert(0, "Все округа")
        
        selected_district = st.selectbox(
            "Федеральный округ",
            districts,
            help="Выберите федеральный округ для фильтрации"
        )
        
        # Фильтр по активности
        show_active_only = st.checkbox("Только активные", value=True)
        
        # Фильтр по наличию sitemap
        sitemap_filter = st.selectbox(
            "Фильтр Sitemap",
            ["Все", "С Sitemap", "Без Sitemap"]
        )
        
        # Статистика
        if selected_district == "Все округа":
            filtered_filials = all_filials
        else:
            filtered_filials = [f for f in all_filials if f['federal_district'] == selected_district]
        
        if show_active_only:
            filtered_filials = [f for f in filtered_filials if f['is_active'] == 1]
        
        # Применяем фильтр sitemap
        if sitemap_filter == "С Sitemap":
            filtered_filials = [f for f in filtered_filials if f.get('sitemap_url')]
        elif sitemap_filter == "Без Sitemap":
            filtered_filials = [f for f in filtered_filials if f.get('website') and not f.get('sitemap_url')]
        
        # Статистика по sitemap
        with_sitemap = len([f for f in filtered_filials if f.get('sitemap_url')])
        without_sitemap = len([f for f in filtered_filials if f.get('website') and not f.get('sitemap_url')])
        
        col_stat1, col_stat2 = st.columns(2)
        with col_stat1:
            st.metric("Найдено филиалов", len(filtered_filials))
        with col_stat2:
            st.metric("С Sitemap", f"{with_sitemap}/{len(filtered_filials)}")
        
        # Кнопка импорта из CSV
        st.markdown("---")
        if st.button("📥 Импортировать из CSV", use_container_width=True):
            csv_path = Path("../ГТРК/vgtrk_filials_final.csv")
            if not csv_path.exists():
                csv_path = Path("ГТРК/vgtrk_filials_final.csv")
            
            if csv_path.exists():
                count = db.import_filials_from_csv(str(csv_path), clear_existing=False)
                st.success(f"✅ Импортировано {count} филиалов")
                st.rerun()
            else:
                st.error("❌ CSV файл не найден")
        
        # Кнопка поиска sitemap
        if st.button("🔍 Найти Sitemap", use_container_width=True,
                     help="Автоматический поиск sitemap для филиалов без sitemap"):
            # Проверяем количество филиалов без sitemap
            without_sitemap = [f for f in filtered_filials
                             if f.get('website') and not f.get('sitemap_url')]
            
            if without_sitemap:
                st.info(f"🔍 Поиск sitemap для {len(without_sitemap)} филиалов...")
                
                # Импортируем модуль поиска sitemap
                from sitemap_finder import find_sitemap_for_filial, save_sitemap_to_db
                
                found_count = 0
                progress_bar = st.progress(0)
                
                for idx, filial in enumerate(without_sitemap[:10]):  # Ограничиваем 10 филиалами за раз
                    progress_bar.progress((idx + 1) / min(len(without_sitemap), 10))
                    website = filial.get('website')
                    if website:
                        if not website.startswith(('http://', 'https://')):
                            website = f'https://{website}'
                        
                        sitemap_url = find_sitemap_for_filial(website)
                        if sitemap_url:
                            # Сохраняем в БД
                            save_sitemap_to_db(filial['id'], sitemap_url, db_path)
                            found_count += 1
                            st.success(f"✅ {filial['name']}: найден {sitemap_url}")
                
                progress_bar.empty()
                if found_count > 0:
                    st.success(f"🎉 Найдено {found_count} новых sitemap!")
                    st.rerun()
                else:
                    st.warning("Новые sitemap не найдены")
            else:
                st.info("✅ У всех активных филиалов есть sitemap или нет сайта")
    
    with col2:
        st.subheader("Список филиалов")
        
        # Режим редактирования
        edit_mode = st.checkbox("🔧 Режим редактирования сайтов")
        
        # Таблица филиалов
        if filtered_filials:
            # Получаем адреса сайтов, коды регионов и sitemap_url из БД
            import sqlite3
            db_path = "data/vgtrk_monitoring.db"
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, website_url, region_code, sitemap_url FROM filials")
                result = cursor.fetchall()
                websites_dict = {r[0]: r[1] for r in result}
                codes_dict = {r[0]: r[2] for r in result}
                sitemaps_dict = {r[0]: r[3] for r in result}
            
            # Обновляем данные филиалов с адресами сайтов, кодами и sitemap
            for filial in filtered_filials:
                if filial['id'] in websites_dict:
                    filial['website'] = websites_dict[filial['id']]
                if filial['id'] in codes_dict:
                    filial['region_code'] = codes_dict[filial['id']]
                if filial['id'] in sitemaps_dict:
                    filial['sitemap_url'] = sitemaps_dict[filial['id']]
            
            if edit_mode:
                # Режим редактирования
                st.info("📝 Режим редактирования: измените адреса сайтов и sitemap и нажмите кнопку сохранения")
                
                for idx, filial in enumerate(filtered_filials):
                    with st.expander(f"{filial['name']} - {filial.get('region', '')}"):
                        col_e1, col_e2, col_e3 = st.columns([3, 3, 1])
                        
                        with col_e1:
                            # Поле для редактирования сайта
                            current_site = filial.get('website', '')
                            new_site = st.text_input(
                                "Адрес сайта",
                                value=current_site or '',
                                key=f"site_{filial['id']}",
                                placeholder="Введите адрес сайта (например: vesti42.ru)"
                            )
                        
                        with col_e2:
                            # Поле для редактирования sitemap
                            current_sitemap = filial.get('sitemap_url', '')
                            new_sitemap = st.text_input(
                                "Sitemap URL",
                                value=current_sitemap or '',
                                key=f"sitemap_{filial['id']}",
                                placeholder="Например: /sitemap.xml или полный URL"
                            )
                        
                        with col_e3:
                            # Показываем код региона
                            code = filial.get('region_code', '')
                            st.metric("Код региона", code if code else "—")
                        
                        # Кнопка сохранения
                        if st.button(f"💾 Сохранить", key=f"save_{filial['id']}"):
                            with sqlite3.connect(db_path) as conn:
                                cursor = conn.cursor()
                                if new_site or new_sitemap:
                                    cursor.execute("""
                                        UPDATE filials
                                        SET website_url = ?, sitemap_url = ?
                                        WHERE id = ?
                                    """, (new_site if new_site else None,
                                          new_sitemap if new_sitemap else None,
                                          filial['id']))
                                else:
                                    cursor.execute("""
                                        UPDATE filials
                                        SET website_url = NULL, sitemap_url = NULL
                                        WHERE id = ?
                                    """, (filial['id'],))
                                conn.commit()
                            st.success(f"✅ Данные обновлены для {filial['name']}")
                            st.rerun()
            else:
                # Обычный режим просмотра
                # Преобразуем в DataFrame для удобного отображения
                df = pd.DataFrame(filtered_filials)
                
                # Выбираем нужные колонки (добавим проверку наличия)
                available_columns = []
                desired_columns = ['id', 'name', 'federal_district', 'region_code', 'website', 'sitemap_url', 'is_active']
                for col in desired_columns:
                    if col in df.columns:
                        available_columns.append(col)
                
                df = df[available_columns]
                
                # Переименовываем колонки для отображения
                column_mapping = {
                    'id': 'ID',
                    'name': 'Название',
                    'federal_district': 'Округ',
                    'region_code': 'Код',
                    'website': 'Сайт',
                    'sitemap_url': 'Sitemap',
                    'is_active': 'Активен'
                }
                df.rename(columns=column_mapping, inplace=True)
                
                # Форматируем колонку Сайт для отображения ссылок
                if 'Сайт' in df.columns:
                    df['Сайт'] = df['Сайт'].fillna('Нет сайта')
                
                # Форматируем код региона
                if 'Код' in df.columns:
                    df['Код'] = df['Код'].fillna(0).astype(int)
                    df['Код'] = df['Код'].apply(lambda x: f"{x:02d}" if x > 0 else "—")
                
                # Форматируем колонку Sitemap с индикаторами
                if 'Sitemap' in df.columns:
                    df['Sitemap'] = df['Sitemap'].apply(lambda x: '✅' if x else '❌')
            
                # Отображаем таблицу с возможностью выбора
                selected_rows = st.dataframe(
                    df,
                    use_container_width='stretch',
                    hide_index=True,
                    selection_mode="multi-row",
                    on_select="rerun"
                )
                
                # Сохраняем выбранные филиалы
                if selected_rows and selected_rows.selection.rows:
                    st.session_state.selected_filials = [
                        filtered_filials[i] for i in selected_rows.selection.rows
                    ]
                    st.info(f"Выбрано филиалов: {len(st.session_state.selected_filials)}")
        else:
            st.info("Филиалы не найдены")

def show_monitoring_tab(db: VGTRKDatabase):
    """Вкладка мониторинга"""
    st.header("🔍 Мониторинг контента")
    
    # Боковая панель настроек
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.subheader("⚙️ Настройки мониторинга")
        
        # Уровень логирования
        st.markdown("### 📊 Уровень детализации логов")
        log_level_options = {
            "🔍 DEBUG - Максимальная детализация": LogLevel.DEBUG,
            "ℹ️ INFO - Основные операции": LogLevel.INFO,
            "⚠️ WARNING - Только предупреждения": LogLevel.WARNING,
            "❌ ERROR - Только ошибки": LogLevel.ERROR
        }
        
        selected_level = st.selectbox(
            "Выберите уровень логирования",
            options=list(log_level_options.keys()),
            index=1,  # По умолчанию INFO
            help="DEBUG показывает все технические детали, ERROR только критические ошибки"
        )
        
        new_level = log_level_options[selected_level]
        if new_level != st.session_state.log_level:
            st.session_state.log_level = new_level
            st.session_state.logger.set_level(new_level)
            st.success(f"✅ Уровень логирования изменен на {new_level.value}")
        
        st.markdown("---")
        
        # Режим поиска
        st.markdown("### 🔎 Режим поиска")
        search_mode_options = {
            "⚡ Только главная страница": "main_only",
            "📰 Главная + Новости": "main_and_news",
            "📡 RSS поиск (новинка!)": "rss_search",
            "🕷️ Sitemap архив (глубокий поиск)": "sitemap_search"
        }
        
        selected_search_mode = st.selectbox(
            "Выберите режим поиска",
            options=list(search_mode_options.keys()),
            index=3,  # По умолчанию Sitemap архив
            help="""
            ⚡ Только главная: быстрый поиск по метаданным главной страницы (10-20x быстрее)
            📰 Главная + Новости: поиск по метаданным главной и новостных страниц (5-10x быстрее)
            📡 RSS поиск: супер-быстрый поиск только по свежим новостям из RSS ленты
            🕷️ Sitemap архив: полный поиск по ВСЕМУ архиву сайта за выбранный период
            """
        )
        
        search_mode = search_mode_options[selected_search_mode]
        
        # Настройки периода для Sitemap поиска
        if search_mode == "sitemap_search":
            st.markdown("### 📅 Период поиска")
            
            # Выбор типа поиска по дате
            date_search_type = st.radio(
                "Тип поиска по дате",
                ["Быстрый выбор", "Конкретная дата", "Диапазон дат"],
                horizontal=True,
                help="Быстрый выбор - предустановленные периоды, Конкретная дата - выбор через календарь, Диапазон дат - выбор периода с/по"
            )
            
            if date_search_type == "Быстрый выбор":
                period_options = {
                    "За сегодня": 1,
                    "За вчера": 1,  # Будет обработано особым образом
                    "За 3 дня": 3,
                    "За 4 дня": 4,
                    "За неделю": 7,
                    "За 2 недели": 14,
                    "За месяц": 30,
                    "За 3 месяца": 90
                }
                
                selected_period = st.selectbox(
                    "Выберите период архива",
                    options=list(period_options.keys()),
                    index=3,  # По умолчанию за 4 дня
                    help="Поиск по архиву сайта за указанный период"
                )
                
                search_days = period_options[selected_period]
                
                # Особая обработка для "За вчера"
                if selected_period == "За вчера":
                    specific_date = datetime.now() - timedelta(days=1)
                    search_specific_date = specific_date.date()
                    search_days = None  # Будем использовать конкретную дату
                else:
                    search_specific_date = None
                    
            elif date_search_type == "Конкретная дата":
                # Календарь для выбора даты
                selected_date = st.date_input(
                    "Выберите дату для поиска",
                    value=datetime.now().date() - timedelta(days=2),  # По умолчанию позавчера
                    max_value=datetime.now().date(),
                    min_value=datetime.now().date() - timedelta(days=365),
                    help="Поиск статей за конкретную дату"
                )
                
                search_specific_date = selected_date
                search_days = None  # Будем использовать конкретную дату
                
            else:  # Диапазон дат
                col_date1, col_date2 = st.columns(2)
                
                with col_date1:
                    date_from = st.date_input(
                        "Дата начала",
                        value=datetime.now().date() - timedelta(days=7),
                        max_value=datetime.now().date(),
                        min_value=datetime.now().date() - timedelta(days=365),
                        help="Начальная дата диапазона"
                    )
                
                with col_date2:
                    date_to = st.date_input(
                        "Дата окончания",
                        value=datetime.now().date(),
                        max_value=datetime.now().date(),
                        min_value=date_from,
                        help="Конечная дата диапазона"
                    )
                
                # Вычисляем количество дней
                search_days = (date_to - date_from).days + 1
                search_specific_date = None
                search_date_range = (date_from, date_to)
            
            # Опция использования GigaChat
            use_gigachat = st.checkbox(
                "🤖 Анализировать через GigaChat",
                value=False,
                help="Отправлять найденные статьи в GigaChat для анализа (использует токены)"
            )
            
            # Формируем информационное сообщение
            if search_specific_date:
                info_msg = f"🕷️ Sitemap поиск: статьи за {search_specific_date.strftime('%d.%m.%Y')}. "
            else:
                info_msg = f"🕷️ Sitemap поиск: полный архив за {search_days} дней. "
            info_msg += 'С анализом GigaChat' if use_gigachat else 'Без GigaChat (список статей)'
            st.info(info_msg)
        else:
            search_days = None
            use_gigachat = True  # Для других режимов всегда используем GigaChat
        
        # Описание выбранного режима
        if search_mode == "main_only":
            st.info("💡 Мета-поиск по главной странице: максимальная скорость, 90% экономия токенов")
        elif search_mode == "main_and_news":
            st.info("💡 Расширенный мета-поиск: включает новостные страницы, 80% экономия токенов")
        elif search_mode == "rss_search":
            st.info("🚀 RSS поиск: только свежие новости, экстремальная скорость, 95% экономия токенов!")
        
        st.markdown("---")
        
        # Выбор режима обработки для Sitemap
        if search_mode == "sitemap_search":
            st.markdown("### ⚡ Режим обработки")
            processing_mode = st.radio(
                "Выберите режим обработки филиалов",
                ["🚀 Асинхронный (параллельно)", "🐌 Синхронный (по очереди)"],
                index=0,
                help="""
                🚀 Асинхронный: обработка до 20 филиалов одновременно (в 5-10 раз быстрее)
                🐌 Синхронный: филиалы обрабатываются последовательно (стабильнее для отладки)
                """
            )
            
            if processing_mode == "🚀 Асинхронный (параллельно)":
                max_concurrent = st.slider(
                    "Макс. параллельных соединений",
                    min_value=5,
                    max_value=50,
                    value=20,
                    help="Больше соединений = быстрее, но выше нагрузка на сеть"
                )
                use_async = True
            else:
                max_concurrent = 1
                use_async = False
        else:
            use_async = False
            max_concurrent = 1
        
        st.markdown("---")
        
        # Выбор филиалов для мониторинга
        monitoring_mode = st.radio(
            "Режим выбора филиалов",
            ["Все активные", "По округу", "Выбранные вручную"]
        )
        
        filials_to_monitor = []
        
        if monitoring_mode == "Все активные":
            filials_to_monitor = db.get_all_filials(active_only=True)
        
        elif monitoring_mode == "По округу":
            all_filials = db.get_all_filials()
            districts = sorted(list(set(f['federal_district'] for f in all_filials)))
            selected_districts = st.multiselect(
                "Выберите округа",
                districts,
                default=["СФО"] if "СФО" in districts else []
            )
            for district in selected_districts:
                filials_to_monitor.extend(db.get_filials_by_district(district))
        
        elif monitoring_mode == "Выбранные вручную":
            if st.session_state.selected_filials:
                filials_to_monitor = st.session_state.selected_filials
            else:
                st.warning("Выберите филиалы на вкладке 'Филиалы'")
        
        st.metric("Филиалов для мониторинга", len(filials_to_monitor))
        
        # Поисковые запросы
        st.markdown("---")
        st.subheader("🔎 Поисковые запросы")
        
        search_queries = db.get_search_queries()
        if search_queries:
            # Группируем по категориям
            categories = {}
            for q in search_queries:
                cat = q.get('category', 'без категории')
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(q)
            
            selected_queries = []
            for cat, queries in categories.items():
                st.write(f"**{cat.capitalize()}:**")
                for q in queries:
                    if st.checkbox(
                        q['query_text'], 
                        key=f"query_{q['id']}",
                        help=q.get('description', '')
                    ):
                        selected_queries.append(q)
        else:
            st.info("Нет доступных поисковых запросов")
            if st.button("Добавить стандартные запросы"):
                # Добавляем стандартные запросы
                standard_queries = [
                    ("ВГТРК", "обязательный", "Упоминание головной компании"),
                    ("губернатор", "региональные", "Деятельность губернатора"),
                    ("местные новости", "региональные", "Региональные события")
                ]
                for query, cat, desc in standard_queries:
                    db.add_search_query(query, cat, desc)
                st.rerun()
        
        # Настройки GigaChat
        st.markdown("---")
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
        
        # Кнопка запуска
        st.markdown("---")
        start_button = st.button(
            "🚀 Начать мониторинг",
            type="primary",
            disabled=st.session_state.processing or not filials_to_monitor,
            use_container_width='stretch'
        )
        
        if st.session_state.processing:
            stop_button = st.button(
                "⏹️ Остановить",
                use_container_width='stretch'
            )
            if stop_button:
                st.session_state.processing = False
                st.rerun()
    
    with col2:
        st.subheader("📋 Процесс мониторинга")
        
        # Статус и прогресс
        status_container = st.container()
        with status_container:
            if st.session_state.processing:
                st.info(f"🔄 {st.session_state.current_status}")
                progress_bar = st.progress(0)
            else:
                st.info(f"💤 {st.session_state.current_status}")
        
        # Запуск мониторинга
        if start_button and filials_to_monitor:
            st.session_state.processing = True
            st.session_state.current_status = "Запуск мониторинга..."
            
            # Запускаем процесс мониторинга с режимом поиска
            monitoring_params = {
                'db': db,
                'filials': filials_to_monitor,
                'queries': selected_queries if 'selected_queries' in locals() else [],
                'model': gigachat_model,
                'temperature': temperature,
                'search_mode': search_mode
            }
            
            # Добавляем параметры для Sitemap поиска
            if search_mode == "sitemap_search":
                monitoring_params['search_days'] = search_days
                monitoring_params['use_gigachat'] = use_gigachat
                monitoring_params['search_specific_date'] = search_specific_date if 'search_specific_date' in locals() else None
                monitoring_params['search_date_range'] = search_date_range if 'search_date_range' in locals() else None
                monitoring_params['use_async'] = use_async if 'use_async' in locals() else False
                monitoring_params['max_concurrent'] = max_concurrent if 'max_concurrent' in locals() else 1
            
            # Выбираем функцию обработки в зависимости от режима
            if monitoring_params.get('use_async') and search_mode == "sitemap_search":
                # Используем асинхронную обработку
                process_monitoring_async_wrapper(**monitoring_params)
            else:
                # Используем синхронную обработку
                process_monitoring(**monitoring_params)
        
        # Логи
        st.markdown("---")
        st.subheader("📝 Логи выполнения")
        
        # Контроль логов
        col_log1, col_log2, col_log3 = st.columns([2, 1, 1])
        with col_log1:
            log_filter = st.selectbox(
                "Фильтр логов",
                ["Все", "DEBUG", "INFO", "WARNING", "ERROR"],
                help="Фильтровать логи по уровню"
            )
        with col_log2:
            if st.button("🗑️ Очистить логи"):
                st.session_state.logger.clear_old_logs(keep_last=0)
                st.rerun()
        with col_log3:
            if st.button("💾 Экспорт логов"):
                export_path = f"logs/export_{datetime.now():%Y%m%d_%H%M%S}.json"
                Path("logs").mkdir(exist_ok=True)
                st.session_state.logger.export_logs(export_path)
                st.success(f"Логи экспортированы в {export_path}")
        
        # Контейнер для логов
        log_container = st.container(height=400)
        with log_container:
            # Получаем отформатированные логи
            filter_level = log_filter if log_filter != "Все" else None
            logs = st.session_state.logger.get_logs(level_filter=filter_level, limit=100)
            
            for log in reversed(logs):  # Показываем новые сверху
                timestamp = log['timestamp']
                message = log['message']
                level = log['level']
                details = log.get('details', {})
                
                # Форматируем вывод в зависимости от уровня
                if level == "ERROR":
                    st.error(f"❌ [{timestamp}] {message}")
                elif level == "WARNING":
                    st.warning(f"⚠️ [{timestamp}] {message}")
                elif level == "DEBUG" and details:
                    # Для DEBUG показываем детали
                    with st.expander(f"🔍 [{timestamp}] {message}"):
                        for key, value in details.items():
                            st.text(f"  {key}: {value}")
                elif level == "INFO":
                    # Особая обработка для разных типов INFO сообщений
                    if "✅" in message:
                        st.success(f"✅ [{timestamp}] {message}")
                    elif "❌" in message:
                        st.error(f"❌ [{timestamp}] {message}")
                    elif "📄" in message and details.get('text_preview'):
                        # Парсинг с ПОДРОБНЫМ превью текста
                        with st.expander(f"📄 [{timestamp}] {message}", expanded=True):
                            st.text(f"URL: {details.get('url', 'не указан')}")
                            st.text("Превью контента сайта (первые 500 символов):")
                            # Разделяем текст на строки для лучшей читаемости
                            preview_text = details['text_preview']
                            # Форматируем текст с переносами
                            formatted_preview = "\n".join([
                                line.strip() for line in preview_text.split("\n")
                                if line.strip()
                            ][:10])  # Показываем первые 10 непустых строк
                            st.text_area(
                                "Содержимое страницы:",
                                value=formatted_preview,
                                height=200,
                                disabled=True
                            )
                    elif "📋" in message and details.get('fragment'):
                        # Найденный фрагмент
                        with st.expander(f"📋 [{timestamp}] {message}"):
                            st.text("Найденный фрагмент:")
                            st.code(details['fragment'], language=None)
                    elif "🤖" in message and details.get('analysis'):
                        # Ответ GigaChat
                        with st.expander(f"🤖 [{timestamp}] {message}"):
                            st.text(f"Запрос: {details.get('query', 'не указан')}")
                            st.text("Ответ GigaChat:")
                            st.info(details['analysis'])
                    elif details:
                        # Общий случай с деталями
                        with st.expander(f"ℹ️ [{timestamp}] {message}"):
                            for key, value in details.items():
                                st.text(f"  {key}: {value}")
                    else:
                        st.info(f"ℹ️ [{timestamp}] {message}")
                else:
                    st.text(f"[{timestamp}] {message}")

def process_monitoring_async_wrapper(db: VGTRKDatabase, filials: list, queries: list, model: str, temperature: float,
                                    search_mode: str = "main_only", search_days: int = None, use_gigachat: bool = True,
                                    search_specific_date = None, search_date_range = None,
                                    use_async: bool = False, max_concurrent: int = 20):
    """Обёртка для асинхронного мониторинга"""
    
    from app_sqlite_async import run_async_monitoring_streamlit
    
    logger = st.session_state.logger
    logger.log("INFO", f"Запуск АСИНХРОННОГО мониторинга с {max_concurrent} параллельными соединениями")
    
    # Создаем сессию мониторинга
    search_period = None
    if search_specific_date:
        search_period = f"Дата: {search_specific_date}"
    elif search_days:
        search_period = f"За {search_days} дней"
    elif search_date_range:
        date_from, date_to = search_date_range
        search_period = f"С {date_from} по {date_to}"
    else:
        search_period = "Текущий день"
    
    session_id = None
    if hasattr(db, 'start_monitoring_session'):
        session_id = db.start_monitoring_session(
            session_name=f"Асинхронный мониторинг {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            search_mode=f"{search_mode}_async",
            search_period=search_period,
            search_date=str(search_specific_date) if search_specific_date else None
        )
        logger.log("INFO", f"Создана сессия мониторинга #{session_id}")
    
    # Прогресс-плейсхолдер
    progress_placeholder = st.empty()
    
    try:
        # Запускаем асинхронный мониторинг
        stats = run_async_monitoring_streamlit(
            db=db,
            filials=filials,
            queries=queries,
            search_days=search_days or 7,
            max_concurrent=max_concurrent,
            session_id=session_id,
            progress_placeholder=progress_placeholder
        )
        
        # Обновляем статус
        st.session_state.processing = False
        st.session_state.current_status = "Мониторинг завершен"
        
        # Логируем результаты
        logger.log("INFO", f"✅ Асинхронный мониторинг завершен за {stats['total_time']:.1f} сек")
        logger.log("INFO", f"Обработано: {stats['total_filials']} филиалов")
        logger.log("INFO", f"Успешно: {stats['success_count']}, Ошибок: {stats['error_count']}, Нет данных: {stats['no_data_count']}")
        logger.log("INFO", f"Найдено статей: {stats['total_articles']}")
        logger.log("INFO", f"Среднее время на филиал: {stats['avg_time_per_filial']:.2f} сек")
        
        # Обновляем сессию
        if session_id and hasattr(db, 'update_monitoring_session'):
            db.update_monitoring_session(
                session_id,
                filials_count=stats['total_filials'],
                queries_count=len(queries),
                results_count=stats['results_saved'],
                status='completed'
            )
        
        # Показываем финальную статистику
        progress_placeholder.success(f"""
        ✅ **Асинхронный мониторинг завершен!**
        
        - Общее время: **{stats['total_time']:.1f} секунд**
        - Обработано филиалов: **{stats['total_filials']}**
        - Средняя скорость: **{stats['total_filials']/stats['total_time']:.2f} филиалов/сек**
        - Найдено статей: **{stats['total_articles']}**
        
        Ускорение по сравнению с синхронным режимом: **~{max_concurrent/2:.0f}x**
        """)
        
    except Exception as e:
        logger.log("ERROR", f"Ошибка асинхронного мониторинга: {str(e)}")
        st.session_state.processing = False
        st.session_state.current_status = f"Ошибка: {str(e)}"
        
        if session_id and hasattr(db, 'update_monitoring_session'):
            db.update_monitoring_session(
                session_id,
                status='error',
                error_message=str(e)
            )

def process_monitoring(db: VGTRKDatabase, filials: list, queries: list, model: str, temperature: float,
                      search_mode: str = "main_only", search_days: int = None, use_gigachat: bool = True,
                      search_specific_date = None, search_date_range = None,
                      use_async: bool = False, max_concurrent: int = 1):
    """Процесс мониторинга филиалов с разными режимами поиска включая Sitemap"""
    try:
        logger = st.session_state.logger
        logger.log("INFO", "Начало мониторинга филиалов ВГТРК")
        
        # Создаем новую сессию мониторинга
        search_period = None
        if search_specific_date:
            search_period = f"Дата: {search_specific_date}"
        elif search_days:
            search_period = f"За {search_days} дней"
        elif search_date_range:
            date_from, date_to = search_date_range
            search_period = f"С {date_from} по {date_to}"
        else:
            search_period = "Текущий день"
            
        # Проверяем поддержку сессий
        if hasattr(db, 'start_monitoring_session'):
            session_id = db.start_monitoring_session(
                session_name=f"Мониторинг {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                search_mode=search_mode,
                search_period=search_period,
                search_date=str(search_specific_date) if search_specific_date else None
            )
            logger.log("INFO", f"Создана сессия мониторинга #{session_id}")
        else:
            session_id = None
            logger.log("WARNING", "База данных не поддерживает сессии мониторинга")
        
        # Статистика сессии
        session_stats = {
            'total_checked': 0,
            'successful': 0,
            'errors': 0,
            'total_time': 0,
            'total_tokens_used': 0,
            'avg_response_time': 0,
            'avg_page_size': 0
        }
        
        session_start = time.time()
        
        # Инициализация компонентов с уровнем логирования
        site_parser = SiteParser(log_level=st.session_state.log_level)
        gigachat_client = GigaChatClient(
            GIGACHAT_API_KEY,
            GIGACHAT_CLIENT_ID,
            model,
            temperature,
            log_level=st.session_state.log_level
        )
        
        total_filials = len(filials)
        search_mode_names = {
            "main_only": "Только главная страница",
            "main_and_news": "Главная + Новости",
            "rss_search": "RSS лента",
            "sitemap_search": f"Sitemap архив ({search_days} дней)"
        }
        logger.log("INFO", f"Филиалов для проверки: {total_filials} | Режим: {search_mode_names.get(search_mode, search_mode)}")
        
        # Инициализация ScrapyParser для Sitemap режима
        if search_mode == "sitemap_search":
            scrapy_parser = ScrapyParser(logger=logger)
        
        response_times = []
        page_sizes = []
        
        # Обработка каждого филиала
        for idx, filial in enumerate(filials):
            if not st.session_state.processing:
                logger.log("WARNING", "Мониторинг остановлен пользователем")
                break
            
            filial_name = filial['name']
            # Сначала пробуем website_url из БД, потом website
            website = filial.get('website_url') or filial.get('website', '')
            
            # Получаем sitemap_url из БД для передачи в парсер
            sitemap_url = None
            if 'id' in filial:
                # Получаем sitemap_url из БД
                filial_full = db.get_filial_by_id(filial['id'])
                if filial_full:
                    sitemap_url = filial_full.get('sitemap_url')
                    filial['sitemap_url'] = sitemap_url  # Добавляем в словарь для дальнейшего использования
            
            if not website:
                logger.log("WARNING", f"{filial_name}: нет сайта")
                session_stats['errors'] += 1
                continue
            
            # Добавляем протокол если нет (но не для telegram ссылок)
            if not website.startswith(('http://', 'https://', 'vk.com')):
                if website.startswith('t.me/'):
                    website = f"https://{website}"
                elif not website.startswith(('http://', 'https://')):
                    website = f"https://{website}"
            
            logger.log("INFO", f"Проверка {idx+1}/{total_filials}: {filial_name}")
            st.session_state.current_status = f"Проверка {idx+1}/{total_filials}: {filial_name}"
            
            try:
                # Выбираем метод парсинга в зависимости от режима
                if search_mode == "sitemap_search":
                    # Sitemap режим - глубокий поиск по архиву
                    logger.log("INFO", f"🕷️ Sitemap поиск для {filial_name} за {search_days} дней")
                    
                    keywords = [q['query_text'] for q in queries]
                    
                    # Проверяем, есть ли прямой sitemap URL в базе данных
                    sitemap_url = filial.get('sitemap_url')
                    if sitemap_url:
                        logger.log("INFO", f"Используем прямой sitemap URL: {sitemap_url}")
                    
                    # Поиск через Sitemap
                    if search_specific_date:
                        # Если выбрана конкретная дата, используем специальный метод
                        sitemap_results = scrapy_parser.search_with_sitemap_date(
                            website,
                            keywords,
                            search_date=search_specific_date,
                            max_articles=150,  # Увеличиваем лимит для конкретной даты
                            sitemap_url=sitemap_url
                        )
                    else:
                        # Обычный поиск за период
                        sitemap_results = scrapy_parser.search_with_sitemap(
                            website,
                            keywords,
                            days=search_days,
                            max_articles=50,  # Ограничиваем количество для производительности
                            sitemap_url=sitemap_url,  # Передаем прямой URL если есть
                            date_from=search_date_range[0] if search_date_range else None,
                            date_to=search_date_range[1] if search_date_range else None
                        )
                    
                    session_stats['total_checked'] += 1
                    
                    # Инициализируем parsed_content и parse_metrics для режима sitemap
                    parsed_content = None  # Sitemap режим не использует parsed_content
                    parse_metrics = {'mode': 'sitemap', 'articles_checked': len(sitemap_results) if sitemap_results else 0}
                    
                    if sitemap_results:
                        logger.log("INFO", f"📊 {filial_name}: найдено {len(sitemap_results)} статей в архиве")
                        
                        if use_gigachat:
                            # Режим с GigaChat - анализируем найденное
                            for query in queries:
                                query_text = query['query_text']
                                
                                # Фильтруем статьи по конкретному запросу
                                relevant_articles = [
                                    article for article in sitemap_results
                                    if query_text.lower() in ' '.join(article.get('keywords', [])).lower()
                                ]
                                
                                if relevant_articles:
                                    # Используем SitemapResultsFormatter для форматирования
                                    formatter = SitemapResultsFormatter()
                                    formatted_results = formatter.format_sitemap_results(
                                        relevant_articles,
                                        filial_name,
                                        query_text,
                                        max_display=10
                                    )
                                    
                                    # Формируем текст для GigaChat
                                    analysis_text = formatter.format_for_gigachat(
                                        formatted_results['articles'],
                                        filial_name,
                                        query_text
                                    )
                                    
                                    # Отправляем в GigaChat
                                    prompt = f"""Проанализируй найденные статьи с сайта {filial_name}.
                                    Определи релевантность к теме '{query_text}'.
                                    Сделай краткое резюме основных упоминаний."""
                                    
                                    analysis, gigachat_metrics = gigachat_client.analyze_content(
                                        analysis_text[:3000],
                                        prompt
                                    )
                                    
                                    # Сохраняем результат с деталями статей
                                    result = {
                                        'filial_id': filial['id'],
                                        'search_query_id': query['id'],
                                        'url': website,
                                        'page_title': filial_name,
                                        'content': formatted_results['content'],
                                        'gigachat_analysis': analysis,
                                        'relevance_score': min(formatted_results['total_count'] / 10, 1.0),
                                        'status': 'success',
                                        'search_mode': 'sitemap',
                                        'articles': formatted_results['articles'],  # Сохраняем детали статей
                                        'metrics': {
                                            'articles_found': formatted_results['total_count'],
                                            'search_days': search_days,
                                            'gigachat_metrics': gigachat_metrics
                                        }
                                    }
                                    db.save_monitoring_result(filial['id'], result, session_id)
                                    
                                    logger.log("INFO", f"✅ {filial_name}: найдено {formatted_results['total_count']} статей для '{query_text}'")
                                    session_stats['successful'] += 1
                                    session_stats['total_tokens_used'] += gigachat_metrics.get('total_tokens', 0)
                                else:
                                    logger.log("INFO", f"❌ {filial_name}: '{query_text}' не найден в архиве за {search_days} дней")
                        else:
                            # Режим без GigaChat - просто сохраняем список статей
                            for query in queries:
                                query_text = query['query_text']
                                
                                # Фильтруем статьи по конкретному запросу
                                relevant_articles = [
                                    article for article in sitemap_results
                                    if query_text.lower() in ' '.join(article.get('keywords', [])).lower()
                                ]
                                
                                if relevant_articles:
                                    # Используем SitemapResultsFormatter для форматирования
                                    formatter = SitemapResultsFormatter()
                                    formatted_results = formatter.format_sitemap_results(
                                        relevant_articles,
                                        filial_name,
                                        query_text,
                                        max_display=10
                                    )
                                    
                                    result = {
                                        'filial_id': filial['id'],
                                        'search_query_id': query['id'],
                                        'url': website,
                                        'page_title': filial_name,
                                        'content': formatted_results['content'],
                                        'gigachat_analysis': f"Найдено {formatted_results['total_count']} статей (без анализа GigaChat)",
                                        'relevance_score': min(formatted_results['total_count'] / 10, 1.0),
                                        'status': 'success',
                                        'search_mode': 'sitemap_no_ai',
                                        'articles': formatted_results['articles'],  # Сохраняем детали статей
                                        'metrics': {
                                            'articles_found': formatted_results['total_count'],
                                            'search_days': search_days
                                        }
                                    }
                                    db.save_monitoring_result(filial['id'], result, session_id)
                                    
                                    logger.log("INFO", f"📋 {filial_name}: найдено {formatted_results['total_count']} статей для '{query_text}' (без GigaChat)")
                                    session_stats['successful'] += 1
                    else:
                        # Если sitemap_results пустой, это может означать две ситуации:
                        # 1. Sitemap не найден вообще (реальная ошибка)
                        # 2. Sitemap найден, но нет статей с ключевыми словами (нормальная ситуация)
                        
                        # Проверяем, был ли найден sitemap
                        if scrapy_parser.find_sitemap(website, sitemap_url):
                            # Sitemap найден, просто нет релевантных статей
                            logger.log("INFO", f"📊 {filial_name}: Sitemap обработан, релевантных статей не найдено")
                            
                            # Сохраняем результат для каждого запроса
                            for query in queries:
                                result = {
                                    'filial_id': filial['id'],
                                    'search_query_id': query['id'],
                                    'url': website,
                                    'page_title': filial_name,
                                    'content': "Sitemap обработан",
                                    'gigachat_analysis': f"В архиве за {search_days} дней не найдено статей с упоминанием '{query['query_text']}'",
                                    'relevance_score': 0.0,
                                    'status': 'no_data',
                                    'search_mode': 'sitemap',
                                    'articles': [],  # Пустой список статей
                                    'metrics': {
                                        'articles_found': 0,
                                        'search_days': search_days,
                                        'sitemap_found': True
                                    }
                                }
                                db.save_monitoring_result(filial['id'], result, session_id)
                            
                            # Это не ошибка, а нормальный результат
                            session_stats['total_checked'] += 1
                        else:
                            # Реальная ошибка - sitemap не найден
                            logger.log("WARNING", f"⚠️ {filial_name}: Sitemap не найден")
                            session_stats['errors'] += 1
                            
                            # Сохраняем ошибку
                            result = {
                                'filial_id': filial['id'],
                                'url': website,
                                'status': 'error',
                                'error_message': 'Sitemap не найден',
                                'search_mode': 'sitemap'
                            }
                            db.save_monitoring_result(filial['id'], result, session_id)
                        
                        # Инициализируем переменные для избежания ошибки
                        parse_metrics = {'mode': 'sitemap'}
                        parsed_content = None
                        
                elif search_mode == "rss_search":
                    # RSS режим
                    rss_data, parse_metrics = site_parser.parse_rss_feed(website)
                    
                    if rss_data:
                        # Формируем текст для поиска из RSS
                        parsed_content = f"=== RSS ЛЕНТА {filial_name} ===\n"
                        parsed_content += f"Канал: {rss_data.get('channel_title', '')}\n"
                        parsed_content += f"Описание: {rss_data.get('channel_description', '')}\n\n"
                        
                        for item in rss_data.get('items', []):
                            parsed_content += f"--- НОВОСТЬ ---\n"
                            parsed_content += f"Заголовок: {item['title']}\n"
                            parsed_content += f"Описание: {item['description']}\n"
                            parsed_content += f"Ссылка: {item['link']}\n"
                            parsed_content += f"Дата: {item['pubDate']}\n\n"
                    else:
                        parsed_content = None
                else:
                    # Мета-парсинг режим
                    include_news = (search_mode == "main_and_news")
                    parsed_content, parse_metrics = site_parser.parse_meta_data(website, include_news=include_news)
                
                # Сохраняем метрики для статистики
                if parse_metrics.get('response_time'):
                    response_times.append(parse_metrics['response_time'])
                if parse_metrics.get('page_size_kb'):
                    page_sizes.append(parse_metrics['page_size_kb'])
                
                # Для режима sitemap_search счетчик уже увеличен выше, не дублируем
                if search_mode != "sitemap_search":
                    session_stats['total_checked'] += 1
                
                if parsed_content:
                    # Логируем успешный парсинг
                    if search_mode == "rss_search":
                        items_count = parse_metrics.get('items_count', 0)
                        logger.log("INFO", f"📡 {filial_name}: RSS получен ({items_count} новостей)", {
                            "rss_url": parse_metrics.get('rss_url'),
                            "url": website,
                            "mode": "rss_search"
                        })
                    else:
                        pages_count = parse_metrics.get('pages_parsed', 1)
                        headers_count = parse_metrics.get('headers_count', 0)
                        meta_tags_count = parse_metrics.get('meta_tags_count', 0)
                        
                        preview_length = 500  # Показываем первые 500 символов
                        text_preview = parsed_content[:preview_length]
                        if len(parsed_content) > preview_length:
                            text_preview += f"\n... (ещё {len(parsed_content) - preview_length} символов)"
                        
                        logger.log("INFO", f"📄 {filial_name}: Мета-данные получены (страниц: {pages_count}, заголовков: {headers_count}, мета-тегов: {meta_tags_count})", {
                            "text_preview": text_preview,
                            "url": website,
                            "mode": "meta_search"
                        })
                    
                    # Поиск ключевых слов
                    keywords = [q['query_text'] for q in queries]
                    search_results = site_parser.search_keywords(parsed_content, keywords)
                    
                    # Анализ для каждого поискового запроса
                    for query in queries:
                        query_text = query['query_text']
                        query_results = search_results.get(query_text, {})
                        
                        # Для мета-поиска всегда используем GigaChat для анализа
                        logger.log_search_results(filial_name, query_text, query_results)
                        
                        # Логируем найденные фрагменты если есть
                        if query_results.get('occurrences', 0) > 0:
                            contexts = query_results.get('contexts', [])
                            if contexts:
                                first_context = contexts[0][:150] if contexts[0] else ""
                                logger.log("INFO", f"📋 {filial_name}: Найден фрагмент в метаданных для '{query_text}'", {
                                    "fragment": first_context.replace("**", "")
                                })
                        
                        # Отправляем метаданные в GigaChat для анализа
                        logger.log("DEBUG", f"Мета-поиск: анализируем метаданные через GigaChat для '{query_text}'")
                        
                        # Формируем промпт для анализа метаданных
                        prompt = f"""Проанализируй метаданные и заголовки страницы.
                        Определи, есть ли упоминания темы '{query_text}'.
                        Метаданные включают: заголовки страниц, описания, ключевые слова, H1-H3 заголовки.
                        Ответь кратко: найдено/не найдено и что именно.
                        
                        Метаданные для анализа:"""
                        
                        analysis, gigachat_metrics = gigachat_client.analyze_content(
                            parsed_content[:3000],
                            prompt
                        )
                        
                        # Логируем метрики GigaChat
                        logger.log_gigachat_analysis(filial_name, gigachat_metrics)
                        
                        # Логируем ответ GigaChat
                        if analysis and not analysis.startswith("Ошибка"):
                            analysis_preview = analysis[:200] + "..." if len(analysis) > 200 else analysis
                            logger.log("INFO", f"🤖 GigaChat анализ метаданных для {filial_name}", {
                                "analysis": analysis_preview,
                                "query": query_text,
                                "mode": "meta_" + search_mode
                            })
                            
                            # Проверяем, нашел ли GigaChat что-то
                            found_by_gigachat = not any(phrase in analysis.lower() for phrase in
                                ["не найден", "не обнаружен", "отсутствует", "нет упоминаний"])
                            
                            if found_by_gigachat:
                                # GigaChat что-то нашел
                                result = {
                                    'filial_id': filial['id'],
                                    'search_query_id': query['id'],
                                    'url': website,
                                    'page_title': filial_name,
                                    'content': parsed_content[:1000],
                                    'gigachat_analysis': analysis,
                                    'relevance_score': 0.7 if query_results.get('occurrences', 0) == 0 else min(query_results['occurrences'] / 10, 1.0),
                                    'status': 'success',
                                    'search_mode': search_mode,
                                    'metrics': {
                                        'parse_metrics': parse_metrics,
                                        'search_results': query_results,
                                        'gigachat_metrics': gigachat_metrics
                                    }
                                }
                                db.save_monitoring_result(filial['id'], result, session_id)
                                
                                if query_results.get('occurrences', 0) > 0:
                                    logger.log("INFO", f"✅ {filial_name}: найдено '{query_text}' в метаданных ({query_results['occurrences']} раз)")
                                else:
                                    logger.log("INFO", f"✅ {filial_name}: GigaChat нашел упоминания '{query_text}' в метаданных")
                                session_stats['successful'] += 1
                            else:
                                # GigaChat не нашел в метаданных
                                logger.log("INFO", f"❌ {filial_name}: '{query_text}' не найден в метаданных", {
                                    "searched_in": f"{parse_metrics.get('pages_parsed', 1)} страниц, {parse_metrics.get('headers_count', 0)} заголовков",
                                    "url": website,
                                    "mode": "meta_" + search_mode
                                })
                                
                                result = {
                                    'filial_id': filial['id'],
                                    'search_query_id': query['id'],
                                    'url': website,
                                    'status': 'no_data',
                                    'error_message': f"Запрос '{query_text}' не найден",
                                    'search_mode': search_mode
                                }
                                db.save_monitoring_result(filial['id'], result, session_id)
                        
                        # Обновляем статистику токенов
                        session_stats['total_tokens_used'] += gigachat_metrics.get('total_tokens', 0)
                else:
                    # Для режима sitemap_search отсутствие parsed_content не является ошибкой,
                    # так как этот режим не использует parsed_content
                    if search_mode != "sitemap_search":
                        # Ошибка парсинга только для других режимов
                        result = {
                            'filial_id': filial['id'],
                            'url': website,
                            'status': 'error',
                            'error_message': parse_metrics.get('error', 'Не удалось получить контент сайта')
                        }
                        db.save_monitoring_result(filial['id'], result, session_id)
                        logger.log("ERROR", f"{filial_name}: ошибка парсинга")
                        session_stats['errors'] += 1
                
                # Обновление прогресса
                progress = (idx + 1) / total_filials
                st.progress(progress)
                
            except Exception as e:
                logger.log("ERROR", f"Ошибка при обработке {filial_name}: {str(e)}")
                db.add_log(filial['id'], 'monitoring_error', 'error', str(e))
                session_stats['errors'] += 1
                continue
        
        # Подсчет финальной статистики
        session_stats['total_time'] = time.time() - session_start
        if response_times:
            session_stats['avg_response_time'] = sum(response_times) / len(response_times)
        if page_sizes:
            session_stats['avg_page_size'] = sum(page_sizes) / len(page_sizes)
        
        # Логируем статистику сессии
        logger.log_session_stats(session_stats)
        
        # Завершение мониторинга
        st.session_state.processing = False
        st.session_state.current_status = "Мониторинг завершен"
        logger.log("INFO", f"✅ Мониторинг завершен за {session_stats['total_time']:.1f} сек")
        
        # Обновляем статистику сессии
        if session_id and hasattr(db, 'update_monitoring_session'):
            db.update_monitoring_session(
                session_id,
                filials_count=len(filials),
                queries_count=len(queries),
                results_count=session_stats['successful'],
                status='completed'
            )
        
        # Добавляем запись в лог БД
        db.add_log(None, 'monitoring_complete', 'success',
                  f'Проверено {total_filials} филиалов, успешно {session_stats["successful"]}, ошибок {session_stats["errors"]}')
        
    except Exception as e:
        logger.log("ERROR", f"Критическая ошибка: {str(e)}")
        st.session_state.processing = False
        st.session_state.current_status = f"Критическая ошибка: {str(e)}"
        
        # Обновляем сессию с ошибкой
        if 'session_id' in locals() and session_id and hasattr(db, 'update_monitoring_session'):
            db.update_monitoring_session(
                session_id,
                status='error',
                error_message=str(e)
            )

def show_results_tab(db: VGTRKDatabase):
    """Вкладка результатов мониторинга"""
    st.header("📊 Результаты мониторинга")
    
    # Выбор сессии мониторинга
    # Проверяем, поддерживает ли БД сессии
    if hasattr(db, 'get_monitoring_sessions'):
        sessions = db.get_monitoring_sessions(limit=50)
    else:
        sessions = []
        st.warning("База данных не поддерживает сессии мониторинга. Обновите систему.")
    
    if sessions:
        col_s1, col_s2 = st.columns([3, 1])
        
        with col_s1:
            session_options = ["Все сессии"] + [
                f"Сессия #{s['id']} от {s.get('started_at', 'неизвестно')} ({s.get('search_mode', 'н/д')}, {s.get('results_count', 0)} результатов)"
                for s in sessions
            ]
            
            selected_session_str = st.selectbox(
                "Выберите сессию мониторинга",
                session_options,
                help="Фильтр результатов по конкретной сессии мониторинга"
            )
            
            # Извлекаем ID выбранной сессии
            selected_session_id = None
            if selected_session_str != "Все сессии":
                # Извлекаем ID из строки "Сессия #123 от ..."
                import re
                match = re.search(r'Сессия #(\d+)', selected_session_str)
                if match:
                    selected_session_id = int(match.group(1))
        
        with col_s2:
            # Показываем информацию о выбранной сессии
            if selected_session_id:
                session_info = next((s for s in sessions if s['id'] == selected_session_id), None)
                if session_info:
                    st.metric("Статус", session_info['status'])
    else:
        selected_session_id = None
        st.info("Нет доступных сессий мониторинга")
    
    st.markdown("---")
    
    # Фильтры
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Фильтр по дате
        date_filter = st.selectbox(
            "Период",
            ["Сегодня", "Вчера", "Последние 7 дней", "Последние 30 дней", "Все время"]
        )
        
        date_from = None
        date_to = None
        
        if date_filter == "Сегодня":
            date_from = datetime.now().strftime("%Y-%m-%d")
            date_to = date_from
        elif date_filter == "Вчера":
            yesterday = datetime.now() - timedelta(days=1)
            date_from = yesterday.strftime("%Y-%m-%d")
            date_to = date_from
        elif date_filter == "Последние 7 дней":
            date_from = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            date_to = datetime.now().strftime("%Y-%m-%d")
        elif date_filter == "Последние 30 дней":
            date_from = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            date_to = datetime.now().strftime("%Y-%m-%d")
    
    with col2:
        # Фильтр по статусу
        status_filter = st.selectbox(
            "Статус",
            ["Все", "Успешно", "Ошибки", "Нет данных"]
        )
        
        status_map = {
            "Успешно": "success",
            "Ошибки": "error",
            "Нет данных": "no_data"
        }
        status = status_map.get(status_filter)
    
    with col3:
        # Фильтр по округу
        all_filials = db.get_all_filials()
        districts = sorted(list(set(f['federal_district'] for f in all_filials)))
        districts.insert(0, "Все округа")
        selected_district = st.selectbox("Округ", districts)
    
    with col4:
        # Режим отображения
        display_mode = st.selectbox(
            "Режим отображения",
            ["📊 Таблица", "🎴 Карточки"]
        )
    
    # Кнопка экспорта
    if st.button("📥 Экспорт в Excel", use_container_width='stretch'):
        export_path = f"exports/monitoring_results_{datetime.now():%Y%m%d_%H%M%S}.xlsx"
        Path("exports").mkdir(exist_ok=True)
        db_path = db.export_to_excel(export_path)
        st.success(f"✅ Экспортировано в {export_path}")
    
    # Получаем результаты с фильтрами
    results = db.get_monitoring_results(
        date_from=date_from,
        date_to=date_to,
        status=status,
        session_id=selected_session_id
    )
    
    # Фильтруем по округу если нужно
    if selected_district != "Все округа":
        results = [r for r in results if r.get('federal_district') == selected_district]
    
    # Отображение результатов
    if results:
        st.metric("Найдено результатов", len(results))
        
        if display_mode == "🎴 Карточки":
            # Режим карточек
            cards_display = ResultsCardsDisplay(results)
            cards_display.display_cards()
        else:
            # Режим таблицы (старый код)
            # Преобразуем в DataFrame
            df = pd.DataFrame(results)
            
            # Выбираем нужные колонки
            display_columns = ['parsing_date', 'filial_name', 'federal_district',
                              'query_text', 'status', 'gigachat_analysis']
            
            # Проверяем наличие колонок
            available_columns = [col for col in display_columns if col in df.columns]
            df = df[available_columns]
            
            # Переименовываем колонки
            column_names = {
                'parsing_date': 'Дата',
                'filial_name': 'Филиал',
                'federal_district': 'Округ',
                'query_text': 'Запрос',
                'status': 'Статус',
                'gigachat_analysis': 'Анализ'
            }
            df.rename(columns=column_names, inplace=True)
            
            # Форматируем дату
            if 'Дата' in df.columns:
                df['Дата'] = pd.to_datetime(df['Дата']).dt.strftime('%Y-%m-%d %H:%M')
            
            # Ограничиваем длину анализа для отображения
            if 'Анализ' in df.columns:
                df['Анализ'] = df['Анализ'].str[:200] + '...'
            
            # Отображаем таблицу
            st.dataframe(
                df,
                use_container_width='stretch',
                hide_index=True
            )
    else:
        st.info("Нет результатов для отображения")

def show_statistics_tab(db: VGTRKDatabase):
    """Вкладка статистики"""
    st.header("📈 Статистика мониторинга")
    
    stats = db.get_statistics()
    
    # Основные метрики
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Всего филиалов", stats['filials']['total'])
    
    with col2:
        st.metric("Активных филиалов", stats['filials']['active'])
    
    with col3:
        st.metric("Проверено сегодня", stats['today']['success'])
    
    with col4:
        st.metric("Ошибок сегодня", stats['today']['errors'])
    
    st.markdown("---")
    
    # Графики
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Распределение по округам")
        if stats['by_district']:
            df_districts = pd.DataFrame(
                list(stats['by_district'].items()),
                columns=['Округ', 'Количество']
            )
            st.bar_chart(df_districts.set_index('Округ'))
    
    with col2:
        st.subheader("📈 Динамика за неделю")
        if stats['last_week']:
            df_week = pd.DataFrame(stats['last_week'])
            if not df_week.empty:
                df_week['date'] = pd.to_datetime(df_week['date'])
                df_week.set_index('date', inplace=True)
                st.line_chart(df_week['count'])
    
    st.markdown("---")
    
    # Топ филиалов
    st.subheader("🏆 Топ-5 филиалов по активности")
    if stats['top_filials']:
        df_top = pd.DataFrame(stats['top_filials'])
        df_top.columns = ['Филиал', 'Количество публикаций']
        st.table(df_top)
    else:
        st.info("Недостаточно данных для статистики")
    
    # Последние логи
    st.markdown("---")
    st.subheader("📝 Последние события")
    
    logs = db.get_logs(limit=20)
    if logs:
        for log in logs:
            icon = "✅" if log['status'] == 'success' else "❌"
            time_str = log['created_at'].split('T')[0] if 'T' in log['created_at'] else log['created_at']
            st.text(f"{icon} [{time_str}] {log['action']}: {log['message']}")
    else:
        st.info("Нет записей в логах")

def show_settings_tab(db: VGTRKDatabase):
    """Вкладка настроек"""
    st.header("⚙️ Настройки системы")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔍 Поисковые запросы")
        
        # Форма добавления нового запроса
        with st.form("add_query"):
            st.write("Добавить новый поисковый запрос")
            query_text = st.text_input("Текст запроса")
            category = st.selectbox(
                "Категория",
                ["обязательный", "федеральные", "региональные", "другое"]
            )
            description = st.text_area("Описание")
            priority = st.slider("Приоритет", 1, 10, 5)
            
            if st.form_submit_button("Добавить"):
                if query_text:
                    db.add_search_query(query_text, category, description, priority)
                    st.success(f"✅ Запрос '{query_text}' добавлен")
                    st.rerun()
        
        # Список существующих запросов
        st.markdown("---")
        st.write("**Существующие запросы:**")
        queries = db.get_search_queries()
        for q in queries:
            col_q1, col_q2 = st.columns([3, 1])
            with col_q1:
                st.text(f"• {q['query_text']} ({q['category']})")
            with col_q2:
                if st.button("Удалить", key=f"del_{q['id']}"):
                    # Здесь можно добавить функцию удаления
                    st.warning("Функция удаления в разработке")
    
    with col2:
        st.subheader("🗄️ База данных")
        
        # Информация о БД
        db_path = Path("data/vgtrk_monitoring.db")
        if db_path.exists():
            size_mb = db_path.stat().st_size / (1024 * 1024)
            st.metric("Размер БД", f"{size_mb:.2f} МБ")
        
        # Очистка старых данных
        st.markdown("---")
        st.write("**Очистка старых данных**")
        days_to_keep = st.number_input(
            "Хранить данные (дней)",
            min_value=7,
            max_value=365,
            value=30
        )
        
        if st.button("🗑️ Очистить старые данные", use_container_width='stretch'):
            deleted = db.clear_old_results(days_to_keep)
            st.success(f"✅ Удалено {deleted} старых записей")
        
        # Экспорт полной БД
        st.markdown("---")
        if st.button("💾 Экспорт всей БД в Excel", use_container_width='stretch'):
            export_path = f"exports/full_database_{datetime.now():%Y%m%d_%H%M%S}.xlsx"
            Path("exports").mkdir(exist_ok=True)
            db.export_to_excel(export_path, include_results=True)
            st.success(f"✅ База данных экспортирована в {export_path}")
        
        # Резервное копирование
        st.markdown("---")
        if st.button("🔒 Создать резервную копию БД", use_container_width='stretch'):
            import shutil
            backup_dir = Path("backups")
            backup_dir.mkdir(exist_ok=True)
            backup_path = backup_dir / f"vgtrk_backup_{datetime.now():%Y%m%d_%H%M%S}.db"
            shutil.copy2(db_path, backup_path)
            st.success(f"✅ Резервная копия создана: {backup_path}")

if __name__ == "__main__":
    main()