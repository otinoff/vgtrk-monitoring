"""
Настройки приложения для парсинга сайтов
"""

# Настройки Google Sheets
GOOGLE_SHEETS_CREDENTIALS = "config/credentials.json"
SHEETS_API_SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# Настройки GigaChat
GIGACHAT_BASE_URL = "https://gigachat.devices.sberbank.ru/api/v1"
GIGACHAT_AUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
GIGACHAT_API_KEY = "OTY3MzMwZDQtZTVhYi00ZmNhLWE4ZTgtMTJhN2Q1MTBkMjQ5Ojk4MmM0NjIyLTU3OWQtNDYxNi04YzVlLWIyMTY3YTZlNzI0NQ=="
GIGACHAT_CLIENT_ID = "967330d4-e5ab-4fca-a8e8-12a7d510d249"
GIGACHAT_SCOPE = "GIGACHAT_API_PERS"

# Настройки парсинга
DEFAULT_TIMEOUT = 30
MAX_CONTENT_LENGTH = 10000  # Максимальная длина извлекаемого контента
PARSER_DELAY = 1  # Задержка между запросами в секундах

# Настройки анализа
ANALYSIS_PROMPT_TEMPLATE = """
Проанализируй следующий текст и ответь на вопрос по теме "{theme}".
Текст для анализа:
{content}

Пожалуйста, предоставь краткое резюме информации, относящейся к теме "{theme}".
"""

# Настройки интерфейса
PAGE_TITLE = "Парсинг сайтов через Google Sheets"
PAGE_ICON = "🔍"
LAYOUT = "wide"

# Лимиты производительности
MAX_SITES_PER_PROCESS = 1000
REQUEST_TIMEOUT = 60