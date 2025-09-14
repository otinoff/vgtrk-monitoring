# 🚨 Решение ошибки HTTP2_PROTOCOL_ERROR в Streamlit

## ❌ Проблема
```
Failed to load resource: net::ERR_HTTP2_PROTOCOL_ERROR
/static/js/index.CD8HuT3N.js:1 Failed to load resource: net::ERR_HTTP2_PROTOCOL_ERROR
evmAsk.js:5 Uncaught TypeError: Cannot redefine property: ethereum
```

## 🔍 Причина
Эта ошибка вызвана **конфликтом браузерных расширений** с Streamlit:
- **evmAsk.js** - расширение для криптокошельков (MetaMask, Trust Wallet и т.д.)
- **gosuslugi.plugin.extension** - расширение Госуслуг
- **HTTP2_PROTOCOL_ERROR** - конфликт протоколов между расширениями и Streamlit

## ✅ Быстрые решения

### 🚀 Решение 1: Режим инкогнито (самое простое)
1. Откройте **режим инкогнито** в браузере (Ctrl+Shift+N)
2. Перейдите на `http://localhost:8501`
3. ✅ Приложение должно работать без ошибок

### 🔧 Решение 2: Отключение расширений
1. Откройте `chrome://extensions/` (или аналог в вашем браузере)
2. **Временно отключите** следующие типы расширений:
   - 🔒 **Криптокошельки** (MetaMask, Trust Wallet, evmAsk)
   - 🏛️ **Госуслуги** (gosuslugi.plugin.extension)
   - 🛡️ **Блокировщики рекламы** (uBlock, Adblock)
   - 🔐 **VPN расширения**
3. Обновите страницу (F5)

### 🌐 Решение 3: Другой браузер
- Попробуйте **Firefox** вместо Chrome
- Или **Edge** без расширений
- Или **Opera** в базовой конфигурации

### ⚙️ Решение 4: Изменение настроек Streamlit
Добавьте в файл `.streamlit/config.toml` (создайте если нет):

```toml
[server]
enableCORS = false
enableXsrfProtection = false
enableWebsocketCompression = false

[browser]
gatherUsageStats = false
```

## 🛠️ Автоматическое исправление

Создайте этот скрипт для запуска с фиксом HTTP2:

```python
# fix_http2_streamlit.py
import subprocess
import os

def create_config():
    """Создание конфигурации Streamlit для решения HTTP2 проблем"""
    config_dir = ".streamlit"
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
    
    config_content = """[server]
enableCORS = false
enableXsrfProtection = false
enableWebsocketCompression = false
port = 8502
headless = false

[browser]
gatherUsageStats = false
serverAddress = "localhost"

[global]
suppressDeprecationWarnings = true
"""
    
    with open(os.path.join(config_dir, "config.toml"), "w") as f:
        f.write(config_content)
    
    print("✅ Создан файл конфигурации .streamlit/config.toml")

def start_streamlit():
    """Запуск Streamlit с безопасными настройками"""
    create_config()
    
    print("🚀 Запуск Streamlit с исправлением HTTP2...")
    print("📱 Откроется в браузере: http://localhost:8502")
    print("💡 Если не работает, используйте режим инкогнито")
    
    subprocess.run([
        "streamlit", "run", "app.py",
        "--server.port", "8502",
        "--server.headless", "false",
        "--browser.gatherUsageStats", "false",
        "--server.enableCORS", "false",
        "--server.enableXsrfProtection", "false"
    ])

if __name__ == "__main__":
    start_streamlit()
```

## 🎯 Специфичные решения для расширений

### MetaMask / evmAsk
```javascript
// Добавьте в консоль браузера (F12):
delete window.ethereum;
location.reload();
```

### Госуслуги
1. Отключите расширение Госуслуг
2. Или добавьте `localhost` в исключения расширения

### Блокировщики рекламы
1. Добавьте `localhost:*` в белый список
2. Или отключите для локальных адресов

## 📋 Пошаговая инструкция

### Для пользователей:
1. **Попробуйте режим инкогнито** - это решает 90% проблем
2. Если не помогло - **отключите все расширения**
3. Если не помогло - попробуйте **другой браузер**
4. Если не помогло - используйте **автоскрипт исправления**

### Для разработчиков:
```bash
# Создайте и запустите скрипт исправления
python -c "
import subprocess
import os

# Создаем безопасную конфигурацию
os.makedirs('.streamlit', exist_ok=True)
with open('.streamlit/config.toml', 'w') as f:
    f.write('''[server]
enableCORS = false
enableXsrfProtection = false
enableWebsocketCompression = false
port = 8502
[browser]
gatherUsageStats = false
''')

# Запускаем с безопасными настройками
subprocess.run(['streamlit', 'run', 'app.py', '--server.port', '8502'])
"
```

## ⚠️ Важные моменты

1. **Проблема не в вашем приложении** - это конфликт браузерных расширений
2. **В режиме инкогнито всё работает** - это подтверждает, что дело в расширениях
3. **Решение временное** - пользователи могут включить расширения после работы с приложением
4. **Альтернативные браузеры** - часто решают проблему полностью

## 🔗 Полезные ссылки

- [Streamlit Configuration](https://docs.streamlit.io/library/advanced-features/configuration)
- [Chrome Extensions Troubleshooting](https://support.google.com/chrome/answer/187443)
- [HTTP2 Protocol Error Solutions](https://developers.google.com/web/fundamentals/performance/http2)

---

**💡 Главное**: Эта ошибка **НЕ связана с вашим кодом**. Это проблема совместимости браузера и его расширений с современными веб-технологиями, которые использует Streamlit.