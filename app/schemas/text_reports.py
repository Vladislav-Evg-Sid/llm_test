from pydantic import BaseModel


class LLMRequest(BaseModel):
    subject: str = ""
    exam_type: str = ""
    year: int = 0
    user_input: str = ""


class LLMResponse(BaseModel):
    text: str = ""
    time: float = 0


class TableStandart(BaseModel):
    table_name: str = ""
    column_names: list[str] = []
    data: list[list[int | float | str]] = []


class GenerateData(BaseModel):
    promt: str = ""
    obligatury_text: list[str] = []
    template: list[str] = []


class LLMGenerateRequest(BaseModel):
    prompt: str


class LLMGenerateResponse(BaseModel):
    success: bool
    text: str
    time: float = 0
