#!/bin/bash

# Скрипт для установки и запуска Streamlit сервиса с nginx

echo "🔧 Установка Streamlit сервиса..."

# Копируем файл сервиса в системную директорию
sudo cp /var/parsing_vesti42/streamlit.service /etc/systemd/system/

# Перезагружаем конфигурацию systemd
sudo systemctl daemon-reload

# Включаем сервис для автозапуска
sudo systemctl enable streamlit.service

# Запускаем сервис
sudo systemctl start streamlit.service

# Настраиваем nginx
echo "🔧 Настройка nginx..."

# Проверяем, установлен ли nginx
if ! command -v nginx &> /dev/null
then
    echo "⚠️  Nginx не установлен. Устанавливаем..."
    sudo apt update
    sudo apt install -y nginx
fi

# Копируем конфигурационный файл nginx
sudo cp /var/parsing_vesti42/nginx.conf /etc/nginx/sites-available/ai-search.onff.ru

# Создаем символическую ссылку для включения сайта
sudo ln -sf /etc/nginx/sites-available/ai-search.onff.ru /etc/nginx/sites-enabled/

# Проверяем конфигурацию nginx
sudo nginx -t

# Перезапускаем nginx
sudo systemctl restart nginx

# Включаем автозапуск nginx
sudo systemctl enable nginx

# Проверяем статус сервиса
echo "🔍 Проверка статуса сервиса..."
sudo systemctl status streamlit.service

echo "✅ Сервис установлен и запущен!"
echo "🌐 Приложение будет доступно по адресу: http://ai-search.onff.ru"
echo "📝 Для завершения настройки убедитесь, что DNS запись ai-search.onff.ru указывает на этот сервер"