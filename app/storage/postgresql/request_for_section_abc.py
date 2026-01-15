from sqlalchemy import func, select, and_, Numeric, Column, CTE
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, InstrumentedAttribute
from sqlalchemy.sql.expression import ColumnElement
from types import SimpleNamespace
from abc import ABC, abstractmethod
from datetime import datetime

from app.models.models import *
from app.schemas.text_reports import *


class RequestsForSections(ABC):
    def __init__(self, year: int, exam_type_id:int , subject_id: int, start_date: datetime, end_date: datetime):
        """Создаёт наследник класса для дальней работы
        
        Args:
            year (int): Текущий год
            exam_type_id (int): Код тип экзамена (4 (ЕГЭ)/6 (ОГЭ))
            subject_id (int): Код типа предмета
            start_date (str): Дата начала экзаменов за все годы
            end_date (str): Дата окончания экзаменов
        """
        self.year = year
        self.exam_type_id = exam_type_id
        self.subject_id = subject_id
        self.start_date = start_date
        self.end_date = end_date
        self._tables = SimpleNamespace()
        self._addClassTables()
    
    def _calculteProcent(self, part: ColumnElement | InstrumentedAttribute | Column, all: ColumnElement | InstrumentedAttribute | Column, rounding: int = 1) -> ColumnElement:
        """Получаем процент от числа
        
        Args:
            part (ColumnElement | InstrumentedAttribute | Column): Столбец с долей
            all (ColumnElement | InstrumentedAttribute | Column): Столбец со всеми значениями
            rounding (int, optional): Количество знаков после запятой. Defaults to 1.
        
        Returns:
            ColumnElement: Итоговый столбец
        """
        return func.round(func.cast(100.0, Numeric) * func.coalesce(part, 0) / all, rounding)
    
    def _getASC(
            self,
            dop_filters: list = [],
            group_by: list[Column] = [TestSchemes.exam_year],
            year_count: int = 3,
            dop_joins: list[tuple[Column, any]] = []
        ) -> tuple[CTE, CTE]:
        only_last_res = (
            select(
                ExamResults.id.label("exam_id"),
                func.row_number().over(
                    partition_by = [ExamResults.student_id, ExamResults.schema_id],
                    order_by=ExamResults.exam_date.desc()
                ).label("rn")
            )
            .join(TestSchemes, ExamResults.schema_id == TestSchemes.id)
            .filter(
                TestSchemes.exam_year.between(self.year+1-year_count, self.year),
                TestSchemes.exam_type_id == self.exam_type_id,
                ExamResults.status_id == 6,
                # ExamResults.exam_date.between(self.start_date, self.end_date),
                *dop_filters
            )
        ).cte("only_last_res")
        
        all_students_count = (
            select(
                *group_by,
                func.count(ExamResults.student_id.distinct()).label("stud_count")
            )
            .join(TestSchemes, ExamResults.schema_id == TestSchemes.id)
            .join(only_last_res, and_(only_last_res.c.exam_id == ExamResults.id, only_last_res.c.rn == 1))
        )
        for j in dop_joins:
            all_students_count = all_students_count.join(j[0], j[1])
        all_students_count = all_students_count.group_by(*group_by).cte("all_students_count")
        
        return all_students_count, only_last_res
    
    @abstractmethod
    def _addClassTables(self) -> None:
        pass
    
    @abstractmethod
    async def getListOfTables(self, session: AsyncSession) -> list[TableStandart]:
        pass
