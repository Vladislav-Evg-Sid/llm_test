from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.storage.postgresql.request_for_section_one import RequestsForFirstSection
from app.storage.postgresql.request_for_section_two import RequestsForSecondSection
from app.schemas.text_reports import TableStandart


async def get_table_by_section(session: AsyncSession, section_num: int, table_num: int) -> TableStandart:  # TODO: Вводить код предмета и экзамена пользователем
    result = TableStandart(table_name="Not found section or table", column_names=[], str_names=[], data=[])
    match section_num:
        case 1:
            manager = RequestsForFirstSection(year=2025, exam_type_id=4, subject_id=2, start_date=datetime(2025, 5, 27), end_date=datetime(2025, 7, 4))
            match table_num:
                case 1:
                    result = await manager.getTable_count(session)
                case 2:
                    result = await manager.getTable_sex(session)
                case 3:
                    result = await manager.getTable_categories(session)
                case 4:
                    result = await manager.getTable_schoolKinds(session)
                case 5:
                    result = await manager.getTable_areas(session)
                case 0:
                    result = await manager.getTable_profBaseMat(session)
        case 2:
            manager = RequestsForSecondSection(year=2025, exam_type_id=4, subject_id=2, start_date="2024-05-27", end_date="2024-07-04")
            match table_num:
                case 1:
                    result = await manager.getTable_scoreDictribution(session)
                case 2:
                    result = await manager.getTable_resultDynamic(session)
                case 3:
                    result = await manager.getTable_resultByStudCat(session)
                case 4:
                    result = await manager.getTable_resultBySchoolKinds(session)
                case 5:
                    result = await manager.getTable_resultBySex(session)
                case 6:
                    result = await manager.getTable_resultByAreas(session)
                case 7:
                    result = await manager.getTable_hightResults(session)
                case 8:
                    result = await manager.getTable_lowResults(session)
    return result