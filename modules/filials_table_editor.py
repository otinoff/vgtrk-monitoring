"""
Интерактивная таблица филиалов с AgGrid
Профессиональная таблица с inline-редактированием и красивым форматированием
"""

import streamlit as st
import pandas as pd
import sqlite3
from typing import List, Dict, Any, Optional
from pathlib import Path
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode, JsCode


class FilialsTableEditor:
    """Интерактивная таблица филиалов с возможностью редактирования"""
    
    def __init__(self, db_path: str = "data/vgtrk_monitoring.db"):
        self.db_path = db_path
        
    def get_filials_data(self, 
                        search_query: str = "", 
                        district_filter: str = "Все",
                        sitemap_filter: str = "Все") -> pd.DataFrame:
        """Получение данных филиалов с фильтрацией"""
        
        conn = sqlite3.connect(self.db_path)
        
        # Базовый SQL запрос
        query = """
            SELECT
                id,
                name,
                federal_district,
                region,
                website as website_url,
                sitemap_url,
                is_active,
                region_code
            FROM filials
            WHERE 1=1
        """
        params = []
        
        # Фильтр по поиску
        if search_query:
            query += " AND (LOWER(name) LIKE LOWER(?) OR LOWER(region) LIKE LOWER(?))"
            params.extend([f"%{search_query}%", f"%{search_query}%"])
        
        # Фильтр по округу
        if district_filter != "Все":
            query += " AND federal_district = ?"
            params.append(district_filter)
        
        # Фильтр по наличию sitemap
        if sitemap_filter == "С Sitemap ✅":
            query += " AND sitemap_url IS NOT NULL AND sitemap_url != ''"
        elif sitemap_filter == "Без Sitemap ❌":
            query += " AND (sitemap_url IS NULL OR sitemap_url = '')"
        
        query += " ORDER BY federal_district, name"
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        return df
    
    def update_sitemap_url(self, filial_id: int, new_sitemap_url: str) -> bool:
        """Обновление sitemap URL для филиала"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "UPDATE filials SET sitemap_url = ? WHERE id = ?",
                (new_sitemap_url if new_sitemap_url else None, filial_id)
            )
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            st.error(f"Ошибка обновления: {e}")
            return False
    
    def update_filial_field(self, filial_id: int, field: str, new_value: Any) -> bool:
        """Универсальный метод для обновления любого поля филиала"""
        try:
            # Список разрешенных для редактирования полей (с маппингом для website_url -> website)
            allowed_fields = ['name', 'federal_district', 'region', 'website_url', 'sitemap_url', 'is_active']
            
            if field not in allowed_fields:
                st.error(f"Поле {field} не разрешено для редактирования")
                return False
            
            # Маппинг полей - если приходит website_url, меняем на website для БД
            db_field = 'website' if field == 'website_url' else field
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Безопасное обновление с использованием параметризованного запроса
            query = f"UPDATE filials SET {db_field} = ? WHERE id = ?"
            cursor.execute(query, (new_value if new_value else None, filial_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            st.error(f"Ошибка обновления поля {field}: {e}")
            return False
    
    def delete_filial(self, filial_id: int) -> bool:
        """Удаление филиала из базы данных"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Сначала удаляем связанные записи из дополнительных таблиц
            cursor.execute("DELETE FROM filial_additional_domains WHERE filial_id = ?", (filial_id,))
            cursor.execute("DELETE FROM monitoring_results WHERE filial_id = ?", (filial_id,))
            
            # Затем удаляем сам филиал
            cursor.execute("DELETE FROM filials WHERE id = ?", (filial_id,))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            st.error(f"Ошибка удаления филиала: {e}")
            return False
    
    def add_filial(self, name: str, federal_district: str, region: str,
                  website: str = "", sitemap_url: str = "") -> bool:
        """Добавление нового филиала"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO filials (name, federal_district, region, website, sitemap_url, is_active, region_code)
                VALUES (?, ?, ?, ?, ?, 1, ?)
            """, (name, federal_district, region,
                  website if website else None,
                  sitemap_url if sitemap_url else None,
                  region[:3].upper()))  # Простой код региона из первых букв
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            st.error(f"Ошибка добавления филиала: {e}")
            return False
    
    def format_website_url(self, url: Optional[str]) -> str:
        """Форматирование URL сайта для отображения"""
        if not url:
            return ""
        
        if not url.startswith(('http://', 'https://')):
            url = f"https://{url}"
        
        return url
    
    def display_interactive_table(self):
        """Отображение профессиональной таблицы AgGrid с inline-редактированием"""
        
        st.markdown("### 📊 Управление филиалами ВГТРК")
        
        # Фильтры
        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
        
        with col1:
            search_query = st.text_input(
                "🔍 Поиск филиала",
                placeholder="Введите название филиала или региона...",
                help="Поиск по названию филиала или региону"
            )
        
        with col2:
            # Получаем список округов
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT federal_district FROM filials ORDER BY federal_district")
            districts = [row[0] for row in cursor.fetchall() if row[0]]
            conn.close()
            
            district_filter = st.selectbox(
                "Федеральный округ",
                ["Все"] + districts
            )
        
        with col3:
            sitemap_filter = st.selectbox(
                "Наличие Sitemap",
                ["Все", "С Sitemap ✅", "Без Sitemap ❌"]
            )
        
        with col4:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🔄 Обновить", use_container_width=True, key="refresh_filters_btn"):
                st.rerun()
        
        # Получаем данные
        df = self.get_filials_data(search_query, district_filter, sitemap_filter)
        
        if df.empty:
            st.warning("Не найдено филиалов по заданным критериям")
            return
        
        # Подготовка данных для отображения
        df['Статус'] = df['is_active'].apply(lambda x: '✅' if x else '❌')
        df['Sitemap'] = df['sitemap_url'].apply(
            lambda x: '✅' if x and str(x).strip() else '❌'
        )
        
        # Подготовка данных для AgGrid
        st.markdown("### 📋 Таблица филиалов")
        
        # Подготавливаем DataFrame
        display_df = df.copy()
        
        # Настройка AgGrid
        gb = GridOptionsBuilder.from_dataframe(display_df)
        
        # Настройка колонок - теперь все основные поля редактируемые
        gb.configure_column("id", header_name="ID", width=60, pinned='left', editable=False)
        
        gb.configure_column("name",
                          header_name="Название",
                          width=250,
                          pinned='left',
                          editable=True,
                          cellStyle={'backgroundColor': '#f8f9fa'},
                          cellEditor='agTextCellEditor')
        
        gb.configure_column("federal_district",
                          header_name="Округ",
                          width=120,
                          editable=True,
                          cellStyle={'backgroundColor': '#f8f9fa'},
                          cellEditor='agSelectCellEditor',
                          cellEditorParams={
                              'values': ['Центральный', 'Северо-Западный', 'Южный', 'Северо-Кавказский',
                                        'Приволжский', 'Уральский', 'Сибирский', 'Дальневосточный']
                          })
        
        gb.configure_column("region",
                          header_name="Регион",
                          width=150,
                          editable=True,
                          cellStyle={'backgroundColor': '#f8f9fa'},
                          cellEditor='agTextCellEditor')
        
        # Делаем сайт редактируемым
        gb.configure_column("website_url",
                          header_name="Сайт",
                          width=200,
                          editable=True,
                          cellStyle={'backgroundColor': '#fff8dc', 'color': '#0068C9', 'cursor': 'pointer'},
                          cellEditor='agTextCellEditor')
        
        # Sitemap URL тоже редактируемый
        gb.configure_column("sitemap_url",
                          header_name="Sitemap URL",
                          width=300,
                          editable=True,
                          cellStyle={'backgroundColor': '#f0f8ff'},
                          cellEditor='agTextCellEditor')
        
        # Индикатор наличия Sitemap
        gb.configure_column("Sitemap",
                          header_name="📡",
                          width=60,
                          cellStyle=JsCode("""
                              function(params) {
                                  if (params.value === '✅') {
                                      return {'color': 'green', 'fontWeight': 'bold', 'textAlign': 'center'};
                                  } else {
                                      return {'color': 'red', 'fontWeight': 'bold', 'textAlign': 'center'};
                                  }
                              }
                          """))
        
        gb.configure_column("Статус",
                          header_name="Активен",
                          width=80,
                          cellStyle=JsCode("""
                              function(params) {
                                  if (params.value === '✅') {
                                      return {'color': 'green', 'textAlign': 'center'};
                                  } else {
                                      return {'color': 'gray', 'textAlign': 'center'};
                                  }
                              }
                          """))
        
        # Скрываем технические колонки
        gb.configure_column("is_active", hide=True)
        gb.configure_column("region_code", hide=True)
        
        # Общие настройки грида
        gb.configure_default_column(
            sortable=True,
            filter=True,
            resizable=True,
            filterable=True,
            groupable=False,
            editable=False
        )
        
        # Настройки сетки
        gb.configure_grid_options(
            domLayout='normal',
            enableCellTextSelection=True,
            ensureDomOrder=True,
            rowHeight=35,
            headerHeight=40,
            tooltipShowDelay=500,
            suppressRowTransform=True,
            animateRows=False,
            onCellValueChanged=JsCode("""
                function(event) {
                    console.log('Cell value changed:', event);
                }
            """),
            onCellClicked=JsCode("""
                function(event) {
                    if (event.colDef.field === 'website_url' && event.value) {
                        var url = event.value;
                        if (!url.startsWith('http://') && !url.startsWith('https://')) {
                            url = 'https://' + url;
                        }
                        window.open(url, '_blank');
                    }
                }
            """)
        )
        
        # Настройка выбора строк - включаем множественный выбор с чекбоксами
        gb.configure_selection(
            selection_mode='multiple',  # Множественный выбор
            use_checkbox=True,  # Добавляем чекбоксы слева
            rowMultiSelectWithClick=False,  # Выбор только через чекбокс
            suppressRowDeselection=False,
            pre_selected_rows=None  # Можно предвыбрать строки если нужно
        )
        
        # Настройка темы и стилей
        custom_css = {
            ".ag-root": {"font-family": "Arial, sans-serif"},
            ".ag-header": {"background-color": "#f0f2f6", "color": "#31333F"},
            ".ag-header-cell": {"font-weight": "bold"},
            ".ag-row-hover": {"background-color": "#f5f7fa"},
            ".ag-cell-focus": {"border": "2px solid #0068C9 !important"},
            ".ag-cell-inline-editing": {"background-color": "#fff3cd !important"}
        }
        
        # Отображение таблицы
        grid_response = AgGrid(
            display_df,
            gridOptions=gb.build(),
            height=500,
            width='100%',
            data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
            update_mode=GridUpdateMode.VALUE_CHANGED,
            fit_columns_on_grid_load=False,
            allow_unsafe_jscode=True,
            enable_enterprise_modules=False,
            custom_css=custom_css,
            theme='streamlit'  # Можно изменить на 'light', 'dark', 'blue', 'fresh', 'material'
        )
        
        # Обработка выбранных строк для мониторинга
        if 'selected_rows' in grid_response and grid_response['selected_rows'] is not None:
            selected_df = pd.DataFrame(grid_response['selected_rows'])
            if not selected_df.empty:
                # Преобразуем в список словарей для совместимости с мониторингом
                selected_filials = selected_df.to_dict('records')
                
                # Сохраняем в session_state для использования в мониторинге
                st.session_state.selected_filials = selected_filials
                
                # Показываем информацию о выбранных филиалах
                st.success(f"✅ Выбрано филиалов для мониторинга: {len(selected_filials)}")
                
                # Показываем список выбранных
                with st.expander("📋 Выбранные филиалы для мониторинга", expanded=False):
                    for filial in selected_filials:
                        st.write(f"• **{filial.get('name', 'Неизвестно')}** ({filial.get('region', '')})")
            else:
                st.session_state.selected_filials = []
                st.info("💡 Выберите филиалы с помощью чекбоксов слева для мониторинга")
        else:
            # Если нет выбранных, очищаем
            if 'selected_filials' not in st.session_state:
                st.session_state.selected_filials = []
        
        # Обработка изменений данных (редактирование полей)
        if grid_response['data'] is not None:
            updated_df = pd.DataFrame(grid_response['data'])
            
            # Проверяем изменения во всех редактируемых полях
            for index, row in updated_df.iterrows():
                original_row = df[df['id'] == row['id']]
                if not original_row.empty:
                    original = original_row.iloc[0]
                    updated = False
                    updated_fields = []
                    
                    # Проверяем каждое поле на изменения
                    fields_to_check = ['name', 'federal_district', 'region', 'website_url', 'sitemap_url']
                    
                    for field in fields_to_check:
                        if str(original[field]) != str(row[field]):
                            if self.update_filial_field(row['id'], field, row[field]):
                                updated = True
                                field_name_ru = {
                                    'name': 'Название',
                                    'federal_district': 'Округ',
                                    'region': 'Регион',
                                    'website_url': 'Сайт',
                                    'sitemap_url': 'Sitemap URL'
                                }.get(field, field)
                                updated_fields.append(field_name_ru)
                    
                    # Если были изменения, показываем уведомление
                    if updated:
                        fields_str = ', '.join(updated_fields)
                        st.success(f"✅ Обновлены поля ({fields_str}) для {row['name']}")
                        st.balloons()
                        # Делаем паузу и перезагружаем
                        import time
                        time.sleep(1)
                        st.rerun()
            
        # Показываем кнопку перехода к мониторингу если есть выбранные филиалы
        if st.session_state.get('selected_filials'):
            st.markdown("---")
            col_monitor1, col_monitor2, col_monitor3 = st.columns([2, 1, 1])
            with col_monitor1:
                st.info(f"🎯 Выбрано {len(st.session_state.selected_filials)} филиалов. Готовы к мониторингу!")
            with col_monitor2:
                if st.button("🚀 Перейти к мониторингу", use_container_width=True, type="primary"):
                    st.info("Перейдите на вкладку '🔍 Мониторинг' для запуска")
            with col_monitor3:
                # Массовое удаление выбранных филиалов
                if st.button("🗑️ Удалить выбранные", use_container_width=True, type="secondary",
                           help="Удалить все выбранные филиалы"):
                    selected_ids = [filial['id'] for filial in st.session_state.selected_filials]
                    selected_names = [filial['name'] for filial in st.session_state.selected_filials]
                    
                    # Показываем диалог подтверждения
                    st.session_state.show_delete_confirmation = True
                    st.session_state.filials_to_delete = selected_ids
                    st.session_state.filials_names_to_delete = selected_names
        
        # Диалог подтверждения массового удаления
        if st.session_state.get('show_delete_confirmation', False):
            st.error("⚠️ **ВНИМАНИЕ!** Вы собираетесь удалить следующие филиалы:")
            for name in st.session_state.filials_names_to_delete:
                st.write(f"• {name}")
            
            col_confirm1, col_confirm2, col_confirm3 = st.columns(3)
            
            with col_confirm1:
                if st.button("✅ ДА, УДАЛИТЬ", use_container_width=True, type="secondary"):
                    # Выполняем удаление
                    deleted_count = 0
                    for filial_id in st.session_state.filials_to_delete:
                        if self.delete_filial(filial_id):
                            deleted_count += 1
                    
                    st.success(f"✅ Удалено {deleted_count} филиалов")
                    
                    # Очищаем состояние
                    st.session_state.show_delete_confirmation = False
                    st.session_state.selected_filials = []
                    if 'filials_to_delete' in st.session_state:
                        del st.session_state.filials_to_delete
                    if 'filials_names_to_delete' in st.session_state:
                        del st.session_state.filials_names_to_delete
                    
                    st.rerun()
            
            with col_confirm2:
                if st.button("❌ ОТМЕНА", use_container_width=True, type="primary"):
                    # Отменяем удаление
                    st.session_state.show_delete_confirmation = False
                    if 'filials_to_delete' in st.session_state:
                        del st.session_state.filials_to_delete
                    if 'filials_names_to_delete' in st.session_state:
                        del st.session_state.filials_names_to_delete
                    st.rerun()
            
            with col_confirm3:
                st.write("")  # Пустая колонка для выравнивания
        
        # Статистика - перенесена вниз
        st.markdown("### 📈 Статистика")
        col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
        
        with col_stat1:
            st.metric("Всего филиалов", len(df))
        
        with col_stat2:
            active_count = len(df[df['is_active'] == 1])
            st.metric("Активных", active_count)
        
        with col_stat3:
            with_sitemap = len(df[df['Sitemap'] == '✅'])
            st.metric("С Sitemap", with_sitemap)
        
        with col_stat4:
            coverage = (with_sitemap / len(df) * 100) if len(df) > 0 else 0
            st.metric("% покрытия", f"{coverage:.1f}%")
        
        # Кнопки действий
        st.markdown("### 🛠️ Действия")
        col_action1, col_action2, col_action3, col_action4 = st.columns(4)
        
        with col_action1:
            # Экспорт в CSV
            csv = df[['name', 'federal_district', 'region', 'website_url', 'sitemap_url']].to_csv(index=False)
            st.download_button(
                label="📥 Скачать CSV",
                data=csv,
                file_name=f"filials_sitemap_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col_action2:
            if st.button("🔍 Найти Sitemap", use_container_width=True, help="Автоматический поиск sitemap для филиалов без sitemap", key="find_sitemap_btn"):
                filials_without_sitemap = df[df['Sitemap'] == '❌']
                if not filials_without_sitemap.empty:
                    st.info(f"🔍 Поиск sitemap для {len(filials_without_sitemap)} филиалов...")
                    # Здесь можно вызвать функцию автопоиска
                else:
                    st.success("✅ У всех филиалов есть sitemap!")
        
        with col_action3:
            if st.button("🔄 Обновить", use_container_width=True, key="refresh_table_btn"):
                st.rerun()
        
        with col_action4:
            # Переключатель темы
            theme_options = ['streamlit', 'light', 'dark', 'blue', 'fresh', 'material']
            selected_theme = st.selectbox("🎨 Тема", theme_options, key="theme_selector")
            if selected_theme != 'streamlit':
                st.info(f"Тема изменится при следующем обновлении таблицы")
        
        # Второй ряд - управление филиалами
        st.markdown("#### ➕➖ Управление филиалами")
        col_manage1, col_manage2 = st.columns(2)
        
        with col_manage1:
            # Добавление филиала
            with st.expander("➕ Добавить филиал", expanded=False):
                with st.form("add_filial_form"):
                    new_name = st.text_input("Название филиала*", placeholder="ГТРК \"Название\"")
                    
                    districts = ['ЦФО', 'СЗФО', 'ЮФО', 'СКФО', 'ПФО', 'УФО', 'СФО', 'ДФО']
                    new_district = st.selectbox("Федеральный округ*", districts)
                    
                    new_region = st.text_input("Регион*", placeholder="Название региона")
                    new_website = st.text_input("Сайт", placeholder="example.ru (без http://)")
                    new_sitemap = st.text_input("Sitemap URL", placeholder="/sitemap.xml")
                    
                    submitted = st.form_submit_button("➕ Добавить филиал", use_container_width=True)
                    
                    if submitted:
                        if new_name and new_district and new_region:
                            if self.add_filial(new_name, new_district, new_region, new_website, new_sitemap):
                                st.success(f"✅ Филиал '{new_name}' добавлен!")
                                st.rerun()
                            else:
                                st.error("❌ Ошибка при добавлении филиала")
                        else:
                            st.error("❌ Заполните обязательные поля (отмечены *)")
        
        with col_manage2:
            # Удаление филиала
            with st.expander("🗑️ Удалить филиал", expanded=False):
                st.warning("⚠️ **Внимание!** Удаление филиала необратимо и удалит все связанные данные мониторинга.")
                
                # Выпадающий список филиалов для удаления
                filial_options = [(row['id'], f"{row['name']} ({row['region']})") for _, row in df.iterrows()]
                
                if filial_options:
                    selected_filial = st.selectbox(
                        "Выберите филиал для удаления:",
                        options=[None] + filial_options,
                        format_func=lambda x: "-- Выберите филиал --" if x is None else x[1]
                    )
                    
                    if selected_filial:
                        filial_id, filial_name = selected_filial
                        
                        # Подтверждение удаления
                        confirm_text = st.text_input(
                            f"Для подтверждения введите 'УДАЛИТЬ':",
                            help="Это дополнительная защита от случайного удаления"
                        )
                        
                        if st.button("🗑️ УДАЛИТЬ ФИЛИАЛ",
                                   use_container_width=True,
                                   type="secondary",
                                   disabled=(confirm_text != "УДАЛИТЬ")):
                            if self.delete_filial(filial_id):
                                st.success(f"✅ Филиал '{filial_name}' удален!")
                                st.rerun()
                            else:
                                st.error("❌ Ошибка при удалении филиала")
                else:
                    st.info("Нет филиалов для удаления")
        
        # Описание возможностей - перенесено в конец
        st.markdown("---")
        st.markdown("### 💡 Справка по использованию")
        st.info("""
        **Возможности таблицы:**
        - **☑️ Выбор филиалов** - используйте чекбоксы слева для выбора филиалов для мониторинга
        - **✏️ Редактирование всех полей** - двойной клик по любой ячейке (кроме ID)
        - **📝 Редактируемые поля:**
          - **Название** - название филиала
          - **Округ** - выбор из списка федеральных округов
          - **Регион** - регион расположения
          - **Сайт** - URL сайта филиала (кликабельный)
          - **Sitemap URL** - путь к sitemap
        - **🔍 Фильтры** в каждой колонке (наведите на заголовок → меню)
        - **📊 Сортировка** по клику на заголовок колонки
        - **↔️ Изменение размера** колонок перетаскиванием границ
        - **💾 Автосохранение** - все изменения сохраняются автоматически
        
        **Управление филиалами:**
        - **➕ Добавить филиал** - форма для создания нового филиала
        - **🗑️ Удалить филиал** - выберите филиал и подтвердите удаление
        - **🗑️ Массовое удаление** - выберите несколько филиалов чекбоксами и удалите все сразу
        
        ⚡ **Для мониторинга:** выберите нужные филиалы чекбоксами и перейдите на вкладку "🔍 Мониторинг"
        """)