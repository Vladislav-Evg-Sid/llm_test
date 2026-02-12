from sqlalchemy import func, select, and_, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import *
from app.schemas.text_reports import TableStandart
from app.storage.postgresql.request_for_section_abc import RequestsForSections
from app.utils.debug.print_orm_query import print_SQL_by_ORM


class RequestsForThirdSection(RequestsForSections):
    def _addClassTables(self) -> None:
        """Создаёт коллекцию таблиц
        """ # TODO: Дописать таблицы, которые можно переиспользовать
    
    async def getListOfTables(self, session: AsyncSession) -> list[TableStandart]:
        """Возвращает списко таблиц, требуемыз для генерации промта
        
        Args:
            session (AsyncSession): Сессия
        
        Returns:
            list[TableStandart]: Список таблиц
        """
        result = [] # TODO: Дописать
        
        return result
    
    async def getTable_baseStatForSkills(self, session: AsyncSession, difficulty_levels: list[int] = [1, 2, 3]) -> TableStandart:
        """Формирует таблицу основных статистических характеристик выполнения заданий
        
        Args:
            session (AsyncSession): Сессия для взаимодействия с БД
            difficulty_levels (list[int], optional): Учитываемые уровни сложности. По умолчанию: все
        
        Returns:
            TableStandart: Итоговая таблица
        """
        all_students_count, only_last_res = self._getASC(year_count=1)
        
        query = (
            select(
                WorkPlans.task_number,
                WorkPlans.skill,
                func.min(Difficuelties.code),
                self._calculteProcent(func.sum(Answers.current_point), func.max(WorkPlans.max_points) * func.min(all_students_count.c.stud_count)),
                self._calculteProcent(func.sum(case((ExamResults.score == 2, 1), else_=0)), func.min(all_students_count.c.stud_count)),
                self._calculteProcent(func.sum(case((and_(ExamResults.score != 2, ExamResults.final_points < 61), 1), else_=0)), func.min(all_students_count.c.stud_count)),
                self._calculteProcent(func.sum(case((ExamResults.final_points.between(61, 80), 1), else_=0)), func.min(all_students_count.c.stud_count)),
                self._calculteProcent(func.sum(case((ExamResults.final_points.between(81, 100), 1), else_=0)), func.min(all_students_count.c.stud_count))
            ).join(TestSchemes, TestSchemes.id == WorkPlans.schema_id)
            .join(ExamResults, ExamResults.schema_id == TestSchemes.id)
            .join(Difficuelties, Difficuelties.id == WorkPlans.difficulty_id)
            .join(Answers, and_(Answers.exam_id == ExamResults.id, Answers.task_number_in_part == WorkPlans.task_number_in_part, Answers.part == WorkPlans.part))
            .join(only_last_res, and_(only_last_res.c.exam_id == ExamResults.id, only_last_res.c.rn == 1))
            .join(all_students_count, all_students_count.c.exam_year == TestSchemes.exam_year)
            .filter(
                WorkPlans.difficulty_id.in_(difficulty_levels)
            )
            .group_by(WorkPlans.task_number, WorkPlans.skill)
            .order_by(WorkPlans.task_number)
        ) # TODO: В номере задания должны быть и критерии. Можно использовать конкатенацию и парсить при заполнении. Придумай чё-нить
        
        query = await session.execute(query)
        data = query.all()
        
        result = TableStandart(
            column_names=[
                "Номер задания в КИМ",
                "Проверяемые элементы содержания/умения",
                "Уровень сложности задания",
                "Процент выполнения задания в субъекте Российской Федерации в группах участников экзамена с разными уровнями подготовки | средний",
                "Процент выполнения задания в субъекте Российской Федерации в группах участников экзамена с разными уровнями подготовки | в группе не преодолевших минимальный балл",
                "Процент выполнения задания в субъекте Российской Федерации в группах участников экзамена с разными уровнями подготовки | в группе от минимального до 60 т.б.",
                "Процент выполнения задания в субъекте Российской Федерации в группах участников экзамена с разными уровнями подготовки | в группе от 61 до 80 т.б.",
                "Процент выполнения задания в субъекте Российской Федерации в группах участников экзамена с разными уровнями подготовки | в группе от 81 до 100 т.б."
            ],
            data=[]
        )
        
        for d in data:
            result.data.append([None]*8)
            for i in range(len(d)):
                if isinstance(d[i], float):
                    result.data[-1][i] = float(d[i])
                else:
                    result.data[-1][i] = d[i]
        result.table_name = "Основные статистические характеристики выполнения заданий КИМ"
        
        return result
    
    async def getTable_statForSkillsAccountingGrades(self, session: AsyncSession, difficulty_levels: list[int] = [1, 2, 3]) -> TableStandart:
        """Формирует таблицу статистических характеристик заданий по количеству полученных баллов
        
        Args:
            session (AsyncSession): Сессия для взаимодействия с БД
            difficulty_levels (list[int], optional): Учитываемые уровни сложности. По умолчанию: все
        
        Returns:
            TableStandart: Итоговая таблица
        """
        all_students_count, only_last_res = self._getASC(year_count=1)
        
        getted_balls = (
            select(
                WorkPlans.task_number,
                WorkPlans.criterion,
                func.generate_series(0, WorkPlans.max_points).label("mark")
            )
            .join(TestSchemes, TestSchemes.id == WorkPlans.schema_id)
            .filter(
                WorkPlans.difficulty_id.in_(difficulty_levels),
            )
        ).cte("getted_balls")
        
        query = (
            select(
                func.concat(WorkPlans.task_number, "-", WorkPlans.criterion),
                getted_balls.c.mark,
                self._calculteProcent(func.sum(case((ExamResults.score == 2, 1), else_=0)), func.min(all_students_count.c.stud_count)),
                self._calculteProcent(func.sum(case((and_(ExamResults.score != 2, ExamResults.final_points < 61), 1), else_=0)), func.min(all_students_count.c.stud_count)),
                self._calculteProcent(func.sum(case((ExamResults.final_points.between(61, 80), 1), else_=0)), func.min(all_students_count.c.stud_count)),
                self._calculteProcent(func.sum(case((ExamResults.final_points.between(81, 100), 1), else_=0)), func.min(all_students_count.c.stud_count))
            ).join(TestSchemes, TestSchemes.id == WorkPlans.schema_id)
            .join(ExamResults, ExamResults.schema_id == TestSchemes.id)
            .join(Difficuelties, Difficuelties.id == WorkPlans.difficulty_id)
            .join(Answers, and_(Answers.exam_id == ExamResults.id, Answers.task_number_in_part == WorkPlans.task_number_in_part, Answers.part == WorkPlans.part))
            .join(only_last_res, and_(only_last_res.c.exam_id == ExamResults.id, only_last_res.c.rn == 1))
            .join(getted_balls, and_(getted_balls.c.task_number == WorkPlans.task_number, getted_balls.c.criterion == WorkPlans.criterion))
            .group_by(WorkPlans.task_number, WorkPlans.criterion, getted_balls.c.mark)
            .order_by(WorkPlans.task_number, WorkPlans.criterion, getted_balls.c.mark)
        ) # TODO: В номере задания должны быть и критерии. Можно использовать конкатенацию и парсить при заполнении. Придумай чё-нить
        print_SQL_by_ORM(query)
        
        query = await session.execute(query)
        data = query.all()
        
        result = TableStandart(
            column_names=[
                "Номер задания в КИМ",
                "Количество полученных первичных баллов",
                "Процент участников экзамена в субъекте Российской Федерации, получивших соответствующий первичный балл за выполнения задания в группах участников экзамена с разными уровнями подготовки | в группе не преодолевших минимальный балл",
                "Процент участников экзамена в субъекте Российской Федерации, получивших соответствующий первичный балл за выполнения задания в группах участников экзамена с разными уровнями подготовки | в группе от минимального до 60 т.б.",
                "Процент участников экзамена в субъекте Российской Федерации, получивших соответствующий первичный балл за выполнения задания в группах участников экзамена с разными уровнями подготовки | в группе от 61 до 80 т.б.",
                "Процент участников экзамена в субъекте Российской Федерации, получивших соответствующий первичный балл за выполнения задания в группах участников экзамена с разными уровнями подготовки | в группе от 81 до 100 т.б."
            ],
            data=[]
        )
        
        for d in data:
            result.data.append([None]*6)
            for i in range(len(d)):
                if isinstance(d[i], float):
                    result.data[-1][i] = float(d[i])
                else:
                    result.data[-1][i] = d[i]
        result.table_name = "Основные статистические характеристики выполнения заданий КИМ по полученным баллам"
        
        return result