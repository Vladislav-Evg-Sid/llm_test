from fastapi import FastAPI

from llm_plug import LlamaChatbot

# Создаем экземпляр FastAPI
app = FastAPI(title="Heavy Class Demo")


@app.on_event("startup")
async def startup_event():
    """Инициализируем LlamaChatbot при запуске приложения"""
    print("🔄 Запуск приложения...")
    # Просто получаем экземпляр - он автоматически инициализируется
    heavy_instance = LlamaChatbot()
    print("✅ Приложение готово к работе")


@app.post("/generate_text")
async def generate_endpoint(user_request: str):
    llm = LlamaChatbot()
    try:
        result = llm.generate_response(user_request)
        return {
            "status": "success",
            "data": result
        }
    except:
        return {
            "status": "failed",
            "data": "Нет файла"
        }
