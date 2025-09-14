"""
Асинхронный модуль мониторинга с пулом соединений
Обрабатывает множество филиалов параллельно для максимальной скорости
"""

import asyncio
import aiohttp
import time
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlparse
import re
from bs4 import BeautifulSoup
import logging
from contextlib import asynccontextmanager
import json

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AsyncMonitoring:
    """Асинхронный мониторинг с переиспользованием соединений"""
    
    def __init__(self, max_concurrent: int = 20, timeout: int = 30):
        """
        Args:
            max_concurrent: Максимальное количество одновременных соединений
            timeout: Таймаут для каждого запроса в секундах
        """
        self.max_concurrent = max_concurrent
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.session = None
        self.connector = None
        
    @asynccontextmanager
    async def get_session(self):
        """Контекстный менеджер для управления сессией"""
        if self.session is None:
            # Создаём коннектор с пулом соединений
            self.connector = aiohttp.TCPConnector(
                limit=100,  # Общий лимит соединений
                limit_per_host=5,  # Лимит на хост (чтобы не забанили)
                ttl_dns_cache=300,  # Кэш DNS на 5 минут
                force_close=False,  # Переиспользуем соединения
                enable_cleanup_closed=True
            )
            
            # Настройки сессии
            self.session = aiohttp.ClientSession(
                connector=self.connector,
                timeout=self.timeout,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )
        
        try:
            yield self.session
        finally:
            pass  # Не закрываем сессию здесь, будем переиспользовать
    
    async def close(self):
        """Закрытие сессии и освобождение ресурсов"""
        if self.session:
            await self.session.close()
            self.session = None
        if self.connector:
            await self.connector.close()
            self.connector = None
    
    async def fetch_sitemap(self, url: str, sitemap_url: Optional[str] = None) -> Optional[str]:
        """Асинхронное получение sitemap"""
        async with self.semaphore:  # Ограничиваем параллельность
            try:
                # Определяем URL sitemap
                if sitemap_url:
                    if sitemap_url.startswith('http'):
                        full_sitemap_url = sitemap_url
                    else:
                        full_sitemap_url = urljoin(url, sitemap_url)
                else:
                    # Пробуем стандартные пути
                    base_url = url.rstrip('/')
                    sitemap_paths = [
                        '/sitemap.xml',
                        '/sitemap_index.xml',
                        '/sitemap2025.xml',
                        '/sitemap2024.xml'
                    ]
                    
                    async with self.get_session() as session:
                        for path in sitemap_paths:
                            try:
                                test_url = base_url + path
                                async with session.head(test_url, ssl=False) as response:
                                    if response.status == 200:
                                        full_sitemap_url = test_url
                                        break
                            except:
                                continue
                        else:
                            return None
                
                # Загружаем sitemap
                async with self.get_session() as session:
                    async with session.get(full_sitemap_url, ssl=False) as response:
                        if response.status == 200:
                            return await response.text()
                        
            except asyncio.TimeoutError:
                logger.warning(f"Timeout при загрузке sitemap: {url}")
            except Exception as e:
                logger.error(f"Ошибка при загрузке sitemap {url}: {e}")
            
            return None
    
    async def is_sitemap_index(self, content: str) -> bool:
        """Проверка, является ли файл sitemap_index"""
        try:
            # Проверяем наличие тега sitemapindex в содержимом
            return '<sitemapindex' in content or 'sitemapindex>' in content
        except:
            return False
    
    async def fetch_and_parse_sitemap_index(self, sitemap_content: str) -> List[str]:
        """Извлечение списка sitemap URL из sitemap_index.xml"""
        sitemap_urls = []
        
        try:
            # Убираем namespace для упрощения парсинга
            clean_content = re.sub(r'xmlns[^=]*=\"[^\"]*\"', '', sitemap_content)
            root = ET.fromstring(clean_content)
            
            # Ищем все теги <loc> внутри <sitemap>
            for sitemap_elem in root.findall('.//sitemap'):
                loc = sitemap_elem.find('loc')
                if loc is not None and loc.text:
                    sitemap_urls.append(loc.text)
            
            logger.info(f"Найдено {len(sitemap_urls)} sitemap файлов в индексе")
            
        except Exception as e:
            logger.error(f"Ошибка парсинга sitemap_index: {e}")
        
        return sitemap_urls
    
    async def parse_sitemap_articles(
        self,
        sitemap_content: str,
        keywords: List[str],
        days: int = 7,
        max_articles: int = 50
    ) -> List[Dict[str, Any]]:
        """Парсинг статей из sitemap с фильтрацией по ключевым словам"""
        
        articles = []
        
        # Проверяем, является ли это sitemap_index
        if await self.is_sitemap_index(sitemap_content):
            logger.info("Обнаружен sitemap_index, загружаем вложенные sitemap файлы...")
            
            # Получаем список sitemap URL
            sitemap_urls = await self.fetch_and_parse_sitemap_index(sitemap_content)
            
            # Загружаем и парсим каждый sitemap
            async with self.get_session() as session:
                for sitemap_url in sitemap_urls[:10]:  # Ограничиваем количество для скорости
                    try:
                        logger.debug(f"Загружаем вложенный sitemap: {sitemap_url}")
                        async with session.get(sitemap_url, ssl=False, timeout=10) as response:
                            if response.status == 200:
                                sub_content = await response.text()
                                # Рекурсивно парсим вложенный sitemap (но без проверки на index)
                                sub_articles = await self._parse_regular_sitemap(
                                    sub_content, keywords, days, max_articles - len(articles)
                                )
                                articles.extend(sub_articles)
                                
                                if len(articles) >= max_articles:
                                    break
                    except Exception as e:
                        logger.warning(f"Ошибка загрузки вложенного sitemap {sitemap_url}: {e}")
                        continue
            
            return articles[:max_articles]
        
        # Если это обычный sitemap, парсим его
        return await self._parse_regular_sitemap(sitemap_content, keywords, days, max_articles)
    
    async def _parse_regular_sitemap(
        self,
        sitemap_content: str,
        keywords: List[str],
        days: int = 7,
        max_articles: int = 50
    ) -> List[Dict[str, Any]]:
        """Парсинг обычного sitemap файла"""
        
        articles = []
        
        try:
            # Убираем namespace для упрощения парсинга
            clean_content = re.sub(r'xmlns[^=]*=\"[^\"]*\"', '', sitemap_content)
            root = ET.fromstring(clean_content)
            
            # Определяем дату отсечки
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Ищем все URL элементы
            for url_elem in root.findall('.//url'):
                loc = url_elem.find('loc')
                lastmod = url_elem.find('lastmod')
                
                if loc is not None and loc.text:
                    url = loc.text
                    
                    # Проверяем дату
                    if lastmod is not None and lastmod.text:
                        try:
                            # Обрабатываем различные форматы даты
                            date_text = lastmod.text
                            if 'T' in date_text:
                                date = datetime.fromisoformat(date_text.replace('Z', '+00:00'))
                            else:
                                date = datetime.strptime(date_text, '%Y-%m-%d')
                            
                            if date < cutoff_date:
                                continue
                        except:
                            pass
                    
                    # Проверяем ключевые слова в URL
                    url_lower = url.lower()
                    found_keywords = []
                    
                    for keyword in keywords:
                        if keyword.lower() in url_lower:
                            found_keywords.append(keyword)
                    
                    if found_keywords:
                        articles.append({
                            'url': url,
                            'date': lastmod.text if lastmod is not None else None,
                            'keywords': found_keywords
                        })
                        
                        if len(articles) >= max_articles:
                            break
            
        except Exception as e:
            logger.error(f"Ошибка парсинга sitemap: {e}")
        
        return articles
    
    async def fetch_article_content(
        self,
        article_url: str,
        keywords: List[str]
    ) -> Optional[Dict[str, Any]]:
        """Асинхронная загрузка и проверка содержимого статьи"""
        
        async with self.semaphore:
            try:
                async with self.get_session() as session:
                    # Используем allow_redirects для автоматической обработки 301
                    async with session.get(
                        article_url,
                        ssl=False,
                        allow_redirects=True,
                        max_redirects=3
                    ) as response:
                        if response.status == 200:
                            content = await response.text()
                            
                            # Быстрая проверка наличия ключевых слов
                            content_lower = content.lower()
                            found_keywords = []
                            
                            for keyword in keywords:
                                if keyword.lower() in content_lower:
                                    found_keywords.append(keyword)
                            
                            if found_keywords:
                                # Извлекаем заголовок
                                soup = BeautifulSoup(content, 'html.parser')
                                title = soup.find('title')
                                title_text = title.text if title else ''
                                
                                # Извлекаем snippet
                                # Ищем первое вхождение ключевого слова
                                snippet = ''
                                for keyword in found_keywords:
                                    pattern = re.compile(
                                        f'.{{0,100}}{re.escape(keyword)}.{{0,100}}',
                                        re.IGNORECASE | re.DOTALL
                                    )
                                    match = pattern.search(content_lower)
                                    if match:
                                        snippet = match.group(0)
                                        break
                                
                                return {
                                    'url': str(response.url),  # Финальный URL после редиректов
                                    'title': title_text,
                                    'keywords': found_keywords,
                                    'snippet': snippet[:200] if snippet else ''
                                }
                        
            except asyncio.TimeoutError:
                logger.debug(f"Timeout при загрузке статьи: {article_url}")
            except Exception as e:
                logger.debug(f"Ошибка при загрузке статьи {article_url}: {e}")
            
            return None
    
    async def process_filial_async(
        self,
        filial: Dict[str, Any],
        keywords: List[str],
        days: int = 7,
        max_articles: int = 50
    ) -> Dict[str, Any]:
        """Асинхронная обработка одного филиала"""
        
        start_time = time.time()
        result = {
            'filial_id': filial.get('id'),
            'filial_name': filial.get('name'),
            'website': filial.get('website_url') or filial.get('website'),
            'status': 'processing',
            'articles': [],
            'error': None,
            'processing_time': 0
        }
        
        try:
            website = result['website']
            if not website:
                result['status'] = 'error'
                result['error'] = 'Нет сайта'
                return result
            
            # Нормализуем URL
            if not website.startswith(('http://', 'https://')):
                website = f'https://{website}'
            
            # Получаем sitemap
            sitemap_url = filial.get('sitemap_url')
            sitemap_content = await self.fetch_sitemap(website, sitemap_url)
            
            if not sitemap_content:
                result['status'] = 'error'
                result['error'] = 'Sitemap не найден'
                return result
            
            # Парсим статьи из sitemap
            sitemap_articles = await self.parse_sitemap_articles(
                sitemap_content,
                keywords,
                days,
                max_articles * 2  # Берём с запасом
            )
            
            if not sitemap_articles:
                result['status'] = 'no_data'
                result['error'] = 'Нет статей с ключевыми словами'
                return result
            
            # Параллельно загружаем и проверяем статьи
            tasks = []
            for article in sitemap_articles[:max_articles]:
                task = self.fetch_article_content(article['url'], keywords)
                tasks.append(task)
            
            # Ждём завершения всех задач
            articles_data = await asyncio.gather(*tasks)
            
            # Фильтруем успешные результаты
            valid_articles = [
                article for article in articles_data
                if article is not None
            ]
            
            result['articles'] = valid_articles
            result['status'] = 'success' if valid_articles else 'no_data'
            
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
            logger.error(f"Ошибка обработки филиала {filial.get('name')}: {e}")
        
        finally:
            result['processing_time'] = time.time() - start_time
        
        return result
    
    async def process_filials_batch(
        self,
        filials: List[Dict[str, Any]],
        keywords: List[str],
        days: int = 7,
        max_articles: int = 50,
        progress_callback=None
    ) -> List[Dict[str, Any]]:
        """Обработка пакета филиалов параллельно"""
        
        results = []
        total = len(filials)
        completed = 0
        
        # Создаём задачи для всех филиалов
        tasks = []
        for filial in filials:
            task = self.process_filial_async(filial, keywords, days, max_articles)
            tasks.append(task)
        
        # Обрабатываем результаты по мере готовности
        for future in asyncio.as_completed(tasks):
            result = await future
            results.append(result)
            completed += 1
            
            # Вызываем callback для обновления прогресса
            if progress_callback:
                progress_callback(completed, total, result)
            
            logger.info(
                f"Обработано {completed}/{total}: {result['filial_name']} "
                f"({result['status']}) за {result['processing_time']:.2f}с"
            )
        
        return results


