from pydantic import BaseModel


class LLMGenerateResponce(BaseModel):
    success: bool
    text: str
    time: float = 0

class LLMGenerateRequest(BaseModel):
    prompt: str