"""
Проверка сырого содержимого sitemap
"""

import requests
import warnings

# Отключаем предупреждения SSL
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

def check_sitemap_raw():
    """Загружает и показывает содержимое sitemap"""
    
    sitemap_url = "https://gtrksakha.ru/sitemap2025.xml"
    
    print(f"[INFO] Загружаем sitemap: {sitemap_url}")
    
    try:
        response = requests.get(sitemap_url, timeout=10, verify=False)
        print(f"[INFO] Статус код: {response.status_code}")
        print(f"[INFO] Content-Type: {response.headers.get('content-type', 'Unknown')}")
        print(f"[INFO] Размер: {len(response.content)} байт")
        
        if response.status_code == 200:
            content = response.text
            
            # Показываем первые 1000 символов
            print("\n[CONTENT] Первые 1000 символов:")
            print("-" * 70)
            print(content[:1000])
            print("-" * 70)
            
            # Проверяем, является ли это sitemap index
            if "sitemapindex" in content:
                print("\n[INFO] Это sitemap INDEX файл!")
            elif "<urlset" in content:
                print("\n[INFO] Это обычный sitemap с URL")
            else:
                print("\n[WARNING] Неизвестный формат sitemap")
                
            # Считаем количество тегов
            loc_count = content.count("<loc>")
            url_count = content.count("<url>")
            sitemap_count = content.count("<sitemap>")
            
            print(f"\n[STATS] Найдено тегов:")
            print(f"   <loc>: {loc_count}")
            print(f"   <url>: {url_count}")
            print(f"   <sitemap>: {sitemap_count}")
            
        else:
            print(f"[ERROR] Не удалось загрузить sitemap")
            
    except Exception as e:
        print(f"[ERROR] Ошибка: {e}")

def check_alternative_sitemaps():
    """Проверяет альтернативные sitemap URL"""
    
    print("\n\n[INFO] Проверка альтернативных sitemap URL...")
    
    base_url = "https://gtrksakha.ru"
    sitemap_variants = [
        "/sitemap.xml",
        "/sitemap_index.xml",
        "/news-sitemap.xml",
        "/yandex-turbo-sitemap.xml",
        "/robots.txt"
    ]
    
    for variant in sitemap_variants:
        url = base_url + variant
        try:
            response = requests.get(url, timeout=5, verify=False)
            if response.status_code == 200:
                print(f"\n[OK] Найден: {url}")
                print(f"     Размер: {len(response.content)} байт")
                
                # Для robots.txt ищем ссылки на sitemap
                if "robots.txt" in url:
                    for line in response.text.split('\n'):
                        if 'sitemap:' in line.lower():
                            print(f"     Sitemap в robots.txt: {line.strip()}")
            else:
                print(f"[X] Не найден: {url} (статус {response.status_code})")
        except Exception as e:
            print(f"[ERROR] {url}: {e}")

def main():
    """Основная функция"""
    print("="*70)
    print("[АНАЛИЗ] Проверка содержимого sitemap")
    print("="*70)
    
    check_sitemap_raw()
    check_alternative_sitemaps()
    
    print("\n" + "="*70)
    print("[INFO] Анализ завершен")
    print("="*70)

if __name__ == "__main__":
    main()