from huggingface_hub import snapshot_download
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
import torch
from time import time as time_now


# os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'


class LLMReportGenerator:
    _instance = None
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, model_name="Qwen/Qwen3-4B"):
        if LLMReportGenerator._initialized:
            return
            
        print(f"⏳ Загружаем модель {model_name}...")
        print("📥 Это может занять несколько минут...")
        
        # Скачиваем модель через mirror
        local_dir = snapshot_download(
            repo_id=model_name,
            local_dir=f"./models/{model_name.replace('/', '_')}",
            endpoint="https://hf-mirror.com"
        )
        
        # Загружаем токенизатор из локальной директории
        self.tokenizer = AutoTokenizer.from_pretrained(
            local_dir,
            trust_remote_code=True
        )
        
        # Устанавливаем pad_token если его нет
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        # Загружаем модель БЕЗ device_map для CPU
        self.model = AutoModelForCausalLM.from_pretrained(
            local_dir,
            torch_dtype=torch.float32,
            device_map="cpu",  # Убираем эту строку
            low_cpu_mem_usage=True,
            trust_remote_code=True
        )
        
        # Явно перемещаем модель на CPU
        # self.model = self.model.to('cpu')
        
        # Переводим в режим инференса
        self.model.eval()
        
        self.history = []
        print("✅ Модель успешно загружена и готова к работе!")
        LLMReportGenerator._initialized = True
    
    def generate_response(self, promt):
        try:
            start_time = time_now()
            messages = [
                {"role": "user", "content": promt}
            ]
            
            text = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
                enable_thinking=False
            )
            
            model_inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)
            
            generated_ids = self.model.generate(
                **model_inputs,
                max_new_tokens=32768
            )
            output_ids = generated_ids[0][len(model_inputs.input_ids[0]):].tolist()
            response = self.tokenizer.decode(output_ids[:], skip_special_tokens=True).strip("\n")
            
            end_time = time_now()
            
            return {
                "response": response,
                "time": end_time - start_time
            }
            
        except Exception as e:
            return f"⚠️ Ошибка при генерации: {str(e)}"
    