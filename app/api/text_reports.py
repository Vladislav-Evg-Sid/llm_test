from fastapi import APIRouter, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import io

from app.schemas.text_reports import TableStandart, LLMResponse, LLMRequest
from app.db.connect_db import get_async_session
from app.services.table_rep_manager import table_rep_manager as tableRepManager
from app.services.llm_service import llm_service as llmService
from app.services.report_to_file import get_file_by_data as getFileByData


router = APIRouter(
    prefix="/textreports",
    tags=["textreports"]
)


# Запросы в БД !!!ТЕСТОВОЕ!!!
@router.post("/db/test/query/all")
async def test_querry(section_num: int, table_num: int, exam_year: int = 2025, exam_type_id: int = 4, subject_id: int = 2, session: AsyncSession = Depends(get_async_session)) -> TableStandart:
    return await tableRepManager.get_table_by_section(session, section_num, table_num, year=exam_year, exam_type_id=exam_type_id, subject_id=subject_id)

# Формирование первого раздела
@router.post("/report/generate/section")
async def generate_sections(request: LLMRequest, section_code: str = "1.7.", session: AsyncSession = Depends(get_async_session)) -> LLMResponse:
    return await llmService.get_generated_text_on_subject_by_section(session, request, section_code)

@router.post("/file")
async def get_file(section_num: int, exam_year: int = 2025, exam_type_id: int = 4, subject_id: int = 2, session: AsyncSession = Depends(get_async_session), background_tasks: BackgroundTasks = BackgroundTasks()):
    buffer = io.BytesIO()
    response_file = await getFileByData.get_docx_file(session, section_num, exam_year=exam_year, exam_type_id=exam_type_id, subject_id=subject_id)
    response_file.save(buffer)
    buffer.seek(0)
    background_tasks.add_task(cleanup_buffer, buffer)
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": "attachment; filename=report.docx"}
    )

def cleanup_buffer(buffer: io.BytesIO):
    try:
        buffer.close()
    except Exception as e:
        print(f"Error cleaning buffer: {e}")

@router.post("/generate")
async def generate_text(request: str) -> LLMResponse:
    return await llmService.get_text_by_reques(request)

@router.get("/generate/all-data")
async def generate_all_data() -> list[LLMResponse]:
    return await llmService.get_all_data_by_section()