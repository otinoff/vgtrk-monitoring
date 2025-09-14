# 🚀 ПРОСТАЯ ИНСТРУКЦИЯ ЗАПУСКА НА VPS

## ШАГ 1: Подключитесь к серверу
```bash
ssh root@5.35.88.251
```

## ШАГ 2: Скачайте проект с GitHub
```bash
cd /var/www
git clone https://github.com/otinoff/vgtrk-monitoring.git
cd vgtrk-monitoring
```

## ШАГ 3: Запустите установку
```bash
chmod +x setup_nginx.sh
./setup_nginx.sh
```

## ШАГ 4: Установите Python пакеты
```bash
python3 -m venv venv
source venv/bin/activate
pip install streamlit pandas requests beautifulsoup4 lxml aiohttp streamlit-aggrid
```

## ШАГ 5: Запустите приложение
```bash
streamlit run app_sqlite.py --server.port 8501 --server.address 0.0.0.0
```

## 🎉 ГОТОВО!
Откройте в браузере:
- http://5.35.88.251:8501
- http://ai-search.onff.ru (если домен настроен)

## Если что-то не работает:
```bash
# Проверьте логи
tail -f /var/log/nginx/error.log

# Перезапустите nginx
systemctl restart nginx

# Убейте старые процессы streamlit
pkill -f streamlit