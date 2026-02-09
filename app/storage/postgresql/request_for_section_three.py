from sqlalchemy import func, select, and_, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import *
from app.schemas.text_reports import *
from app.storage.postgresql.request_for_section_abc import RequestsForSections

class RequestsForThirdSection(RequestsForSections):
    def _addClassTables(self) -> None:
        """Создаёт коллекцию таблиц
        """
        self._tables.allSkills = None
    
    async def getListOfTables(self, session: AsyncSession) -> list[TableStandart]:
        """Возвращает списко таблиц, требуемыз для генерации промта
        
        Args:
            session (AsyncSession): Сессия
        
        Returns:
            list[TableStandart]: Список таблиц
        """
        result = []
        
        return result
    
    async def getTable_allSkills(self, session: AsyncSession) -> TableStandart:
        """Формирует таблицу Основных статистических характеристик выполнения заданий
        
        Args:
            session (AsyncSession): Сессия для взаимодействия с БД
        
        Returns:
            TableStandart: Итоговая таблица
        """
        if self._tables.allSkills is not None:
            return self._tables.allSkills
        
        all_students_count, only_last_res = self._getASC()
        
        query = (
            select(
                WorkPlans.skill,
                func.min(Difficuelties.code)
            ).join(TestSchemes, TestSchemes.id == WorkPlans.schema_id)
            .join(ExamResults, ExamResults.schema_id == TestSchemes.id)
            .join(Difficuelties, Difficuelties.id == WorkPlans.difficulty_id)
            .join(Answers, and_(Answers.result_id == ExamResults.id, Answers.task_number_in_part == WorkPlans.task_number_in_part, Answers.part == WorkPlans.part))
            .join(only_last_res, and_(only_last_res.c.exam_id == ExamResults.id, only_last_res.c.rn == 1))
            .filter(TestSchemes.exam_year == self.year)
            .filter(TestSchemes.exam_type_id == self.exam_type_id)
            .filter(TestSchemes.subject_id == self.subject_id)
            .group_by(WorkPlans.task_number, WorkPlans.skill)
            .order_by(WorkPlans.task_number)
        ) # TODO: Доделать запрос, переделать всё с этого момента
        
        data = query.all()
        
        result = TableStandart(
            column_names=[
                "",
                "Номер задания в КИМ",
                "Проверяемые элементы содержания/умения",
                "Процент выполнения задания в субъекте Российской Федерации в группах участников экзамена с разными уровнями подготовки | средний",
                "Процент выполнения задания в субъекте Российской Федерации в группах участников экзамена с разными уровнями подготовки | в группе не преодолевших минимальный балл",
                "Процент выполнения задания в субъекте Российской Федерации в группах участников экзамена с разными уровнями подготовки | в группе от минимального до 60 т.б.",
                "Процент выполнения задания в субъекте Российской Федерации в группах участников экзамена с разными уровнями подготовки | в группе от 61 до 80 т.б.",
                "Процент выполнения задания в субъекте Российской Федерации в группах участников экзамена с разными уровнями подготовки | в группе от 81 до 100 т.б."
            ],
            str_names=[""],
            data=[[0]*6]
        )
        
        for i in range(len(data)):
            result.data[0][i*2] = data[i][1]
            result.data[0][i*2+1] = float(data[i][2])
        result.table_name = "Основные статистические характеристики выполнения заданий КИМ"
        
        self._tables.count = result
        
        return result