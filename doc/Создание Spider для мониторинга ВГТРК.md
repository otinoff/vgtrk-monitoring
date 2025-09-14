<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

## Создание Spider для мониторинга ВГТРК

### **1. Базовый Spider класс**

```python
# vgtrk_health_monitor/spiders/vgtrk_congress_spider.py

import scrapy
import pandas as pd
from datetime import datetime, timedelta
from scrapy.http import Request
import re
from urllib.parse import urljoin, urlparse
from dateutil import parser as date_parser
```


### **2. Основной Spider с использованием Scrapy Selectors**

```python
class VGTRKCongressSpider(scrapy.Spider):
    name = 'vgtrk_congress_monitor'
    
    # Список ключевых слов для поиска
    congress_keywords = [
        "Национальное здравоохранение 2025",
        "4-й Национальный конгресс", 
        "конгресс здравоохранение",
        "медицинский конгресс 2025",
        "здравоохранение конгресс октябрь",
        "национальный центр россия конгресс"
    ]
    
    # Временные рамки (последние 7 дней)
    def __init__(self):
        self.end_date = datetime(2025, 9, 13)
        self.start_date = self.end_date - timedelta(days=7)
        
        # Загружаем список сайтов ВГТРК
        self.vgtrk_sites = pd.read_csv('vgtrk_sites.csv')
        
        # Создаем allowed_domains из URL
        self.allowed_domains = []
        for url in self.vgtrk_sites['Сайт']:
            domain = urlparse(url).netloc.replace('www.', '')
            if domain:
                self.allowed_domains.append(domain)
    
    def start_requests(self):
        """Генерируем начальные запросы для всех сайтов ВГТРК"""
        
        for _, row in self.vgtrk_sites.iterrows():
            branch_name = row['Филиал']
            site_url = row['Сайт']
            
            # Основная страница новостей
            yield Request(
                url=site_url,
                callback=self.parse_main_page,
                meta={
                    'branch': branch_name,
                    'base_url': site_url
                },
                dont_filter=True
            )
            
            # Попытка найти страницу новостей
            news_urls = [
                f"{site_url}/news/",
                f"{site_url}/novosti/", 
                f"{site_url}/local/",
                f"{site_url}/health/",
                f"{site_url}/medicina/"
            ]
            
            for news_url in news_urls:
                yield Request(
                    url=news_url,
                    callback=self.parse_news_section,
                    meta={
                        'branch': branch_name,
                        'base_url': site_url
                    },
                    dont_filter=True,
                    errback=self.handle_error
                )
```


### **3. Методы парсинга с использованием CSS и XPath селекторов**

```python
    def parse_main_page(self, response):
        """Парсинг главной страницы сайта филиала ВГТРК"""
        
        branch = response.meta['branch']
        base_url = response.meta['base_url']
        
        # Поиск ссылок на новости с помощью CSS селекторов
        news_links = response.css('a[href*="news"], a[href*="novosti"]::attr(href)').getall()
        
        # Дополнительный поиск с помощью XPath
        news_links.extend(
            response.xpath('//a[contains(@href, "news") or contains(@href, "novosti")]/@href').getall()
        )
        
        # Поиск по тексту ссылок
        news_links.extend(
            response.xpath('//a[contains(text(), "Новост") or contains(text(), "новост")]/@href').getall()
        )
        
        # Обработка найденных ссылок
        for link in set(news_links):  # убираем дубликаты
            full_url = urljoin(base_url, link)
            yield Request(
                url=full_url,
                callback=self.parse_news_section,
                meta={
                    'branch': branch,
                    'base_url': base_url
                }
            )
        
        # Поиск статей прямо на главной странице
        yield from self.extract_articles(response, branch, base_url)
    
    def parse_news_section(self, response):
        """Парсинг раздела новостей"""
        
        branch = response.meta['branch']
        base_url = response.meta['base_url']
        
        # Различные селекторы для поиска статей
        article_selectors = [
            # CSS селекторы
            'article', 
            '.news-item', 
            '.article-item',
            '.post',
            '.entry',
            'div[class*="news"]',
            'div[class*="article"]',
            
            # XPath селекторы для более сложных случаев
            '//div[contains(@class, "news")]',
            '//article',
            '//div[contains(@class, "post")]',
            '//li[contains(@class, "news")]'
        ]
        
        articles_found = []
        
        # Пробуем различные селекторы
        for selector in article_selectors:
            if selector.startswith('//'):
                # XPath селектор
                articles = response.xpath(selector)
            else:
                # CSS селектор  
                articles = response.css(selector)
                
            if articles:
                articles_found.extend(articles)
                break  # Используем первый успешный селектор
        
        # Если статьи не найдены, ищем любые ссылки с датами
        if not articles_found:
            # Поиск ссылок, которые могут быть статьями
            potential_articles = response.xpath('//a[contains(@href, "2025")]')
            articles_found.extend(potential_articles)
        
        # Обрабатываем найденные статьи
        for article in articles_found:
            yield from self.process_article(article, response, branch, base_url)
        
        # Поиск ссылок на другие страницы новостей (пагинация)
        pagination_links = response.css('a[class*="next"], a[class*="page"], a[rel="next"]::attr(href)').getall()
        pagination_links.extend(
            response.xpath('//a[contains(text(), "Далее") or contains(text(), "Следующая")]/@href').getall()
        )
        
        for page_link in pagination_links[:5]:  # ограничиваем до 5 страниц
            full_url = urljoin(base_url, page_link)
            yield Request(
                url=full_url,
                callback=self.parse_news_section,
                meta=response.meta
            )
```


