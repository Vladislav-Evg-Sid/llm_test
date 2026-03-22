from sqlalchemy import Select
from sqlalchemy.dialects import postgresql


def print_SQL_by_ORM(query: Select):
        print('*'*100)
        compiled = query.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True}
        )
        print(str(compiled))
        print('='*100)