import os
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
import torch
import logging

logging.getLogger("transformers").setLevel(logging.ERROR)

class LLMReportGenerator:
    _instance = None
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, model_path="./models/tinyllama"):
        if LLMReportGenerator._initialized:
            return
            
        print(f"🔄 Загрузка модели из {model_path}...")
        
        try:
            # Загружаем из локальной директории
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_path,
                trust_remote_code=True,
                local_files_only=True
            )
            
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            self.model = AutoModelForCausalLM.from_pretrained(
                model_path,
                torch_dtype=torch.float32,
                device_map="cpu",
                low_cpu_mem_usage=True,
                trust_remote_code=True,
                local_files_only=True
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
            print("✅ Модель успешно загружена из локальной директории!")
            LLMReportGenerator._initialized = True
            
        except Exception as e:
            print(f"❌ Ошибка загрузки модели: {e}")
            self.pipe = None
    
    def generate_response(self, user_input):
        if self.pipe is None:
            return "Модель не загружена. Сначала скачайте модель в ./models/tinyllama/"
        
        try:
            prompt = f"### Instruction: Ответь на вопрос\n### Question: {user_input}\n### Answer:"
            
            outputs = self.pipe(
                prompt,
                max_new_tokens=100,
                do_sample=True,
                temperature=0.7,
                top_p=0.9,
                repetition_penalty=1.1,
                pad_token_id=self.tokenizer.eos_token_id,
                num_return_sequences=1
            )
            
            full_text = outputs[0]['generated_text']
            response = full_text.replace(prompt, "").strip()
            
            if "###" in response:
                response = response.split("###")[0].strip()
                
            return response
            
        except Exception as e:
            return f"Ошибка генерации: {str(e)}"