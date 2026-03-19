import os
from qdrant_client import QdrantClient
from qdrant_client.http import models
import numpy as np

from app.schemas.qdrant import (
    QdrantCollectionResponse,
    QdrantAllReportsResponse,
    QdrantDeleteReportResponse,
    QdrantTitleReport,
    QdrantReportSectionsComparisonResponse,
    QdrantReportDataResponse,
    QdrantReportSectionResponse,
)

class QdrantReportsStorage:
    """
    Класс для реализации взаимодействия с БД Qdrant
    """
    _instance = None
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        """Переписанный метод. Контролирует единственность экземпляря класса1
        
        Returns:
            _type_: _description_
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self) -> None:
        """Реализация инстанаса класса
        Подключаем порты
        Создаём подключения с приоритетом на HTTP
        Создаём векторизатор
        """
        if type(self)._initialized:
            return
        self.host = os.getenv('QDRANT_HOST')
        self.http_port = int(os.getenv('QDRANT_PORT_HTTP'))
        self.grpc_port = int(os.getenv('QDRANT_PORT_GRPC'))
        self.vect_model_name = os.getenv('VECT_MODEL')
        
        self.client = QdrantClient(
            host=self.host,
            port=self.http_port,
            grpc_port=self.grpc_port,
            prefer_grpc=False
        )
        self.collection_name = "reports"
        self.vector_size = 1024
        self.__init_collection()
        print("Installing completed")
        type(self)._initialized = True
    
    def __init_collection(self) -> QdrantCollectionResponse:
        """Создание коллекции для хранения отчёта
        
        Returns:
            QdrantCollectionResponse: результат создания коллекции и сообщение
        """
        try:
            # Создаём коллекцию с настройками для векторного поиска
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=self.vector_size,
                    distance=models.Distance.COSINE
                )
            )
            
            # Создаём индексы для полей-фильтров
            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="year",
                field_schema="integer"
            )
            
            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="subject", 
                field_schema="integer"
            )
            
            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="type",
                field_schema="keyword"
            )

            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="report_id",
                field_schema="keyword"
            )

            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="section_code",
                field_schema="keyword"
            )
            
            return QdrantCollectionResponse(
                success=True,
                messange="Collection created"
            )
            
        except Exception as e:
            # Если коллекция уже существует - это не ошибка
            if "already exists" in str(e):
                return QdrantCollectionResponse(
                    success=True,
                    messange="Collection is already exists"
                )
            else:
                return QdrantCollectionResponse(
                    success=False,
                    messange="Error when creating a collection: " + str(e)
                )
    
    def get_all_reports(self) -> QdrantAllReportsResponse:
        try:
            reports = []
            next_page_offset = None
            while True:
                points, next_page_offset = self.client.scroll(
                    collection_name=self.collection_name,
                    limit=100,
                    offset=next_page_offset,
                    with_payload=True,
                    with_vectors=False,
                    scroll_filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="type",
                                match=models.MatchValue(value="document")
                            )
                        ]
                    )
                )

                if not points:
                    break

                for point in points:
                    reports.append(
                        QdrantTitleReport(
                            id=point.id,
                            title=point.payload.get("title", "Без названия")
                        )
                    )

                if next_page_offset is None:
                    break

            return QdrantAllReportsResponse(reports=reports)

        except Exception as e:
            print(f"❌ {e}")
            return QdrantAllReportsResponse(reports=[])
    
    def get_report(self, report_id: str) -> QdrantReportDataResponse:
        try:
            # 1. Получаем документ
            doc = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[report_id],
                with_payload=True,
                with_vectors=True
            )

            if not doc:
                return None

            doc = doc[0]

            # 2. Получаем секции
            sections, _ = self.client.scroll(
                collection_name=self.collection_name,
                limit=1000,
                with_payload=True,
                with_vectors=True,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="type",
                            match=models.MatchValue(value="section")
                        ),
                        models.FieldCondition(
                            key="report_id",
                            match=models.MatchValue(value=report_id)
                        )
                    ]
                )
            )

            return QdrantReportDataResponse(
                id=doc.id,
                vector=doc.vector,
                sections=[
                    QdrantReportSectionResponse(
                        code=s.payload.get("section_code"),
                        name=s.payload.get("title"),
                        text=s.payload.get("text"),
                        vector=s.vector
                    )
                    for s in sections
                ]
            )

        except Exception as e:
            print(f"❌ get_report: {e}")
            return None
    
    def delete_report(self, report_id: str) -> QdrantDeleteReportResponse:
        try:
            # удаляем документ
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.PointIdsList(points=[report_id])
            )

            # удаляем все секции
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.FilterSelector(
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="report_id",
                                match=models.MatchValue(value=report_id)
                            )
                        ]
                    )
                )
            )

            return QdrantDeleteReportResponse(
                success=True,
                message="Удалено"
            )

        except Exception as e:
            return QdrantDeleteReportResponse(
                success=False,
                message=str(e)
            )
    
    def compare_single_section_pair(
        self,
        report1_id: str,
        report2_id: str,
        section_code: str
    ) -> QdrantReportSectionsComparisonResponse:

        try:
            # 1. Найти секцию из первого отчёта
            section1, _ = self.client.scroll(
                collection_name=self.collection_name,
                limit=1,
                with_vectors=True,
                with_payload=True,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(key="type", match=models.MatchValue(value="section")),
                        models.FieldCondition(key="report_id", match=models.MatchValue(value=report1_id)),
                        models.FieldCondition(key="section_code", match=models.MatchValue(value=section_code)),
                    ]
                )
            )

            if not section1:
                return QdrantReportSectionsComparisonResponse(
                    success=False,
                    message="Секция не найдена в отчёте 1",
                    section_code=section_code
                )

            section1 = section1[0]

            # 2. Ищем такую же секцию во втором отчёте через search
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=section1.vector,
                limit=1,
                query_filter=models.Filter(
                    must=[
                        models.FieldCondition(key="type", match=models.MatchValue(value="section")),
                        models.FieldCondition(key="report_id", match=models.MatchValue(value=report2_id)),
                        models.FieldCondition(key="section_code", match=models.MatchValue(value=section_code)),
                    ]
                )
            )

            if not results:
                return QdrantReportSectionsComparisonResponse(
                    success=False,
                    message="Секция не найдена во втором отчёте",
                    section_code=section_code
                )

            match = results[0]

            return QdrantReportSectionsComparisonResponse(
                success=True,
                message="OK",
                section_code=section_code,
                section_title=section1.payload.get("title"),
                cosine_similarity=match.score
            )

        except Exception as e:
            return QdrantReportSectionsComparisonResponse(
                success=False,
                message=str(e),
                section_code=section_code
            )
