from pydantic import BaseModel


class QdrantAddReportResponse(BaseModel):
    success: bool = True
    id: str = ""
    messange: str = ""

class QdrantReportSectionData(BaseModel):
    code: str
    name: str
    text: str

class QdrantReportData(BaseModel):
    year: int
    title: str
    subject: int 
    exam_type: int
    sections: list[QdrantReportSectionData]
