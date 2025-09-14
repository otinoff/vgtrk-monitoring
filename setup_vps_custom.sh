#!/bin/bash

# ====================================
# VPS Setup Script для ai-search.onff.ru
# Сервер: 5.35.88.251
# ====================================

set -e  # Остановка при ошибке

echo "🚀 Начинаем установку VGTRK Monitor на VPS..."
echo "================================================"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Проверка root прав
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}Этот скрипт должен быть запущен с правами root${NC}" 
   exit 1
fi

# Определение ОС
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    VER=$VERSION_ID
else
    echo -e "${RED}Не удалось определить операционную систему${NC}"
    exit 1
fi

echo -e "${GREEN}Обнаружена ОС: $OS $VER${NC}"

# 1. Обновление системы
echo -e "\n${YELLOW}1. Обновление системы...${NC}"
if [[ "$OS" == "ubuntu" ]] || [[ "$OS" == "debian" ]]; then
    apt-get update && apt-get upgrade -y
    apt-get install -y python3-pip python3-venv git nginx certbot python3-certbot-nginx supervisor
elif [[ "$OS" == "centos" ]] || [[ "$OS" == "rhel" ]]; then
    yum update -y
    yum install -y python3-pip python3-virtualenv git nginx certbot python3-certbot-nginx supervisor
fi

# 2. Создание виртуального окружения
echo -e "\n${YELLOW}2. Настройка Python окружения...${NC}"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip

# Создаем requirements.txt если его нет
if [ ! -f "requirements.txt" ]; then
    echo -e "\n${YELLOW}Создаем requirements.txt...${NC}"
    cat > requirements.txt << 'EOF'
streamlit==1.28.1
streamlit-aggrid==0.3.4.post3
pandas==2.1.3
requests==2.31.0
beautifulsoup4==4.12.2
lxml==4.9.3
aiohttp==3.9.0
asyncio==3.4.3
python-dateutil==2.8.2
pytz==2023.3
urllib3==2.1.0
numpy==1.26.2
EOF
fi

pip install -r requirements.txt

# 5. Создание systemd сервиса
echo -e "\n${YELLOW}3. Создание systemd сервиса...${NC}"
cat > /etc/systemd/system/vgtrk-monitoring.service << 'EOF'
[Unit]
Description=VGTRK Monitoring System
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/vgtrk-monitoring
Environment="PATH=/opt/vgtrk-monitoring/venv/bin"
ExecStart=/opt/vgtrk-monitoring/venv/bin/streamlit run app_sqlite.py --server.port 8501 --server.address 0.0.0.0
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 6. Настройка Nginx
echo -e "\n${YELLOW}4. Настройка Nginx...${NC}"
cat > /etc/nginx/sites-available/vgtrk-monitoring << 'EOF'
server {
    listen 80;
    server_name ai-search.onff.ru;
    
    client_max_body_size 100M;
    
    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
    
    location /_stcore/stream {
        proxy_pass http://localhost:8501/_stcore/stream;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
EOF

# Создание символической ссылки
ln -sf /etc/nginx/sites-available/vgtrk-monitoring /etc/nginx/sites-enabled/

# Проверка конфигурации Nginx
nginx -t

# 7. Настройка файрвола (если установлен)
echo -e "\n${YELLOW}5. Настройка файрвола...${NC}"
if command -v ufw &> /dev/null; then
    ufw allow 22/tcp
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw allow 8501/tcp
    echo "y" | ufw enable
    echo -e "${GREEN}UFW настроен${NC}"
elif command -v firewall-cmd &> /dev/null; then
    firewall-cmd --permanent --add-service=http
    firewall-cmd --permanent --add-service=https
    firewall-cmd --permanent --add-port=8501/tcp
    firewall-cmd --reload
    echo -e "${GREEN}Firewalld настроен${NC}"
fi

# 8. Запуск сервисов
echo -e "\n${YELLOW}6. Запуск сервисов...${NC}"
systemctl daemon-reload
systemctl enable vgtrk-monitoring
systemctl start vgtrk-monitoring
systemctl restart nginx
systemctl enable nginx

# 9. Настройка SSL сертификата (опционально)
echo -e "\n${YELLOW}7. Настройка SSL...${NC}"
echo -e "${YELLOW}Хотите настроить SSL сертификат? (y/n)${NC}"
read -r setup_ssl

if [[ "$setup_ssl" == "y" ]]; then
    certbot --nginx -d ai-search.onff.ru --non-interactive --agree-tos --email admin@onff.ru
    echo -e "${GREEN}SSL сертификат установлен${NC}"
fi

# 10. Создание скрипта для обновления
echo -e "\n${YELLOW}8. Создание скрипта обновления...${NC}"
cat > /opt/vgtrk-monitoring/update.sh << 'EOF'
#!/bin/bash
cd /opt/vgtrk-monitoring
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
systemctl restart vgtrk-monitoring
echo "✅ Обновление завершено!"
EOF

chmod +x /opt/vgtrk-monitoring/update.sh

# Финальная проверка
echo -e "\n${GREEN}============================================${NC}"
echo -e "${GREEN}✅ Установка завершена успешно!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "📋 Информация о развертывании:"
echo -e "   ${YELLOW}URL:${NC} http://ai-search.onff.ru"
echo -e "   ${YELLOW}IP:${NC} 5.35.88.251:8501"
echo ""
echo -e "🔧 Полезные команды:"
echo -e "   ${YELLOW}Статус:${NC} systemctl status vgtrk-monitoring"
echo -e "   ${YELLOW}Логи:${NC} journalctl -u vgtrk-monitoring -f"
echo -e "   ${YELLOW}Перезапуск:${NC} systemctl restart vgtrk-monitoring"
echo -e "   ${YELLOW}Обновление:${NC} /opt/vgtrk-monitoring/update.sh"
echo ""
echo -e "📁 Пути:"
echo -e "   ${YELLOW}Проект:${NC} /opt/vgtrk-monitoring"
echo -e "   ${YELLOW}Логи:${NC} /var/log/nginx/"
echo -e "   ${YELLOW}База данных:${NC} /opt/vgtrk-monitoring/data/vgtrk_monitoring.db"