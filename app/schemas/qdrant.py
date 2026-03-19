from pydantic import BaseModel

class QdrantCollectionResponse(BaseModel):
    success: bool = True
    messange: str = ""

class QdrantAddReport(BaseModel):
    year: int
    title: str
    super_subject_id: int 
    exam_type: str

class QdrantReportSection(BaseModel):
    code: str
    name: str
    text: str | list[str]

class QdrantAddReportResponse(BaseModel):
    success: bool = True
    id: str = ""
    messange: str = ""

class QdrantTitleReport(BaseModel):
    id: str
    title: str

class QdrantAllReportsResponse(BaseModel):
    reports: list[QdrantTitleReport]

class QdrantDeleteReportRequest(BaseModel):
    report_id: str

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
    text: str | list[str]
    vector: list[float]

class QdrantReportDataResponse(BaseModel):
    id: str = "x-x-x-x-x"
    sections: list[QdrantReportSectionResponse] = list()
    vector: list[float] = list()

class QdrantReportData(BaseModel):
    year: int
    title: str
    super_subject_id: int 
    exam_type: str
    sections: list[QdrantReportSection]