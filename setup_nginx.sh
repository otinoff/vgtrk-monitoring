#!/bin/bash

# ====================================
# Скрипт настройки Nginx для VGTRK Monitor
# ====================================

echo "🔧 Настройка Nginx для VGTRK Monitor..."
echo "========================================"

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 1. Создаем конфигурацию Nginx
echo -e "\n${YELLOW}Создаем конфигурацию Nginx...${NC}"

# Создаем новый конфиг
cat > /etc/nginx/sites-available/vgtrk-monitor << 'EOF'
server {
    listen 80;
    listen [::]:80;
    
    # Домены
    server_name ai-search.onff.ru 5.35.88.251;
    
    # Увеличиваем лимиты
    client_max_body_size 100M;
    proxy_read_timeout 86400;
    proxy_connect_timeout 60;
    proxy_send_timeout 60;
    
    # Основная локация - проксирование на Streamlit
    location / {
        proxy_pass http://127.0.0.1:8501;
        
        # WebSocket поддержка для Streamlit
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Заголовки
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Буферизация
        proxy_buffering off;
        proxy_request_buffering off;
    }
    
    # Специальная локация для Streamlit WebSocket
    location /_stcore/stream {
        proxy_pass http://127.0.0.1:8501/_stcore/stream;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }
    
    # Статические файлы Streamlit
    location /static {
        proxy_pass http://127.0.0.1:8501/static;
    }
    
    # Healthcheck endpoint
    location /healthz {
        proxy_pass http://127.0.0.1:8501/healthz;
    }
}
EOF

echo -e "${GREEN}✅ Конфигурация создана${NC}"

# 2. Удаляем старые конфиги если есть
echo -e "\n${YELLOW}Очищаем старые конфигурации...${NC}"
rm -f /etc/nginx/sites-enabled/default
rm -f /etc/nginx/sites-enabled/vgtrk-monitoring

# 3. Активируем новую конфигурацию
echo -e "\n${YELLOW}Активируем конфигурацию...${NC}"
ln -sf /etc/nginx/sites-available/vgtrk-monitor /etc/nginx/sites-enabled/

# 4. Проверяем конфигурацию
echo -e "\n${YELLOW}Проверяем конфигурацию Nginx...${NC}"
nginx -t

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Конфигурация корректна${NC}"
    
    # 5. Перезапускаем Nginx
    echo -e "\n${YELLOW}Перезапускаем Nginx...${NC}"
    systemctl restart nginx
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Nginx успешно перезапущен${NC}"
    else
        echo -e "${RED}❌ Ошибка при перезапуске Nginx${NC}"
        echo "Попробуйте выполнить: systemctl status nginx"
    fi
else
    echo -e "${RED}❌ Ошибка в конфигурации Nginx${NC}"
    echo "Проверьте файл: /etc/nginx/sites-available/vgtrk-monitor"
fi

# 6. Проверяем статус
echo -e "\n${YELLOW}Статус Nginx:${NC}"
systemctl status nginx --no-pager | head -10

# 7. Открываем порты в файрволе
echo -e "\n${YELLOW}Настраиваем файрвол...${NC}"
if command -v ufw &> /dev/null; then
    ufw allow 80/tcp
    ufw allow 8501/tcp
    echo -e "${GREEN}✅ Порты открыты в UFW${NC}"
elif command -v firewall-cmd &> /dev/null; then
    firewall-cmd --permanent --add-service=http
    firewall-cmd --permanent --add-port=8501/tcp
    firewall-cmd --reload
    echo -e "${GREEN}✅ Порты открыты в firewalld${NC}"
else
    echo -e "${YELLOW}⚠️ Файрвол не найден, убедитесь что порты 80 и 8501 открыты${NC}"
fi

# 8. Финальная информация
echo -e "\n${GREEN}============================================${NC}"
echo -e "${GREEN}✅ Nginx настроен успешно!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "📋 Приложение будет доступно по адресам:"
echo -e "   ${YELLOW}http://ai-search.onff.ru${NC}"
echo -e "   ${YELLOW}http://5.35.88.251${NC}"
echo -e "   ${YELLOW}http://5.35.88.251:8501${NC} (прямой доступ)"
echo ""
echo -e "🔧 Полезные команды:"
echo -e "   ${YELLOW}Логи Nginx:${NC} tail -f /var/log/nginx/error.log"
echo -e "   ${YELLOW}Перезапуск:${NC} systemctl restart nginx"
echo -e "   ${YELLOW}Статус:${NC} systemctl status nginx"
echo -e "   ${YELLOW}Конфиг:${NC} nano /etc/nginx/sites-available/vgtrk-monitor"