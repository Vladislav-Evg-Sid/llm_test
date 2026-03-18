from huggingface_hub import snapshot_download
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from time import time as time_now
from pathlib import Path

from llm_app.schemas.llm import LLMGenerateResponce


def check_folder(folder_path: str) -> bool:
    """Проверяет наличие папки и то, что она не пуста

    Args:
        path (str): Путь к папке

    Returns:
        bool: Вердикт
    """
    path = Path(folder_path)
    if not path.exists():
        return False
    
    if not path.is_dir():
        return False
    
    try:
        next(path.iterdir())
        return True
    except:
        return False


class LLMService:
    _instance = None
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, model_name="Qwen/Qwen3-4B"):
        if LLMService._initialized:
            return
            
        print(f"⏳ Загружаем модель {model_name}...")
        print("📥 Это может занять несколько минут...")
        path_to_model = "app/models_ml/"
        if not check_folder(path_to_model + model_name.replace('/', '_')):
            # Скачиваем модель через mirror, если нет локальной папки
            local_dir = snapshot_download(
                repo_id=model_name,
                local_dir=path_to_model + model_name.replace('/', '_'),
                # endpoint="https://hf-mirror.com"
            )
        else:
            print("Модель уже скачана, загружаем из локальной папки")
            local_dir = path_to_model + model_name.replace('/', '_')
        
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
            device_map="cpu",
            low_cpu_mem_usage=True,
            trust_remote_code=True
        )
        
        # Переводим в режим инференса
        self.model.eval()
        
        self.history = []
        print("✅ Модель успешно загружена и готова к работе!")
        LLMService._initialized = True
    
    def generate_response(self, promt) -> LLMGenerateResponce:
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
            
            return LLMGenerateResponce(
                success=True,
                text=response,
                time=end_time-start_time
            )
            
        except Exception as e:
            return LLMGenerateResponce(
                success=False,
                text=f"⚠️ Ошибка при генерации: {str(e)}",
                time=0
            )


def get_llm_service():
    yield LLMService()