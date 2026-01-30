from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
import os

from app.schemas.text_reports import LLMResponse, LLMRequest
from app.services.llm_service import promt as promtService

if os.getenv('CURRENT_DEVICE') == "server":
    from app.services.llm_service.llm import LLMService
else:
    from app.services.llm_service.llm_plug import LLMService

async def get_generated_text_on_subject_by_section(session: AsyncSession, request: LLMRequest, section_code: str) -> LLMResponse:
    data = await promtService.get_report_generate_data(session=session, request=request, section_code=section_code)
    
    with open ('promt.txt', 'w') as f:
        f.write(data.promt)
    
    # Генерируем ответ
    result = LLMResponse()
    try:
        # Используем синглтон - всегда получаем тот же экземпляр
        llm = LLMService()
        
        # Запускаем генерацию в отдельном потоке
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: llm.generate_response(data.promt)
        )
        llm_text = response.text
        result.time = response.time
    except Exception as e:
        result.text = f"Ошибка генерации: {str(e)}"
        llm_text = ""
    
    for part in data.template:
        if result.text != "":
            result.text += "\n"
        if "obligatury_text-" in part:
            result.text += data.obligatury_text[int(part.replace("obligatury_text-", ""))]
        elif part == "llm_text":
            result.text += llm_text
    
    with open ('result.txt', 'w') as f:
        f.write(result.text)
    return result