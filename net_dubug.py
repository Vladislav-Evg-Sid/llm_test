import requests
import os
import time

print("=== ДИАГНОСТИКА СЕТИ ===")

# 1. Проверяем переменные окружения
print("1. Проверяем переменные окружения...")
print(f"   HTTP_PROXY: {os.environ.get('HTTP_PROXY', 'не установлен')}")
print(f"   HTTPS_PROXY: {os.environ.get('HTTPS_PROXY', 'не установлен')}")

# 2. Проверяем доступ к интернету
print("2. Проверяем доступ к интернету...")
sites = [
    "https://huggingface.co",
    "https://google.com", 
    "https://github.com"
]

for site in sites:
    try:
        start = time.time()
        response = requests.get(site, timeout=10)
        delay = time.time() - start
        print(f"   ✅ {site} - {response.status_code} ({delay:.2f}сек)")
    except Exception as e:
        print(f"   ❌ {site} - {e}")

print("3. Проверяем загрузку маленького файла...")
try:
    # Пробуем скачать маленький конфиг
    url = "https://huggingface.co/sberbank-ai/rugpt3small_based_on_gpt2/raw/main/config.json"
    response = requests.get(url, timeout=30)
    print(f"   ✅ Конфиг загружен, размер: {len(response.text)} байт")
except Exception as e:
    print(f"   ❌ Ошибка загрузки: {e}")