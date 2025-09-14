# 🔄 УПРАВЛЕНИЕ ДАННЫМИ МЕЖДУ СРЕДАМИ РАЗРАБОТКИ И ПРОДАКШНА

## 📋 ОБЗОР

Этот документ описывает процедуры управления данными между средами разработки и продакшна для системы мониторинга ВГТРК.

## 🗂️ СТРУКТУРА БАЗЫ ДАННЫХ

### Основные таблицы:

1. **filials** - Филиалы ВГТРК
   - `id` - Уникальный идентификатор
   - `name` - Название филиала
   - `region` - Регион
   - `city` - Город
   - `website` - URL сайта филиала
   - `federal_district` - Федеральный округ
   - `all_sites` - Все сайты филиала
   - `sitemap_url` - URL sitemap.xml
   - `is_active` - Активен ли филиал

2. **search_queries** - Поисковые запросы
   - `id` - Уникальный идентификатор
   - `query_text` - Текст запроса
   - `category` - Категория запроса
   - `description` - Описание
   - `priority` - Приоритет (1-10)
   - `is_active` - Активен ли запрос

3. **monitoring_sessions** - Сессии мониторинга
   - `id` - Уникальный идентификатор
   - `session_name` - Название сессии
   - `search_mode` - Режим поиска
   - `search_period` - Период поиска
   - `filials_count` - Количество филиалов
   - `status` - Статус сессии

4. **monitoring_results** - Результаты мониторинга
   - `id` - Уникальный идентификатор
   - `filial_id` - ID филиала
   - `search_query_id` - ID поискового запроса
   - `url` - URL найденной статьи
   - `page_title` - Заголовок страницы
   - `content` - Содержимое
   - `relevance_score` - Оценка релевантности
   - `status` - Статус обработки

## 🚀 ПРОЦЕДУРЫ УПРАВЛЕНИЯ ДАННЫМИ

### 1. ЭКСПОРТ ДАННЫХ

#### Экспорт всей базы данных:
```bash
python export_import_data.py export data/vgtrk_monitoring.db data/export.json
```

#### Экспорт с указанием конкретной директории:
```bash
python export_import_data.py export data/vgtrk_monitoring.db /path/to/export/directory/export.json
```

### 2. ИМПОРТ ДАННЫХ

#### Импорт данных в базу:
```bash
python export_import_data.py import data/vgtrk_monitoring.db data/export.json
```

#### Импорт с очисткой существующих данных:
```bash
python export_import_data.py import data/vgtrk_monitoring.db data/export.json --clear-existing
```

### 3. ПРОСМОТР ИНФОРМАЦИИ О БАЗЕ

#### Просмотр информации о базе данных:
```bash
python export_import_data.py info data/vgtrk_monitoring.db
```

## 📦 РЕЗЕРВНОЕ КОПИРОВАНИЕ

### Создание резервной копии:
```bash
python backup_database.py create data/vgtrk_monitoring.db
```

### Просмотр списка резервных копий:
```bash
python backup_database.py list
```

### Восстановление из резервной копии:
```bash
python backup_database.py restore data/backups/vgtrk_monitoring_backup_20230101_120000.db data/vgtrk_monitoring.db
```

### Очистка старых резервных копий:
```bash
python backup_database.py cleanup data/backups 30
```

## 🔄 СЦЕНАРИИ РАЗВЕРТЫВАНИЯ

### 1. Первоначальное развертывание

1. **Экспорт данных из среды разработки:**
   ```bash
   python export_import_data.py export data/vgtrk_monitoring.db dev_export.json
   ```

2. **Перенос файла экспорта на продакшн сервер:**
   ```bash
   scp dev_export.json user@production-server:/path/to/project/data/
   ```

3. **Импорт данных на продакшн сервере:**
   ```bash
   python export_import_data.py import data/vgtrk_monitoring.db data/dev_export.json
   ```

### 2. Обновление продакшна новыми данными

1. **Создание резервной копии продакшна:**
   ```bash
   python backup_database.py create data/vgtrk_monitoring.db
   ```

2. **Экспорт новых данных из среды разработки:**
   ```bash
   python export_import_data.py export data/vgtrk_monitoring.db new_data.json
   ```

3. **Перенос и импорт на продакшн:**
   ```bash
   scp new_data.json user@production-server:/path/to/project/data/
   ssh user@production-server "cd /path/to/project && python export_import_data.py import data/vgtrk_monitoring.db data/new_data.json"
   ```

### 3. Перенос данных с продакшна в разработку

1. **Экспорт данных с продакшна:**
   ```bash
   ssh user@production-server "cd /path/to/project && python export_import_data.py export data/vgtrk_monitoring.db prod_data.json"
   ```

2. **Копирование файла на локальную машину:**
   ```bash
   scp user@production-server:/path/to/project/data/prod_data.json ./
   ```

3. **Импорт в среду разработки:**
   ```bash
   python export_import_data.py import data/vgtrk_monitoring.db prod_data.json
   ```

## ⚠️ ВАЖНЫЕ ЗАМЕЧАНИЯ

### 1. Совместимость структур
- Убедитесь, что структуры баз данных совместимы перед импортом
- Новые поля автоматически добавляются при импорте

### 2. Резервное копирование
- Всегда создавайте резервные копии перед импортом данных
- Храните резервные копии в безопасном месте

### 3. Безопасность
- Не храните чувствительные данные в файлах экспорта
- Используйте защищенные каналы передачи данных

### 4. Автоматизация
- CI/CD автоматически сохраняет данные при каждом деплое
- Регулярные резервные копии создаются по расписанию

## 🛠️ УСТРАНЕНИЕ НЕИСПРАВНОСТЕЙ

### Проблемы с импортом:
1. Проверьте совместимость структур баз данных
2. Убедитесь, что файл экспорта не поврежден
3. Проверьте права доступа к файлам

### Проблемы с резервным копированием:
1. Убедитесь, что достаточно свободного места
2. Проверьте права доступа к директории резервных копий
3. Проверьте целостность файлов резервных копий

## 📊 МОНИТОРИНГ

### Просмотр статистики:
```bash
python export_import_data.py info data/vgtrk_monitoring.db
```

### Проверка целостности:
```bash
python backup_database.py create data/vgtrk_monitoring.db /tmp/test_backup.db
python backup_database.py restore /tmp/test_backup.db /tmp/restored.db
```

## 📞 ПОДДЕРЖКА

При возникновении проблем:
1. Проверьте логи системы
2. Создайте issue в репозитории
3. Свяжитесь с администратором системы