### **4. Извлечение и фильтрация контента**

```python
    def extract_articles(self, response, branch, base_url):
        """Извлечение статей с текущей страницы"""
        
        # Ищем статьи различными способами
        article_links = []
        
        # CSS селекторы для ссылок на статьи
        article_links.extend(
            response.css('h2 a::attr(href), h3 a::attr(href), .title a::attr(href)').getall()
        )
        
        # XPath для поиска ссылок в заголовках
        article_links.extend(
            response.xpath('//h1/a/@href | //h2/a/@href | //h3/a/@href').getall()
        )
        
        # Поиск ссылок со словами о здравоохранении
        health_links = response.xpath('''
            //a[contains(text(), "здравоохранение") or 
                contains(text(), "медицин") or 
                contains(text(), "конгресс") or
                contains(text(), "здоровье")]/@href
        ''').getall()
        
        article_links.extend(health_links)
        
        # Обрабатываем найденные ссылки
        for link in set(article_links):
            full_url = urljoin(base_url, link)
            yield Request(
                url=full_url,
                callback=self.parse_article_page,
                meta={
                    'branch': branch,
                    'base_url': base_url
                }
            )
    
    def process_article(self, article_selector, response, branch, base_url):
        """Обработка отдельной статьи"""
        
        # Извлекаем заголовок
        title_selectors = [
            'h1::text', 'h2::text', 'h3::text',
            '.title::text', '.headline::text',
            'a::text'
        ]
        
        title = None
        for sel in title_selectors:
            title = article_selector.css(sel).get()
            if title:
                break
        
        if not title:
            # Пробуем XPath
            title = article_selector.xpath('.//h1/text() | .//h2/text() | .//h3/text()').get()
        
        # Проверяем релевантность заголовка
        if title and self.is_relevant_content(title):
            
            # Извлекаем ссылку на полную статью
            article_link = article_selector.css('a::attr(href)').get()
            if not article_link:
                article_link = article_selector.xpath('.//a/@href').get()
            
            if article_link:
                full_url = urljoin(base_url, article_link)
                
                # Извлекаем дату публикации
                date_text = self.extract_date(article_selector)
                
                if self.is_within_date_range(date_text):
                    yield Request(
                        url=full_url,
                        callback=self.parse_article_page,
                        meta={
                            'branch': branch,
                            'base_url': base_url,
                            'title': title.strip(),
                            'date': date_text
                        }
                    )
```


### **5. Парсинг полных статей**

```python
    def parse_article_page(self, response):
        """Парсинг полной страницы статьи"""
        
        branch = response.meta['branch']
        title = response.meta.get('title')
        
        # Если заголовок не был передан, извлекаем его
        if not title:
            title_selectors = [
                'h1::text',
                '.article-title::text',
                '.entry-title::text', 
                '.post-title::text',
                'title::text'
            ]
            
            for sel in title_selectors:
                title = response.css(sel).get()
                if title:
                    break
            
            if not title:
                title = response.xpath('//h1/text()').get()
        
        # Проверяем релевантность
        if not title or not self.is_relevant_content(title):
            return
        
        # Извлекаем содержимое статьи
        content_selectors = [
            '.article-content',
            '.entry-content', 
            '.post-content',
            '.content',
            'article',
            '.text'
        ]
        
        content = None
        for sel in content_selectors:
            content_elements = response.css(f'{sel} p::text').getall()
            if content_elements:
                content = ' '.join(content_elements)
                break
        
        if not content:
            # Пробуем XPath
            content_elements = response.xpath('//div[contains(@class, "content")]//p/text()').getall()
            content = ' '.join(content_elements) if content_elements else ''
        
        # Проверяем содержимое на релевантность
        if content and self.is_relevant_content(content):
            
            # Извлекаем дату публикации
            date_published = self.extract_date_from_page(response)
            
            if self.is_within_date_range(date_published):
                
                # Извлекаем дополнительные метаданные
                author = self.extract_author(response)
                tags = self.extract_tags(response)
                
                yield {
                    'branch': branch,
                    'url': response.url,
                    'title': title.strip(),
                    'content': content.strip(),
                    'date_published': date_published,
                    'author': author,
                    'tags': tags,
                    'scraped_at': datetime.now().isoformat(),
                    'relevance_score': self.calculate_relevance_score(title, content)
                }
```


