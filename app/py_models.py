from pydantic import BaseModel


class LLLMResponse(BaseModel):
    text: str = ""