"""
Модуль для глубокого парсинга сайтов ВГТРК через Scrapy и Sitemap
Позволяет искать статьи за определенный период с опциональным анализом через GigaChat
"""

import os
import json
import tempfile
import subprocess
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import requests
from xml.etree import ElementTree as ET
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse, urljoin

class ScrapyParser:
    """Парсер для глубокого поиска через sitemap"""
    
    def __init__(self, logger=None):
        self.logger = logger
        self.sitemap_urls_templates = [
            "/sitemap_index.xml",  # Ставим первым - часто используется
            "/sitemap.xml",
            "/news-sitemap.xml",
            "/post-sitemap.xml",
            "/sitemap/sitemap.xml",
            "/yandex-turbo-sitemap.xml"
        ]
        
    def find_sitemap(self, base_url: str, sitemap_url: str = None) -> Optional[Tuple[str, str]]:
        """
        Находит sitemap для сайта
        
        Args:
            base_url: Базовый URL сайта
            sitemap_url: Прямой URL sitemap (если известен)
            
        Returns:
            Tuple (url sitemap, содержимое) или None
        """
        # Если передан прямой URL sitemap, используем его
        if sitemap_url:
            try:
                if self.logger:
                    self.logger.log("INFO", f"Используем прямой sitemap URL: {sitemap_url}")
                response = requests.get(sitemap_url, timeout=10, verify=False)
                if response.status_code == 200:
                    if self.logger:
                        self.logger.log("INFO", f"[OK] Sitemap успешно загружен: {sitemap_url}")
                    return sitemap_url, response.text
                else:
                    if self.logger:
                        self.logger.log("WARNING", f"Не удалось загрузить sitemap по прямому URL: {sitemap_url}, статус: {response.status_code}")
            except Exception as e:
                if self.logger:
                    self.logger.log("ERROR", f"Ошибка при загрузке sitemap по прямому URL: {e}")
                    
        # Пробуем стандартные локации
        for template in self.sitemap_urls_templates:
            sitemap_url = base_url.rstrip('/') + template
            try:
                response = requests.get(sitemap_url, timeout=5, verify=False)
                if response.status_code == 200 and 'xml' in response.headers.get('content-type', ''):
                    if self.logger:
                        self.logger.log("INFO", f"[OK] Найден sitemap: {sitemap_url}")
                    return sitemap_url, response.text
            except Exception as e:
                continue
        
        # ВАЖНО: Сначала проверяем robots.txt - это правильный способ найти sitemap
        try:
            robots_url = base_url.rstrip('/') + '/robots.txt'
            response = requests.get(robots_url, timeout=5, verify=False)
            if response.status_code == 200:
                if self.logger:
                    self.logger.log("DEBUG", f"Проверяем robots.txt: {robots_url}")
                    
                for line in response.text.split('\n'):
                    if 'Sitemap:' in line or 'sitemap:' in line.lower():
                        sitemap_url = line.split(':', 1)[1].strip()
                        if self.logger:
                            self.logger.log("INFO", f"Найден Sitemap в robots.txt: {sitemap_url}")
                        
                        try:
                            sitemap_response = requests.get(sitemap_url, timeout=10, verify=False)
                            if sitemap_response.status_code == 200:
                                if self.logger:
                                    self.logger.log("INFO", f"[OK] Sitemap успешно загружен из robots.txt: {sitemap_url}")
                                return sitemap_url, sitemap_response.text
                        except Exception as e:
                            if self.logger:
                                self.logger.log("WARNING", f"Не удалось загрузить sitemap из robots.txt: {e}")
        except Exception as e:
            if self.logger:
                self.logger.log("DEBUG", f"Ошибка при проверке robots.txt: {e}")
            
        if self.logger:
            self.logger.log("WARNING", f"[X] Sitemap не найден для {base_url}")
        return None
    
    def parse_sitemap_urls(self, xml_content: str, date_from: datetime = None, date_to: datetime = None) -> List[Dict]:
        """
        Парсит sitemap и извлекает URL с фильтрацией по датам
        
        Args:
            xml_content: Содержимое sitemap XML
            date_from: Начальная дата фильтрации
            date_to: Конечная дата фильтрации
            
        Returns:
            Список словарей с URL и датами
        """
        articles = []
        
        try:
            # Убираем BOM если есть
            if xml_content.startswith('\ufeff'):
                xml_content = xml_content[1:]
                
            root = ET.fromstring(xml_content.encode('utf-8'))
            
            # Определяем namespace (пробуем оба варианта - с https и без)
            # Сначала пытаемся определить правильный namespace из XML
            if 'xmlns="https://www.sitemaps.org' in xml_content:
                sitemap_ns = 'https://www.sitemaps.org/schemas/sitemap/0.9'
            else:
                sitemap_ns = 'http://www.sitemaps.org/schemas/sitemap/0.9'
                
            namespaces = {
                's': sitemap_ns,
                'news': 'http://www.google.com/schemas/sitemap-news/0.9'
            }
            
            # Если это sitemap index (содержит другие sitemap)
            if 'sitemapindex' in root.tag:
                if self.logger:
                    self.logger.log("INFO", "Обнаружен sitemap_index.xml, обрабатываем вложенные sitemap файлы")
                    
                for sitemap in root.findall('s:sitemap', namespaces):
                    loc = sitemap.find('s:loc', namespaces)
                    if loc is not None:
                        nested_url = loc.text
                        
                        # Пропускаем старые sitemap если указаны даты
                        if date_from and date_to:
                            # Проверяем, есть ли год в URL sitemap
                            year_match = re.search(r'sitemap(\d{4})\.xml', nested_url)
                            if year_match:
                                sitemap_year = int(year_match.group(1))
                                if sitemap_year < date_from.year:
                                    if self.logger:
                                        self.logger.log("DEBUG", f"Пропускаем старый sitemap: {nested_url}")
                                    continue
                        
                        # Рекурсивно загружаем вложенные sitemap
                        try:
                            if self.logger:
                                self.logger.log("DEBUG", f"Загружаем вложенный sitemap: {nested_url}")
                            response = requests.get(nested_url, timeout=5, verify=False)
                            if response.status_code == 200:
                                nested_articles = self.parse_sitemap_urls(response.text, date_from, date_to)
                                articles.extend(nested_articles)
                                if self.logger:
                                    self.logger.log("DEBUG", f"Найдено {len(nested_articles)} статей в {nested_url}")
                        except Exception as e:
                            if self.logger:
                                self.logger.log("WARNING", f"Ошибка загрузки вложенного sitemap {nested_url}: {e}")
                            continue
            else:
                # Обычный sitemap с URL
                for url_elem in root.findall('s:url', namespaces):
                    loc = url_elem.find('s:loc', namespaces)
                    if loc is None:
                        continue
                        
                    url = loc.text
                    lastmod = url_elem.find('s:lastmod', namespaces)
                    
                    # Извлекаем дату
                    article_date = None
                    if lastmod is not None:
                        try:
                            # Парсим дату (убираем timezone для простоты)
                            date_str = lastmod.text.split('T')[0]
                            article_date = datetime.strptime(date_str, '%Y-%m-%d')
                        except:
                            pass
                    
                    # Если даты нет, пробуем извлечь из URL
                    if not article_date:
                        date_match = re.search(r'/(\d{4})/(\d{2})/(\d{2})/', url)
                        if date_match:
                            try:
                                year, month, day = date_match.groups()
                                article_date = datetime(int(year), int(month), int(day))
                            except:
                                pass
                    
                    # Фильтруем по датам если указаны
                    # Если дата не найдена, включаем статью (может быть важной)
                    if date_from and date_to:
                        if article_date and not (date_from <= article_date <= date_to):
                            continue
                    
                    articles.append({
                        'url': url,
                        'date': article_date,
                        'title': None,
                        'content': None
                    })
                    
        except Exception as e:
            if self.logger:
                self.logger.log("ERROR", f"Ошибка парсинга sitemap: {e}")
                
        return articles
    
    def search_in_article(self, url: str, keywords: List[str]) -> Optional[Dict]:
        """
        Загружает статью и проверяет на наличие ключевых слов
        
        Args:
            url: URL статьи
            keywords: Список ключевых слов для поиска
            
        Returns:
            Словарь с данными статьи или None
        """
        try:
            response = requests.get(url, timeout=5, verify=False)
            if response.status_code != 200:
                return None
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Извлекаем заголовок
            title = None
            for tag in ['h1', 'title']:
                elem = soup.find(tag)
                if elem:
                    title = elem.get_text(strip=True)
                    break
            
            # Извлекаем текст статьи
            content = ""
            # Ищем основной контент
            content_tags = soup.find_all(['article', 'main', 'div'], 
                                        class_=re.compile(r'content|article|post|text|body'))
            if content_tags:
                for tag in content_tags:
                    paragraphs = tag.find_all('p')
                    if paragraphs:
                        content = ' '.join([p.get_text(strip=True) for p in paragraphs])
                        break
            
            # Если контент не найден, берем все параграфы
            if not content:
                paragraphs = soup.find_all('p')
                content = ' '.join([p.get_text(strip=True) for p in paragraphs[:20]])  # Ограничиваем
            
            # Проверяем ключевые слова
            full_text = f"{title or ''} {content}".lower()
            found_keywords = []
            
            for keyword in keywords:
                if keyword.lower() in full_text:
                    found_keywords.append(keyword)
            
            if found_keywords:
                # Находим фрагмент с ключевым словом для snippet
                snippet = ""
                for keyword in found_keywords[:1]:  # Берем первое найденное
                    pos = full_text.find(keyword.lower())
                    if pos > -1:
                        # Расширяем контекст для лучшего понимания
                        start = max(0, pos - 150)
                        end = min(len(content), pos + 150)
                        
                        # Извлекаем фрагмент из оригинального контента (не lowercase)
                        snippet_text = content[start:end].strip()
                        
                        # Удаляем лишние пробелы и переносы строк
                        snippet_text = ' '.join(snippet_text.split())
                        
                        # Обрезаем по границам слов
                        if start > 0:
                            # Находим первое слово
                            first_space = snippet_text.find(' ')
                            if first_space > 0:
                                snippet_text = snippet_text[first_space+1:]
                        
                        if end < len(content):
                            # Находим последнее полное слово
                            last_space = snippet_text.rfind(' ')
                            if last_space > 0:
                                snippet_text = snippet_text[:last_space]
                        
                        # Добавляем многоточие только если текст обрезан
                        if start > 0:
                            snippet = "..." + snippet_text
                        else:
                            snippet = snippet_text
                            
                        if end < len(content):
                            snippet += "..."
                            
                        break
                
                return {
                    'url': url,
                    'title': title or "Без заголовка",
                    'content': content[:1000],  # Ограничиваем размер
                    'snippet': snippet,
                    'keywords': found_keywords
                }
                
        except Exception as e:
            if self.logger:
                self.logger.log("DEBUG", f"Ошибка загрузки {url}: {e}")
                
        return None
    
    def search_with_sitemap(self, site_url: str, keywords: List[str],
                          days: int = 7, max_articles: int = 100,
                          sitemap_url: str = None, date_from = None, date_to = None) -> List[Dict]:
        """
        Основной метод поиска через sitemap
        
        Args:
            site_url: URL сайта
            keywords: Ключевые слова для поиска
            days: Количество дней для поиска (игнорируется если указаны date_from/date_to)
            max_articles: Максимальное количество статей для проверки
            sitemap_url: Прямой URL sitemap (опционально)
            date_from: Начальная дата (date объект, опционально)
            date_to: Конечная дата (date объект, опционально)
            
        Returns:
            Список найденных релевантных статей
        """
        results = []
        
        # Определяем период
        if date_from and date_to:
            # Если переданы конкретные даты, используем их
            from datetime import time
            date_from = datetime.combine(date_from, time.min)
            date_to = datetime.combine(date_to, time.max)
        else:
            # Иначе используем days
            date_to = datetime.now()
            date_from = date_to - timedelta(days=days)
        
        if self.logger:
            period_str = f"с {date_from.strftime('%d.%m.%Y')} по {date_to.strftime('%d.%m.%Y')}"
            self.logger.log("INFO", f"[SEARCH] Поиск на {site_url} за период {period_str}")
            self.logger.log("INFO", f"Ключевые слова: {', '.join(keywords)}")
        
        # Находим sitemap
        sitemap_data = self.find_sitemap(site_url, sitemap_url)
        if not sitemap_data:
            if self.logger:
                self.logger.log("WARNING", "Sitemap не найден, поиск невозможен")
            return results
        
        sitemap_url, xml_content = sitemap_data
        
        # Парсим URL из sitemap
        articles = self.parse_sitemap_urls(xml_content, date_from, date_to)
        
        if self.logger:
            self.logger.log("INFO", f"[INFO] Найдено {len(articles)} URL за период {date_from.date()} - {date_to.date()}")
        
        # Ограничиваем количество
        articles = articles[:max_articles]
        
        # Проверяем каждую статью
        checked = 0
        for article_data in articles:
            checked += 1
            if self.logger and checked % 10 == 0:
                self.logger.log("INFO", f"Проверено {checked}/{len(articles)} статей...")
            
            # Ищем ключевые слова в статье
            article_result = self.search_in_article(article_data['url'], keywords)
            
            if article_result:
                # Добавляем дату если была в sitemap
                if article_data['date']:
                    article_result['date'] = article_data['date']
                else:
                    article_result['date'] = None
                    
                results.append(article_result)
                
                if self.logger:
                    self.logger.log("INFO", f"[OK] Найдено: {article_result['title'][:50]}...")
        
        if self.logger:
            self.logger.log("INFO", f"[DONE] Найдено {len(results)} релевантных статей из {checked} проверенных")
        
        return results
    
    def search_with_sitemap_date(self, site_url: str, keywords: List[str],
                               search_date, max_articles: int = 150,
                               sitemap_url: str = None) -> List[Dict]:
        """
        Поиск через sitemap за конкретную дату
        
        Args:
            site_url: URL сайта
            keywords: Ключевые слова для поиска
            search_date: Конкретная дата для поиска (date object)
            max_articles: Максимальное количество статей для проверки
            sitemap_url: Прямой URL sitemap (опционально)
            
        Returns:
            Список найденных релевантных статей
        """
        results = []
        
        # Преобразуем date в datetime для начала и конца дня
        from datetime import datetime, time
        date_from = datetime.combine(search_date, time.min)  # 00:00:00
        date_to = datetime.combine(search_date, time.max)    # 23:59:59
        
        if self.logger:
            self.logger.log("INFO", f"[SEARCH] Поиск на {site_url} за {search_date.strftime('%d.%m.%Y')}")
            self.logger.log("INFO", f"Ключевые слова: {', '.join(keywords)}")
        
        # Находим sitemap
        sitemap_data = self.find_sitemap(site_url, sitemap_url)
        if not sitemap_data:
            if self.logger:
                self.logger.log("WARNING", "Sitemap не найден, поиск невозможен")
            return results
        
        sitemap_url, xml_content = sitemap_data
        
        # Парсим URL из sitemap с фильтром по конкретной дате
        articles = self.parse_sitemap_urls(xml_content, date_from, date_to)
        
        if self.logger:
            self.logger.log("INFO", f"[INFO] Найдено {len(articles)} URL за {search_date.strftime('%d.%m.%Y')}")
        
        # Не ограничиваем количество для конкретной даты (обычно их немного)
        articles = articles[:max_articles] if len(articles) > max_articles else articles
        
        # Проверяем каждую статью
        checked = 0
        for article_data in articles:
            checked += 1
            if self.logger and checked % 10 == 0:
                self.logger.log("INFO", f"Проверено {checked}/{len(articles)} статей...")
            
            # Ищем ключевые слова в статье
            article_result = self.search_in_article(article_data['url'], keywords)
            
            if article_result:
                # Добавляем дату если была в sitemap
                if article_data['date']:
                    article_result['date'] = article_data['date']
                else:
                    article_result['date'] = None
                    
                results.append(article_result)
                
                if self.logger:
                    self.logger.log("INFO", f"[OK] Найдено: {article_result['title'][:50]}...")
        
        if self.logger:
            self.logger.log("INFO", f"[DONE] Найдено {len(results)} релевантных статей из {checked} проверенных")
        
        return results
    
    def get_results_simple(self, results: List[Dict]) -> str:
        """
        Форматирует результаты для простого вывода (без GigaChat)
        
        Args:
            results: Список найденных статей
            
        Returns:
            Отформатированная строка с результатами
        """
        if not results:
            return "Статьи не найдены"
        
        output = []
        output.append(f"[STATS] Найдено статей: {len(results)}\n")
        output.append("=" * 50 + "\n")
        
        for i, article in enumerate(results, 1):
            date_str = article['date'].strftime('%d.%m.%Y') if article.get('date') else 'Дата неизвестна'
            output.append(f"\n{i}. {article['title']}")
            output.append(f"   [DATE] {date_str}")
            output.append(f"   [URL] {article['url']}")
            output.append(f"   [KEYWORDS] Ключевые слова: {', '.join(article['keywords'])}")
            if article.get('snippet'):
                output.append(f"   [SNIPPET] {article['snippet'][:200]}")
            output.append("-" * 50)
        
        return '\n'.join(output)
    
    def get_results_with_ai(self, results: List[Dict], gigachat_client=None) -> Dict:
        """
        Анализирует результаты через GigaChat
        
        Args:
            results: Список найденных статей
            gigachat_client: Клиент GigaChat для анализа
            
        Returns:
            Словарь с результатами анализа
        """
        if not results:
            return {
                'status': 'no_results',
                'message': 'Статьи не найдены'
            }
        
        if not gigachat_client:
            return {
                'status': 'no_gigachat',
                'message': 'GigaChat не настроен'
            }
        
        # Готовим данные для анализа (берем топ-20)
        top_articles = results[:20]
        
        # Формируем текст для анализа
        analysis_text = f"""
        Проанализируй найденные статьи с сайтов ВГТРК.
        
        Найдено статей: {len(results)}
        Период: последние дни
        
        Топ статьи для анализа:
        """
        
        for i, article in enumerate(top_articles, 1):
            date_str = article['date'].strftime('%d.%m.%Y') if article.get('date') else ''
            analysis_text += f"\n{i}. {date_str} - {article['title']}"
            analysis_text += f"\n   Ключевые слова: {', '.join(article['keywords'])}"
            analysis_text += f"\n   Фрагмент: {article.get('snippet', '')[:200]}\n"
        
        analysis_text += """
        
        Задачи:
        1. Определи основные темы
        2. Найди упоминания важных событий (конгрессы, форумы)
        3. Выдели ключевые тренды
        4. Сделай краткое резюме
        """
        
        try:
            # Отправляем в GigaChat
            response = gigachat_client.analyze(analysis_text)
            
            return {
                'status': 'success',
                'total_articles': len(results),
                'analyzed_articles': len(top_articles),
                'analysis': response,
                'articles': top_articles
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Ошибка анализа: {str(e)}',
                'articles': top_articles
            }


# Вспомогательный класс для работы со Scrapy (если Scrapy установлен)
class ScrapySpiderRunner:
    """Запускает Scrapy Spider для более сложного парсинга"""
    
    def __init__(self):
        self.has_scrapy = self._check_scrapy()
        
    def _check_scrapy(self) -> bool:
        """Проверяет установлен ли Scrapy"""
        try:
            import scrapy
            return True
        except ImportError:
            return False
    
    def run_spider(self, spider_code: str, output_file: str) -> bool:
        """
        Запускает Spider и сохраняет результаты
        
        Args:
            spider_code: Код Spider
            output_file: Файл для сохранения результатов
            
        Returns:
            True если успешно
        """
        if not self.has_scrapy:
            return False
            
        try:
            # Создаем временный файл со Spider
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(spider_code)
                spider_file = f.name
            
            # Запускаем Scrapy
            cmd = f'scrapy runspider {spider_file} -o {output_file}'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            # Удаляем временный файл
            os.unlink(spider_file)
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"Ошибка запуска Spider: {e}")
            return False