"""
Модуль для работы с SQLite базой данных системы мониторинга ВГТРК
"""

import sqlite3
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional, Any
from contextlib import contextmanager
from datetime import datetime
import json


class VGTRKDatabase:
    """Класс для работы с базой данных филиалов ВГТРК и результатов мониторинга"""
    
    def __init__(self, db_path: str = "data/vgtrk_monitoring.db"):
        """
        Инициализация подключения к базе данных
        
        Args:
            db_path: Путь к файлу базы данных SQLite
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        """Контекстный менеджер для безопасной работы с соединением БД"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row  # Для удобного доступа к полям как к словарю
        try:
            yield conn
        finally:
            conn.close()
    
    def init_database(self):
        """Инициализация структуры базы данных"""
        with self.get_connection() as conn:
            # Таблица филиалов ВГТРК
            conn.execute('''
                CREATE TABLE IF NOT EXISTS filials (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    region TEXT,
                    city TEXT,
                    website TEXT,
                    federal_district TEXT NOT NULL,
                    all_sites TEXT,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблица сессий мониторинга
            conn.execute('''
                CREATE TABLE IF NOT EXISTS monitoring_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_name TEXT,
                    search_mode TEXT NOT NULL,
                    search_period TEXT,
                    search_date DATE,
                    filials_count INTEGER DEFAULT 0,
                    queries_count INTEGER DEFAULT 0,
                    results_count INTEGER DEFAULT 0,
                    status TEXT CHECK(status IN ('running', 'completed', 'error')) DEFAULT 'running',
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    duration_seconds INTEGER,
                    error_message TEXT
                )
            ''')
            
            # Таблица поисковых запросов/тем для мониторинга
            conn.execute('''
                CREATE TABLE IF NOT EXISTS search_queries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query_text TEXT NOT NULL UNIQUE,
                    category TEXT,
                    description TEXT,
                    priority INTEGER DEFAULT 1,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблица результатов парсинга и анализа
            conn.execute('''
                CREATE TABLE IF NOT EXISTS monitoring_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filial_id INTEGER NOT NULL,
                    search_query_id INTEGER,
                    url TEXT,
                    page_title TEXT,
                    content TEXT,
                    gigachat_analysis TEXT,
                    relevance_score REAL,
                    status TEXT CHECK(status IN ('success', 'error', 'no_data')),
                    error_message TEXT,
                    parsing_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (filial_id) REFERENCES filials(id),
                    FOREIGN KEY (search_query_id) REFERENCES search_queries(id)
                )
            ''')
            
            # Таблица логов системы
            conn.execute('''
                CREATE TABLE IF NOT EXISTS monitoring_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filial_id INTEGER,
                    action TEXT NOT NULL,
                    status TEXT,
                    message TEXT,
                    details TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (filial_id) REFERENCES filials(id)
                )
            ''')
            
            # Создаем индексы для ускорения поиска
            conn.execute('CREATE INDEX IF NOT EXISTS idx_filials_district ON filials(federal_district)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_filials_active ON filials(is_active)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_results_date ON monitoring_results(parsing_date)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_results_filial ON monitoring_results(filial_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_results_status ON monitoring_results(status)')
            
            conn.commit()
    
    def import_filials_from_csv(self, csv_path: str, clear_existing: bool = False) -> int:
        """
        Импорт филиалов из CSV файла
        
        Args:
            csv_path: Путь к CSV файлу с данными филиалов
            clear_existing: Очистить существующие данные перед импортом
            
        Returns:
            Количество импортированных записей
        """
        df = pd.read_csv(csv_path)
        
        with self.get_connection() as conn:
            if clear_existing:
                conn.execute('DELETE FROM filials')
                conn.commit()
            
            # Подготавливаем данные для вставки
            records = []
            for _, row in df.iterrows():
                # Обрабатываем возможные варианты названий колонок
                name = row.get('Название', row.get('name', ''))
                region = row.get('Регион', row.get('region', ''))
                city = row.get('Город', row.get('city', ''))
                website = row.get('Сайт', row.get('website', ''))
                district = row.get('Округ', row.get('federal_district', ''))
                all_sites = row.get('Все_сайты', row.get('all_sites', ''))
                
                if name and district:  # Минимальные требования
                    records.append((
                        name, region, city, website, district, all_sites
                    ))
            
            # Вставляем записи
            conn.executemany('''
                INSERT OR REPLACE INTO filials 
                (name, region, city, website, federal_district, all_sites)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', records)
            
            conn.commit()
            
            # Логируем операцию
            self.add_log(None, 'import_filials', 'success', 
                        f'Импортировано {len(records)} филиалов из {csv_path}')
            
            return len(records)
    
    def get_all_filials(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """
        Получить список всех филиалов
        
        Args:
            active_only: Возвращать только активные филиалы
            
        Returns:
            Список филиалов в виде словарей
        """
        with self.get_connection() as conn:
            query = 'SELECT * FROM filials'
            if active_only:
                query += ' WHERE is_active = 1'
            query += ' ORDER BY federal_district, name'
            
            cursor = conn.execute(query)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_filials_by_district(self, district: str, active_only: bool = True) -> List[Dict[str, Any]]:
        """
        Получить филиалы по федеральному округу
        
        Args:
            district: Код федерального округа (ЦФО, СФО, ДФО и т.д.)
            active_only: Возвращать только активные филиалы
            
        Returns:
            Список филиалов в виде словарей
        """
        with self.get_connection() as conn:
            query = 'SELECT * FROM filials WHERE federal_district = ?'
            params = [district]
            
            if active_only:
                query += ' AND is_active = 1'
            query += ' ORDER BY name'
            
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_filial_by_id(self, filial_id: int) -> Optional[Dict[str, Any]]:
        """
        Получить информацию о филиале по ID
        
        Args:
            filial_id: ID филиала
            
        Returns:
            Словарь с данными филиала или None
        """
        with self.get_connection() as conn:
            cursor = conn.execute('SELECT * FROM filials WHERE id = ?', (filial_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def update_filial(self, filial_id: int, **kwargs) -> bool:
        """
        Обновить данные филиала
        
        Args:
            filial_id: ID филиала
            **kwargs: Поля для обновления
            
        Returns:
            True если обновление успешно
        """
        if not kwargs:
            return False
        
        allowed_fields = ['name', 'region', 'city', 'website', 'federal_district', 'all_sites', 'is_active']
        fields_to_update = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if not fields_to_update:
            return False
        
        with self.get_connection() as conn:
            set_clause = ', '.join([f'{k} = ?' for k in fields_to_update.keys()])
            set_clause += ', updated_at = CURRENT_TIMESTAMP'
            values = list(fields_to_update.values()) + [filial_id]
            
            conn.execute(f'UPDATE filials SET {set_clause} WHERE id = ?', values)
            conn.commit()
            
            return conn.total_changes > 0
    
    def add_search_query(self, query_text: str, category: str = None, 
                        description: str = None, priority: int = 1) -> int:
        """
        Добавить поисковый запрос для мониторинга
        
        Args:
            query_text: Текст поискового запроса
            category: Категория запроса
            description: Описание запроса
            priority: Приоритет (1-10)
            
        Returns:
            ID добавленного запроса
        """
        with self.get_connection() as conn:
            cursor = conn.execute('''
                INSERT OR IGNORE INTO search_queries 
                (query_text, category, description, priority)
                VALUES (?, ?, ?, ?)
            ''', (query_text, category, description, priority))
            conn.commit()
            
            if cursor.lastrowid:
                return cursor.lastrowid
            else:
                # Если запрос уже существует, получаем его ID
                cursor = conn.execute('SELECT id FROM search_queries WHERE query_text = ?', (query_text,))
                row = cursor.fetchone()
                return row[0] if row else None
    
    def get_search_queries(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """
        Получить список поисковых запросов
        
        Args:
            active_only: Только активные запросы
            
        Returns:
            Список запросов
        """
        with self.get_connection() as conn:
            query = 'SELECT * FROM search_queries'
            if active_only:
                query += ' WHERE is_active = 1'
            query += ' ORDER BY priority DESC, query_text'
            
            cursor = conn.execute(query)
            return [dict(row) for row in cursor.fetchall()]
    
    def save_monitoring_result(self, filial_id: int, result: Dict[str, Any], session_id: int = None) -> int:
        """
        Сохранить результат мониторинга
        
        Args:
            filial_id: ID филиала
            result: Словарь с результатами парсинга и анализа
            session_id: ID сессии мониторинга
            
        Returns:
            ID сохраненной записи
        """
        with self.get_connection() as conn:
            # Сначала добавим колонки для дополнительных данных, если их нет
            # Проверяем, есть ли колонки search_mode, metrics, articles и session_id
            cursor = conn.execute("PRAGMA table_info(monitoring_results)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'search_mode' not in columns:
                conn.execute('ALTER TABLE monitoring_results ADD COLUMN search_mode TEXT')
            if 'metrics' not in columns:
                conn.execute('ALTER TABLE monitoring_results ADD COLUMN metrics TEXT')
            if 'articles' not in columns:
                conn.execute('ALTER TABLE monitoring_results ADD COLUMN articles TEXT')
            if 'session_id' not in columns:
                conn.execute('ALTER TABLE monitoring_results ADD COLUMN session_id INTEGER REFERENCES monitoring_sessions(id)')
            
            # Сериализуем сложные данные в JSON
            metrics_json = json.dumps(result.get('metrics', {})) if result.get('metrics') else None
            articles_json = json.dumps(result.get('articles', []), ensure_ascii=False) if result.get('articles') else None
            
            cursor = conn.execute('''
                INSERT INTO monitoring_results
                (filial_id, search_query_id, url, page_title, content,
                 gigachat_analysis, relevance_score, status, error_message,
                 search_mode, metrics, articles, session_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                filial_id,
                result.get('search_query_id'),
                result.get('url'),
                result.get('page_title'),
                result.get('content', '')[:5000] if result.get('content') else None,  # Ограничиваем размер
                result.get('gigachat_analysis'),
                result.get('relevance_score'),
                result.get('status', 'success'),
                result.get('error_message'),
                result.get('search_mode'),
                metrics_json,
                articles_json,
                session_id
            ))
            conn.commit()
            
            return cursor.lastrowid
    
    def start_monitoring_session(self, session_name: str = None,
                               search_mode: str = None,
                               search_period: str = None,
                               search_date: str = None) -> int:
        """
        Начать новую сессию мониторинга
        
        Args:
            session_name: Название сессии
            search_mode: Режим поиска
            search_period: Период поиска
            search_date: Дата поиска
            
        Returns:
            ID созданной сессии
        """
        with self.get_connection() as conn:
            cursor = conn.execute('''
                INSERT INTO monitoring_sessions
                (session_name, search_mode, search_period, search_date, status)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                session_name or f"Мониторинг {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                search_mode,
                search_period,
                search_date,
                'running'
            ))
            conn.commit()
            return cursor.lastrowid
    
    def update_monitoring_session(self, session_id: int, **kwargs):
        """
        Обновить информацию о сессии мониторинга
        
        Args:
            session_id: ID сессии
            **kwargs: Поля для обновления (filials_count, queries_count, results_count, status, error_message)
        """
        with self.get_connection() as conn:
            # Формируем список полей для обновления
            allowed_fields = ['filials_count', 'queries_count', 'results_count', 'status', 'error_message']
            update_fields = []
            update_values = []
            
            for field, value in kwargs.items():
                if field in allowed_fields:
                    update_fields.append(f"{field} = ?")
                    update_values.append(value)
            
            # Если статус изменился на completed, обновляем время завершения
            if kwargs.get('status') == 'completed':
                update_fields.append("completed_at = CURRENT_TIMESTAMP")
                # Вычисляем продолжительность
                cursor = conn.execute('SELECT started_at FROM monitoring_sessions WHERE id = ?', (session_id,))
                row = cursor.fetchone()
                if row:
                    started_at = datetime.fromisoformat(row[0].replace(' ', 'T'))
                    duration = int((datetime.now() - started_at).total_seconds())
                    update_fields.append("duration_seconds = ?")
                    update_values.append(duration)
            
            if update_fields:
                update_values.append(session_id)
                query = f"UPDATE monitoring_sessions SET {', '.join(update_fields)} WHERE id = ?"
                conn.execute(query, update_values)
                conn.commit()
    
    def get_monitoring_sessions(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Получить список сессий мониторинга
        
        Args:
            limit: Максимальное количество сессий
            
        Returns:
            Список сессий
        """
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT * FROM monitoring_sessions
                ORDER BY started_at DESC
                LIMIT ?
            ''', (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_session_info(self, session_id: int) -> Optional[Dict[str, Any]]:
        """
        Получить информацию о конкретной сессии
        
        Args:
            session_id: ID сессии
            
        Returns:
            Информация о сессии или None
        """
        with self.get_connection() as conn:
            cursor = conn.execute('SELECT * FROM monitoring_sessions WHERE id = ?', (session_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_monitoring_results(self, filial_id: int = None,
                              date_from: str = None,
                              date_to: str = None,
                              status: str = None,
                              session_id: int = None) -> List[Dict[str, Any]]:
        """
        Получить результаты мониторинга с фильтрацией
        
        Args:
            filial_id: ID филиала (опционально)
            date_from: Начальная дата (YYYY-MM-DD)
            date_to: Конечная дата (YYYY-MM-DD)
            status: Фильтр по статусу
            session_id: ID сессии мониторинга (опционально)
            
        Returns:
            Список результатов
        """
        with self.get_connection() as conn:
            # Проверяем наличие новых колонок
            cursor = conn.execute("PRAGMA table_info(monitoring_results)")
            columns = [col[1] for col in cursor.fetchall()]
            
            # Формируем список колонок для запроса
            mr_columns = ['mr.*']
            if 'search_mode' in columns:
                mr_columns.append('mr.search_mode')
            if 'metrics' in columns:
                mr_columns.append('mr.metrics')
            if 'articles' in columns:
                mr_columns.append('mr.articles')
            
            query = f'''
                SELECT {', '.join(mr_columns)}, f.name as filial_name, f.federal_district, f.region, sq.query_text
                FROM monitoring_results mr
                LEFT JOIN filials f ON mr.filial_id = f.id
                LEFT JOIN search_queries sq ON mr.search_query_id = sq.id
                WHERE 1=1
            '''
            params = []
            
            if filial_id:
                query += ' AND mr.filial_id = ?'
                params.append(filial_id)
            
            if date_from:
                query += ' AND DATE(mr.parsing_date) >= ?'
                params.append(date_from)
            
            if date_to:
                query += ' AND DATE(mr.parsing_date) <= ?'
                params.append(date_to)
            
            if status:
                query += ' AND mr.status = ?'
                params.append(status)
            
            if session_id is not None:
                query += ' AND mr.session_id = ?'
                params.append(session_id)
            
            query += ' ORDER BY mr.parsing_date DESC'
            
            cursor = conn.execute(query, params)
            results = []
            
            for row in cursor.fetchall():
                result_dict = dict(row)
                
                # Десериализуем JSON поля, если они есть
                if 'metrics' in result_dict and result_dict['metrics']:
                    try:
                        result_dict['metrics'] = json.loads(result_dict['metrics'])
                    except json.JSONDecodeError:
                        result_dict['metrics'] = {}
                
                if 'articles' in result_dict and result_dict['articles']:
                    try:
                        result_dict['articles'] = json.loads(result_dict['articles'])
                    except json.JSONDecodeError:
                        result_dict['articles'] = []
                
                results.append(result_dict)
            
            return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Получить статистику мониторинга
        
        Returns:
            Словарь со статистикой
        """
        with self.get_connection() as conn:
            stats = {}
            
            # Общее количество филиалов
            cursor = conn.execute('SELECT COUNT(*) as total, COUNT(CASE WHEN is_active = 1 THEN 1 END) as active FROM filials')
            row = cursor.fetchone()
            stats['filials'] = {'total': row[0], 'active': row[1]}
            
            # Статистика по федеральным округам
            cursor = conn.execute('''
                SELECT federal_district, COUNT(*) as count 
                FROM filials 
                WHERE is_active = 1 
                GROUP BY federal_district
                ORDER BY federal_district
            ''')
            stats['by_district'] = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Статистика парсинга за сегодня
            cursor = conn.execute('''
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN status = 'success' THEN 1 END) as success,
                    COUNT(CASE WHEN status = 'error' THEN 1 END) as errors,
                    COUNT(CASE WHEN status = 'no_data' THEN 1 END) as no_data
                FROM monitoring_results
                WHERE DATE(parsing_date) = DATE('now', 'localtime')
            ''')
            row = cursor.fetchone()
            stats['today'] = {
                'total': row[0],
                'success': row[1],
                'errors': row[2],
                'no_data': row[3]
            }
            
            # Статистика за последние 7 дней
            cursor = conn.execute('''
                SELECT DATE(parsing_date) as date, COUNT(*) as count
                FROM monitoring_results
                WHERE DATE(parsing_date) >= DATE('now', '-7 days', 'localtime')
                GROUP BY DATE(parsing_date)
                ORDER BY date DESC
            ''')
            stats['last_week'] = [{'date': row[0], 'count': row[1]} for row in cursor.fetchall()]
            
            # Топ-5 филиалов по количеству найденного контента
            cursor = conn.execute('''
                SELECT f.name, COUNT(*) as count
                FROM monitoring_results mr
                JOIN filials f ON mr.filial_id = f.id
                WHERE mr.status = 'success' 
                  AND DATE(mr.parsing_date) >= DATE('now', '-30 days', 'localtime')
                GROUP BY f.id, f.name
                ORDER BY count DESC
                LIMIT 5
            ''')
            stats['top_filials'] = [{'name': row[0], 'count': row[1]} for row in cursor.fetchall()]
            
            return stats
    
    def add_log(self, filial_id: Optional[int], action: str, 
                status: str, message: str, details: str = None):
        """
        Добавить запись в лог
        
        Args:
            filial_id: ID филиала (может быть None для системных событий)
            action: Действие
            status: Статус выполнения
            message: Сообщение
            details: Дополнительные детали (JSON)
        """
        with self.get_connection() as conn:
            conn.execute('''
                INSERT INTO monitoring_logs (filial_id, action, status, message, details)
                VALUES (?, ?, ?, ?, ?)
            ''', (filial_id, action, status, message, details))
            conn.commit()
    
    def get_logs(self, limit: int = 100, filial_id: int = None) -> List[Dict[str, Any]]:
        """
        Получить последние записи из логов
        
        Args:
            limit: Максимальное количество записей
            filial_id: Фильтр по филиалу
            
        Returns:
            Список записей логов
        """
        with self.get_connection() as conn:
            query = '''
                SELECT l.*, f.name as filial_name
                FROM monitoring_logs l
                LEFT JOIN filials f ON l.filial_id = f.id
            '''
            params = []
            
            if filial_id:
                query += ' WHERE l.filial_id = ?'
                params.append(filial_id)
            
            query += ' ORDER BY l.created_at DESC LIMIT ?'
            params.append(limit)
            
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def clear_old_results(self, days_to_keep: int = 30) -> int:
        """
        Очистить старые результаты мониторинга
        
        Args:
            days_to_keep: Количество дней для хранения
            
        Returns:
            Количество удаленных записей
        """
        with self.get_connection() as conn:
            cursor = conn.execute('''
                DELETE FROM monitoring_results
                WHERE DATE(parsing_date) < DATE('now', ? || ' days', 'localtime')
            ''', (-days_to_keep,))
            conn.commit()
            
            deleted_count = cursor.rowcount
            
            # Логируем операцию
            self.add_log(None, 'cleanup', 'success', 
                        f'Удалено {deleted_count} старых записей (старше {days_to_keep} дней)')
            
            return deleted_count
    
    def export_to_excel(self, output_path: str, include_results: bool = True) -> str:
        """
        Экспорт данных в Excel файл
        
        Args:
            output_path: Путь для сохранения файла
            include_results: Включать ли результаты мониторинга
            
        Returns:
            Путь к созданному файлу
        """
        output_path = Path(output_path)
        
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Экспорт филиалов
            filials_df = pd.DataFrame(self.get_all_filials())
            if not filials_df.empty:
                filials_df.to_excel(writer, sheet_name='Филиалы', index=False)
            
            # Экспорт поисковых запросов
            queries_df = pd.DataFrame(self.get_search_queries())
            if not queries_df.empty:
                queries_df.to_excel(writer, sheet_name='Поисковые запросы', index=False)
            
            # Экспорт результатов мониторинга
            if include_results:
                results_df = pd.DataFrame(self.get_monitoring_results())
                if not results_df.empty:
                    # Ограничиваем длину контента для Excel
                    if 'content' in results_df.columns:
                        results_df['content'] = results_df['content'].str[:500]
                    results_df.to_excel(writer, sheet_name='Результаты', index=False)
            
            # Экспорт статистики
            stats = self.get_statistics()
            stats_data = []
            for district, count in stats['by_district'].items():
                stats_data.append({'Округ': district, 'Количество филиалов': count})
            if stats_data:
                stats_df = pd.DataFrame(stats_data)
                stats_df.to_excel(writer, sheet_name='Статистика', index=False)
        
        return str(output_path)