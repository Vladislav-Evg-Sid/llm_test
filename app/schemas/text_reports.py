from pydantic import BaseModel


class LLMResponse(BaseModel):
    text: str = ""
    time: int = 0


class TableStandart(BaseModel):
    table_name: str = ""
    column_names: list[str] = []
    str_names: list[str] = []
    data: list[list[int | float]] = []


class GenerateData(BaseModel):
    promt: str = ""
    obligatury_text: list[str] = []
    template: list[str] = []