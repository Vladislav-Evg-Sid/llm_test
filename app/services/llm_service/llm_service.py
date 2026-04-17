from os import getenv
import time
import requests
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.text_reports import LLMResponse, LLMRequest
from app.services.llm_service import promt as promtService


LLAMA_BASE_URL = getenv("LLAMA_BASE_URL", "http://llama-cpp:8011").rstrip("/")
LLAMA_MODEL_ALIAS = getenv("LLAMA_MODEL_ALIAS", "local-gguf")
LLAMA_GENERATION_TEMPERATURE = float(getenv("LLAMA_GENERATION_TEMPERATURE", "0"))
LLAMA_GENERATION_MAX_TOKENS = int(getenv("LLAMA_GENERATION_MAX_TOKENS", "1024"))
LLAMA_REQUEST_TIMEOUT = float(getenv("LLAMA_REQUEST_TIMEOUT", "600"))
LLAMA_GENERATION_SEED = int(getenv("LLAMA_GENERATION_SEED", "42"))
LLAMA_GENERATION_TOP_K = int(getenv("LLAMA_GENERATION_TOP_K", "1"))
LLAMA_GENERATION_TOP_P = float(getenv("LLAMA_GENERATION_TOP_P", "1.0"))
LLAMA_GENERATION_MIN_P = float(getenv("LLAMA_GENERATION_MIN_P", "0.0"))


def generate_with_llama(prompt: str) -> tuple[str, float]:
    started_at = time.perf_counter()
    response = requests.post(
        f"{LLAMA_BASE_URL}/v1/chat/completions",
        json={
            "model": LLAMA_MODEL_ALIAS,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "temperature": LLAMA_GENERATION_TEMPERATURE,
            "max_tokens": LLAMA_GENERATION_MAX_TOKENS,
            "seed": LLAMA_GENERATION_SEED,
            "top_k": LLAMA_GENERATION_TOP_K,
            "top_p": LLAMA_GENERATION_TOP_P,
            "min_p": LLAMA_GENERATION_MIN_P,
            "stream": False,
        },
        timeout=LLAMA_REQUEST_TIMEOUT,
    )
    response.raise_for_status()

    response_data = response.json()
    choices = response_data.get("choices", [])
    text = ""
    if choices:
        text = choices[0].get("message", {}).get("content", "") or ""

    return text.replace(prompt, "").strip(), round(time.perf_counter() - started_at, 3)


async def get_generated_text_on_subject_by_section(
    session: AsyncSession, request: LLMRequest, section_code: str
) -> LLMResponse:
    data = await promtService.get_report_generate_data(
        session=session, request=request, section_code=section_code
    )

    with open("promt.txt", "w") as f:
        f.write(data.promt)

    result = LLMResponse()
    try:
        llm_text, result.time = generate_with_llama(data.promt)
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

    with open("result.txt", "w") as f:
        f.write(result.text)
    return result


async def get_text_by_request(request: str) -> LLMResponse:
    result = LLMResponse()
    try:
        result.text, result.time = generate_with_llama(request)
    except Exception as e:
        result.text = f"Ошибка генерации: {str(e)}"
    return result
