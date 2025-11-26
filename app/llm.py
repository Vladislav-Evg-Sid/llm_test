from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
import torch


class LLMReportGenerator:
    _instance = None
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, model_name="Vikhrmodels/Vikhr-YandexGPT-5-Lite-8B-it_MLX-8bit"):
        if LLMReportGenerator._initialized:
            return
            
        print(f"⏳ Загружаем модель {model_name}...")
        print("📥 Это может занять несколько минут...")
        
        try:
            # Загружаем токенизатор
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                trust_remote_code=True
            )
            
            # Устанавливаем pad_token если его нет
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # Загружаем модель с оптимизациями для больших моделей
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float16,  # Используем float16 для экономии памяти
                device_map="cpu",
                low_cpu_mem_usage=True,
                trust_remote_code=True,
                load_in_8bit=True,          # 8-битная загрузка для экономии памяти
            )
            
            # Переводим в режим инференса
            self.model.eval()
            
            # Создаём пайплайн для упрощённой работы
            self.pipe = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                torch_dtype=torch.float16,
                device_map="cpu"
            )
            
            self.history = []
            print("✅ Модель успешно загружена и готова к работе!")
            LLMReportGenerator._initialized = True
            
        except Exception as e:
            print(f"❌ Ошибка при загрузке модели: {str(e)}")
            # Сбрасываем флаг инициализации при ошибке
            LLMReportGenerator._initialized = False
            raise
    
    def generate_response(self, user_input):
        try:
            # Формируем промт в формате, подходящем для модели
            if self.history:
                conversation = "\n".join([f"{'User' if i % 2 == 0 else 'Assistant'}: {msg['content']}" 
                                        for i, msg in enumerate(self.history[-4:])])
                prompt = f"{conversation}\nUser: {user_input}\nAssistant:"
            else:
                prompt = f"User: {user_input}\nAssistant:"
            
            # Генерируем ответ с настройками для русскоязычной модели
            outputs = self.pipe(
                prompt,
                max_new_tokens=256,        # Увеличим немного для более полных ответов
                do_sample=True,
                temperature=0.7,
                top_p=0.9,
                top_k=50,                  # Добавляем top_k для лучшего контроля
                repetition_penalty=1.1,
                pad_token_id=self.tokenizer.eos_token_id,
                num_return_sequences=1,
                eos_token_id=self.tokenizer.eos_token_id,
            )
            
            # Извлекаем ответ
            full_text = outputs[0]['generated_text']
            response = full_text.replace(prompt, "").strip()
            
            # Очищаем ответ от лишнего
            if "\nUser:" in response:
                response = response.split("\nUser:")[0]
            if "<|endoftext|>" in response:
                response = response.split("<|endoftext|>")[0]
            
            # Обновляем историю
            self.history.append({"role": "user", "content": user_input})
            self.history.append({"role": "assistant", "content": response})
            
            # Ограничиваем историю
            if len(self.history) > 10:
                self.history = self.history[-10:]
                
            return response
            
        except Exception as e:
            return f"⚠️ Ошибка при генерации: {str(e)}"
    
    def clear_history(self):
        """Очищает историю диалога"""
        self.history = []