from fastapi import APIRouter, HTTPException

from app.schemas.qdrant import QdrantAddReportResponse, QdrantAddReportRequest, QdrantAllReportsResponse, QdrantDeleteReportResponse, QdrantReportSectionsComparisonResponce
from app.services.qdrant_service import QdrantReportsService

router = APIRouter(
    prefix="/qdrant",
    tags=["qdrant"]
)

# Взаимодействие с qdrant
@router.post("/qdrant", response_model=QdrantAddReportResponse)
async def qdrant_set_data(data: QdrantAddReportRequest) -> QdrantAddReportResponse:
    """Добавление отчёта в векторную БД"""
    qd_manager = QdrantReportsService()
    result = await qd_manager.add_report(data)
    return result

@router.get("/qdrant/reports", response_model=QdrantAllReportsResponse)
async def get_all_reports() -> QdrantAllReportsResponse:
    """Получение списка всех отчётов"""
    qd_manager = QdrantReportsService()
    result = await qd_manager.get_all_reports()
    return result

@router.get("/qdrant/reports/{report_id}")
async def get_report_by_id(report_id: str):
    """Получение полных данных отчёта по ID"""
    qd_manager = QdrantReportsService()
    report = await qd_manager.get_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Отчёт не найден")
    return report

@router.delete("/qdrant/reports/{report_id}", response_model=QdrantDeleteReportResponse)
async def delete_report(report_id: str) -> QdrantDeleteReportResponse:
    """Удаление отчёта по ID"""
    qd_manager = QdrantReportsService()
    result = await qd_manager.delete_report(report_id)
    return result

@router.post("/qdrant/reports/distance")
async def get_distance(report1_id: str, report2_id: str, section_code: str) -> QdrantReportSectionsComparisonResponce:
    qd_manager = QdrantReportsService()
    result = await qd_manager.compare_single_section_pair(report1_id, report2_id, section_code)
    return result