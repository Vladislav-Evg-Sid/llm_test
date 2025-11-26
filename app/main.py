from fastapi import FastAPI, HTTPException
from pathlib import Path
from dotenv import load_dotenv
import os

from py_models import LLLMResponse
import asyncio

env_path = Path(__file__).resolve().parents[0] / ".env"
load_dotenv(dotenv_path=env_path)

if os.getenv('CURRENT_DEVICE') == "server":
    from llm import LLMReportGenerator
else:
    from llm_plug import LLMReportGenerator

app = FastAPI(title="Heavy Class Demo")

@app.on_event("startup")
async def startup_event():
    """Инициализируем модель при запуске"""
    print("🔄 Запуск приложения...")
    
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        None, 
        lambda: LLMReportGenerator()
    )
    print("✅ Приложение готово к работе")

@app.post("/generate_text")
async def generate_endpoint(user_request: str):
    result = LLLMResponse()
    try:
        # Используем синглтон - всегда получаем тот же экземпляр
        llm = LLMReportGenerator()
        
        # Запускаем генерацию в отдельном потоке
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: llm.generate_response(user_request)
        )
        result.text = response
    except Exception as e:
        result.text = f"Ошибка генерации: {str(e)}"
    
    return result