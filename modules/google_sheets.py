import gspread
from google.oauth2.service_account import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
import pandas as pd
from typing import List, Dict, Optional
import time
import os
import pickle

class GoogleSheetsManager:
    def __init__(self, credentials_path: str):
        """
        Инициализация менеджера Google Sheets
        
        Args:
            credentials_path: Путь к файлу с учетными данными
        """
        self.credentials_path = credentials_path
        self.client = None
        self._authorize()
    
    def _authorize(self):
        """Авторизация в Google Sheets API"""
        try:
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            
            # Проверяем тип учетных данных
            if os.path.exists(self.credentials_path):
                # Пробуем загрузить токен из файла
                creds = None
                token_path = self.credentials_path.replace('.json', '_token.pickle')
                
                if os.path.exists(token_path):
                    with open(token_path, 'rb') as token:
                        creds = pickle.load(token)
                
                # Если нет действительных учетных данных, запрашиваем авторизацию у пользователя
                if not creds or not creds.valid:
                    if creds and creds.expired and creds.refresh_token:
                        creds.refresh(Request())
                    else:
                        # Определяем тип учетных данных
                        with open(self.credentials_path, 'r') as f:
                            import json
                            cred_data = json.load(f)
                        
                        # Если это OAuth учетные данные
                        if 'installed' in cred_data:
                            flow = InstalledAppFlow.from_client_secrets_file(
                                self.credentials_path, scopes)
                            creds = flow.run_local_server(port=0)
                        # Если это Service Account учетные данные
                        elif 'type' in cred_data and cred_data['type'] == 'service_account':
                            creds = Credentials.from_service_account_file(
                                self.credentials_path, scopes=scopes)
                    
                    # Сохраняем учетные данные для следующего запуска
                    with open(token_path, 'wb') as token:
                        pickle.dump(creds, token)
                
                self.client = gspread.authorize(creds)
            else:
                raise Exception(f"Файл учетных данных не найден: {self.credentials_path}")
                
        except Exception as e:
            raise Exception(f"Ошибка авторизации в Google Sheets: {e}")
    
    def read_sites_sheet(self, spreadsheet_url: str, start_row: int = 1, end_row: int = 100) -> List[Dict]:
        """
        Чтение списка сайтов из Google таблицы
        
        Args:
            spreadsheet_url: URL таблицы
            start_row: Начальная строка (с 1)
            end_row: Конечная строка
            
        Returns:
            Список словарей с информацией о сайтах
        """
        try:
            # Открываем таблицу
            sheet = self.client.open_by_url(spreadsheet_url)
            
            # Получаем первый лист (с сайтами)
            worksheet = sheet.get_worksheet(0)
            
            # Получаем все данные
            all_data = worksheet.get_all_records()
            
            # Извлекаем нужный диапазон
            sites_data = []
            for i in range(start_row - 1, min(end_row, len(all_data))):
                row = all_data[i]
                
                # Ищем колонки с URL и темой
                url = None
                theme = None
                
                # Поиск URL в различных возможных колонках
                for key, value in row.items():
                    if isinstance(key, str) and ('url' in key.lower() or 'сайт' in key.lower() or 'link' in key.lower()):
                        url = str(value).strip() if value else None
                        break
                
                # Если URL не найден в специальных колонках, берем первую колонку
                if not url:
                    first_key = list(row.keys())[0] if row.keys() else None
                    url = str(row[first_key]).strip() if first_key and row[first_key] else None
                
                # Поиск темы
                for key, value in row.items():
                    if isinstance(key, str) and ('theme' in key.lower() or 'тема' in key.lower()):
                        theme = str(value).strip() if value else 'Не указана'
                        break
                
                if url and url.startswith(('http://', 'https://')):
                    sites_data.append({
                        'url': url,
                        'theme': theme or 'Не указана',
                        'row_index': i + 1  # Индекс строки в таблице (с 1)
                    })
            
            return sites_data
            
        except Exception as e:
            raise Exception(f"Ошибка чтения таблицы: {e}")
    
    def write_analysis_result(self, spreadsheet_url: str, row_index: int, analysis_result: str, status: str):
        """
        Запись результата анализа в Google таблицу
        
        Args:
            spreadsheet_url: URL таблицы
            row_index: Индекс строки для записи (с 1)
            analysis_result: Результат анализа
            status: Статус обработки
        """
        try:
            # Открываем таблицу
            sheet = self.client.open_by_url(spreadsheet_url)
            
            # Получаем или создаем второй лист (для результатов)
            try:
                worksheet = sheet.get_worksheet(1)
            except:
                # Если второго листа нет, создаем его
                worksheet = sheet.add_worksheet(title="Результаты", rows=1000, cols=3)
                # Добавляем заголовки
                worksheet.update('A1', 'URL')
                worksheet.update('B1', 'Статус')
                worksheet.update('C1', 'Анализ')
            
            # Записываем результат
            worksheet.update(f'A{row_index}', worksheet.cell(row_index, 1).value or '')  # URL уже должен быть в первой колонке
            worksheet.update(f'B{row_index}', status)
            worksheet.update(f'C{row_index}', analysis_result[:49999])  # Ограничиваем длину ячейки
            
        except Exception as e:
            raise Exception(f"Ошибка записи результата: {e}")
    
    def create_results_sheet(self, spreadsheet_url: str):
        """
        Создание листа для результатов анализа
        
        Args:
            spreadsheet_url: URL таблицы
        """
        try:
            sheet = self.client.open_by_url(spreadsheet_url)
            
            # Проверяем, существует ли лист "Результаты"
            try:
                worksheet = sheet.worksheet("Результаты")
            except:
                # Создаем новый лист
                worksheet = sheet.add_worksheet(title="Результаты", rows=100, cols=3)
                # Добавляем заголовки
                worksheet.update('A1', 'URL')
                worksheet.update('B1', 'Статус')
                worksheet.update('C1', 'Анализ')
                
        except Exception as e:
            raise Exception(f"Ошибка создания листа результатов: {e}")