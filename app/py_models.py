from pydantic import BaseModel


# Для LLM
class LLMResponse(BaseModel):
    text: str = ""
    time: int = 0

# Для Qdrant
class QdrantCollectionResponse(BaseModel):
    success: bool = True
    messange: str = ""

class QdrantReportSection(BaseModel):
    code: str
    text: str | list[str]

class QdrantAddReportRequest(BaseModel):
    year: int
    title: str
    super_subject_id: int 
    exam_type: str
    sections: list[QdrantReportSection]

class QdrantAddReportResponse(BaseModel):
    success: bool = True
    id: str = ""
    messange: str = ""

class QdrantReportTitle(BaseModel):
    id: str
    title: str

class QdrantAllReportsResponse(BaseModel):
    reports: list[QdrantReportTitle]

class QdrantDeleteReportRequest(BaseModel):
    report_id: str

class QdrantDeleteReportResponse(BaseModel):
    success: bool = True
    message: str = ""

# Для БД
class TableStandart(BaseModel):
    table_name: str = ""
    column_names: list[str] = []
    str_names: list[str] = []
    data: list[list[int | float]] = []