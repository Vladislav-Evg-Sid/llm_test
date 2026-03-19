from sqlalchemy.ext.asyncio import AsyncSession
from os import getenv
import requests

from app.schemas.text_reports import LLMResponse, LLMRequest, LLMGenerateRequest, LLMGenerateResponse
from app.services.llm_service import promt as promtService


LLM_PORT = getenv('LLM_PORT', None)

async def get_generated_text_on_subject_by_section(session: AsyncSession, request: LLMRequest, section_code: str) -> LLMResponse:
    data = await promtService.get_report_generate_data(session=session, request=request, section_code=section_code)
    
    with open ('promt.txt', 'w') as f:
        f.write(data.promt)
    
    # Генерируем ответ
    result = LLMResponse()
    try:
        # Запускаем генерацию в отдельном потоке
        response = requests.post(
            f'http://llm:{LLM_PORT}/text_generate/generate',
            json=LLMGenerateRequest(
                prompt=data.promt
            )
        )
        if response.ok:
            response_data = LLMGenerateResponse(**response.json())
            if response_data.success:
                llm_text = response_data.text
                result.time = response_data.time
            else:
                return LLMResponse(
                    text="Ошибка при общании к llm: " + response_data.text
                )
        else:
            return LLMResponse(
                text="Ошибка обращения к сервису LLM: " + response.status_code
            )
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