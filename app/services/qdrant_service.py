from app.schemas.qdrant import QdrantAddReportResponse, QdrantAddReportRequest, QdrantAllReportsResponse, QdrantDeleteReportResponse, QdrantReportSectionsComparisonResponce
from app.storage.qdrant.qdrant_manager import QdrantReportsStorage

class QdrantReportsService:
    def __init__(self):
        self.storage = QdrantReportsStorage()
    
    async def qdrant_set_data(self, data: QdrantAddReportRequest) -> QdrantAddReportResponse:
        """Добавление отчёта в векторную БД"""
        return self.storage.add_report(data)

    async def get_all_reports(self) -> QdrantAllReportsResponse:
        """Получение списка всех отчётов"""
        return self.storage.get_all_reports()

    async def get_report_by_id(self, report_id: str):
        """Получение полных данных отчёта по ID"""
        return self.storage.get_report(report_id)

    async def delete_report(self, report_id: str) -> QdrantDeleteReportResponse:
        """Удаление отчёта по ID"""
        return self.storage.delete_report(report_id)

    async def get_distance(self, report1_id: str, report2_id: str, section_code: str) -> QdrantReportSectionsComparisonResponce:
        return self.storage.compare_single_section_pair(report1_id, report2_id, section_code)