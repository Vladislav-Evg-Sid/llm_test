from pydantic import BaseModel


class QdrantAddReportResponse(BaseModel):
    success: bool = True
    id: str = ""
    messange: str = ""

class QdrantReportSectionData(BaseModel):
    code: str
    name: str
    text: str | list[str]

class QdrantReportData(BaseModel):
    year: int
    title: str
    super_subject_id: int 
    exam_type: str
    sections: list[QdrantReportSectionData]
