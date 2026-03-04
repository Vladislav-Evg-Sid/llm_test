from huggingface_hub import snapshot_download

import os
from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer
from pathlib import Path
from dotenv import load_dotenv
import uuid
import numpy as np

from app.schemas.qdrant import (
    QdrantCollectionResponse,
    QdrantReportSectionData,
    QdrantAddReportResponse,
    QdrantAllReportsResponse,
    QdrantDeleteReportResponse,
    QdrantTitleReport,
    QdrantReportSectionsComparisonResponce,
    QdrantReportDataResponce,
)
from app.utils.models_ml.local_dir import check_folder

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
    
    def __init__(self):
        """Реализация инстанаса класса
        Подключаем порты
        Создаём подключения с приоритетом на HTTP
        Создаём векторизатор
        """
        if self._initialized:
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
        path_to_model = "app/models_ml/"
        print("Installing vectorization model...")
        match self.vect_model_name:
            case 'BBAI/bge-m3':
                if not check_folder(path_to_model + self.vect_model_name.replace('/', '_')):
                    local_dir = snapshot_download(
                        repo_id=self.vect_model_name,
                        local_dir=path_to_model+self.vect_model_name.replace('/', '_'),
                    )
                else:
                    local_dir = path_to_model + self.vect_model_name.replace('/', '_')
                self.model = SentenceTransformer(local_dir, device='cpu')
                self.vector_size = 1024
                self.tokenizer = None
                self.chunk_size = None
        self.__init_collection()
        print("Installing completed")
        self._initialized = True
    
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
                field_name="super_subject_id", 
                field_schema="integer"
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
    
    def __chunk_split(self, text: str) -> list[str]:
        """Делит текст на чанки, если это необходимо
        
        Args:
            text (str): Исходный текст
        
        Returns:
            list[str]: Список чанков текста
        """
        if self.chunk_size is None:
            return [text]
        tokens = self.tokenizer.encode(text, add_special_tokens=False)
        if len(tokens) <= self.chunk_size:
            return [text]
        
        chunks = []
        step = self.chunk_size - int(0.25 * self.chunk_size)
        for start_idx in range(0, len(tokens), step):
            end_idx = start_idx + self.chunk_size
            chunk_tokens = tokens[start_idx:end_idx]
            chunk_text = self.tokenizer.decode(chunk_tokens, skip_special_tokens=True)
            chunks.append(chunk_text)
        
        return chunks
    
    def __get_document_embedding(self, text: str) -> list[float]:
        """Возвращает вектор текста
        Использует разбиение по чанкам, если текст больше возможной длинны
        
        Args:
            text (str): Исходный текст
        
        Returns:
            list[float]: Вектор
        """
        chunks = self.__chunk_split(text)
        if len(chunks) == 1:
            return self.model.encode(chunks[0]).tolist()
        
        chunks_embeding = []
        for chunk in chunks:
            chunk_vector = self.model.encode(chunk)
            chunks_embeding.append(chunk_vector)
        
        avg_embeding = np.mean(chunks_embeding)
        
        return avg_embeding.tolist()
    
    def add_report(self, report_data: QdrantReportSectionData) -> QdrantAddReportResponse:
        """Добавляет запись в векторную БД
        
        Args:
            report_data (QdrantAddReportRequest): Модель данных, которые требуется записать
        
        Returns:
            QdrantAddReportResponse: Результат добавления записи, uuid записи, текст ошибки
        """
        try:
            report_id = str(uuid.uuid4())
            
            # Векторизация каждого раздела
            sections = []
            for section in report_data.sections:
                section_vector = self.__get_document_embedding(section.text)
                sections.append({
                    "code": section.code,
                    "text": section.text,
                    "vector": section_vector
                })
            
            # Аггрегация разделов в вектор отчёта
            full_text = "\n".join([sec.text for sec in report_data.sections])
            report_vector = self.__get_document_embedding(full_text)
            
            # Сохранение в Qdrant
            self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    models.PointStruct(
                        id=report_id,
                        vector=report_vector,
                        payload={
                            "year": report_data.year,
                            "title": report_data.title,
                            "super_subject_id": report_data.super_subject_id,
                            "exam_type": report_data.exam_type,
                            "sections": sections
                        }
                    )
                ]
            )
            
            return QdrantAddReportResponse(
                success=True,
                id=report_id,
                messange="Отчёт успешно добавлен"
            )
            
        except Exception as e:
            return QdrantAddReportResponse(
                success=False,
                id="",
                messange=f"Ошибка при добавлении отчёта: {str(e)}"
            )
    
    def get_all_reports(self) -> QdrantAllReportsResponse:
        """Возвращает список всех отчётов (id + title)"""
        try:
            reports = []
            next_page_offset = None
            
            # Обрабатываем пагинацию через scroll
            while True:
                scroll_result = self.client.scroll(
                    collection_name=self.collection_name,
                    limit=100,  # Количество точек за один запрос
                    offset=next_page_offset,
                    with_payload=True,
                    with_vectors=False  # Нам не нужны векторы для списка
                )
                
                # points - список точек, next_page_offset - смещение для следующей страницы
                points, next_page_offset = scroll_result
                
                # Добавляем точки в результат
                for point in points:
                    reports.append(
                        QdrantTitleReport(
                            id=point.id,
                            title=point.payload.get("title", "Без названия")
                        )
                    )
                
                # Если next_page_offset is None - значит это последняя страница
                if next_page_offset is None:
                    break
            
            print(f"📊 Найдено отчётов: {len(reports)}")
            return QdrantAllReportsResponse(reports=reports)
            
        except Exception as e:
            print(f"❌ Ошибка при получении списка отчётов: {e}")
            return QdrantAllReportsResponse(reports=[])
    
    def get_report(self, report_id: str) -> QdrantReportDataResponce:
        """Возвращает отчёт по id
        
        Args:
            report_id (str): uuid искомого отчёта
            
        Returns:
            QdrantReportDataResponce: Вся информация об отчёте
        """
        try:
            points = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[report_id],
                with_payload=True
            )
            
            if points and len(points) > 0:
                point = points[0]
                return {
                    "id": point.id,
                    "payload": point.payload,
                    "vector": point.vector
                }
            else:
                return None
                
        except Exception as e:
            print(f"Ошибка при получении отчёта: {e}")
            return None
    
    def delete_report(self, report_id: str) -> QdrantDeleteReportResponse:
        """Удаляет отчёт по ID
        
        Args:
            report_id: UUID отчёта для удаления
            
        Returns:
            QdrantDeleteReportResponse: Результат операции
        """
        try:
            # Сначала проверим, существует ли отчёт
            existing_report = self.get_report(report_id)
            if not existing_report:
                return QdrantDeleteReportResponse(
                    success=False,
                    message=f"Отчёт с ID {report_id} не найден"
                )
            
            # Удаляем отчёт
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.PointIdsList(
                    points=[report_id]
                )
            )
            
            print(f"✅ Отчёт {report_id} успешно удалён")
            return QdrantDeleteReportResponse(
                success=True,
                message=f"Отчёт {report_id} успешно удалён"
            )
            
        except Exception as e:
            print(f"❌ Ошибка при удалении отчёта {report_id}: {e}")
            return QdrantDeleteReportResponse(
                success=False,
                message=f"Ошибка при удалении отчёта: {str(e)}"
            )
    
    def compare_single_section_pair(self, report1_id: str, report2_id: str, section_code: str) -> QdrantReportSectionsComparisonResponce:
        """
        Сравнивает одну пару секций (с одинаковым кодом) в двух отчётах.
        
        Args:
            report1_id: UUID первого отчёта
            report2_id: UUID второго отчёта  
            section_code: Код секции для сравнения (должен быть в обоих отчётах)
            
        Returns:
            QdrantReportSectionsComparison: Результат сравнения с косинусным расстоянием
        """
        # 1. Проверка наличия отчётов в базе
        report1 = self.get_report(report1_id)
        if not report1:
            return QdrantReportSectionsComparisonResponce(
                success=False,
                message=f"Отчёт 1 с ID {report1_id} не найден",
                section_code=section_code
            )
        
        report2 = self.get_report(report2_id)
        if not report2:
            return QdrantReportSectionsComparisonResponce(
                success=False,
                message=f"Отчёт 2 с ID {report2_id} не найден",
                section_code=section_code
            )
        
        # 2. Проверка наличия секций в отчётах
        report1_sections = report1["payload"].get("sections", [])
        report2_sections = report2["payload"].get("sections", [])
        
        # Находим нужную секцию в первом отчёте
        section1 = None
        for sec in report1_sections:
            if sec.get("code") == section_code:
                section1 = sec
                break
        
        if not section1:
            print('error')
            print("Секция с кодом '{section_code}' не найдена в отчёте 1 ({report1_id})")
            return QdrantReportSectionsComparisonResponce(
                success=False,
                message=f"Секция с кодом '{section_code}' не найдена в отчёте 1 ({report1_id})",
                section_code=section_code
            )
        
        # Находим нужную секцию во втором отчёте
        section2 = None
        for sec in report2_sections:
            if sec.get("code") == section_code:
                section2 = sec
                break
        
        if not section2:
            return QdrantReportSectionsComparisonResponce(
                success=False,
                message=f"Секция с кодом '{section_code}' не найдена в отчёте 2 ({report2_id})",
                section_code=section_code
            )
        
        # 3. Проверка наличия векторов у секций
        vector1 = section1.get("vector", [])
        vector2 = section2.get("vector", [])
        
        if not vector1:
            return QdrantReportSectionsComparisonResponce(
                success=False,
                message=f"У секции '{section_code}' в отчёте 1 отсутствует вектор",
                section_code=section_code,
                section_title=section1.get("title", section_code)
            )
        
        if not vector2:
            return QdrantReportSectionsComparisonResponce(
                success=False,
                message=f"У секции '{section_code}' в отчёте 2 отсутствует вектор",
                section_code=section_code,
                section_title=section2.get("title", section_code)
            )
        
        # 4. Вычисление косинусного расстояния
        # Косинусное расстояние = 1 - косинусная схожесть
        # Косинусная схожесть = (A·B) / (||A|| * ||B||)
        
        vec1_np = np.array(vector1)
        vec2_np = np.array(vector2)
        
        # Вычисляем нормы векторов
        norm1 = np.linalg.norm(vec1_np)
        norm2 = np.linalg.norm(vec2_np)
        
        if norm1 == 0 or norm2 == 0:
            return QdrantReportSectionsComparisonResponce(
                success=False,
                message="Один из векторов имеет нулевую длину",
                section_code=section_code,
                section_title=section1.get("title", section_code)
            )
        
        # Вычисляем косинусную схожесть
        cosine_similarity = np.dot(vec1_np, vec2_np) / (norm1 * norm2)
        
        # Преобразуем в расстояние: 1 - similarity
        # Диапазон: 0 (идентичные) - 2 (противоположные)
        cosine_distance = 1.0 - cosine_similarity
        
        return QdrantReportSectionsComparisonResponce(
            success=True,
            message=f"Секция '{section_code}' успешно сравнена",
            section_code=section_code,
            section_title=section1.get("title", section_code),
            cosine_distance=cosine_similarity
        )
    
    def get_report_by_parametrs(self, super_subject_id: int, year: int): # TODO Тоже должен возвращать модель
        try:
            points = self.client.retrieve(
                collection_name=self.collection_name,
                year=year,
                super_subject_id=super_subject_id,
                with_payload=True
            )
            return points[0] if points else None
        except:
            return None