### **6. Вспомогательные методы**

```python
    def is_relevant_content(self, text):
        """Проверка релевантности контента"""
        if not text:
            return False
            
        text_lower = text.lower()
        
        # Проверяем наличие ключевых слов
        for keyword in self.congress_keywords:
            if keyword.lower() in text_lower:
                return True
        
        # Дополнительные релевантные термины
        health_terms = [
            'здравоохранение', 'медицин', 'конгресс', 'здоровье',
            'врач', 'больниц', 'поликлиник', 'пациент', 'лечение',
            'диагностик', 'терапи', 'профилактик', 'вакцинаци'
        ]
        
        congress_terms = [
            'конгресс', 'форум', 'конференци', 'симпозиум', 
            'съезд', 'саммит', 'мероприятие', 'событие'
        ]
        
        # Проверяем комбинацию терминов
        has_health_term = any(term in text_lower for term in health_terms)
        has_congress_term = any(term in text_lower for term in congress_terms)
        
        return has_health_term and has_congress_term
    
    def extract_date(self, selector):
        """Извлечение даты из селектора"""
        
        # Различные селекторы для поиска даты
        date_selectors = [
            '.date::text',
            '.published::text', 
            '.post-date::text',
            'time::attr(datetime)',
            'time::text',
            '.timestamp::text'
        ]
        
        for sel in date_selectors:
            date_text = selector.css(sel).get()
            if date_text:
                return self.parse_date_string(date_text)
        
        # Пробуем XPath
        date_xpath_selectors = [
            './/time/@datetime',
            './/time/text()',
            './/span[contains(@class, "date")]/text()',
            './/div[contains(@class, "date")]/text()'
        ]
        
        for xpath in date_xpath_selectors:
            date_text = selector.xpath(xpath).get()
            if date_text:
                return self.parse_date_string(date_text)
        
        return None
    
    def extract_date_from_page(self, response):
        """Извлечение даты публикации со страницы статьи"""
        
        # JSON-LD structured data
        json_ld = response.xpath('//script[@type="application/ld+json"]/text()').get()
        if json_ld:
            try:
                import json
                data = json.loads(json_ld)
                if 'datePublished' in data:
                    return self.parse_date_string(data['datePublished'])
            except:
                pass
        
        # Meta теги
        meta_date = response.xpath('//meta[@property="article:published_time"]/@content').get()
        if meta_date:
            return self.parse_date_string(meta_date)
        
        # Обычные селекторы
        date_selectors = [
            '.article-date::text',
            '.published::text',
            '.date::text',
            'time::attr(datetime)',
            'time::text'
        ]
        
        for sel in date_selectors:
            date_text = response.css(sel).get()
            if date_text:
                return self.parse_date_string(date_text)
        
        # Поиск даты в тексте с помощью регулярных выражений
        text_content = response.xpath('//text()').getall()
        full_text = ' '.join(text_content)
        
        # Паттерны для поиска дат
        date_patterns = [
            r'\b(\d{1,2})\s+(сентября|октября|ноября)\s+(\d{4})\b',
            r'\b(\d{1,2})\.(\d{1,2})\.(\d{4})\b',
            r'\b(\d{4})-(\d{1,2})-(\d{1,2})\b'
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, full_text)
            if matches:
                # Берем первое совпадение
                return self.parse_date_string(' '.join(matches[^0]))
        
        return None
    
    def parse_date_string(self, date_str):
        """Парсинг строки даты в объект datetime"""
        if not date_str:
            return None
            
        try:
            # Убираем лишние символы
            date_str = date_str.strip()
            
            # Словарь русских месяцев
            russian_months = {
                'января': 'January', 'февраля': 'February', 'марта': 'March',
                'апреля': 'April', 'мая': 'May', 'июня': 'June',
                'июля': 'July', 'августа': 'August', 'сентября': 'September',
                'октября': 'October', 'ноября': 'November', 'декабря': 'December'
            }
            
            # Заменяем русские названия месяцев
            for ru_month, en_month in russian_months.items():
                date_str = date_str.replace(ru_month, en_month)
            
            # Пробуем распарсить дату
            parsed_date = date_parser.parse(date_str)
            return parsed_date
            
        except Exception as e:
            self.logger.debug(f"Не удалось распарсить дату: {date_str}, ошибка: {e}")
            return None
    
    def is_within_date_range(self, date_obj):
        """Проверка, попадает ли дата в нужный диапазон"""
        if not date_obj:
            return True  # Если дату не удалось определить, включаем статью
        
        return self.start_date <= date_obj <= self.end_date
    
    def extract_author(self, response):
        """Извлечение автора статьи"""
        author_selectors = [
            '.author::text',
            '.byline::text', 
            '.post-author::text',
            'meta[name="author"]::attr(content)'
        ]
        
        for sel in author_selectors:
            author = response.css(sel).get()
            if author:
                return author.strip()
        
        return None
    
    def extract_tags(self, response):
        """Извлечение тегов статьи"""
        tags = []
        
        tag_selectors = [
            '.tags a::text',
            '.categories a::text',
            '.tag::text',
            'meta[name="keywords"]::attr(content)'
        ]
        
        for sel in tag_selectors:
            found_tags = response.css(sel).getall()
            if found_tags:
                tags.extend([tag.strip() for tag in found_tags])
        
        return tags
    
    def calculate_relevance_score(self, title, content):
        """Расчет релевантности статьи"""
        score = 0
        text = f"{title} {content}".lower()
        
        # Прямые упоминания конгресса
        if "национальное здравоохранение 2025" in text:
            score += 10
        if "4-й национальный конгресс" in text:
            score += 10
        
        # Общие термины
        health_terms = ['здравоохранение', 'медицин', 'врач', 'больниц']
        congress_terms = ['конгресс', 'форум', 'конференци']
        
        for term in health_terms:
            score += text.count(term) * 2
        
        for term in congress_terms:
            score += text.count(term) * 3
        
        return score
    
    def handle_error(self, failure):
        """Обработка ошибок"""
        self.logger.error(f"Ошибка при обработке {failure.request.url}: {failure.value}")
```


