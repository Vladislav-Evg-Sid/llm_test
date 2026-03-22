from fastapi import APIRouter, Depends

from llm_app.schemas.llm import LLMGenerateRequest, LLMGenerateResponse
from llm_app.services.llm import LLMService, get_llm_service

router = APIRouter(
    prefix="/text_generate",
    tags=["text_generate"]
)

@router.post("/generate", response_model=LLMGenerateResponse)
async def qdrant_set_data(data: LLMGenerateRequest, llm: LLMService = Depends(get_llm_service)) -> LLMGenerateResponse:
    """Добавление отчёта в векторную БД"""
    return llm.generate_response(data.prompt)
