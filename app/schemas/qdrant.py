from pydantic import BaseModel

class QdrantCollectionResponse(BaseModel):
    success: bool = True
    messange: str = ""

class QdrantReportSection(BaseModel):
    code: str
    name: str
    text: str

class QdrantAddReportResponse(BaseModel):
    success: bool = True
    id: str = ""
    messange: str = ""

class QdrantTitleReport(BaseModel):
    id: str
    title: str

class QdrantDeleteReportResponse(BaseModel):
    success: bool = True
    message: str = ""

class QdrantReportSectionsComparisonResponse(BaseModel):
    success: bool = True
    messange: str = ""
    section_code: str = ""
    section_title: str = ""
    cosine_similarity: float = 0.0

class QdrantReportSectionResponse(BaseModel):
    code: str
    name: str
    text: str
    vector: list[float]

class QdrantReportDataResponse(BaseModel):
    id: str = "x-x-x-x-x"
    sections: list[QdrantReportSectionResponse] = list()
    vector: list[float] = list()

class QdrantReportData(BaseModel):
    year: int
    title: str
    subject: int 
    exam_type: int
    sections: list[QdrantReportSection]