### **7. Настройки Spider**

```python
# vgtrk_health_monitor/settings.py

BOT_NAME = 'vgtrk_health_monitor'

SPIDER_MODULES = ['vgtrk_health_monitor.spiders']
NEWSPIDER_MODULE = 'vgtrk_health_monitor.spiders'

# Настройки для вежливого скрапинга
ROBOTSTXT_OBEY = True
DOWNLOAD_DELAY = 2
RANDOMIZE_DOWNLOAD_DELAY = 0.5
CONCURRENT_REQUESTS = 8
CONCURRENT_REQUESTS_PER_DOMAIN = 2

# User-Agent
USER_AGENT = 'VGTRKHealthMonitor (+https://example.com/bot)'

# Автотроттлинг
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0

# Pipelines для обработки данных
ITEM_PIPELINES = {
    'vgtrk_health_monitor.pipelines.DateFilterPipeline': 300,
    'vgtrk_health_monitor.pipelines.DuplicatesPipeline': 400,
    'vgtrk_health_monitor.pipelines.RelevanceFilterPipeline': 500,
}

# Экспорт результатов
FEEDS = {
    'results/vgtrk_congress_%(time)s.json': {
        'format': 'json',
        'encoding': 'utf8',
        'store_empty': False,
        'fields': ['branch', 'title', 'url', 'date_published', 'relevance_score'],
    },
    'results/vgtrk_congress_%(time)s.csv': {
        'format': 'csv',
        'encoding': 'utf8',
        'store_empty': False,
    },
}

# Логирование
LOG_LEVEL = 'INFO'
LOG_FILE = 'logs/vgtrk_spider.log'
```


### **8. Pipelines для обработки данных**

