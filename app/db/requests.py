from sqlalchemy import func, select, and_, or_, case, MetaData, types, desc, asc, Numeric, any_, not_, text, Table, Column, Select
from sqlalchemy.engine import Row
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, InstrumentedAttribute
from sqlalchemy.sql.expression import ColumnElement
from decimal import Decimal
from types import SimpleNamespace
from abc import ABC, abstractmethod

from db.models import *
from py_models import *


class RequestsForSections(ABC):
    def __init__(self, year: int, exam_type_id:int , subject_id: int, start_date: str, end_date: str):
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
        ):
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
                # ExamResults.exam_date.between(self.start_date, self.end_date)
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
    def _addClassTables(self):
        pass
    
    @abstractmethod
    async def getListOfTables(self, session: AsyncSession) -> list[TableStandart]:
        pass

class RequestsForFirstSection(RequestsForSections):
    def _addClassTables(self):
        self._tables.count = None
        self._tables.sex = None
        self._tables.categories = None
        self._tables.schoolKinds = None
        self._tables.areas = None
    
    async def getListOfTables(self, session: AsyncSession) -> list[TableStandart]:
        result = []
        tables = [
            self.getTable_count(session),
            self.getTable_sex(session),
            self.getTable_categories(session),
            self.getTable_schoolKinds(session),
            self.getTable_areas(session),
        ]
        
        for corutine_table in tables:
            table = await corutine_table
            result.append(table)
        
        return result
    
    async def getTable_count(self, session: AsyncSession) -> TableStandart:
        """Формирует таблицу количества участников за текущий год и 2 предыдущих
        
        Args:
            session (AsyncSession): Сессия для взаимодействия с БД
        
        Returns:
            TableStandart: Итоговая таблица
        """
        if self._tables.count is not None:
            return self._tables.count
        
        all_students_count, only_last_res = self._getASC()
        
        subjects_students_count = (
            select(
                TestSchemes.exam_year.label("year"),
                func.count(ExamResults.student_id.distinct()).label("stud_count")
            ).join(TestSchemes, TestSchemes.id == ExamResults.schema_id)
            .join(only_last_res, and_(only_last_res.c.exam_id == ExamResults.id, only_last_res.c.rn == 1))
            .filter(TestSchemes.exam_year.between(self.year-2, self.year))
            .filter(TestSchemes.exam_type_id == self.exam_type_id)
            .filter(TestSchemes.subject_id == self.subject_id)
            .group_by(TestSchemes.exam_year)
        ).cte("subjects_students_count")
        
        query = await session.execute(
            select(
                subjects_students_count.c.year,
                subjects_students_count.c.stud_count,
                self._calculteProcent(subjects_students_count.c.stud_count, all_students_count.c.stud_count)
            ).select_from(subjects_students_count)
            .join(all_students_count, all_students_count.c.exam_year == subjects_students_count.c.year)
        )
        
        data = query.all()
        
        result = TableStandart(
            column_names=[
                f"{self.year-2} г. | чел.",
                f"{self.year-2} г. | % от общего числа участников",
                f"{self.year-1} г. | чел.",
                f"{self.year-1} г. | % от общего числа участников",
                f"{self.year} г. | чел.",
                f"{self.year} г. | % от общего числа участников",
            ],
            data=[[0]*6]
        )
        
        for i in range(len(data)):
            result.data[0][i*2] = data[i][1]
            result.data[0][i*2+1] = float(data[i][2])
        result.table_name = "Количество участников ЕГЭ по учебному предмету (за 3 года)"
        
        self._tables.count = result
        
        return result
    
    async def getTable_sex(self, session: AsyncSession) -> TableStandart:
        """Формирует таблицу гендерного распределения участников по 3 годам
        
        Args:
            session (AsyncSession): Сессия для взаимодействия с БД
        
        Returns:
            TableStandart: Итоговая таблица
        """
        if self._tables.sex is not None:
            return self._tables.sex
        
        categories = ["Женский","Мужской"]
        all_students_count, only_last_res = self._getASC()
        
        subjects_students_count = (
            select(
                Students.sex.label("sex"),
                TestSchemes.exam_year.label("year"),
                func.count(ExamResults.student_id.distinct()).label("stud_count")
            ).join(TestSchemes, TestSchemes.id == ExamResults.schema_id)
            .join(Students, Students.id == ExamResults.student_id)
            .join(only_last_res, and_(only_last_res.c.exam_id == ExamResults.id, only_last_res.c.rn == 1))
            .filter(TestSchemes.exam_year.between(self.year-2, self.year))
            .filter(TestSchemes.exam_type_id == self.exam_type_id)
            .filter(TestSchemes.subject_id == self.subject_id)
            .group_by(Students.sex)
            .group_by(TestSchemes.exam_year)
        ).cte("subjects_students_count")
        
        query = await session.execute(
            select(
                case((subjects_students_count.c.sex, "Женский"), else_ = "Мужской").label("sex"),
                subjects_students_count.c.year,
                subjects_students_count.c.stud_count,
                self._calculteProcent(subjects_students_count.c.stud_count, all_students_count.c.stud_count)
            ).select_from(subjects_students_count)
            .join(all_students_count, all_students_count.c.exam_year == subjects_students_count.c.year)
            .order_by("sex", subjects_students_count.c.year)
        )
        
        data = query.all()
        
        result = TableStandart(
            column_names=[
                "Пол",
                f"{self.year-2} г. | чел.",
                f"{self.year-2} г. | % от общего числа участников",
                f"{self.year-1} г. | чел.",
                f"{self.year-1} г. | % от общего числа участников",
                f"{self.year} г. | чел.",
                f"{self.year} г. | % от общего числа участников",
            ],
            str_names=categories,
            data=[[0]*6 for i in range(3)]
        )
        
        for a in data:
            ind_y = categories.index(a[0])
            ind_x = (a[1] - self.year - 1) * 2
            result.data[ind_y][ind_x] = a[2]
            result.data[ind_y][ind_x+1] = float(a[3])
            
            self._tables.sex = result
        result.table_name = "Процентное соотношение юношей и девушек, участвующих в ЕГЭ (за 3 года)"
        
        self._tables.sex = result
        
        return result
    
    async def getTable_categories(self, session: AsyncSession) -> TableStandart:
        """Формирует таблицу по категориям участников
        
        Args:
            session (AsyncSession): Сессия для взаимодействия с БД
        
        Returns:
            TableStandart: Таблица данных
        """
        if self._tables.categories is not None:
            return self._tables.categories
        
        categories = [1, 3, 4]
        category_names = ["ВТГ, обучающихся по программам СОО", "ВТГ, обучающихся по программам СПО", "ВПЛ"]
        all_students_count, only_last_res = self._getASC()
        
        subjects_students_count = (
            select(
                Students.category_id.label("category_id"),
                TestSchemes.exam_year.label("year"),
                func.count(ExamResults.student_id.distinct()).label("stud_count")
            ).join(TestSchemes, TestSchemes.id == ExamResults.schema_id)
            .join(Students, Students.id == ExamResults.student_id)
            .join(only_last_res, and_(only_last_res.c.exam_id == ExamResults.id, only_last_res.c.rn == 1))
            .filter(
                TestSchemes.exam_year.between(self.year-2, self.year),
                TestSchemes.exam_type_id == self.exam_type_id,
                TestSchemes.subject_id == self.subject_id,
                Students.category_id.in_(categories)
            )
            .group_by(Students.category_id)
            .group_by(TestSchemes.exam_year)
        ).cte("subjects_students_count")
        
        query = await session.execute(
            select(
                subjects_students_count.c.category_id,
                subjects_students_count.c.year,
                subjects_students_count.c.stud_count,
                self._calculteProcent(subjects_students_count.c.stud_count, all_students_count.c.stud_count)
            ).select_from(subjects_students_count)
            .join(all_students_count, all_students_count.c.exam_year == subjects_students_count.c.year)
            .order_by(subjects_students_count.c.category_id, subjects_students_count.c.year)
        )
        
        data = query.all()
        
        result = TableStandart(
            column_names=[
                "Категория участника",
                f"{self.year-2} г. | чел.",
                f"{self.year-2} г. | % от общего числа участников",
                f"{self.year-1} г. | чел.",
                f"{self.year-1} г. | % от общего числа участников",
                f"{self.year} г. | чел.",
                f"{self.year} г. | % от общего числа участников",
            ],
            str_names=category_names,
            data=[[0]*6 for i in range(3)]
        )
        
        for a in data:
            ind_y = categories.index(a[0])
            ind_x = (a[1] - self.year - 1) * 2
            result.data[ind_y][ind_x] = a[2]
            result.data[ind_y][ind_x+1] = float(a[3])
        result.table_name = "Количество участников экзамена в регионе по категориям (за 3 года)"
        
        self._tables.categories = result
        
        return result
    
    async def getTable_schoolKinds(self, session: AsyncSession) -> TableStandart:
        """Формирует таблицу по видом ОО
        
        Args:
            session (AsyncSession): Сессия для взаимодействия с БД
        
        Returns:
            TableStandart: Таблица данных
        """
        if self._tables.schoolKinds is not None:
            return self._tables.schoolKinds
        
        all_students_count, only_last_res = self._getASC()
        
        subjects_students_count = (
            select(
                SchoolKinds.code.label("code"),
                SchoolKinds.name.label("school_kind"),
                TestSchemes.exam_year.label("year"),
                func.count(ExamResults.student_id.distinct()).label("stud_count")
            ).join(TestSchemes, TestSchemes.id == ExamResults.schema_id)
            .join(Students, Students.id == ExamResults.student_id)
            .join(Schools, Schools.code == Students.school_id)
            .join(SchoolKinds, SchoolKinds.code == Schools.kind_code)
            .join(only_last_res, and_(only_last_res.c.exam_id == ExamResults.id, only_last_res.c.rn == 1))
            .filter(
                TestSchemes.exam_year.between(self.year-2, self.year),
                TestSchemes.exam_type_id == self.exam_type_id,
                TestSchemes.subject_id == self.subject_id,
                SchoolKinds.code.in_([101, 102, 103, 104, 1001, 2201])
            )
            .group_by(SchoolKinds.code)
            .group_by(TestSchemes.exam_year)
        ).cte("subjects_students_count")
        
        query = (
            select(
                subjects_students_count.c.school_kind,
                subjects_students_count.c.year,
                subjects_students_count.c.stud_count,
                self._calculteProcent(subjects_students_count.c.stud_count, all_students_count.c.stud_count)
            ).select_from(subjects_students_count)
            .join(all_students_count, all_students_count.c.exam_year == subjects_students_count.c.year)
            .order_by(subjects_students_count.c.code, subjects_students_count.c.year)
        )
        
        query = await session.execute(query)
        data = query.all()
        
        result = TableStandart(
            column_names=[
                "Категория участника",
                f"{self.year-2} г. | чел.",
                f"{self.year-2} г. | % от общего числа участников",
                f"{self.year-1} г. | чел.",
                f"{self.year-1} г. | % от общего числа участников",
                f"{self.year} г. | чел.",
                f"{self.year} г. | % от общего числа участников",
            ],
            data=[[0]*6 for i in range(len(data)//3)]
        )
        ind_x = 0
        ind_y = -1
        for i in range(len(data)):
            if data[i][0] in result.str_names:
                result.data[ind_y][ind_x] = data[i][2]
                result.data[ind_y][ind_x+1] = float(data[i][3])
                ind_x += 2
            else:
                ind_y += 1
                ind_x = 0
                result.str_names.append(data[i][0])
                result.data[ind_y][ind_x] = data[i][2]
                result.data[ind_y][ind_x+1] = float(data[i][3])
                ind_x += 2
        result.table_name = "Количество участников экзамена в регионе по типам ОО"
        
        self._tables.schoolKinds = result
        
        return result
    
    async def getTable_areas(self, session: AsyncSession) -> TableStandart:
        """Формирует таблицу по АТЕ региона
        
        Args:
            session (AsyncSession): Сессия для взаимодействия с БД
        
        Returns:
            TableStandart: Итоговая таблица
        """
        if self._tables.areas is not None:
            return self._tables.areas
        
        all_students_count_query = await session.execute(
            select(
                func.count(ExamResults.student_id.distinct()).label("stud_count")
            ).join(TestSchemes, ExamResults.schema_id == TestSchemes.id)
            .filter(TestSchemes.exam_year == self.year)
            .filter(TestSchemes.exam_type_id == self.exam_type_id)
            # .filter(ExamResults.exam_date.between(self.start_date, self.end_date))
        )
        all_students_count = all_students_count_query.first()[0]
        
        query = await session.execute(
            select(
                func.concat(Areas.code, " - ", Areas.name),
                func.count(ExamResults.student_id.distinct()),
                self._calculteProcent(func.count(ExamResults.student_id.distinct()), all_students_count)
            ).join(Schools, Schools.area_id == Areas.code)
            .join(Students, Students.school_id == Schools.code)
            .join(ExamResults, ExamResults.student_id == Students.id)
            .join(TestSchemes, TestSchemes.id == ExamResults.schema_id)
            .filter(TestSchemes.exam_year == self.year)
            .filter(TestSchemes.exam_type_id == self.exam_type_id)
            .filter(TestSchemes.subject_id == self.subject_id)
            .group_by(Areas.code)
        )
        
        result = TableStandart(
            column_names=[
                "Наименование АТЕ",
                "Количество участников ЕГЭ по учебному предмету",
                "% от общего числа участников в регионе",
            ]
        )
        for a in query.all():
            result.str_names.append(a[0])
            result.data.append([a[1], float(a[2])])
        result.table_name = "Количество участников ЕГЭ по учебному предмету по АТЕ региона"
        
        self._tables.areas = result
        
        return result


class RequestsForSecondSection(RequestsForSections):
    def _addClassTables(self):
        self._tables.scoreDictribution = None
        self._tables.resultDynamic = None
        self._tables.resultByStudCat = None
        self._tables.resultBySchoolTypes = None
        self._tables.resultBySex = None
        self._tables.resultByAreas = None
        self._tables.hightResults = None
        self._tables.lowResults = None
    
    async def getListOfTables(self, session: AsyncSession) -> list[TableStandart]:
        result = []
        tables = [
            self.getTable_scoreDictribution(session),
            self.getTable_resultDynamic(session),
            self.getTable_resultByStudCat(session),
            self.getTable_resultBySchoolTypes(session),
            self.getTable_resultBySex(session),
            self.getTable_resultByAreas(session),
            self.getTable_hightResults(session),
            self.getTable_lowResults(session),
        ]
        
        for corutine_table in tables:
            table = await corutine_table
            result.append(table)
        
        return result
    
    async def getTable_scoreDictribution(self, session: AsyncSession) -> TableStandart:
        """Формирует таблицу распределения тестовых баллов
        
        Args:
            session (AsyncSession): Сессия для взаимодействия с БД
        
        Returns:
            TableDicTableStandarttribution: Готовая таблица
        """
        if self._tables.scoreDictribution is not None:
            return self._tables.scoreDictribution
        
        query = await session.execute(
            select(
                ExamResults.final_points,
                func.count(ExamResults.student_id.distinct())
            )
            .join(TestSchemes, TestSchemes.id == ExamResults.schema_id)
            .filter(
                TestSchemes.exam_year.between(self.year-2, self.year),
                TestSchemes.exam_type_id == self.exam_type_id,
                TestSchemes.subject_id == self.subject_id
            )
            .group_by(ExamResults.final_points)
            .order_by(ExamResults.final_points)
        )
        
        result = TableStandart(column_names=["Балл", "Количество"])
        for data in query.all():
            result.str_names.append(data[0])
            result.data.append(data[1])
        result.table_name = "Диаграмма распределения тестовых баллов участников ЕГЭ по предмету в 2025 г."
        
        self._tables.scoreDictribution = result
        
        return result
    
    async def _getTable_scoreRanges(
            self,
            session: AsyncSession,
            group_by: list[Column],
            dop_col: ColumnElement,
            year_count: int,
            dop_joins: list[tuple[Column, any]] = [],
            dop_joins_for_cte: list[tuple[Column, any]] = [],
        ) -> list[tuple[int | float]]:
        """Дополнительный метод, обобщающий логику формирования таблиц результатов участников по диапазонам баллов
        
        Args:
            session (AsyncSession): Сессия для взаимодействия с БД
            group_by (list[Column]): Параметры группировки
            dop_col (ColumnElement): Дополнительная колонка
            year_count (int): Для диапазона лет (обычно 1 или 3)
            dop_joins (list[tuple[Column, any]], optional): Дополнительные JOIN таблиц для связности запроса. Defaults to [].
            dop_joins_for_cte (list[tuple[Column, any]], optional): Дополнительные JOIN для подзапроса. Defaults to [].
        
        Returns:
            list[tuple[int | float]]: Результат запроса
        """
        all_students_count, only_last_res = self._getASC(
            dop_filters=[TestSchemes.subject_id == self.subject_id],
            year_count=year_count,
            group_by=group_by,
            dop_joins=dop_joins_for_cte,
        )
        
        query = (
            select(
                *group_by,
                self._calculteProcent(func.sum(case((ExamResults.score == 2, 1), else_=0)), func.min(all_students_count.c.stud_count)),
                self._calculteProcent(func.sum(case((and_(ExamResults.score != 2, ExamResults.final_points < 61), 1), else_=0)), func.min(all_students_count.c.stud_count)),
                self._calculteProcent(func.sum(case((ExamResults.final_points.between(61, 80), 1), else_=0)), func.min(all_students_count.c.stud_count)),
                self._calculteProcent(func.sum(case((ExamResults.final_points.between(81, 100), 1), else_=0)), func.min(all_students_count.c.stud_count)),
                dop_col
            ).select_from(ExamResults)
            .join(TestSchemes, TestSchemes.id == ExamResults.schema_id)
            .join(only_last_res, and_(only_last_res.c.exam_id == ExamResults.id, only_last_res.c.rn == 1))
        )
        
        for joins in dop_joins:
            query = query.join(joins[0], joins[1])
        
        conditions = []
        for i in range(len(group_by)):
            conditions.append(all_students_count.c[i] == group_by[i])
        query = query.join(all_students_count, *conditions)
        
        query = query.group_by(*group_by).order_by(*group_by)
        
        query = await session.execute(query)
        
        return query.all()
    
    async def getTable_resultDynamic(self, session: AsyncSession) -> TableStandart:
        """Формирует таблицу динамики результатов ЕГЭ в разрезе трёх лет
        
        Args:
            session (AsyncSession): Сессия для взаимодействия с БД
        
        Returns:
            TableStandart: Готовая таблица
        """
        if self._tables.resultDynamic is not None:
            return self._tables.resultDynamic
        
        data = await self._getTable_scoreRanges(
            session=session,
            group_by=[TestSchemes.exam_year],
            dop_col=func.round(func.avg(ExamResults.final_points), 1),
            year_count=3
        )
        
        result = TableStandart(
            column_names=[
                "Участников, набравших балл",
                f"Год проведения ГИА | {self.year-2} г.",
                f"Год проведения ГИА | {self.year-1} г.",
                f"Год проведения ГИА | {self.year} г.",
            ],
            str_names=[
                "ниже минимального балла, %",
                "от минимального балла до 60 баллов, %",
                "от 61 до 80 баллов, %",
                "от 81 до 100 баллов, %",
                "Средний тестовый балл",
            ],
            data = [[0]*3 for i in range(5)]
        )
        for i in range(len(data)):
            for j in range(1, len(data[i])):
                result.data[j-1][i] = float(data[i][j])
        result.table_name = "Динамика результатов ЕГЭ по предмету за последние 3 года"
        
        self._tables.resultDynamic = result
        
        return result
    
    async def getTable_resultByStudCat(self, session: AsyncSession) -> TableStandart:
        """Формирует таблицу динамики результатов ЕГЭ в разрезе категорий участников
        
        Args:
            session (AsyncSession): Сессия для взаимодействия с БД
        
        Returns:
            TableStandart: Готовая таблица
        """
        if self._tables.resultByStudCat is not None:
            return self._tables.resultByStudCat
        
        categories = [1, 3, 4]
        category_names = ["ВТГ, обучающихся по программам СОО", "ВТГ, обучающихся по программам СПО", "ВПЛ"]
        
        data = await self._getTable_scoreRanges(
            session=session,
            group_by=[Students.is_ovz, Students.category_id],
            dop_col=func.count(Students.id),
            year_count=1,
            dop_joins=[(Students, Students.id == ExamResults.student_id)]
        )
        
        result = TableStandart(
            column_names=[
                "Категории участников",
                "Количество участников, чел.",
                "Доля участников, у которых полученный тестовый балл | ниже минимального",
                "Доля участников, у которых полученный тестовый балл | от минимального балла до 60 баллов",
                "Доля участников, у которых полученный тестовый балл | от 61 до 80 баллов",
                "Доля участников, у которых полученный тестовый балл | от 81 до 100 баллов",
            ],
            str_names=category_names+["Участники экзамена с ОВЗ"],
            data=[[0]*5, [0]*5, [0]*5, [0]*5]
        )
        for d in data:
            if d[0]:
                for i in range(2, len(d)):
                    if isinstance(d[i], Decimal):
                        result.data[-1][i-1] = float(d[i])
                    else:
                        result.data[-1][0] += d[i]
            else:
                for c in range(len(categories)):
                    if categories[c] == d[1]:
                        for i in range(2, len(d)):
                            if isinstance(d[i], Decimal):
                                result.data[c][i-1] += float(d[i])
                            else:
                                result.data[c][0] += d[i]
                        break
        result.table_name = "Результаты ЕГЭ по учебному предмету по группам участников экзамена с различным уровнем подготовки в разрезе категории участника ЕГЭ"
        
        self._tables.resultByStudCat = result
        
        return result
    
    async def getTable_resultBySchoolTypes(self, session: AsyncSession) -> TableStandart:
        """Формирует таблицу динамики результатов ЕГЭ в разрезе типов школ
        
        Args:
            session (AsyncSession): Сессия для взаимодействия с БД
        
        Returns:
            TableStandart: Готовая таблица
        """
        if self._tables.resultBySchoolTypes is not None:
            return self._tables.resultBySchoolTypes
        
        data = await self._getTable_scoreRanges(
            session=session,
            group_by=[SchoolKinds.name],
            dop_col=func.count(Students.id),
            year_count=1,
            dop_joins=[
                (Students, Students.id == ExamResults.student_id),
                (Schools, Schools.code == Students.school_id),
                (SchoolKinds, SchoolKinds.code == Schools.kind_code)
            ]
        )
        
        result = TableStandart(
            column_names=[
                "Тип ОО",
                "Количество участников, чел.",
                "Доля участников, у которых полученный тестовый балл | ниже минимального",
                "Доля участников, у которых полученный тестовый балл | от минимального балла до 60 баллов",
                "Доля участников, у которых полученный тестовый балл | от 61 до 80 баллов",
                "Доля участников, у которых полученный тестовый балл | от 81 до 100 баллов",
            ]
        )
        for d in data:
            result.str_names.append(d[0])
            result.data.append([0]*5)
            for i in range(1, len(d)):
                if isinstance(d[i], Decimal):
                    result.data[-1][i] = float(d[i])
                else:
                    result.data[-1][0] += d[i]
        result.table_name = "Результаты ЕГЭ по учебному предмету по группам участников экзамена с различным уровнем подготовки в разрезе типа ОО"
        
        self._tables.resultBySchoolTypes = result
        
        return result
    
    async def getTable_resultBySex(self, session: AsyncSession) -> TableStandart:
        """Формирует таблицу динамики результатов ЕГЭ в разрезе пола участника
        
        Args:
            session (AsyncSession): Сессия для взаимодействия с БД
        
        Returns:
            TableStandart: Готовая таблица
        """
        if self._tables.resultBySex is not None:
            return self._tables.resultBySex
        
        data = await self._getTable_scoreRanges(
            session=session,
            group_by=[Students.sex],
            dop_col=func.count(Students.id),
            year_count=1,
            dop_joins=[
                (Students, Students.id == ExamResults.student_id)
            ],
            dop_joins_for_cte=[
                (Students, Students.id == ExamResults.student_id)
            ]
        )
        
        result = TableStandart(
            column_names=[
                "Пол",
                "Количество участников, чел.",
                "Доля участников, у которых полученный тестовый балл | ниже минимального",
                "Доля участников, у которых полученный тестовый балл | от минимального балла до 60 баллов",
                "Доля участников, у которых полученный тестовый балл | от 61 до 80 баллов",
                "Доля участников, у которых полученный тестовый балл | от 81 до 100 баллов",
            ]
        )
        for d in data:
            result.str_names.append("женский" if d[0] else "мужской")
            result.data.append([0]*5)
            for i in range(1, len(d)):
                if isinstance(d[i], Decimal):
                    result.data[-1][i] = float(d[i])
                else:
                    result.data[-1][0] += d[i]
        result.table_name = "Результаты ЕГЭ по учебному предмету по группам участников экзамена с различным уровнем подготовки юношей и девушек"
        
        self._tables.resultBySex = result
        
        return result
    
    async def getTable_resultByAreas(self, session: AsyncSession) -> TableStandart:
        """Формирует таблицу динамики результатов ЕГЭ в разрезе АТЕ региона
        
        Args:
            session (AsyncSession): Сессия для взаимодействия с БД
        
        Returns:
            TableStandart: Готовая таблица
        """
        if self._tables.resultByAreas is not None:
            return self._tables.resultByAreas
        
        data = await self._getTable_scoreRanges(
            session=session,
            group_by=[func.concat(Areas.code, " - ", Areas.name)],
            dop_col=func.count(Students.id),
            year_count=1,
            dop_joins=[
                (Students, Students.id == ExamResults.student_id),
                (Schools, Schools.code == Students.school_id),
                (Areas, Areas.code == Schools.area_id),
            ],
            dop_joins_for_cte=[
                (Students, Students.id == ExamResults.student_id),
                (Schools, Schools.code == Students.school_id),
                (Areas, Areas.code == Schools.area_id),
            ]
        )
        
        result = TableStandart(
            column_names=[
                "Наименование АТЕ",
                "Количество участников, чел.",
                "Доля участников, у которых полученный тестовый балл | ниже минимального",
                "Доля участников, у которых полученный тестовый балл | от минимального балла до 60 баллов",
                "Доля участников, у которых полученный тестовый балл | от 61 до 80 баллов",
                "Доля участников, у которых полученный тестовый балл | от 81 до 100 баллов",
            ]
        )
        for d in data:
            result.str_names.append(d[0])
            result.data.append([0]*5)
            for i in range(1, len(d)):
                if isinstance(d[i], Decimal):
                    result.data[-1][i] = float(d[i])
                else:
                    result.data[-1][0] += d[i]
        result.table_name = "Результаты ЕГЭ по учебному предмету по группам участников экзамена с различным уровнем подготовки в сравнении по АТЕ"
        
        self._tables.resultByAreas = result
        
        return result
    
    async def getTable_hightResults(self, session: AsyncSession) -> TableStandart:
        """Формирует таблицу динамики для топ 14 лучших школ
        
        Args:
            session (AsyncSession): Сессия для взаимодействия с БД
        
        Returns:
            TableStandart: Готовая таблица
        """
        if self._tables.hightResults is not None:
            return self._tables.hightResults
        
        all_students_count, only_last_res = self._getASC(
            dop_filters=[TestSchemes.subject_id == self.subject_id],
            year_count=1,
            group_by=[func.concat(Schools.code, " - ", Schools.short_name)],
            dop_joins=[
                (Students, Students.id == ExamResults.student_id),
                (Schools, Schools.code == Students.school_id),
            ],
        )
        
        query = (
            select(
                func.concat(Schools.code, " - ", Schools.short_name).label("str_names"),
                self._calculteProcent(func.sum(case((ExamResults.score == 2, 1), else_=0)), func.min(all_students_count.c.stud_count)).label("to_order_4"),
                self._calculteProcent(func.sum(case((and_(ExamResults.score != 2, ExamResults.final_points < 61), 1), else_=0)), func.min(all_students_count.c.stud_count)).label("to_order_3"),
                self._calculteProcent(func.sum(case((ExamResults.final_points.between(61, 80), 1), else_=0)), func.min(all_students_count.c.stud_count)).label("to_order_2"),
                self._calculteProcent(func.sum(case((ExamResults.final_points.between(81, 100), 1), else_=0)), func.min(all_students_count.c.stud_count)).label("to_order_1"),
                func.count(Students.id)
            ).select_from(ExamResults)
            .join(TestSchemes, TestSchemes.id == ExamResults.schema_id)
            .join(only_last_res, and_(only_last_res.c.exam_id == ExamResults.id, only_last_res.c.rn == 1))
            .join(Students, Students.id == ExamResults.student_id)
            .join(Schools, Schools.code == Students.school_id)
            .join(all_students_count, all_students_count.c[0] == func.concat(Schools.code, " - ", Schools.short_name))
            .group_by("str_names")
            .order_by(desc("to_order_1"), desc("to_order_2"), desc("to_order_3"), desc("to_order_4"))
            .limit(14)
        )
        
        query = await session.execute(query)
        data = query.all()
        
        result = TableStandart(
            column_names=[
                "Наименование АТЕ",
                "Количество участников, чел.",
                "Доля участников, у которых полученный тестовый балл | от 81 до 100 баллов",
                "Доля участников, у которых полученный тестовый балл | от 61 до 80 баллов",
                "Доля участников, у которых полученный тестовый балл | от минимального балла до 60 баллов",
                "Доля участников, у которых полученный тестовый балл | ниже минимального",
            ]
        )
        for d in data:
            result.str_names.append(d[0])
            result.data.append([0]*5)
            for i in range(1, len(d)):
                if isinstance(d[i], Decimal):
                    result.data[-1][-i] = float(d[i])
                else:
                    result.data[-1][0] += d[i]
        result.table_name = "Перечень ОО, продемонстрировавших наиболее высокие результаты ЕГЭ по предмету"
        
        self._tables.hightResults = result
        
        return result
    
    async def getTable_lowResults(self, session: AsyncSession) -> TableStandart:
        """Формирует таблицу динамики для топ 14 лучших школ
        
        Args:
            session (AsyncSession): Сессия для взаимодействия с БД
        
        Returns:
            TableStandart: Готовая таблица
        """
        if self._tables.lowResults is not None:
            return self._tables.lowResults
        
        all_students_count, only_last_res = self._getASC(
            dop_filters=[TestSchemes.subject_id == self.subject_id],
            year_count=1,
            group_by=[func.concat(Schools.code, " - ", Schools.short_name)],
            dop_joins=[
                (Students, Students.id == ExamResults.student_id),
                (Schools, Schools.code == Students.school_id),
            ],
        )
        
        query = (
            select(
                func.concat(Schools.code, " - ", Schools.short_name).label("str_names"),
                self._calculteProcent(func.sum(case((ExamResults.score == 2, 1), else_=0)), func.min(all_students_count.c.stud_count)).label("to_order_1"),
                self._calculteProcent(func.sum(case((and_(ExamResults.score != 2, ExamResults.final_points < 61), 1), else_=0)), func.min(all_students_count.c.stud_count)).label("to_order_2"),
                self._calculteProcent(func.sum(case((ExamResults.final_points.between(61, 80), 1), else_=0)), func.min(all_students_count.c.stud_count)).label("to_order_3"),
                self._calculteProcent(func.sum(case((ExamResults.final_points.between(81, 100), 1), else_=0)), func.min(all_students_count.c.stud_count)).label("to_order_4"),
                func.count(Students.id)
            ).select_from(ExamResults)
            .join(TestSchemes, TestSchemes.id == ExamResults.schema_id)
            .join(only_last_res, and_(only_last_res.c.exam_id == ExamResults.id, only_last_res.c.rn == 1))
            .join(Students, Students.id == ExamResults.student_id)
            .join(Schools, Schools.code == Students.school_id)
            .join(all_students_count, all_students_count.c[0] == func.concat(Schools.code, " - ", Schools.short_name))
            .group_by("str_names")
            .order_by(desc("to_order_1"), desc("to_order_2"), desc("to_order_3"), desc("to_order_4"))
            .limit(14)
        )
        
        query = await session.execute(query)
        data = query.all()
        
        result = TableStandart(
            column_names=[
                "Наименование АТЕ",
                "Количество участников, чел.",
                "Доля участников, у которых полученный тестовый балл | ниже минимального",
                "Доля участников, у которых полученный тестовый балл | от минимального балла до 60 баллов",
                "Доля участников, у которых полученный тестовый балл | от 61 до 80 баллов",
                "Доля участников, у которых полученный тестовый балл | от 81 до 100 баллов",
            ]
        )
        for d in data:
            result.str_names.append(d[0])
            result.data.append([0]*5)
            for i in range(1, len(d)):
                if isinstance(d[i], Decimal):
                    result.data[-1][i] = float(d[i])
                else:
                    result.data[-1][0] += d[i]
        result.table_name = "Перечень ОО, продемонстрировавших низкие результаты ЕГЭ по предмету"
        
        self._tables.lowResults = result
        
        return result