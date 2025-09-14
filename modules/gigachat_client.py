import requests
import json
import time
from typing import Optional, Dict, Any, Tuple
import uuid
import urllib3
from config.settings import GIGACHAT_BASE_URL, GIGACHAT_AUTH_URL, ANALYSIS_PROMPT_TEMPLATE
from modules.advanced_logger import get_logger, LogLevel

# Отключаем предупреждения о SSL для GigaChat (у них самоподписанный сертификат)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class GigaChatClient:
    def __init__(self, api_key: str, client_id: str, model: str = "GigaChat",
                 temperature: float = 0.7, log_level: LogLevel = LogLevel.INFO):
        """
        Инициализация клиента GigaChat
        
        Args:
            api_key: API ключ для доступа к GigaChat
            client_id: Client ID для авторизации
            model: Модель GigaChat для использования
            temperature: Температура генерации
            log_level: Уровень логирования
        """
        self.api_key = api_key
        self.client_id = client_id
        self.model = model
        self.temperature = temperature
        self.access_token = None
        self.token_expires_at = 0
        self.logger = get_logger(log_level)
        self._get_access_token()
    
    def _get_access_token(self):
        """Получение токена доступа для GigaChat"""
        if self.access_token and time.time() < self.token_expires_at:
            return  # Токен еще действителен
        
        try:
            self.logger.start_timer("gigachat_auth")
            
            headers = {
                "Authorization": f"Basic {self.api_key}",
                "RqUID": str(uuid.uuid4()),
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            data = {
                "scope": "GIGACHAT_API_PERS"
            }
            
            # Отключаем проверку SSL для GigaChat API (самоподписанный сертификат)
            response = requests.post(GIGACHAT_AUTH_URL, headers=headers, data=data, verify=False)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data["access_token"]
            # Токен действует 30 минут, обновляем за 5 минут до истечения
            self.token_expires_at = time.time() + token_data.get("expires_in", 1800) - 300
            
            auth_time = self.logger.end_timer("gigachat_auth")
            self.logger.log("DEBUG", f"Токен GigaChat получен за {auth_time:.2f} сек")
            
        except Exception as e:
            self.logger.log("ERROR", f"Ошибка получения токена доступа к GigaChat: {e}")
            raise Exception(f"Ошибка получения токена доступа к GigaChat: {e}")
    
    def analyze_content(self, content: str, theme: str) -> Tuple[str, Dict[str, Any]]:
        """
        Анализ контента с помощью GigaChat с сбором метрик
        
        Args:
            content: Текстовый контент для анализа
            theme: Тема анализа
            
        Returns:
            Кортеж (результат анализа, метрики)
        """
        metrics = {
            'model': self.model,
            'temperature': self.temperature,
            'processing_time': 0,
            'prompt_tokens': 0,
            'completion_tokens': 0,
            'total_tokens': 0,
            'error': None
        }
        
        try:
            # Начинаем замер времени
            self.logger.start_timer("gigachat_analysis")
            start_time = time.time()
            
            # Обновляем токен при необходимости
            self._get_access_token()
            
            # Формируем промпт для анализа
            prompt = ANALYSIS_PROMPT_TEMPLATE.format(
                theme=theme,
                content=content[:8000]  # Ограничиваем длину контента для промпта
            )
            
            # Примерный подсчет токенов (1 токен ≈ 4 символа)
            metrics['prompt_tokens'] = len(prompt) // 4
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": self.temperature
            }
            
            self.logger.log("DEBUG", f"Отправка запроса к GigaChat, модель: {self.model}, температура: {self.temperature}")
            
            # Отключаем проверку SSL для GigaChat API (самоподписанный сертификат)
            response = requests.post(f"{GIGACHAT_BASE_URL}/chat/completions", headers=headers, json=data, verify=False)
            response.raise_for_status()
            
            result_data = response.json()
            
            # Собираем метрики из ответа
            metrics['processing_time'] = time.time() - start_time
            
            if "usage" in result_data:
                metrics['prompt_tokens'] = result_data["usage"].get("prompt_tokens", 0)
                metrics['completion_tokens'] = result_data["usage"].get("completion_tokens", 0)
                metrics['total_tokens'] = result_data["usage"].get("total_tokens", 0)
            
            # Завершаем замер времени
            self.logger.end_timer("gigachat_analysis")
            
            # Логируем метрики
            self.logger.log("DEBUG", f"GigaChat анализ завершен", {
                "processing_time": f"{metrics['processing_time']:.2f} сек",
                "total_tokens": metrics['total_tokens']
            })
            
            if "choices" in result_data and len(result_data["choices"]) > 0:
                result = result_data["choices"][0]["message"]["content"].strip()
                metrics['completion_tokens'] = len(result) // 4  # Примерный подсчет если нет в ответе
                return result, metrics
            else:
                metrics['error'] = "Нет результата в ответе"
                self.logger.log("WARNING", "GigaChat не вернул результат анализа")
                return "Не удалось получить результат анализа", metrics
                
        except Exception as e:
            metrics['error'] = str(e)
            metrics['processing_time'] = time.time() - start_time if 'start_time' in locals() else 0
            self.logger.log("ERROR", f"Ошибка анализа контента с помощью GigaChat: {e}")
            return f"Ошибка анализа: {e}", metrics
    
    def generate_summary(self, content: str) -> Tuple[str, Dict[str, Any]]:
        """
        Генерация краткого содержания контента с метриками
        
        Args:
            content: Текстовый контент для суммирования
            
        Returns:
            Кортеж (краткое содержание, метрики)
        """
        metrics = {
            'model': self.model,
            'temperature': 0.3,
            'processing_time': 0,
            'prompt_tokens': 0,
            'completion_tokens': 0,
            'total_tokens': 0,
            'error': None
        }
        
        try:
            self.logger.start_timer("gigachat_summary")
            start_time = time.time()
            
            # Обновляем токен при необходимости
            self._get_access_token()
            
            prompt = f"Пожалуйста, предоставь краткое содержание следующего текста:\n\n{content[:8000]}"
            metrics['prompt_tokens'] = len(prompt) // 4
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.3  # Более низкая температура для суммирования
            }
            
            # Отключаем проверку SSL для GigaChat API (самоподписанный сертификат)
            response = requests.post(f"{GIGACHAT_BASE_URL}/chat/completions", headers=headers, json=data, verify=False)
            response.raise_for_status()
            
            result_data = response.json()
            
            metrics['processing_time'] = time.time() - start_time
            
            if "usage" in result_data:
                metrics['prompt_tokens'] = result_data["usage"].get("prompt_tokens", 0)
                metrics['completion_tokens'] = result_data["usage"].get("completion_tokens", 0)
                metrics['total_tokens'] = result_data["usage"].get("total_tokens", 0)
            
            self.logger.end_timer("gigachat_summary")
            
            if "choices" in result_data and len(result_data["choices"]) > 0:
                result = result_data["choices"][0]["message"]["content"].strip()
                return result, metrics
            else:
                metrics['error'] = "Нет результата в ответе"
                return "Не удалось получить краткое содержание", metrics
                
        except Exception as e:
            metrics['error'] = str(e)
            metrics['processing_time'] = time.time() - start_time if 'start_time' in locals() else 0
            self.logger.log("ERROR", f"Ошибка генерации краткого содержания: {e}")
            return f"Ошибка: {e}", metrics