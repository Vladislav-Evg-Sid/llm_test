from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
import torch
import os
import logging

# Уменьшаем логирование
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)

class LLMReportGenerator:
    _instance = None
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, model_name="TinyLlama/TinyLlama-1.1B-Chat-v1.0"):
        if LLMReportGenerator._initialized:
            return
            
        print("⏳ Загрузка модели...")
        
        try:
            # Пробуем загрузить с локального кеша без скачивания
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                trust_remote_code=True,
                local_files_only=True  # Не скачивать новые файлы
            )
        except:
            print("⚠️ Модель не найдена в кеше. Начинаем скачивание...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                trust_remote_code=True
            )
        
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        try:
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float32,
                device_map="cpu",
                low_cpu_mem_usage=True,
                trust_remote_code=True,
                local_files_only=True  # Не скачивать новые файлы
            )
        except:
            print("⚠️ Загружаем модель...")
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float32,
                device_map="cpu", 
                low_cpu_mem_usage=True,
                trust_remote_code=True
            )
        
        self.model.eval()
        
        self.pipe = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
            torch_dtype=torch.float32,
            device="cpu"
        )
        
        self.history = []
        print("✅ Модель успешно загружена!")
        LLMReportGenerator._initialized = True
    
    def generate_response(self, user_input):
        # Упрощенная версия для теста
        return f"Тестовый ответ на: {user_input}"
    
        # try:
        #     # Формируем промт для чата
        #     if self.history:
        #         conversation = "\n".join([f"{'User' if i % 2 == 0 else 'Assistant'}: {msg['content']}" 
        #                                 for i, msg in enumerate(self.history[-4:])])  # Берём последние 4 сообщения
        #         prompt = f"{conversation}\nUser: {user_input}\nAssistant:"
        #     else:
        #         prompt = f"User: {user_input}\nAssistant:"
            
        #     # Генерируем ответ
        #     outputs = self.pipe(
        #         prompt,
        #         max_new_tokens=150,
        #         do_sample=True,
        #         temperature=0.7,
        #         top_p=0.9,
        #         repetition_penalty=1.1,
        #         pad_token_id=self.tokenizer.eos_token_id,
        #         num_return_sequences=1
        #     )
            
        #     # Извлекаем ответ
        #     full_text = outputs[0]['generated_text']
        #     response = full_text.replace(prompt, "").strip()
            
        #     # Очищаем ответ от лишнего
        #     if "\nUser:" in response:
        #         response = response.split("\nUser:")[0]
            
        #     # Обновляем историю
        #     self.history.append({"role": "user", "content": user_input})
        #     self.history.append({"role": "assistant", "content": response})
            
        #     # Ограничиваем историю
        #     if len(self.history) > 10:
        #         self.history = self.history[-10:]
                
        #     return response
            
        # except Exception as e:
        #     return f"⚠️ Ошибка при генерации: {str(e)}"