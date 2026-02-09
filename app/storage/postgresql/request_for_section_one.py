from sqlalchemy import func, select, and_, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import *
from app.schemas.text_reports import TableStandart
from app.storage.postgresql.request_for_section_abc import RequestsForSections

class RequestsForFirstSection(RequestsForSections):
    def _addClassTables(self) -> None:
        """Создаёт коллекцию таблиц
        """
        self._tables.count = None
        self._tables.sex = None
        self._tables.categories = None
        self._tables.schoolKinds = None
        self._tables.areas = None
    
    async def getListOfTables(self, session: AsyncSession) -> list[TableStandart]:
        """Возвращает списко таблиц, требуемыз для генерации промта
        
        Args:
            session (AsyncSession): Сессия
        
        Returns:
            list[TableStandart]: Список таблиц
        """
        result = []
        tables = [
            self.getTable_count(session),
            self.getTable_sex(session),
            self.getTable_schoolKinds(session),
        ]
        
        if self.subject_id in (2, 22):
            tables.append(self.getTable_profBaseMat(session))
        
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
            data=[[""]*6]
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
            data=[[""]*7 for i in range(2)]
        )
        
        for a in data:
            ind_y = categories.index(a[0])
            ind_x = (a[1] - self.year - 1) * 2
            result.data[ind_y][0] = a[0]
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
            data=[[0]*7 for i in range(3)]
        )
        for i, cn in enumerate(category_names):
            result.data[i][0] = cn
        
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
                "№ п/п",
                "Категория участника",
                f"{self.year-2} г. | чел.",
                f"{self.year-2} г. | % от общего числа участников",
                f"{self.year-1} г. | чел.",
                f"{self.year-1} г. | % от общего числа участников",
                f"{self.year} г. | чел.",
                f"{self.year} г. | % от общего числа участников",
            ],
            data=[[0]*8 for i in range(len(data)//3)]
        )
        ind_x = 2
        ind_y = -1
        used_categories = set()
        for i in range(len(data)):
            if data[i][0] in used_categories:
                result.data[ind_y][ind_x] = data[i][2]
                result.data[ind_y][ind_x+1] = float(data[i][3])
                ind_x += 2
            else:
                ind_y += 1
                ind_x = 2
                used_categories.add(data[i][0])
                result.data[ind_y][0] = f"{ind_y+1}."
                result.data[ind_y][1] = data[i][0]
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
            .filter(
                TestSchemes.exam_year == self.year,
                TestSchemes.exam_type_id == self.exam_type_id,
                ExamResults.status_id == 6
            )
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
            .filter(
                TestSchemes.exam_year == self.year,
                TestSchemes.exam_type_id == self.exam_type_id,
                TestSchemes.subject_id == self.subject_id,
                ExamResults.status_id == 6
            )
            .group_by(Areas.code)
        )
        
        result = TableStandart(
            column_names=[
                "№ п/п",
                "Наименование АТЕ",
                "Количество участников ЕГЭ по учебному предмету",
                "% от общего числа участников в регионе",
            ]
        )
        for i, a in enumerate(query.all()):
            result.data.append([f"{i+1}.", a[0], a[1], float(a[2])])
        result.table_name = "Количество участников ЕГЭ по учебному предмету по АТЕ региона"
        
        self._tables.areas = result
        
        return result
    
    async def getTable_profBaseMat(self, session: AsyncSession) -> TableStandart:
        """Формирует таблицу для сравнения часточности выбора профильной и базовой математики за 3 года
        
        Args:
            session (AsyncSession): Сессия для взаимодействия с БД
        
        Returns:
            TableStandart: Готовая таблица
        """
        only_last_res = (
            select(
                ExamResults.id.label("exam_id"),
                func.row_number().over(
                    partition_by = [ExamResults.student_id, TestSchemes.exam_year],
                    order_by=ExamResults.exam_date.desc()
                ).label("rn")
            )
            .join(TestSchemes, ExamResults.schema_id == TestSchemes.id)
            .filter(
                TestSchemes.exam_year.between(self.year-3, self.year),
                TestSchemes.exam_type_id == self.exam_type_id,
                TestSchemes.subject_id.in_([2, 22]),
                ExamResults.status_id == 6
                # ExamResults.exam_date.between(self.start_date, self.end_date)
            )
        ).cte("only_last_res")
        
        all_students_count = (
            select(
                TestSchemes.exam_year,
                func.count(ExamResults.student_id).label("stud_count")
            )
            .join(TestSchemes, ExamResults.schema_id == TestSchemes.id)
            .join(only_last_res, and_(only_last_res.c.exam_id == ExamResults.id, only_last_res.c.rn == 1))
            .group_by(TestSchemes.exam_year)
        ).cte("all_students_count")
        
        query = await session.execute(
            select(
                TestSchemes.exam_year,
                self._calculteProcent(func.sum(case((TestSchemes.subject_id==2, 1), else_=0)), func.min(all_students_count.c.stud_count)),
                self._calculteProcent(func.sum(case((TestSchemes.subject_id==22, 1), else_=0)), func.min(all_students_count.c.stud_count))
            )
            .join(ExamResults, ExamResults.schema_id == TestSchemes.id)
            .join(only_last_res, and_(only_last_res.c.exam_id == ExamResults.id, only_last_res.c.rn == 1))
            .join(all_students_count, all_students_count.c.exam_year == TestSchemes.exam_year)
            .group_by(TestSchemes.exam_year)
            .order_by(TestSchemes.exam_year)
        )
        
        result = TableStandart(
            column_names=[
                "Год экзамена",
                "Процент выбора профильной математики в году",
                "Процент выбора базовой математики в году",
            ]
        )
        for a in query.all():
            result.data.append([a[0], float(a[1]), float(a[2])])
        result.table_name = "Распределение базовой и профильной метематики"
        
        self._tables.areas = result
        
        return result
