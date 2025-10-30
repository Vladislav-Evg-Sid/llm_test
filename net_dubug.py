import os
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"

from transformers import GPT2LMHeadModel, GPT2Tokenizer
import torch
import time
import sys

print("=== ТЕСТ ЗАГРУЗКИ МОДЕЛИ ===")

def test_model_loading():
    print("1. Загружаем токенизатор...")
    sys.stdout.flush()
    
    start = time.time()
    try:
        tokenizer = GPT2Tokenizer.from_pretrained(
            "sberbank-ai/rugpt3small_based_on_gpt2",
            local_files_only=False  # Разрешаем скачивание
        )
        tokenizer.pad_token = tokenizer.eos_token
        print(f"   ✅ Токенизатор загружен за {time.time()-start:.1f}сек")
        sys.stdout.flush()
    except Exception as e:
        print(f"   ❌ Ошибка токенизатора: {e}")
        return False

    print("2. Загружаем модель...")
    sys.stdout.flush()
    
    start = time.time()
    try:
        model = GPT2LMHeadModel.from_pretrained(
            "sberbank-ai/rugpt3small_based_on_gpt2",
            torch_dtype=torch.float32,
            local_files_only=False
        )
        model.eval()
        print(f"   ✅ Модель загружена за {time.time()-start:.1f}сек")
        sys.stdout.flush()
    except Exception as e:
        print(f"   ❌ Ошибка модели: {e}")
        return False

    print("3. Тестируем генерацию...")
    sys.stdout.flush()
    
    try:
        inputs = tokenizer.encode("Привет", return_tensors="pt")
        with torch.no_grad():
            outputs = model.generate(inputs, max_new_tokens=10)
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        print(f"   ✅ Генерация работает: '{response}'")
        return True
    except Exception as e:
        print(f"   ❌ Ошибка генерации: {e}")
        return False

if __name__ == "__main__":
    success = test_model_loading()
    if success:
        print("\n🎉 ВСЁ РАБОТАЕТ! Проблема в твоём основном коде")
    else:
        print("\n💥 Проблема с загрузкой модели")