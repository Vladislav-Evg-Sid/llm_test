from pydantic import BaseModel


# Для LLM
class LLMResponse(BaseModel):
    text: str = ""

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
class Table_1_1(BaseModel):
    years: list[int] = []
    counts: list[int] = []
    procents: list[float] = []

class Table_1_2(BaseModel):
    category: list[str] = []
    col_1: list[tuple[int, int, float]] = []
    col_2: list[tuple[int, int, float]] = []
    col_3: list[tuple[int, int, float]] = []

class Table_1_5(BaseModel):
    areas: list[str] = []
    counts: list[int] = []
    procents: list[float] = []