#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Диагностика конфликтов браузерных расширений со Streamlit
Определение проблемных расширений по ошибкам JavaScript
"""

import webbrowser
import time
import os

def analyze_js_errors():
    """Анализ типичных JavaScript ошибок от расширений"""
    
    print("=== АНАЛИЗ ОШИБОК РАСШИРЕНИЙ ===")
    print()
    
    error_patterns = {
        "HTTP2_PROTOCOL_ERROR": {
            "description": "Конфликт HTTP/2 протокола с расширениями",
            "likely_extensions": [
                "AdBlock, uBlock Origin (блокировщики рекламы)",
                "MetaMask, Trust Wallet (криптокошельки)", 
                "VPN расширения (NordVPN, ExpressVPN)",
                "Переводчики (Google Translate)"
            ],
            "solutions": [
                "Отключите блокировщики рекламы",
                "Отключите VPN расширения",
                "Используйте режим инкогнито",
                "Запустите на порту 8502"
            ]
        },
        "evmAsk.js": {
            "description": "Конфликт с криптокошельками",
            "likely_extensions": [
                "MetaMask",
                "Trust Wallet",
                "Coinbase Wallet",
                "WalletConnect"
            ],
            "solutions": [
                "Отключите все криптокошельки",
                "В консоли браузера: delete window.ethereum",
                "Используйте другой браузер без кошельков"
            ]
        },
        "polyfill.js:500": {
            "description": "Ошибка WebExtension API polyfill",
            "likely_extensions": [
                "Яндекс.Переводчик",
                "Google Translate",
                "LastPass, 1Password (менеджеры паролей)",
                "VK, Facebook расширения",
                "Темы и скины браузера",
                "Расширения для скриншотов"
            ],
            "solutions": [
                "Отключите переводчики",
                "Отключите менеджеры паролей",
                "Отключите социальные расширения",
                "Обновите проблемные расширения"
            ]
        },
        "gosuslugi.plugin.extension": {
            "description": "Конфликт с расширением Госуслуг",
            "likely_extensions": [
                "Госуслуги.Плагин",
                "ЭЦП расширения"
            ],
            "solutions": [
                "Отключите расширение Госуслуг",
                "Добавьте localhost в исключения",
                "Используйте браузер без госрасширений"
            ]
        }
    }
    
    for error_name, info in error_patterns.items():
        print(f"🔍 ОШИБКА: {error_name}")
        print(f"   Описание: {info['description']}")
        print(f"   Вероятные расширения:")
        for ext in info['likely_extensions']:
            print(f"     - {ext}")
        print(f"   Решения:")
        for solution in info['solutions']:
            print(f"     ✅ {solution}")
        print()

def create_browser_test_page():
    """Создание тестовой HTML страницы для диагностики"""
    
    html_content = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Тест расширений браузера</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f0f2f6; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }
        .error-box { background: #ffebee; border: 1px solid #f44336; padding: 15px; margin: 10px 0; border-radius: 5px; }
        .success-box { background: #e8f5e8; border: 1px solid #4caf50; padding: 15px; margin: 10px 0; border-radius: 5px; }
        .extension-list { background: #fff3e0; border: 1px solid #ff9800; padding: 15px; margin: 10px 0; border-radius: 5px; }
        button { background: #1976d2; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin: 5px; }
        button:hover { background: #1565c0; }
        #results { margin-top: 20px; }
        .step { margin: 15px 0; padding: 15px; background: #f5f5f5; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 Диагностика расширений браузера для Streamlit</h1>
        
        <div class="step">
            <h3>Шаг 1: Проверка активных расширений</h3>
            <button onclick="checkExtensions()">Проверить расширения</button>
            <div id="extension-results"></div>
        </div>
        
        <div class="step">
            <h3>Шаг 2: Тест JavaScript ошибок</h3>
            <button onclick="testJavaScriptErrors()">Запустить тест</button>
            <div id="js-results"></div>
        </div>
        
        <div class="step">
            <h3>Шаг 3: Симуляция Streamlit окружения</h3>
            <button onclick="testStreamlitLike()">Тест Streamlit-подобного окружения</button>
            <div id="streamlit-results"></div>
        </div>
        
        <div class="extension-list">
            <h3>🚨 Проблемные расширения:</h3>
            <ul>
                <li><strong>Криптокошельки:</strong> MetaMask, Trust Wallet, Coinbase Wallet</li>
                <li><strong>Блокировщики:</strong> AdBlock, uBlock Origin</li>
                <li><strong>VPN:</strong> NordVPN, ExpressVPN, Surfshark</li>
                <li><strong>Переводчики:</strong> Google Translate, Яндекс.Переводчик</li>
                <li><strong>Пароли:</strong> LastPass, 1Password, Bitwarden</li>
                <li><strong>Госуслуги:</strong> Госуслуги.Плагин</li>
                <li><strong>Соцсети:</strong> VK расширения, Facebook Container</li>
            </ul>
        </div>
        
        <div id="results"></div>
        
        <div class="step">
            <h3>💡 Решения:</h3>
            <ol>
                <li><strong>Режим инкогнито</strong> - отключает все расширения</li>
                <li><strong>Отключите расширения по одному</strong> до исчезновения ошибки</li>
                <li><strong>Используйте другой браузер</strong> (Firefox вместо Chrome)</li>
                <li><strong>Добавьте localhost в исключения</strong> проблемных расширений</li>
            </ol>
        </div>
    </div>

    <script>
        function checkExtensions() {
            const results = document.getElementById('extension-results');
            let extensionTests = [];
            
            // Проверка MetaMask
            if (typeof window.ethereum !== 'undefined') {
                extensionTests.push('<div class="error-box">❌ Обнаружен MetaMask/криптокошелек (window.ethereum)</div>');
            }
            
            // Проверка Госуслуг
            if (window.gosuslugi || document.querySelector('[src*="gosuslugi"]')) {
                extensionTests.push('<div class="error-box">❌ Обнаружено расширение Госуслуг</div>');
            }
            
            // Проверка блокировщиков (косвенно)
            if (window.chrome && window.chrome.extension) {
                extensionTests.push('<div class="error-box">⚠️ Возможны расширения Chrome (включая блокировщики)</div>');
            }
            
            if (extensionTests.length === 0) {
                results.innerHTML = '<div class="success-box">✅ Проблемных расширений не обнаружено</div>';
            } else {
                results.innerHTML = extensionTests.join('');
            }
        }
        
        function testJavaScriptErrors() {
            const results = document.getElementById('js-results');
            let errorCount = 0;
            
            // Слушаем ошибки JavaScript
            window.onerror = function(msg, url, line, col, error) {
                errorCount++;
                console.error('JS Error:', msg, url, line);
                return false;
            };
            
            // Пытаемся создать конфликты
            try {
                // Симуляция конфликта с ethereum
                if (window.ethereum) {
                    Object.defineProperty(window, 'ethereum', {
                        value: 'test',
                        writable: false
                    });
                }
            } catch (e) {
                results.innerHTML += '<div class="error-box">❌ Конфликт с криптокошельком: ' + e.message + '</div>';
            }
            
            setTimeout(() => {
                if (errorCount === 0) {
                    results.innerHTML = '<div class="success-box">✅ JavaScript ошибки не обнаружены</div>';
                } else {
                    results.innerHTML += '<div class="error-box">❌ Обнаружено ' + errorCount + ' JavaScript ошибок</div>';
                }
            }, 1000);
        }
        
        function testStreamlitLike() {
            const results = document.getElementById('streamlit-results');
            
            // Симуляция загрузки Streamlit-подобных ресурсов
            const testUrls = [
                '/static/js/index.js',
                '/static/css/streamlit.css',
                'http://localhost:8501/_stcore/health'
            ];
            
            let testResults = [];
            
            testUrls.forEach(url => {
                fetch(url).then(response => {
                    testResults.push('<div class="success-box">✅ ' + url + ' - OK</div>');
                }).catch(error => {
                    if (error.message.includes('HTTP2') || error.message.includes('net::')) {
                        testResults.push('<div class="error-box">❌ ' + url + ' - HTTP2/Network Error (возможна блокировка расширениями)</div>');
                    } else {
                        testResults.push('<div class="error-box">⚠️ ' + url + ' - ' + error.message + '</div>');
                    }
                }).finally(() => {
                    if (testResults.length === testUrls.length) {
                        results.innerHTML = testResults.join('');
                    }
                });
            });
        }
        
        // Автоматический запуск проверки при загрузке
        window.onload = function() {
            checkExtensions();
        };
    </script>
</body>
</html>
    """
    
    try:
        with open("browser_extension_test.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        print("✅ Создана тестовая страница: browser_extension_test.html")
        return True
    except Exception as e:
        print(f"❌ Ошибка создания тестовой страницы: {e}")
        return False

def main():
    """Основная функция диагностики"""
    print("🔍 ДИАГНОСТИКА КОНФЛИКТОВ РАСШИРЕНИЙ СО STREAMLIT")
    print("=" * 60)
    print()
    
    # Анализируем известные ошибки
    analyze_js_errors()
    
    # Создаем тестовую страницу
    if create_browser_test_page():
        print("🌐 Откройте browser_extension_test.html в браузере для интерактивной диагностики")
        print()
        
        # Пытаемся открыть автоматически
        try:
            file_path = os.path.abspath("browser_extension_test.html")
            webbrowser.open(f"file://{file_path}")
            print("🚀 Тестовая страница открыта в браузере")
        except:
            print("⚠️ Не удалось автоматически открыть. Откройте browser_extension_test.html вручную")
    
    print()
    print("=== ИТОГОВЫЕ РЕКОМЕНДАЦИИ ===")
    print("1. 🔒 Режим инкогнито - решает 95% проблем с расширениями")
    print("2. 🔧 Отключите криптокошельки (MetaMask, Trust Wallet)")
    print("3. 🛡️ Отключите блокировщики рекламы (AdBlock, uBlock)")
    print("4. 🌐 Попробуйте Firefox вместо Chrome")
    print("5. ⚙️ Запустите: python fix_http2_streamlit.py")
    print()
    print("📞 Если проблема остается - используйте созданную тестовую страницу")

if __name__ == "__main__":
    main()