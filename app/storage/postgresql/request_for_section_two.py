from sqlalchemy import func, select, and_, case, desc, Column
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import ColumnElement
from decimal import Decimal

from app.models.models import *
from app.schemas.text_reports import *
from app.storage.postgresql.request_for_section_abc import RequestsForSections


class RequestsForSecondSection(RequestsForSections):
    def _addClassTables(self):
        """Создаёт коллекцию таблиц
        """
        self._tables.scoreDictribution = None
        self._tables.resultDynamic = None
        self._tables.resultByStudCat = None
        self._tables.resultBySchoolTypes = None
        self._tables.resultBySex = None
        self._tables.resultByAreas = None
        self._tables.hightResults = None
        self._tables.lowResults = None
    
    async def getListOfTables(self, session: AsyncSession) -> list[TableStandart]:
        """Возвращает списко таблиц, требуемыз для генерации промта
        
        Args:
            session (AsyncSession): Сессия
        
        Returns:
            list[TableStandart]: Список таблиц
        """
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
            result.data.append([data[0], data[1]])
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
        query = query.join(all_students_count, and_(*conditions))
        
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
        
        category_names = [
            "ниже минимального балла, %",
            "от минимального балла до 60 баллов, %",
            "от 61 до 80 баллов, %",
            "от 81 до 100 баллов, %",
            "Средний тестовый балл",
        ]
        
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
            data = [[""]*4 for i in range(5)]
        )
        
        for i in range(len(data)):
            for j in range(1, len(data[i])):
                result.data[j-1][0] = category_names[j-1]
                result.data[j-1][i+1] = float(data[i][j])
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
        category_names = ["ВТГ, обучающихся по программам СОО", "ВТГ, обучающихся по программам СПО", "ВПЛ", "Участники экзамена с ОВЗ"]
        
        data = await self._getTable_scoreRanges(
            session=session,
            group_by=[Students.is_ovz, Students.category_id],
            dop_col=func.count(Students.id),
            year_count=1,
            dop_joins=[(Students, Students.id == ExamResults.student_id)],
            dop_joins_for_cte=[(Students, Students.id == ExamResults.student_id)],
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
            data=[[0]*6 for i in range(5)]
        )
        for d in data:
            if d[0]:
                for i in range(2, len(d)):
                    if isinstance(d[i], Decimal):
                        result.data[-1][i] = float(d[i])
                    else:
                        result.data[-1][1] += d[i]
            else:
                for c in range(len(categories)):
                    if categories[c] == d[1]:
                        for i in range(2, len(d)):
                            if isinstance(d[i], Decimal):
                                print(">>>", len(result.data[c]), i)
                                result.data[c][i] += float(d[i])
                            else:
                                result.data[c][1] += d[i]
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
            result.data.append([0]*6)
            result.data[-1][0] = d[0]
            for i in range(1, len(d)):
                if isinstance(d[i], Decimal):
                    result.data[-1][i+1] = float(d[i])
                else:
                    result.data[-1][1] += d[i]
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
            result.data.append([0]*6)
            result.data[-1][0] = "женский" if d[0] else "мужской"
            for i in range(1, len(d)):
                if isinstance(d[i], Decimal):
                    result.data[-1][i+1] = float(d[i])
                else:
                    result.data[-1][1] += d[i]
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
            result.data.append([0]*6)
            result.data[-1][0] = d[0]
            for i in range(1, len(d)):
                if isinstance(d[i], Decimal):
                    result.data[-1][i+1] = float(d[i])
                else:
                    result.data[-1][1] += d[i]
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
            result.data.append([0]*6)
            result.data[-1][0] = d[0]
            for i in range(1, len(d)):
                if isinstance(d[i], Decimal):
                    result.data[-1][-i+1] = float(d[i])
                else:
                    result.data[-1][1] += d[i]
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
            result.data.append([0]*6)
            result.data[-1][0] = d[0]
            for i in range(1, len(d)):
                if isinstance(d[i], Decimal):
                    result.data[-1][i+1] = float(d[i])
                else:
                    result.data[-1][1] += d[i]
        result.table_name = "Перечень ОО, продемонстрировавших низкие результаты ЕГЭ по предмету"
        
        self._tables.lowResults = result
        
        return result