from fastapi import APIRouter, HTTPException, Depends

from app.schemas.qdrant import QdrantAddReportResponse, QdrantAddReportRequest, QdrantAllReportsResponse, QdrantDeleteReportResponse, QdrantReportSectionsComparisonResponce
from app.services.qdrant_service.qdrant_service import QdrantReportsService, get_qdrant_report_service

router = APIRouter(
    prefix="/qdrant",
    tags=["qdrant"]
)

# Взаимодействие с qdrant
@router.post("/qdrant", response_model=QdrantAddReportResponse)
async def qdrant_set_data(data: QdrantAddReportRequest, qd_manager: QdrantReportsService = Depends(get_qdrant_report_service)) -> QdrantAddReportResponse:
    """Добавление отчёта в векторную БД"""
    return await qd_manager.add_report(data)


@router.get("/qdrant/reports", response_model=QdrantAllReportsResponse)
async def get_all_reports(qd_manager: QdrantReportsService = Depends(get_qdrant_report_service)) -> QdrantAllReportsResponse:
    """Получение списка всех отчётов"""
    return await qd_manager.get_all_reports()


@router.get("/qdrant/reports/{report_id}")
async def get_report_by_id(report_id: str, qd_manager: QdrantReportsService = Depends(get_qdrant_report_service)):
    """Получение полных данных отчёта по ID"""
    report = await qd_manager.get_report_by_id(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Отчёт не найден")
    return report


@router.delete("/qdrant/reports/{report_id}", response_model=QdrantDeleteReportResponse)
async def delete_report(report_id: str, qd_manager: QdrantReportsService = Depends(get_qdrant_report_service)) -> QdrantDeleteReportResponse:
    """Удаление отчёта по ID"""
    return await qd_manager.delete_report(report_id)


@router.post("/qdrant/reports/distance")
async def get_distance(report1_id: str, report2_id: str, section_code: str, qd_manager: QdrantReportsService = Depends(get_qdrant_report_service)) -> QdrantReportSectionsComparisonResponce:
    return await qd_manager.get_distance(report1_id, report2_id, section_code)
