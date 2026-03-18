import requests
from os import getenv

from app.schemas.qdrant import (
    QdrantAddReportResponse,
    QdrantReportSectionData,
    QdrantAllReportsResponse,
    QdrantDeleteReportResponse,
    QdrantReportSectionsComparisonResponce,
    QdrantReportDataResponce,
)
from app.storage.qdrant.qdrant_manager import QdrantReportsStorage


class QdrantReportsService:
    def __init__(self):
        self.storage = QdrantReportsStorage()
        self.vectoriser_port = getenv('VECT_QD_PORT', None)

    async def add_report(self, data: QdrantReportSectionData) -> QdrantAddReportResponse:
        """Добавление отчёта в векторную БД"""
        if self.vectoriser_port is None:
            return QdrantAddReportResponse(
                success=False,
                messange="Vectoriser service is unavailable"
            )
        return requests.get(f'http://vectoriser:{self.vectoriser_port}/data')

    async def get_all_reports(self) -> QdrantAllReportsResponse:
        """Получение списка всех отчётов"""
        return self.storage.get_all_reports()

    async def get_report_by_id(self, report_id: str) -> QdrantReportDataResponce:
        """Получение полных данных отчёта по ID"""
        return self.storage.get_report(report_id)

    async def delete_report(self, report_id: str) -> QdrantDeleteReportResponse:
        """Удаление отчёта по ID"""
        return self.storage.delete_report(report_id)

    async def get_distance(self, report1_id: str, report2_id: str, section_code: str) -> QdrantReportSectionsComparisonResponce:
        """Получение векторного расстояния между разделами отчётов"""
        return self.storage.compare_single_section_pair(report1_id, report2_id, section_code)


async def get_qdrant_report_service():
    yield QdrantReportsService()