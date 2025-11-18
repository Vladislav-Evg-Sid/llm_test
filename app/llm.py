from transformers import pipeline
import logging

logging.getLogger("transformers").setLevel(logging.ERROR)

class LLMReportGenerator:
    _instance = None
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, model_name="microsoft/DialoGPT-small"):
        if LLMReportGenerator._initialized:
            return
            
        print("⏳ Загрузка легкой модели...")
        
        # Используем готовый pipeline - он проще и быстрее
        self.pipe = pipeline(
            "text-generation",
            model=model_name,
            device="cpu"
        )
        
        print("✅ Модель успешно загружена!")
        LLMReportGenerator._initialized = True
    
    def generate_response(self, user_input):
        try:
            # Простая генерация
            result = self.pipe(
                user_input,
                max_new_tokens=50,
                do_sample=True,
                temperature=0.7
            )
            return result[0]['generated_text']
        except Exception as e:
            return f"Ответ: {user_input} (режим эхо)"