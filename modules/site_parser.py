import requests
from bs4 import BeautifulSoup
import time
from typing import Optional, Dict, Any, Tuple, List
import re
from urllib.parse import urljoin, urlparse
from config.settings import DEFAULT_TIMEOUT, MAX_CONTENT_LENGTH, PARSER_DELAY
from modules.advanced_logger import get_logger, LogLevel

class SiteParser:
    def __init__(self, log_level: LogLevel = LogLevel.INFO):
        """Инициализация парсера сайтов"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.logger = get_logger(log_level)
        self.metrics = {}
    
    def parse_site(self, url: str) -> Tuple[Optional[str], Dict[str, Any]]:
        """
        Парсинг контента сайта с сбором метрик
        
        Args:
            url: URL сайта для парсинга
            
        Returns:
            Кортеж (извлеченный текстовый контент, метрики)
        """
        metrics = {
            'url': url,
            'http_status': None,
            'response_time': 0,
            'page_size_kb': 0,
            'text_blocks_count': 0,
            'text_length': 0,
            'encoding': None,
            'error': None
        }
        
        try:
            # Начинаем замер времени
            self.logger.start_timer(f"parse_{url}")
            start_time = time.time()
            
            # Добавляем задержку между запросами
            time.sleep(PARSER_DELAY)
            
            # Выполняем запрос к сайту
            response = self.session.get(url, timeout=DEFAULT_TIMEOUT)
            response.raise_for_status()
            
            # Собираем метрики ответа
            metrics['response_time'] = time.time() - start_time
            metrics['http_status'] = response.status_code
            metrics['page_size_kb'] = len(response.content) / 1024
            
            # Определяем кодировку
            if response.encoding is None or response.encoding.lower() == 'iso-8859-1':
                # Пытаемся определить кодировку из заголовков
                content_type = response.headers.get('content-type', '')
                if 'charset=' in content_type:
                    encoding = content_type.split('charset=')[-1]
                    response.encoding = encoding
                else:
                    # По умолчанию используем utf-8
                    response.encoding = 'utf-8'
            
            metrics['encoding'] = response.encoding
            
            # Парсим HTML
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Подсчитываем текстовые блоки до удаления
            text_blocks = soup.find_all(['p', 'div', 'span', 'article', 'section'])
            metrics['text_blocks_count'] = len(text_blocks)
            
            # Удаляем скрипты и стили
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Извлекаем текст
            text = soup.get_text()
            
            # Очищаем текст от лишних пробелов и переносов
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            # Собираем метрики текста
            metrics['text_length'] = len(text)
            
            # Ограничиваем длину текста
            if len(text) > MAX_CONTENT_LENGTH:
                text = text[:MAX_CONTENT_LENGTH]
                self.logger.log("INFO", f"Текст обрезан до {MAX_CONTENT_LENGTH} символов для {url}")
            
            # Завершаем замер времени
            duration = self.logger.end_timer(f"parse_{url}")
            
            # Логируем метрики
            self.logger.log_parsing_metrics(url, metrics)
            
            return text, metrics
            
        except requests.RequestException as e:
            metrics['error'] = str(e)
            self.logger.log("ERROR", f"Ошибка запроса к сайту {url}: {e}")
            return None, metrics
        except Exception as e:
            metrics['error'] = str(e)
            self.logger.log("ERROR", f"Ошибка парсинга сайта {url}: {e}")
            return None, metrics
    
    def extract_main_content(self, html_content: str) -> str:
        """
        Извлечение основного контента из HTML
        
        Args:
            html_content: HTML контент страницы
            
        Returns:
            Основной текстовый контент
        """
        try:
            soup = BeautifulSoup(html_content, 'lxml')
            
            # Удаляем скрипты и стили
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Пытаемся найти основной контент в типичных тегах
            main_content = None
            
            # Поиск по приоритетным селекторам
            priority_selectors = [
                'main',
                'article',
                '.content',
                '#content',
                '.post',
                '.entry',
                '.article'
            ]
            
            for selector in priority_selectors:
                element = soup.select_one(selector)
                if element:
                    main_content = element
                    break
            
            # Если не нашли по селекторам, берем body
            if main_content is None:
                main_content = soup.find('body')
            
            if main_content:
                # Извлекаем текст
                text = main_content.get_text()
                
                # Очищаем текст
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text = ' '.join(chunk for chunk in chunks if chunk)
                
                return text
            else:
                return ""
                
        except Exception as e:
            raise Exception(f"Ошибка извлечения основного контента: {e}")
    
    def is_valid_url(self, url: str) -> bool:
        """
        Проверка валидности URL
        
        Args:
            url: URL для проверки
            
        Returns:
            True если URL валиден, иначе False
        """
        if not url:
            return False
            
        # Проверяем, что URL начинается с http:// или https://
        if not url.startswith(('http://', 'https://')):
            return False
            
        # Простая проверка формата URL
        url_pattern = re.compile(
            r'^https?://'
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
            r'localhost|'
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
            r'(?::\d+)?'
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
            
        return url_pattern.match(url) is not None
    
    def search_keywords(self, text: str, keywords: list) -> Dict[str, Any]:
        """
        Поиск ключевых слов в тексте с контекстом
        
        Args:
            text: Текст для поиска
            keywords: Список ключевых слов
            
        Returns:
            Словарь с результатами поиска
        """
        results = {}
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            text_lower = text.lower()
            
            # Подсчет вхождений
            occurrences = text_lower.count(keyword_lower)
            
            # Поиск контекстов (50 символов до и после)
            contexts = []
            start = 0
            while True:
                pos = text_lower.find(keyword_lower, start)
                if pos == -1:
                    break
                
                context_start = max(0, pos - 50)
                context_end = min(len(text), pos + len(keyword) + 50)
                context = text[context_start:context_end]
                
                # Выделяем найденное слово
                context = context.replace(keyword, f"**{keyword}**")
                contexts.append(context)
                
                start = pos + 1
                
                # Ограничиваем количество контекстов
                if len(contexts) >= 5:
                    break
            
            results[keyword] = {
                'occurrences': occurrences,
                'contexts': contexts
            }
            
            # Логируем результаты поиска
            if occurrences > 0:
                self.logger.log("DEBUG", f"Найдено '{keyword}': {occurrences} раз", {
                    "first_context": contexts[0] if contexts else None
                })
        
        return results
    
    def parse_meta_data(self, url: str, include_news: bool = False) -> Tuple[Optional[str], Dict[str, Any]]:
        """
        Парсинг только метаданных и заголовков страницы (быстрый режим)
        
        Args:
            url: URL сайта для парсинга
            include_news: Включать ли новостные страницы
            
        Returns:
            Кортеж (извлеченные метаданные и заголовки, метрики)
        """
        metrics = {
            'url': url,
            'http_status': None,
            'response_time': 0,
            'page_size_kb': 0,
            'headers_count': 0,
            'meta_tags_count': 0,
            'text_length': 0,
            'pages_parsed': 1,
            'mode': 'meta_only',
            'error': None
        }
        
        all_text = []
        
        try:
            # Начинаем замер времени
            self.logger.start_timer(f"parse_meta_{url}")
            start_time = time.time()
            
            # Парсим главную страницу
            main_text, main_metrics = self._extract_meta_from_page(url)
            if main_text:
                all_text.append(f"=== ГЛАВНАЯ СТРАНИЦА ===\n{main_text}")
                metrics['http_status'] = main_metrics.get('http_status')
                metrics['headers_count'] += main_metrics.get('headers_count', 0)
                metrics['meta_tags_count'] += main_metrics.get('meta_tags_count', 0)
            
            # Если нужно, парсим новостные страницы
            if include_news and main_text:
                self.logger.log("DEBUG", f"Поиск новостных страниц на {url}")
                news_urls = self._find_news_urls(url)
                
                if news_urls:
                    self.logger.log("INFO", f"Найдено {len(news_urls)} новостных страниц")
                    
                    # Парсим первые 3-5 новостных страниц
                    for news_url in news_urls[:5]:
                        time.sleep(PARSER_DELAY)  # Задержка между запросами
                        news_text, news_metrics = self._extract_meta_from_page(news_url)
                        if news_text:
                            all_text.append(f"\n=== НОВОСТЬ: {news_url} ===\n{news_text}")
                            metrics['pages_parsed'] += 1
                            metrics['headers_count'] += news_metrics.get('headers_count', 0)
            
            # Собираем итоговые метрики
            metrics['response_time'] = time.time() - start_time
            result_text = "\n".join(all_text)
            metrics['text_length'] = len(result_text)
            metrics['page_size_kb'] = len(result_text.encode()) / 1024
            
            # Завершаем замер времени
            duration = self.logger.end_timer(f"parse_meta_{url}")
            
            # Логируем метрики
            self.logger.log("INFO", f"Мета-парсинг завершен: {metrics['pages_parsed']} страниц, {metrics['text_length']} символов")
            self.logger.log_parsing_metrics(url, metrics)
            
            return result_text if result_text else None, metrics
            
        except Exception as e:
            metrics['error'] = str(e)
            self.logger.log("ERROR", f"Ошибка мета-парсинга {url}: {e}")
            return None, metrics
    
    def _extract_meta_from_page(self, url: str) -> Tuple[Optional[str], Dict[str, Any]]:
        """
        Извлечение метаданных и заголовков с одной страницы
        
        Args:
            url: URL страницы
            
        Returns:
            Кортеж (текст метаданных, метрики страницы)
        """
        metrics = {
            'http_status': None,
            'headers_count': 0,
            'meta_tags_count': 0
        }
        
        try:
            # Запрос страницы
            response = self.session.get(url, timeout=DEFAULT_TIMEOUT)
            response.raise_for_status()
            metrics['http_status'] = response.status_code
            
            # Определяем кодировку
            if response.encoding is None or response.encoding.lower() == 'iso-8859-1':
                content_type = response.headers.get('content-type', '')
                if 'charset=' in content_type:
                    response.encoding = content_type.split('charset=')[-1]
                else:
                    response.encoding = 'utf-8'
            
            # Парсим HTML
            soup = BeautifulSoup(response.text, 'lxml')
            
            text_parts = []
            
            # Извлекаем title
            title = soup.find('title')
            if title:
                text_parts.append(f"Заголовок: {title.get_text().strip()}")
            
            # Извлекаем meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc and meta_desc.get('content'):
                text_parts.append(f"Описание: {meta_desc['content']}")
                metrics['meta_tags_count'] += 1
            
            # Извлекаем meta keywords
            meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
            if meta_keywords and meta_keywords.get('content'):
                text_parts.append(f"Ключевые слова: {meta_keywords['content']}")
                metrics['meta_tags_count'] += 1
            
            # Извлекаем OG meta теги
            og_tags = soup.find_all('meta', attrs={'property': re.compile('^og:')})
            for tag in og_tags:
                if tag.get('content'):
                    prop_name = tag['property'].replace('og:', '')
                    text_parts.append(f"OG {prop_name}: {tag['content']}")
                    metrics['meta_tags_count'] += 1
            
            # Извлекаем заголовки H1-H3
            for level in ['h1', 'h2', 'h3']:
                headers = soup.find_all(level)
                for header in headers[:5]:  # Ограничиваем количество
                    header_text = header.get_text().strip()
                    if header_text:
                        text_parts.append(f"{level.upper()}: {header_text}")
                        metrics['headers_count'] += 1
            
            # Извлекаем первый параграф (лид)
            first_p = soup.find('p')
            if first_p:
                lead_text = first_p.get_text().strip()
                if lead_text and len(lead_text) > 50:
                    text_parts.append(f"Первый абзац: {lead_text[:300]}...")
            
            return "\n".join(text_parts), metrics
            
        except Exception as e:
            self.logger.log("ERROR", f"Ошибка извлечения метаданных с {url}: {e}")
            return None, metrics
    
    def _find_news_urls(self, base_url: str) -> List[str]:
        """
        Поиск ссылок на новостные страницы
        
        Args:
            base_url: Базовый URL сайта
            
        Returns:
            Список URL новостных страниц
        """
        news_urls = []
        
        try:
            response = self.session.get(base_url, timeout=DEFAULT_TIMEOUT)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Паттерны для поиска новостных ссылок
            news_patterns = [
                r'/news/',
                r'/novosti/',
                r'/press/',
                r'/article/',
                r'/\d{4}/\d{2}/',  # Даты в URL
                r'/post/',
                r'/publikacii/'
            ]
            
            # Ищем ссылки на новости
            all_links = soup.find_all('a', href=True)
            
            for link in all_links:
                href = link['href']
                
                # Преобразуем относительные ссылки в абсолютные
                full_url = urljoin(base_url, href)
                
                # Проверяем, что это ссылка на новость
                for pattern in news_patterns:
                    if re.search(pattern, href, re.IGNORECASE):
                        if full_url not in news_urls and self.is_valid_url(full_url):
                            news_urls.append(full_url)
                            break
                
                # Ограничиваем количество найденных ссылок
                if len(news_urls) >= 10:
                    break
            
            # Также ищем прямые ссылки на разделы новостей
            news_section_links = self._find_article_links(soup, base_url)
            news_urls.extend(news_section_links)
            
            # Убираем дубликаты
            news_urls = list(set(news_urls))[:10]
            
            self.logger.log("DEBUG", f"Найдено новостных ссылок: {len(news_urls)}")
            
            return news_urls
            
        except Exception as e:
            self.logger.log("ERROR", f"Ошибка поиска новостных ссылок: {e}")
            return []
    
    def _find_article_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """
        Поиск ссылок на статьи по семантическим признакам
        
        Args:
            soup: BeautifulSoup объект страницы
            base_url: Базовый URL сайта
            
        Returns:
            Список URL статей
        """
        article_urls = []
        
        # Ищем контейнеры с новостями по классам
        news_containers = soup.find_all(['div', 'section', 'article'],
                                       class_=re.compile(r'news|article|post|content|story', re.I))
        
        for container in news_containers[:5]:
            links = container.find_all('a', href=True)
            for link in links[:3]:
                full_url = urljoin(base_url, link['href'])
                if self.is_valid_url(full_url) and full_url not in article_urls:
                    article_urls.append(full_url)
        
        return article_urls[:5]
    
    def parse_rss_feed(self, url: str, max_items: int = 20) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
        """
        Парсинг RSS-ленты сайта для быстрого поиска в новостях
        
        Args:
            url: URL сайта (будет искать RSS автоматически)
            max_items: Максимальное количество элементов для обработки
            
        Returns:
            Кортеж (словарь с RSS данными, метрики)
        """
        metrics = {
            'url': url,
            'rss_url': None,
            'items_count': 0,
            'response_time': 0,
            'mode': 'rss',
            'error': None
        }
        
        try:
            start_time = time.time()
            self.logger.start_timer(f"parse_rss_{url}")
            
            # Пытаемся найти RSS ленту
            rss_url = self._find_rss_url(url)
            if not rss_url:
                # Стандартные варианты RSS
                possible_rss = [
                    urljoin(url, '/rss'),
                    urljoin(url, '/rss.xml'),
                    urljoin(url, '/feed'),
                    urljoin(url, '/feed.xml'),
                    urljoin(url, '/rss/news'),
                    urljoin(url, '/export/rss.xml')
                ]
                
                for rss_candidate in possible_rss:
                    try:
                        response = self.session.head(rss_candidate, timeout=5)
                        if response.status_code == 200:
                            rss_url = rss_candidate
                            break
                    except:
                        continue
            
            if not rss_url:
                metrics['error'] = "RSS лента не найдена"
                self.logger.log("WARNING", f"RSS не найден для {url}")
                return None, metrics
            
            metrics['rss_url'] = rss_url
            self.logger.log("INFO", f"Найден RSS: {rss_url}")
            
            # Загружаем RSS
            response = self.session.get(rss_url, timeout=DEFAULT_TIMEOUT)
            response.raise_for_status()
            
            # Парсим RSS как XML
            soup = BeautifulSoup(response.content, 'xml')
            
            # Извлекаем информацию о канале
            channel = soup.find('channel')
            if not channel:
                metrics['error'] = "Некорректный формат RSS"
                return None, metrics
            
            rss_data = {
                'channel_title': '',
                'channel_description': '',
                'items': []
            }
            
            # Информация о канале
            channel_title = channel.find('title')
            if channel_title:
                rss_data['channel_title'] = channel_title.get_text().strip()
            
            channel_desc = channel.find('description')
            if channel_desc:
                rss_data['channel_description'] = channel_desc.get_text().strip()
            
            # Извлекаем новости
            items = soup.find_all('item')[:max_items]
            metrics['items_count'] = len(items)
            
            for item in items:
                item_data = {
                    'title': '',
                    'description': '',
                    'link': '',
                    'pubDate': '',
                    'full_text': ''  # Объединенный текст для поиска
                }
                
                # Заголовок
                title = item.find('title')
                if title:
                    item_data['title'] = title.get_text().strip()
                
                # Описание
                description = item.find('description')
                if description:
                    # Очищаем от HTML тегов если есть
                    desc_text = description.get_text().strip()
                    # Пробуем распарсить как HTML
                    try:
                        desc_soup = BeautifulSoup(desc_text, 'html.parser')
                        desc_text = desc_soup.get_text().strip()
                    except:
                        pass
                    item_data['description'] = desc_text
                
                # Ссылка
                link = item.find('link')
                if link:
                    item_data['link'] = link.get_text().strip()
                
                # Дата публикации
                pub_date = item.find('pubDate')
                if pub_date:
                    item_data['pubDate'] = pub_date.get_text().strip()
                
                # Объединяем для поиска
                item_data['full_text'] = f"{item_data['title']} {item_data['description']}"
                
                rss_data['items'].append(item_data)
            
            # Метрики
            metrics['response_time'] = time.time() - start_time
            duration = self.logger.end_timer(f"parse_rss_{url}")
            
            self.logger.log("INFO", f"RSS обработан: {metrics['items_count']} новостей за {metrics['response_time']:.2f} сек")
            
            return rss_data, metrics
            
        except Exception as e:
            metrics['error'] = str(e)
            self.logger.log("ERROR", f"Ошибка парсинга RSS для {url}: {e}")
            return None, metrics
    
    def _find_rss_url(self, base_url: str) -> Optional[str]:
        """
        Поиск RSS ленты на странице сайта
        
        Args:
            base_url: URL сайта
            
        Returns:
            URL RSS ленты или None
        """
        try:
            response = self.session.get(base_url, timeout=DEFAULT_TIMEOUT)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Ищем link с type="application/rss+xml"
            rss_link = soup.find('link', attrs={'type': 'application/rss+xml'})
            if rss_link and rss_link.get('href'):
                return urljoin(base_url, rss_link['href'])
            
            # Ищем ссылки с текстом RSS
            rss_anchors = soup.find_all('a', string=re.compile(r'RSS', re.I))
            for anchor in rss_anchors:
                href = anchor.get('href')
                if href:
                    return urljoin(base_url, href)
            
            # Ищем ссылки содержащие /rss или /feed
            all_links = soup.find_all('a', href=re.compile(r'/(rss|feed)', re.I))
            if all_links:
                return urljoin(base_url, all_links[0]['href'])
            
            return None
            
        except Exception as e:
            self.logger.log("DEBUG", f"Не удалось найти RSS на странице {base_url}: {e}")
            return None
    
    def search_in_rss(self, rss_data: Dict[str, Any], keywords: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Поиск ключевых слов в RSS данных
        
        Args:
            rss_data: Данные RSS из parse_rss_feed
            keywords: Список ключевых слов для поиска
            
        Returns:
            Словарь {keyword: [список найденных новостей]}
        """
        results = {}
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            found_items = []
            
            # Ищем в каждой новости
            for item in rss_data.get('items', []):
                full_text = item.get('full_text', '').lower()
                
                if keyword_lower in full_text:
                    # Подсчитываем вхождения
                    occurrences = full_text.count(keyword_lower)
                    
                    # Добавляем информацию о находке
                    found_item = {
                        'title': item['title'],
                        'description': item['description'][:200] + '...' if len(item['description']) > 200 else item['description'],
                        'link': item['link'],
                        'pubDate': item['pubDate'],
                        'occurrences': occurrences
                    }
                    found_items.append(found_item)
            
            results[keyword] = found_items
            
            if found_items:
                self.logger.log("INFO", f"RSS: Найдено {len(found_items)} новостей с '{keyword}'")
            else:
                self.logger.log("DEBUG", f"RSS: '{keyword}' не найден в новостях")
        
        return results