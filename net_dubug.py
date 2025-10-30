import os
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"

from transformers import GPT2LMHeadModel, GPT2Tokenizer
import torch
import requests
import time

print("🚀 ЗАПУСК УПРОЩЁННОЙ ВЕРСИИ БЕЗ ACCELERATE")
print("=" * 50)

class SimpleChatbot:
    _instance = None

    def __init__(self, name="sberbank-ai/rugpt3small_based_on_gpt2"):
        if SimpleChatbot._instance is not None:
            return
            
        print("⚡ Инициализация модели...")
        start_time = time.time()
        
        try:
            # 1. Токенизатор (быстро)
            print("📥 Загружаем токенизатор...")
            self.tokenizer = GPT2Tokenizer.from_pretrained(name)
            self.tokenizer.pad_token = self.tokenizer.eos_token
            print("✅ Токенизатор загружен")
            
            # 2. Модель (БЕЗ любых оптимизаций)
            print("📥 Загружаем модель (может занять 2-5 минут)...")
            
            # ВАРИАНТ А: Простая загрузка
            self.model = GPT2LMHeadModel.from_pretrained(
                name,
                torch_dtype=torch.float32
                # НИКАКИХ low_cpu_mem_usage, device_map и т.д.
            )
            
            self.model.eval()
            
            load_time = time.time() - start_time
            print(f"✅ Модель загружена за {load_time:.1f} секунд")
            print("🎉 Модель готова к работе!")
            
            SimpleChatbot._instance = self
            
        except Exception as e:
            print(f"💥 Критическая ошибка: {e}")
            raise

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = SimpleChatbot()
        return cls._instance
    
    def generate_response(self, user_input):
        print(f"🔧 Генерация ответа для: '{user_input}'")
        
        try:
            inputs = self.tokenizer.encode(user_input, return_tensors="pt")
            
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs,
                    max_new_tokens=50,  # Уменьшил для скорости
                    do_sample=True,
                    temperature=0.7,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            clean_response = response.replace(user_input, "").strip()
            
            print(f"📝 Ответ: '{clean_response}'")
            return clean_response
            
        except Exception as e:
            return f"Ошибка генерации: {e}"

# ========== ТЕСТОВЫЙ СТЕНД ==========
if __name__ == "__main__":
    print("🧪 ТЕСТИРУЕМ РАБОТОСПОСОБНОСТЬ...")
    print("⏰ Ожидайте 2-5 минут для загрузки модели")
    print("-" * 40)
    
    try:
        # Тест 1: Создаем экземпляр
        bot = SimpleChatbot.get_instance()
        
        # Тест 2: Быстрая генерация
        test_text = "Привет, как дела?"
        print(f"\n📋 Тестовый запрос: '{test_text}'")
        
        response = bot.generate_response(test_text)
        print(f"✅ ТЕСТ ПРОЙДЕН! Ответ: '{response}'")
        
    except Exception as e:
        print(f"❌ ТЕСТ ПРОВАЛЕН: {e}")
        
    print("=" * 50)