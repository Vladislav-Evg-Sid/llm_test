import os
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"  # Отключаем ускоренную загрузку

from transformers import GPT2LMHeadModel, GPT2Tokenizer
import torch
import requests
import time

print("⚡ Загрузка с увеличенными таймаутами...")

# Увеличиваем таймауты для больших файлов
from transformers.utils.hub import http_get

def custom_http_get(url, temp_file, proxies=None, resume_size=0, headers=None, timeout=180):
    return http_get(url, temp_file, proxies=proxies, resume_size=resume_size, headers=headers, timeout=timeout)

# Монkey-patch для увеличения таймаута
import transformers.modeling_utils
transformers.modeling_utils.http_get = custom_http_get

class LlamaChatbot:
    def __init__(self, name="sberbank-ai/rugpt3small_based_on_gpt2"):
        print("📥 Загружаем токенизатор...")
        self.tokenizer = GPT2Tokenizer.from_pretrained(name)
        self.tokenizer.pad_token = self.tokenizer.eos_token
        print("✅ Токенизатор готов")
        
        print("📥 Загружаем модель (это может занять 2-3 минуты)...")
        start_time = time.time()
        
        self.model = GPT2LMHeadModel.from_pretrained(
            name,
            torch_dtype=torch.float32,
            low_cpu_mem_usage=True,  # Важно для больших файлов!
            force_download=True,     # Принудительно перезагружаем
            resume_download=False    # Запрещаем докачку
        )
        self.model.eval()
        
        print(f"✅ Модель загружена за {time.time()-start_time:.1f}сек")