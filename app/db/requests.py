from sqlalchemy import func, select, and_, or_, case, MetaData, types, desc, asc, Numeric, any_, not_, text, Table, Column, Select, distinct, between
from sqlalchemy.engine import Row
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased
from models import *


class RequestsForFirstSection:
    def __init__(self, year: int):
        self.year = year
    
    def getTable_count(self):
        cte_query = (
            select(
                TestSchemes.exam_year,
                func.count(distinct(ExamResults.student_id))
            ).join(ExamResults, ExamResults.schema_id == TestSchemes.id)
            .filter(between(self.year-2, self.year))
            .group_by(TestSchemes.exam_year)
        )
        #############################################
        print('*'*100)###############################
        compiled = cte_query.compile(####################
            dialect=postgresql.dialect(),############
            compile_kwargs={"literal_binds": True}###
        )############################################
        print(str(compiled))#########################
        print('='*100)###############################
        #############################################


def requestTesting():
    ins = RequestsForFirstSection(2025)
    ins.getTable_count()


if __name__ == "__main__":
    requestTesting()