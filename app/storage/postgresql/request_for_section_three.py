from sqlalchemy import func, select, and_, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import *
from app.schemas.text_reports import TableStandart
from app.storage.postgresql.request_for_section_abc import RequestsForSections
from app.utils.debug.print_orm_query import print_SQL_by_ORM

class RequestsForThirdSection(RequestsForSections):
    def _addClassTables(self) -> None:
        """Создаёт коллекцию таблиц
        """ # TODO: Дописать остальные таблицы
        self._tables.baseStatAllSkills = None
    
    async def getListOfTables(self, session: AsyncSession) -> list[TableStandart]:
        """Возвращает списко таблиц, требуемыз для генерации промта
        
        Args:
            session (AsyncSession): Сессия
        
        Returns:
            list[TableStandart]: Список таблиц
        """
        result = [] # TODO: Дописать
        
        return result
    
    async def getTable_baseStatAllSkills(self, session: AsyncSession) -> TableStandart:
        """Формирует таблицу Основных статистических характеристик выполнения заданий
        
        Args:
            session (AsyncSession): Сессия для взаимодействия с БД
        
        Returns:
            TableStandart: Итоговая таблица
        """
        if self._tables.baseStatAllSkills is not None:
            return self._tables.baseStatAllSkills
        
        all_students_count, only_last_res = self._getASC()
        
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
            .filter(TestSchemes.exam_year == self.year)
            .filter(TestSchemes.exam_type_id == self.exam_type_id)
            .filter(TestSchemes.subject_id == self.subject_id)
            .group_by(WorkPlans.task_number, WorkPlans.skill)
            .order_by(WorkPlans.task_number)
        )
        print_SQL_by_ORM(query)
        
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
        
        self._tables.baseStatAllSkills = result
        
        return result