async def run_async_monitoring(
    filials: List[Dict[str, Any]],
    queries: List[str],
    days: int = 7,
    max_concurrent: int = 20,
    progress_callback=None
) -> List[Dict[str, Any]]:
    """
    Главная функция для запуска асинхронного мониторинга
    
    Args:
        filials: Список филиалов для мониторинга
        queries: Список ключевых слов для поиска
        days: Количество дней для поиска
        max_concurrent: Максимальное количество параллельных соединений
        progress_callback: Функция обратного вызова для прогресса
    
    Returns:
        Список результатов мониторинга
    """
    
    monitor = AsyncMonitoring(max_concurrent=max_concurrent)
    
    try:
        # Преобразуем запросы в список ключевых слов
        keywords = [q if isinstance(q, str) else q.get('query_text', '') for q in queries]
        
        # Запускаем асинхронную обработку
        results = await monitor.process_filials_batch(
            filials,
            keywords,
            days,
            max_articles=50,
            progress_callback=progress_callback
        )
        
        return results
        
    finally:
        # Закрываем сессию
        await monitor.close()


# Вспомогательная функция для запуска из синхронного кода
def run_monitoring_async(filials, queries, days=7, max_concurrent=20, progress_callback=None):
    """Обёртка для запуска асинхронного мониторинга из синхронного кода"""
    
    # Создаём новый event loop если его нет
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    # Запускаем асинхронную функцию
    return loop.run_until_complete(
        run_async_monitoring(
            filials,
            queries,
            days,
            max_concurrent,
            progress_callback
        )
    )