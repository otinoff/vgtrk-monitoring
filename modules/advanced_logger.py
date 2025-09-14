"""
Модуль расширенного логирования для системы мониторинга ВГТРК
Поддерживает уровни детализации и сбор метрик
"""

import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum
import json
from pathlib import Path

class LogLevel(Enum):
    """Уровни логирования"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"

class AdvancedLogger:
    """Расширенный логгер с метриками и уровнями детализации"""
    
    def __init__(self, log_level: LogLevel = LogLevel.INFO):
        """
        Инициализация логгера
        
        Args:
            log_level: Начальный уровень логирования
        """
        self.log_level = log_level
        self.logs = []
        self.metrics = {}
        self.start_times = {}
        
        # Настройка файлового логирования
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        self.log_file = log_dir / f"monitoring_{datetime.now():%Y%m%d}.log"
        
        # Настройка стандартного логгера Python
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def set_level(self, level: LogLevel):
        """Установка уровня логирования"""
        self.log_level = level
        self.log("INFO", f"Уровень логирования изменен на {level.value}")
    
    def should_log(self, level: LogLevel) -> bool:
        """Проверка, нужно ли логировать сообщение данного уровня"""
        level_order = {
            LogLevel.DEBUG: 0,
            LogLevel.INFO: 1,
            LogLevel.WARNING: 2,
            LogLevel.ERROR: 3
        }
        
        # Обрабатываем случай, когда level может быть строкой
        if isinstance(level, str):
            try:
                level = LogLevel[level]
            except KeyError:
                # Если неизвестный уровень, логируем всегда
                return True
                
        return level_order.get(level, 0) >= level_order.get(self.log_level, 0)
    
    def log(self, level: str, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Основной метод логирования
        
        Args:
            level: Уровень сообщения (DEBUG, INFO, WARNING, ERROR)
            message: Текст сообщения
            details: Дополнительные детали для DEBUG уровня
        """
        try:
            log_level = LogLevel[level]
        except KeyError:
            # Если неизвестный уровень, используем INFO по умолчанию
            log_level = LogLevel.INFO
            self.logger.warning(f"Неизвестный уровень логирования: {level}, используется INFO")
        
        if not self.should_log(log_level):
            return
        
        timestamp = datetime.now()
        log_entry = {
            'timestamp': timestamp.strftime("%H:%M:%S.%f")[:-3],
            'date': timestamp.isoformat(),
            'level': level,
            'message': message,
            'details': details or {}
        }
        
        self.logs.append(log_entry)
        
        # Логирование в файл
        if details and log_level == LogLevel.DEBUG:
            self.logger.debug(f"{message} | Details: {json.dumps(details, ensure_ascii=False)}")
        elif log_level == LogLevel.INFO:
            self.logger.info(message)
        elif log_level == LogLevel.WARNING:
            self.logger.warning(message)
        elif log_level == LogLevel.ERROR:
            self.logger.error(message)
    
    def start_timer(self, operation: str):
        """Начало отсчета времени для операции"""
        self.start_times[operation] = time.time()
        if self.log_level == LogLevel.DEBUG:
            self.log("DEBUG", f"Таймер запущен: {operation}")
    
    def end_timer(self, operation: str) -> float:
        """
        Завершение отсчета времени и возврат длительности
        
        Returns:
            Время выполнения в секундах
        """
        if operation not in self.start_times:
            return 0.0
        
        duration = time.time() - self.start_times[operation]
        del self.start_times[operation]
        
        if self.log_level == LogLevel.DEBUG:
            self.log("DEBUG", f"Таймер остановлен: {operation}", {"duration_sec": round(duration, 3)})
        
        return duration
    
    def log_parsing_metrics(self, url: str, metrics: Dict[str, Any]):
        """
        Логирование метрик парсинга сайта
        
        Args:
            url: URL сайта
            metrics: Словарь с метриками
        """
        # Сохраняем метрики
        if url not in self.metrics:
            self.metrics[url] = []
        self.metrics[url].append({
            'timestamp': datetime.now().isoformat(),
            **metrics
        })
        
        # Формируем сообщение в зависимости от уровня
        if self.log_level == LogLevel.DEBUG:
            # Подробный вывод для DEBUG
            details = {
                "url": url,
                "http_status": metrics.get('http_status', 'N/A'),
                "response_time": f"{metrics.get('response_time', 0):.2f} сек",
                "page_size": f"{metrics.get('page_size_kb', 0):.1f} КБ",
                "text_blocks": metrics.get('text_blocks_count', 0),
                "text_length": f"{metrics.get('text_length', 0)} символов",
                "encoding": metrics.get('encoding', 'unknown')
            }
            self.log("DEBUG", f"Детали парсинга: {url}", details)
        elif self.log_level == LogLevel.INFO:
            # Краткий вывод для INFO
            status = metrics.get('http_status', 'N/A')
            time_sec = metrics.get('response_time', 0)
            size_kb = metrics.get('page_size_kb', 0)
            self.log("INFO", f"Парсинг {url}: {status} ({time_sec:.1f}с, {size_kb:.1f}КБ)")
        
        # Предупреждения о проблемах
        if metrics.get('response_time', 0) > 5:
            self.log("WARNING", f"Медленный ответ от {url}: {metrics['response_time']:.1f} сек")
        
        if metrics.get('http_status') and metrics['http_status'] >= 400:
            self.log("ERROR", f"Ошибка HTTP {metrics['http_status']} для {url}")
    
    def log_search_results(self, filial: str, search_query: str, results: Dict[str, Any]):
        """
        Логирование результатов поиска
        
        Args:
            filial: Название филиала
            search_query: Поисковый запрос
            results: Результаты поиска
        """
        found_count = results.get('occurrences', 0)
        contexts = results.get('contexts', [])
        
        if found_count > 0:
            if self.log_level == LogLevel.DEBUG:
                # Показываем контексты в DEBUG режиме
                details = {
                    "query": search_query,
                    "occurrences": found_count,
                    "contexts": contexts[:3]  # Первые 3 контекста
                }
                self.log("DEBUG", f"{filial}: найдено '{search_query}'", details)
            else:
                self.log("INFO", f"{filial}: найдено '{search_query}' ({found_count} вхождений)")
        else:
            self.log("INFO", f"{filial}: '{search_query}' не найден")
    
    def log_gigachat_analysis(self, filial: str, metrics: Dict[str, Any]):
        """
        Логирование метрик анализа GigaChat
        
        Args:
            filial: Название филиала
            metrics: Метрики анализа
        """
        if self.log_level == LogLevel.DEBUG:
            details = {
                "processing_time": f"{metrics.get('processing_time', 0):.2f} сек",
                "prompt_tokens": metrics.get('prompt_tokens', 0),
                "completion_tokens": metrics.get('completion_tokens', 0),
                "total_tokens": metrics.get('total_tokens', 0),
                "model": metrics.get('model', 'unknown'),
                "temperature": metrics.get('temperature', 0)
            }
            self.log("DEBUG", f"GigaChat анализ для {filial}", details)
        else:
            time_sec = metrics.get('processing_time', 0)
            tokens = metrics.get('total_tokens', 0)
            self.log("INFO", f"GigaChat анализ {filial}: {time_sec:.1f}с, {tokens} токенов")
    
    def log_session_stats(self, stats: Dict[str, Any]):
        """
        Логирование статистики сессии
        
        Args:
            stats: Статистика сессии мониторинга
        """
        message = (
            f"Статистика сессии: "
            f"Проверено {stats.get('total_checked', 0)} филиалов, "
            f"Успешно {stats.get('successful', 0)}, "
            f"Ошибок {stats.get('errors', 0)}, "
            f"Время {stats.get('total_time', 0):.1f} сек"
        )
        
        if self.log_level == LogLevel.DEBUG:
            # Добавляем детальную статистику
            details = {
                **stats,
                "avg_response_time": f"{stats.get('avg_response_time', 0):.2f} сек",
                "avg_page_size": f"{stats.get('avg_page_size', 0):.1f} КБ",
                "total_tokens_used": stats.get('total_tokens_used', 0)
            }
            self.log("DEBUG", message, details)
        else:
            self.log("INFO", message)
    
    def get_logs(self, level_filter: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """
        Получение логов с фильтрацией
        
        Args:
            level_filter: Фильтр по уровню (опционально)
            limit: Максимальное количество записей
            
        Returns:
            Список логов
        """
        logs = self.logs
        
        if level_filter:
            logs = [log for log in logs if log['level'] == level_filter]
        
        return logs[-limit:]
    
    def get_formatted_logs(self, use_icons: bool = True) -> List[str]:
        """
        Получение отформатированных логов для отображения
        
        Args:
            use_icons: Использовать иконки для уровней
            
        Returns:
            Список отформатированных строк
        """
        icons = {
            "DEBUG": "🔍",
            "INFO": "ℹ️",
            "WARNING": "⚠️",
            "ERROR": "❌"
        } if use_icons else {
            "DEBUG": "[DEBUG]",
            "INFO": "[INFO]",
            "WARNING": "[WARN]",
            "ERROR": "[ERROR]"
        }
        
        formatted = []
        for log in self.get_logs():
            icon = icons.get(log['level'], "")
            timestamp = log['timestamp']
            message = log['message']
            
            if log['level'] == 'DEBUG' and log.get('details'):
                # Форматируем детали для DEBUG
                details_str = " | ".join([f"{k}: {v}" for k, v in log['details'].items()])
                formatted.append(f"{icon} [{timestamp}] {message}\n  └─ {details_str}")
            else:
                formatted.append(f"{icon} [{timestamp}] {message}")
        
        return formatted
    
    def export_logs(self, filepath: str):
        """
        Экспорт логов в JSON файл
        
        Args:
            filepath: Путь к файлу для экспорта
        """
        export_data = {
            'export_date': datetime.now().isoformat(),
            'log_level': self.log_level.value,
            'total_logs': len(self.logs),
            'logs': self.logs,
            'metrics': self.metrics
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        self.log("INFO", f"Логи экспортированы в {filepath}")
    
    def clear_old_logs(self, keep_last: int = 1000):
        """
        Очистка старых логов, сохраняя последние N записей
        
        Args:
            keep_last: Количество записей для сохранения
        """
        if len(self.logs) > keep_last:
            removed = len(self.logs) - keep_last
            self.logs = self.logs[-keep_last:]
            self.log("INFO", f"Очищено {removed} старых записей логов")

# Глобальный экземпляр логгера
_logger_instance = None

def get_logger(log_level: LogLevel = LogLevel.INFO) -> AdvancedLogger:
    """
    Получение глобального экземпляра логгера
    
    Args:
        log_level: Уровень логирования
        
    Returns:
        Экземпляр AdvancedLogger
    """
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = AdvancedLogger(log_level)
    return _logger_instance