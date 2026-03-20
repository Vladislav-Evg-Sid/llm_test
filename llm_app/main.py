from fastapi import FastAPI

from llm_app.api import llm_request
from llm_app.services.llm import LLMService

app = FastAPI(title="llm container")

app.include_router(llm_request.router)

@app.on_event("startup")
async def startup_event():
    """Инициализируем модель при запуске"""
    return LLMService()
