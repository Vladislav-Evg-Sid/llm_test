from sqlalchemy import func, select, and_, or_, case, MetaData, types, desc, asc, Numeric, any_, not_, text, Table, Column, Select
from sqlalchemy.engine import Row
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, InstrumentedAttribute
from sqlalchemy.sql.expression import ColumnElement
from db.models import *

from py_models import *


class RequestsForFirstSection:
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

    def _calculteProcent(self, part: ColumnElement | InstrumentedAttribute | Column, all: ColumnElement | InstrumentedAttribute | Column, rounding: int = 1) -> ColumnElement:
        """Получаем процент от числа

        Args:
            part (ColumnElement | InstrumentedAttribute | Column): Столбец с долей
            all (ColumnElement | InstrumentedAttribute | Column): Столбец со всеми значениями
            rounding (int, optional): Количество знаков после запятой. Defaults to 1.

        Returns:
            ColumnElement: Итоговый столбец
        """
        return func.cast(100.0 * func.nullif(part, 0) / all, Numeric(3, rounding))
    
    async def getTable_count(self, session: AsyncSession) -> Table_1_1:
        """Формирует таблицу количества участников за текущий год и 2 предыдущих

        Args:
            session (AsyncSession): Сессия для взаимодействия с БД

        Returns:
            table_1_1: Итоговая таблица
        """
        all_students_count = (
            select(
                TestSchemes.exam_year.label("year"),
                func.count(ExamResults.student_id.distinct()).label("stud_count")
            ).join(TestSchemes, ExamResults.schema_id == TestSchemes.id)
            .filter(TestSchemes.exam_year.between(self.year-2, self.year))
            .filter(TestSchemes.exam_type_id == self.exam_type_id)
            # .filter(ExamResults.exam_date.between(self.start_date, self.end_date))
            .group_by(TestSchemes.exam_year)
        ).cte("all_students_count")
        
        subjects_students_count = (
            select(
                TestSchemes.exam_year.label("year"),
                func.count(ExamResults.student_id.distinct()).label("stud_count")
            ).join(TestSchemes, TestSchemes.id == ExamResults.schema_id)
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
            .join(all_students_count, all_students_count.c.year == subjects_students_count.c.year)
        )
        
        result = Table_1_1()
        for a in query.all():
            result.years.append(a[0])
            result.counts.append(a[1])
            result.procents.append(a[2])
        
        return result

    async def getTable_sex(self, session: AsyncSession) -> Table_1_2:
        """Формирует таблицу гендерного распределения участников по 3 годам

        Args:
            session (AsyncSession): Сессия для взаимодействия с БД

        Returns:
            table_1_2: Итоговая таблица
        """
        all_students_count = (
            select(
                TestSchemes.exam_year.label("year"),
                func.count(ExamResults.student_id.distinct()).label("stud_count")
            ).join(TestSchemes, ExamResults.schema_id == TestSchemes.id)
            .filter(TestSchemes.exam_year.between(self.year-2, self.year))
            .filter(TestSchemes.exam_type_id == self.exam_type_id)
            # .filter(ExamResults.exam_date.between(self.start_date, self.end_date))
            .group_by(TestSchemes.exam_year)
        ).cte("all_students_count")
        
        subjects_students_count = (
            select(
                Students.sex.label("sex"),
                TestSchemes.exam_year.label("year"),
                func.count(ExamResults.student_id.distinct()).label("stud_count")
            ).join(TestSchemes, TestSchemes.id == ExamResults.schema_id)
            .join(Students, Students.id == ExamResults.student_id)
            .filter(TestSchemes.exam_year.between(self.year-2, self.year))
            .filter(TestSchemes.exam_type_id == self.exam_type_id)
            .filter(TestSchemes.subject_id == self.subject_id)
            .group_by(Students.sex)
            .group_by(TestSchemes.exam_year)
        ).cte("subjects_students_count")
        
        query = await session.execute(
            select(
                case((subjects_students_count.c.sex, "Женский"), else_ = "Мужской"),
                subjects_students_count.c.year,
                subjects_students_count.c.stud_count,
                self._calculteProcent(subjects_students_count.c.stud_count, all_students_count.c.stud_count)
            ).select_from(subjects_students_count)
            .join(all_students_count, all_students_count.c.year == subjects_students_count.c.year)
        )
        
        result = Table_1_2()
        for a in query.all():
            if not a[0] in result.category:
                result.category.append(a[0])
            temp = (a[1], a[2], float(a[3]))
            if a[1] == self.year - 2:
                result.col_1.append(temp)
            elif a[1] == self.year - 1:
                result.col_2.append(temp)
            elif a[1] == self.year:
                result.col_3.append(temp)
        
        return result

    async def getTable_categories(self, session: AsyncSession) -> Table_1_2:
        """Формирует таблицу по категориям участников

        Args:
            session (AsyncSession): Сессия для взаимодействия с БД

        Returns:
            Table_1_2: Таблица данных
        """
        categories = [1, 3, 4]
        category_names: list[str] = ["ВТГ, обучающихся по программам СОО", "ВТГ, обучающихся по программам СПО", "ВПЛ"]
        all_students_count = (
            select(
                TestSchemes.exam_year.label("year"),
                func.count(ExamResults.student_id.distinct()).label("stud_count")
            ).join(TestSchemes, ExamResults.schema_id == TestSchemes.id)
            .filter(TestSchemes.exam_year.between(self.year-2, self.year))
            .filter(TestSchemes.exam_type_id == self.exam_type_id)
            # .filter(ExamResults.exam_date.between(self.start_date, self.end_date))
            .group_by(TestSchemes.exam_year)
        ).cte("all_students_count")
        
        subjects_students_count = (
            select(
                Students.category_id.label("category_id"),
                TestSchemes.exam_year.label("year"),
                func.count(ExamResults.student_id.distinct()).label("stud_count")
            ).join(TestSchemes, TestSchemes.id == ExamResults.schema_id)
            .join(Students, Students.id == ExamResults.student_id)
            .filter(TestSchemes.exam_year.between(self.year-2, self.year))
            .filter(TestSchemes.exam_type_id == self.exam_type_id)
            .filter(TestSchemes.subject_id == self.subject_id)
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
            .join(all_students_count, all_students_count.c.year == subjects_students_count.c.year)
        )
        
        result = Table_1_2()
        result.category = category_names
        for i in range(len(categories)):
            result.col_1.append([self.year - 2, 0, 0])
            result.col_2.append([self.year - 1, 0, 0])
            result.col_3.append([self.year, 0, 0])
        
        for a in query.all():
            str_num = None
            for i in range(len(categories)):
                if a[0] == categories[i]:
                    str_num = i
                    break
            if str_num is None: continue
            if a[1] == self.year - 2:
                result.col_1[str_num] = (result.col_1[str_num][0], a[2], float(a[3]))
            if a[1] == self.year - 1:
                result.col_2[str_num] = (result.col_2[str_num][0], a[2], float(a[3]))
            if a[1] == self.year:
                result.col_3[str_num] = (result.col_3[str_num][0], a[2], float(a[3]))
        
        return result

    async def getTable_schoolKinds(self, session: AsyncSession) -> Table_1_2:
        """Формирует таблицу по видом ОО

        Args:
            session (AsyncSession): Сессия для взаимодействия с БД

        Returns:
            Table_1_2: Таблица данных
        """
        all_students_count = (
            select(
                TestSchemes.exam_year.label("year"),
                func.count(ExamResults.student_id.distinct()).label("stud_count")
            ).join(TestSchemes, ExamResults.schema_id == TestSchemes.id)
            .filter(TestSchemes.exam_year.between(self.year-2, self.year))
            .filter(TestSchemes.exam_type_id == self.exam_type_id)
            # .filter(ExamResults.exam_date.between(self.start_date, self.end_date))
            .group_by(TestSchemes.exam_year)
        ).cte("all_students_count")
        
        subjects_students_count = (
            select(
                SchoolKinds.name.label("school_kind"),
                TestSchemes.exam_year.label("year"),
                func.count(ExamResults.student_id.distinct()).label("stud_count")
            ).join(TestSchemes, TestSchemes.id == ExamResults.schema_id)
            .join(Students, Students.id == ExamResults.student_id)
            .join(Schools, Schools.code == Students.school_id)
            .join(SchoolKinds, SchoolKinds.code == Schools.kind_code)
            .filter(TestSchemes.exam_year.between(self.year-2, self.year))
            .filter(TestSchemes.exam_type_id == self.exam_type_id)
            .filter(TestSchemes.subject_id == self.subject_id)
            .group_by(SchoolKinds.name)
            .group_by(TestSchemes.exam_year)
        ).cte("subjects_students_count")
        
        query = await session.execute(
            select(
                subjects_students_count.c.school_kind,
                subjects_students_count.c.year,
                subjects_students_count.c.stud_count,
                self._calculteProcent(subjects_students_count.c.stud_count, all_students_count.c.stud_count)
            ).select_from(subjects_students_count)
            .join(all_students_count, all_students_count.c.year == subjects_students_count.c.year)
        )
        
        result = Table_1_2()
        for a in query.all():
            if not a[0] in result.category:
                result.category.append(a[0])
            temp = (a[1], a[2], float(a[3]))
            if a[1] == self.year - 2:
                result.col_1.append(temp)
            elif a[1] == self.year - 1:
                result.col_2.append(temp)
            elif a[1] == self.year:
                result.col_3.append(temp)
        
        return result


    async def getTable_areas(self, session: AsyncSession) -> Table_1_5:
        """Формирует таблицу по АТЕ региона

        Args:
            session (AsyncSession): Сессия для взаимодействия с БД

        Returns:
            Table_1_5: Итоговая таблица
        """
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
        
        result = Table_1_5()
        for a in query.all():
            result.areas.append(a[0])
            result.counts.append(a[1])
            result.procents.append(a[2])
        
        return result