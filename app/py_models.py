from pydantic import BaseModel


class LLMResponse(BaseModel):
    text: str = ""


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