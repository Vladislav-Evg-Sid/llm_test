from pydantic import BaseModel


class LLMGenerateResponse(BaseModel):
    success: bool
    text: str
    time: float = 0

class LLMGenerateRequest(BaseModel):
    prompt: str