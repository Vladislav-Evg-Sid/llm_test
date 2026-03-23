from fastapi import FastAPI

from qdrant_app.api import add_report
from qdrant_app.storage.qdrant_manager import QdrantReportsStorage

app = FastAPI(title="vectoriser for qdrant")

app.include_router(add_report.router)

@app.on_event("startup")
async def startup_event():
    """Инициализируем модель при запуске"""
    temp = QdrantReportsStorage()
