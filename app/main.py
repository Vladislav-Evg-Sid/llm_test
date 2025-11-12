from fastapi import FastAPI

from llm_plug import LLMReportGenerator
from py_models import LLLMResponse

# Создаем экземпляр FastAPI
app = FastAPI(title="Heavy Class Demo")


@app.on_event("startup")
async def startup_event():
    """Инициализируем LlamaChatbot при запуске приложения"""
    print("🔄 Запуск приложения...")
    # Просто получаем экземпляр - он автоматически инициализируется
    heavy_instance = LLMReportGenerator()
    print("✅ Приложение готово к работе")


@app.post("/generate_text")
async def generate_endpoint(user_request: str):
    llm = LLMReportGenerator()
    result = LLLMResponse()
    try:
        result.text = llm.generate_response(user_request)
    except:
        result.text = "Ошибка генерации"
    return result
