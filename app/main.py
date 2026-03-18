from fastapi import FastAPI

from app.api import qdrant, text_reports


app = FastAPI(title="Heavy Class Demo")

app.include_router(qdrant.router)
app.include_router(text_reports.router)
