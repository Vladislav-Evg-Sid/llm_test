from transformers import GPT2LMHeadModel, GPT2Tokenizer
import torch


class LlamaChatbot:
    _instance = None
    _initialized = False

    def __init__(self, name="sberbank-ai/rugpt3small_based_on_gpt2"):
        if LlamaChatbot._initialized:
            return
            
        print("⚡ Загрузка ультра-лёгкой модели...")
        
        self.tokenizer = GPT2Tokenizer.from_pretrained(name)
        self.tokenizer.pad_token = self.tokenizer.eos_token
        
        self.model = GPT2LMHeadModel.from_pretrained(
            name,
            torch_dtype=torch.float32
        )
        self.model.eval()
        
        LlamaChatbot._initialized = True
        print("✅ Ультра-лёгкая модель загружена!")

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = LlamaChatbot()
        return cls._instance
    
    def generate_response(self, user_input):
        inputs = self.tokenizer.encode(user_input, return_tensors="pt")
        
        with torch.no_grad():
            outputs = self.model.generate(
                inputs,
                max_new_tokens=100,
                do_sample=True,
                temperature=0.7,
                pad_token_id=self.tokenizer.eos_token_id
            )
        
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return response.replace(user_input, "").strip()


if __name__ == "__main__":
    print("🧪 Запуск тестового стенда для LlamaChatbot")
    print("=" * 50)
    
    # Тест 1: Проверка синглтона
    print("1. Тестируем синглтон...")
    bot1 = LlamaChatbot.get_instance()
    bot2 = LlamaChatbot.get_instance()
    
    print(f"   bot1 id: {id(bot1)}")
    print(f"   bot2 id: {id(bot2)}")
    print(f"   Это один и тот же объект: {bot1 is bot2}")
    
    print("\n" + "=" * 50)
    
    # Тест 2: Хардкодные тестовые запросы
    test_queries = [
        "Привет, как дела?",
        "Что такое искусственный интеллект?",
        "Напиши короткий рассказ про кота",
        "Сколько будет 2+2?",
        "Что ты умеешь?"
    ]
    
    print("2. Тестируем генерацию ответов:")
    print("-" * 30)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 Тест {i}:")
        print(f"👤 Вопрос: {query}")
        
        try:
            response = bot1.generate_response(query)
            print(f"🤖 Ответ: {response}")
        except Exception as e:
            print(f"❌ Ошибка: {e}")
        
        print("-" * 30)
    
    print("\n" + "=" * 50)
    
    # Тест 3: Интерактивный режим (опционально)
    print("3. Интерактивный режим (для выхода введите 'выход' или 'quit')")
    print("-" * 40)
    
    while True:
        user_input = input("\n👤 Ваш вопрос: ").strip()
        
        if user_input.lower() in ['выход', 'quit', 'exit', '']:
            print("👋 Завершение работы...")
            break
            
        if user_input:
            try:
                response = bot1.generate_response(user_input)
                print(f"🤖 Ответ: {response}")
            except Exception as e:
                print(f"❌ Ошибка при генерации: {e}")
        else:
            print("⚠️ Введите текст вопроса")
    
    print("✅ Тестирование завершено!")