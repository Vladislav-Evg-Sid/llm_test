from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os

from app.llm import LlamaChatbot

# Создаем экземпляр FastAPI
app = FastAPI(title="Heavy Class Demo")

# Настраиваем шаблоны
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "static"))

# Dependency для получения экземпляра LlamaChatbot
def get_llm_obj() -> LlamaChatbot:
    return LlamaChatbot.get_instance()

@app.on_event("startup")
async def startup_event():
    """Инициализируем LlamaChatbot при запуске приложения"""
    print("🔄 Запуск приложения...")
    # Просто получаем экземпляр - он автоматически инициализируется
    heavy_instance = LlamaChatbot.get_instance()
    print("✅ Приложение готово к работе")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Главная страница с кнопкой"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/generate")
async def generate_endpoint(llm: LlamaChatbot = Depends(get_llm_obj)):
    """Эндпоинт для генерации, использует общий экземпляр LlamaChatbot"""
    try:
        with open("app/text.txt", "r") as f:
            result = llm.generate_response(f.read())
        return {
            "status": "success",
            "data": result
        }
    except:
        return {
            "status": "failed",
            "data": "Нет файла"
        }
