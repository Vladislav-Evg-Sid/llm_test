from fastapi import APIRouter, Depends

from qdrant_app.schemas.qdrant import QdrantAddReportResponse, QdrantReportSectionData
from qdrant_app.storage.qdrant_manager import QdrantReportsStorage, get_qdrant_report_service

router = APIRouter(
    prefix="/vect_qdrant",
    tags=["vect_qdrant"]
)

# Взаимодействие с qdrant
@router.post("/add", response_model=QdrantAddReportResponse)
async def qdrant_set_data(data: QdrantReportSectionData, qd_manager: QdrantReportsStorage = Depends(get_qdrant_report_service)) -> QdrantAddReportResponse:
    """Добавление отчёта в векторную БД"""
    return await qd_manager.add_report(data)
