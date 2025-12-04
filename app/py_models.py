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
class TableCNP(BaseModel):
    category: list[int] = []
    counts: list[int] = []
    procents: list[float] = []

class Table3PairCols(BaseModel):
    category: list[str] = []
    col_1: list[tuple[int, int, float]] = []
    col_2: list[tuple[int, int, float]] = []
    col_3: list[tuple[int, int, float]] = []

class Table3Cols(BaseModel):
    category: list[str] = []
    col_1: list[tuple[int, float]] = []
    col_2: list[tuple[int, float]] = []
    col_3: list[tuple[int, float]] = []

class TableDictribution(BaseModel):
    data: list[int] = []
    count: list[int] = []

class TableStandart(BaseModel):
    column_names: list[str] = []
    str_names: list[str] = []
    data: list[list[int | float]] = []