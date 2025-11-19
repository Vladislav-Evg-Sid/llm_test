from pydantic import BaseModel


class LLMResponse(BaseModel):
    text: str = ""


class QdrantCollectionResponse(BaseModel):
    success: bool = True
    messange: str = ""


class QdrantReportSection(BaseModel):
    code: str
    text: str

class QdrantAddReportRequest(BaseModel):
    year: int
    super_subject_id: int 
    exam_type: str
    sections: list[QdrantReportSection]

class QdrantAddReportResponse(BaseModel):
    success: bool = True
    id: str = ""
    messange: str = ""


class QdrantCollection(BaseModel):
    id: str