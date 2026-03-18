from sqlalchemy.ext.asyncio import AsyncSession

from app.storage.postgresql.request_for_section_one import RequestsForFirstSection
from app.storage.postgresql.request_for_section_two import RequestsForSecondSection
from app.storage.postgresql.request_for_section_three import RequestsForThirdSection
from app.schemas.text_reports import TableStandart


async def get_table_by_section(session: AsyncSession, section_num: int, table_num: int, year: int, exam_type_id: int, subject_id: int) -> TableStandart:
    result = TableStandart(table_name="Not found section or table", column_names=[], str_names=[], data=[])
    match section_num:
        case 1:
            manager = RequestsForFirstSection(year=year, exam_type_id=exam_type_id, subject_id=subject_id)
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
            manager = RequestsForSecondSection(year=year, exam_type_id=exam_type_id, subject_id=subject_id)
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
        case 3:
            manager = RequestsForThirdSection(year=year, exam_type_id=exam_type_id, subject_id=subject_id)
            match table_num:
                case 1:
                    result = await manager.getTable_baseStatForSkills(session)
                case 2:
                    result = await manager.getTable_statForSkillsAccountingGrades(session)
    return result