```python
# vgtrk_health_monitor/pipelines.py

from datetime import datetime, timedelta
import hashlib

class DateFilterPipeline:
    """Фильтрация по дате публикации"""
    
    def __init__(self):
        self.end_date = datetime(2025, 9, 13)
        self.start_date = self.end_date - timedelta(days=7)
    
    def process_item(self, item, spider):
        if item.get('date_published'):
            if not (self.start_date <= item['date_published'] <= self.end_date):
                raise DropItem(f"Статья не в нужном временном диапазоне: {item['date_published']}")
        return item

class DuplicatesPipeline:
    """Удаление дубликатов"""
    
    def __init__(self):
        self.seen = set()
    
    def process_item(self, item, spider):
        # Создаем хеш на основе заголовка и URL
        item_hash = hashlib.md5(
            f"{item.get('title', '')}{item.get('url', '')}".encode()
        ).hexdigest()
        
        if item_hash in self.seen:
            raise DropItem(f"Дубликат статьи: {item.get('title', '')}")
        else:
            self.seen.add(item_hash)
            return item

class RelevanceFilterPipeline:
    """Фильтрация по релевантности"""
    
    def process_item(self, item, spider):
        relevance_score = item.get('relevance_score', 0)
        if relevance_score < 3:  # Минимальный порог релевантности
            raise DropItem(f"Низкая релевантность: {relevance_score}")
        return item
```


### **9. Запуск и мониторинг**

```bash
# Запуск spider
scrapy crawl vgtrk_congress_monitor

# Запуск с дополнительными параметрами
scrapy crawl vgtrk_congress_monitor -s LOG_LEVEL=DEBUG -o results.json

# Периодический запуск (cron)
# Добавить в crontab для ежедневного запуска в 9:00
# 0 9 * * * cd /path/to/project && scrapy crawl vgtrk_congress_monitor
```


### **10. Анализ результатов**

<span style="display:none">[^1][^10][^11][^12][^13][^14][^15][^16][^17][^18][^19][^2][^20][^3][^4][^5][^6][^7][^8][^9]</span>

<div style="text-align: center">⁂</div>

[^1]: https://ru.wikipedia.org/wiki/Категория:Филиалы_%D0%92%D0%93%D0%A2%D0%A0%D0%9A

[^2]: https://vgtrk.ru/russiatv

[^3]: https://ru.wikipedia.org/wiki/Россия-1

[^4]: https://vgtrk.ru/regions

[^5]: https://telepedia.fandom.com/ru/wiki/ВГТРК

[^6]: https://руни.рф/Россия-1

[^7]: https://ru.wikipedia.org/wiki/Всероссийская_%D0%B3%D0%BE%D1%81%D1%83%D0%B4%D0%B0%D1%80%D1%81%D1%82%D0%B2%D0%B5%D0%BD%D0%BD%D0%B0%D1%8F_%D1%82%D0%B5%D0%BB%D0%B5%D0%B2%D0%B8%D0%B7%D0%B8%D0%BE%D0%BD%D0%BD%D0%B0%D1%8F_%D0%B8_%D1%80%D0%B0%D0%B4%D0%B8%D0%BE%D0%B2%D0%B5%D1%89%D0%B0%D1%82%D0%B5%D0%BB%D1%8C%D0%BD%D0%B0%D1%8F_%D0%BA%D0%BE%D0%BC%D0%BF%D0%B0%D0%BD%D0%B8%D1%8F

[^8]: https://alaniatv.ru/kontakty/

[^9]: https://smotrim.ru/channel/1

[^10]: https://telepedia.fandom.com/ru/wiki/Категория:Региональные_%D1%84%D0%B8%D0%BB%D0%B8%D0%B0%D0%BB%D1%8B_%D0%92%D0%93%D0%A2%D0%A0%D0%9A

[^11]: https://dontr.ru/contacts/

[^12]: https://ru.ruwiki.ru/wiki/Россия-1

[^13]: https://www.cnews.ru/book/ВГТРК_%D0%93%D0%A2%D0%A0%D0%9A_%D0%A4%D0%B8%D0%BB%D0%B8%D0%B0%D0%BB%D1%8B

[^14]: https://www.list-org.com/company/50887

[^15]: https://vgtrk.ru

[^16]: https://vestiprim.ru/news/ptrnews/133649-tri-filiala-vgtrk-voshli-v-top-20-sajtov-regionalnyh-telekanalov-rossii.html

[^17]: https://telepedia.fandom.com/ru/wiki/Список_%D1%80%D0%B5%D0%B3%D0%B8%D0%BE%D0%BD%D0%B0%D0%BB%D1%8C%D0%BD%D1%8B%D1%85_%D0%93%D0%A2%D0%A0%D0%9A_%D0%B2_%D0%A0%D0%BE%D1%81%D1%81%D0%B8%D0%B8

[^18]: https://vgtrk.ru/about

[^19]: https://digital.gov.ru/organizations/fgup-vgtrk

[^20]: https://ppl-ai-code-interpreter-files.s3.amazonaws.com/web/direct-files/c7660626f21093e1abffa28941237a26/38a367ad-27e2-45e1-b783-50f326727421/b060be28.csv

