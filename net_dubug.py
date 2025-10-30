import os
import time
import torch
import requests
from transformers import GPT2LMHeadModel, GPT2Tokenizer

# ========== НАСТРОЙКИ ОКРУЖЕНИЯ ==========
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["TRANSFORMERS_VERBOSITY"] = "error" 
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"  # Отключаем ускоренную загрузку

print("🚀 ТЕСТОВЫЙ СТЕНД - ЗАГРУЗКА МОДЕЛИ С УВЕЛИЧЕННЫМИ ТАЙМАУТАМИ")
print("=" * 60)

# ========== ДИАГНОСТИКА СИСТЕМЫ ==========
def system_diagnostics():
    print("📊 ДИАГНОСТИКА СИСТЕМЫ:")
    try:
        import shutil
        import psutil
        
        # Диск
        disk_free = shutil.disk_usage('/').free / 1024**3
        print(f"   💾 Свободно места на диске: {disk_free:.1f} GB")
        
        # Память
        mem = psutil.virtual_memory()
        print(f"   🧠 Доступно памяти: {mem.available / 1024**3:.1f} GB ({mem.percent}% используется)")
        
        # Сеть
        print(f"   🌐 Проверяем доступ к HuggingFace...")
        response = requests.get("https://huggingface.co", timeout=10)
        print(f"   ✅ HuggingFace доступен (статус: {response.status_code})")
        
    except Exception as e:
        print(f"   ⚠️ Ошибка диагностики: {e}")

system_diagnostics()
print("-" * 40)

# ========== КАСТОМНЫЕ ТАЙМАУТЫ ==========
print("⏱️  НАСТРАИВАЕМ ТАЙМАУТЫ...")

from transformers.utils.hub import http_get

original_http_get = http_get

def custom_http_get(url, temp_file, proxies=None, resume_size=0, headers=None, timeout=180):
    """Увеличенный таймаут для больших файлов"""
    print(f"   📥 Загружаем: {url.split('/')[-1]}")
    start_time = time.time()
    
    try:
        result = original_http_get(
            url, temp_file, 
            proxies=proxies, 
            resume_size=resume_size, 
            headers=headers, 
            timeout=timeout
        )
        download_time = time.time() - start_time
        print(f"   ✅ Файл загружен за {download_time:.1f}сек")
        return result
    except Exception as e:
        download_time = time.time() - start_time
        print(f"   ❌ Ошибка загрузки через {download_time:.1f}сек: {e}")
        raise

# Применяем кастомный http_get
import transformers.modeling_utils
import transformers.tokenization_utils_base
transformers.modeling_utils.http_get = custom_http_get
transformers.tokenization_utils_base.http_get = custom_http_get

print("✅ Таймауты настроены (180 секунд)")
print("-" * 40)

# ========== ТЕСТ ЗАГРУЗКИ ==========
def test_model_loading():
    print("🧪 ТЕСТ ЗАГРУЗКИ МОДЕЛИ:")
    
    # 1. Токенизатор
    print("1. Загружаем токенизатор...")
    tokenizer_start = time.time()
    try:
        tokenizer = GPT2Tokenizer.from_pretrained(
            "sberbank-ai/rugpt3small_based_on_gpt2",
            local_files_only=False
        )
        tokenizer.pad_token = tokenizer.eos_token
        tokenizer_time = time.time() - tokenizer_start
        print(f"   ✅ Токенизатор загружен за {tokenizer_time:.1f}сек")
    except Exception as e:
        print(f"   ❌ Ошибка загрузки токенизатора: {e}")
        return False, None, None

    # 2. Модель
    print("2. Загружаем модель (~500MB)...")
    model_start = time.time()
    try:
        model = GPT2LMHeadModel.from_pretrained(
            "sberbank-ai/rugpt3small_based_on_gpt2",
            torch_dtype=torch.float32,
            low_cpu_mem_usage=True,
            force_download=True,      # Принудительно перезагружаем
            resume_download=False,    # Запрещаем докачку
            local_files_only=False
        )
        model.eval()
        model_time = time.time() - model_start
        print(f"   ✅ Модель загружена за {model_time:.1f}сек")
    except Exception as e:
        print(f"   ❌ Ошибка загрузки модели: {e}")
        return False, None, None

    return True, tokenizer, model

# ========== ТЕСТ ГЕНЕРАЦИИ ==========
def test_generation(tokenizer, model):
    print("3. Тестируем генерацию...")
    
    test_queries = [
        "Привет",
        "Как дела?",
        "Что такое искусственный интеллект?"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"   {i}. Запрос: '{query}'")
        try:
            inputs = tokenizer.encode(query, return_tensors="pt")
            
            with torch.no_grad():
                outputs = model.generate(
                    inputs,
                    max_new_tokens=20,
                    do_sample=True,
                    temperature=0.7,
                    pad_token_id=tokenizer.eos_token_id
                )
            
            response = tokenizer.decode(outputs[0], skip_special_tokens=True)
            clean_response = response.replace(query, "").strip()
            print(f"      Ответ: '{clean_response}'")
            
        except Exception as e:
            print(f"      ❌ Ошибка генерации: {e}")
            return False
    
    return True

# ========== ЗАПУСК ТЕСТА ==========
if __name__ == "__main__":
    print("🎯 ЗАПУСКАЕМ ТЕСТ...")
    print("⚠️  Если зависнет - ждём до 3 минут на загрузку модели")
    print("=" * 60)
    
    total_start = time.time()
    
    # Загружаем модель
    success, tokenizer, model = test_model_loading()
    
    if success and tokenizer and model:
        # Тестируем генерацию
        gen_success = test_generation(tokenizer, model)
        
        total_time = time.time() - total_start
        
        if gen_success:
            print("=" * 60)
            print(f"🎉 ТЕСТ ПРОЙДЕН УСПЕШНО!")
            print(f"⏱️  Общее время: {total_time:.1f} секунд")
            print("✅ Модель готова к использованию!")
        else:
            print("=" * 60)
            print("⚠️  Модель загрузилась, но есть проблемы с генерацией")
    else:
        print("=" * 60)
        print("💥 ТЕСТ ПРОВАЛЕН!")
        print("❌ Не удалось загрузить модель")
        
    print("=" * 60)