# Архитектура обработки Sitemap

## Проблема
Многие сайты используют двухуровневую структуру sitemap:
```
sitemap_index.xml (главный индекс)
├── sitemap2025.xml (sitemap для 2025 года)
│   ├── URL статьи 1
│   ├── URL статьи 2
│   └── ...
├── sitemap2024.xml (sitemap для 2024 года)
│   ├── URL статьи 1
│   ├── URL статьи 2
│   └── ...
└── sitemap_news.xml (sitemap для новостей)
    ├── URL новости 1
    └── ...
```

## Текущая реализация (неправильная)
```python
# Пытаемся парсить sitemap_index.xml как обычный sitemap
# Результат: 0 URL, так как в индексе нет прямых ссылок на статьи
```

## Правильная реализация

### 1. Определение типа sitemap
```xml
<!-- sitemap_index.xml -->
<sitemapindex>
    <sitemap>
        <loc>https://site.ru/sitemap2025.xml</loc>
        <lastmod>2025-09-11</lastmod>
    </sitemap>
</sitemapindex>

<!-- обычный sitemap -->
<urlset>
    <url>
        <loc>https://site.ru/article.html</loc>
        <lastmod>2025-09-11</lastmod>
    </url>
</urlset>
```

### 2. Алгоритм обработки

```
1. Загрузить sitemap_index.xml
2. Проверить корневой элемент:
   - Если <sitemapindex> → извлечь список вложенных sitemap
   - Если <urlset> → извлечь URL статей
3. Для каждого вложенного sitemap:
   - Загрузить XML
   - Рекурсивно обработать (может быть еще один индекс)
   - Извлечь URL статей
4. Фильтровать по датам
5. Вернуть объединенный список URL
```

### 3. Оптимизации

#### По названию файла
```python
# Если sitemap называется по годам, можем загружать только нужные
if days <= 365:
    current_year = datetime.now().year
    sitemaps_to_load = [f"sitemap{current_year}.xml"]
    if days > 30:
        sitemaps_to_load.append(f"sitemap{current_year-1}.xml")
```

#### По lastmod в индексе
```python
# Проверяем дату последнего изменения sitemap
sitemap_lastmod = parse_date(sitemap['lastmod'])
if sitemap_lastmod < start_date:
    continue  # Пропускаем старые sitemap
```

### 4. Обработка часовых поясов
```python
# ГТРК Саха использует +09:00
from dateutil import parser
date_str = "2025-09-11T17:02:41+09:00"
date = parser.parse(date_str)
# Конвертируем в UTC или локальное время для сравнения
```

## Реализация в коде

### Метод parse_sitemap_urls (обновленный)
```python
def parse_sitemap_urls(self, sitemap_url, start_date=None, end_date=None):
    """
    Рекурсивно парсит sitemap или sitemap_index
    
    Args:
        sitemap_url: URL sitemap файла
        start_date: начальная дата фильтрации
        end_date: конечная дата фильтрации
    
    Returns:
        list: список URL с метаданными
    """
    urls = []
    
    # Загружаем XML
    response = requests.get(sitemap_url, timeout=10)
    root = ET.fromstring(response.content)
    
    # Определяем тип sitemap по корневому элементу
    if root.tag.endswith('sitemapindex'):
        # Это индексный файл - парсим вложенные sitemap
        for sitemap in root.findall('.//{*}sitemap'):
            loc = sitemap.find('{*}loc')
            if loc is not None:
                nested_url = loc.text
                # Рекурсивно обрабатываем вложенный sitemap
                nested_urls = self.parse_sitemap_urls(
                    nested_url, start_date, end_date
                )
                urls.extend(nested_urls)
    
    elif root.tag.endswith('urlset'):
        # Это обычный sitemap - извлекаем URL
        for url in root.findall('.//{*}url'):
            loc = url.find('{*}loc')
            lastmod = url.find('{*}lastmod')
            
            if loc is not None:
                url_data = {'url': loc.text}
                
                # Парсим дату если есть
                if lastmod is not None:
                    try:
                        date = parser.parse(lastmod.text)
                        url_data['date'] = date
                        
                        # Фильтруем по датам
                        if start_date and date < start_date:
                            continue
                        if end_date and date > end_date:
                            continue
                    except:
                        pass
                
                urls.append(url_data)
    
    return urls
```

## Тестирование

### Тестовый сценарий для ГТРК Саха
1. Загружаем https://gtrksakha.ru/sitemap_index.xml
2. Находим sitemap2025.xml в индексе
3. Загружаем https://gtrksakha.ru/sitemap2025.xml
4. Находим статью про конгресс от 11.09.2025
5. Проверяем фильтрацию по датам

### Ожидаемый результат
```
✓ Найден sitemap_index.xml
✓ Найдено 3 вложенных sitemap
✓ Обработка sitemap2025.xml
✓ Найдено 150 URL за 2025 год
✓ После фильтрации по датам: 5 URL за последние 7 дней
✓ Найдена статья: "Конгресс 'Национальное здравоохранение'"
```

## Преимущества решения
1. **Универсальность** - работает с любой структурой sitemap
2. **Рекурсивность** - поддерживает многоуровневые индексы
3. **Оптимизация** - загружает только нужные sitemap
4. **Точность** - правильно обрабатывает даты и часовые пояса
5. **Масштабируемость** - может обработать тысячи URL