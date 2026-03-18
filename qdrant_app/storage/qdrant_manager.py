from huggingface_hub import snapshot_download

import os
from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer
from pathlib import Path
import uuid
import numpy as np

from qdrant_app.schemas.qdrant import (
    QdrantReportData,
    QdrantAddReportResponse,
)


def check_folder(folder_path: str) -> bool:
    """Проверяет наличие папки и то, что она не пуста

    Args:
        path (str): Путь к папке

    Returns:
        bool: Вердикт
    """
    path = Path(folder_path)
    if not path.exists():
        return False
    
    if not path.is_dir():
        return False
    
    try:
        next(path.iterdir())
        return True
    except:
        return False


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
            case 'BAAI/bge-m3':
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
        print("Installing completed")
        self._initialized = True
    
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
    
    def add_report(self, report_data: QdrantReportData) -> QdrantAddReportResponse:
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
                    "name": section.name,
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

async def get_qdrant_report_service():
    yield QdrantReportsStorage()