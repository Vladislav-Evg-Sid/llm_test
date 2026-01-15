from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy import String, SmallInteger, TIMESTAMP, ForeignKey, Integer, Text, Boolean, JSON, Date, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

import uuid
from datetime import date, datetime
from app.db.base import Base

from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTableUUID

# Models for the application, defining the database schema using SQLAlchemy ORM
class StudentCategories(Base):
    __tablename__ = 'student_categories'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    description: Mapped[str] = mapped_column(String(127), nullable=False)

    students: Mapped[list["Students"]] = relationship("Students", back_populates="category")


class Students(Base):
    __tablename__ = 'students'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=func.gen_random_uuid(), server_default="gen_random_uuid()")
    base_code: Mapped[str] = mapped_column(String(7), nullable=True)
    stud_code: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    school_id: Mapped[int] = mapped_column(ForeignKey('schools.code', name="student-school"), nullable=False)
    category_id: Mapped[int] = mapped_column(ForeignKey('student_categories.id', name="student-category"), nullable=True)
    person_code: Mapped[str] = mapped_column(UUID(as_uuid=True), nullable=False)
    class_name: Mapped[str] = mapped_column('class', String(5), nullable=False)
    is_ovz: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, server_default='false')
    is_medalist: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, server_default='false')
    is_admit: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, server_default='true')
    sex: Mapped[bool] = mapped_column(Boolean, nullable=False)
    has_attestat: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, server_default='false')

    school: Mapped['Schools'] = relationship('Schools', back_populates='students')
    category: Mapped["StudentCategories"] = relationship("StudentCategories", back_populates="students")
    planned_exams: Mapped[list['PlannedExams']] = relationship('PlannedExams', back_populates='student')
    exam_results: Mapped[list['ExamResults']] = relationship('ExamResults', back_populates='student')
    
    __table_args__ = (
        UniqueConstraint("base_code", "stud_code", name='uniq_students'),
    )


class ExamResultStatus(Base):
    __tablename__ = 'exam_result_status'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    description: Mapped[str] = mapped_column(String(150), nullable=False)
    add_to_report: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, server_default='false')

    exam_results: Mapped[list['ExamResults']] = relationship('ExamResults', back_populates='status')


class PlannedExams(Base):
    __tablename__ = 'planned_exams'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, nullable=False)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('students.id', name="plannedExams-students"), nullable=False)
    schema_id: Mapped[int] = mapped_column(ForeignKey('test_schemes.id', name="plannedExams-testSchemes"), nullable=False)

    student: Mapped['Students'] = relationship('Students', back_populates='planned_exams')
    schema: Mapped['TestSchemes'] = relationship('TestSchemes', back_populates='planned_exams')
    
    __table_args__ = (
        UniqueConstraint("student_id", "schema_id", name='uniq_plannedexams'),
    )


class ExamResults(Base):
    __tablename__ = 'exam_results'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=func.gen_random_uuid(), server_default="gen_random_uuid()")
    base_code: Mapped[str] = mapped_column(String(7), nullable=False)
    exam_code: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    first_points: Mapped[SmallInteger] = mapped_column(SmallInteger, nullable=True)
    final_points: Mapped[SmallInteger] = mapped_column(SmallInteger, nullable=True)
    completion_percents: Mapped[SmallInteger] = mapped_column(SmallInteger, nullable=True)
    score: Mapped[SmallInteger] = mapped_column(SmallInteger, nullable=True)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('students.id', name="examResult-student"), nullable=False)
    schema_id: Mapped[int] = mapped_column(ForeignKey('test_schemes.id', name="examResult-testSchemes"), nullable=False)
    status_id: Mapped[int] = mapped_column(ForeignKey('exam_result_status.id', name="examResult-status"), nullable=False)
    auditorium: Mapped[str] = mapped_column(String(4), nullable=True)
    exam_date: Mapped[date] = mapped_column(Date, nullable=False)
    ppe_code: Mapped[str] = mapped_column(String(6), nullable=False)
    variant: Mapped[int] = mapped_column(Integer, nullable=False)

    test_scheme: Mapped['TestSchemes'] = relationship('TestSchemes', back_populates='exam_results')
    student: Mapped['Students'] = relationship('Students', back_populates='exam_results')
    status: Mapped['ExamResultStatus'] = relationship('ExamResultStatus', back_populates='exam_results')
    answers: Mapped[list['Answers']] = relationship('Answers', back_populates='exam_result')
    
    __table_args__ = (
        UniqueConstraint("base_code", "exam_code", name='uniq_examRes'),
    )


class Answers(Base):
    __tablename__ = 'answers'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=func.gen_random_uuid(), server_default="gen_random_uuid()")
    exam_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('exam_results.id', name="answers-examResult"), nullable=False)
    current_point: Mapped[SmallInteger] = mapped_column(SmallInteger, nullable=False)
    task_number_in_part: Mapped[SmallInteger] = mapped_column(SmallInteger, nullable=False)
    part: Mapped[SmallInteger] = mapped_column(SmallInteger, nullable=False)

    exam_result: Mapped['ExamResults'] = relationship('ExamResults', back_populates='answers')
    
    __table_args__ = (
        UniqueConstraint("exam_id", "part", "task_number_in_part", name='uniq_answers'),
    )


class Areas(Base):
    __tablename__ = 'areas'

    code: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(127), nullable=False)

    users: Mapped[list['User']] = relationship("User", back_populates="area")
    schools: Mapped[list['Schools']] = relationship('Schools', back_populates='area')


class SchoolKinds(Base):
    __tablename__ = 'school_kinds'

    code: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)

    schools: Mapped[list['Schools']] = relationship('Schools', back_populates='kind')


class SchoolProperties(Base):
    __tablename__ = 'school_properties'

    code: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    
    schools: Mapped[list['Schools']] = relationship('Schools', back_populates='property')


class TownTypes(Base):
    __tablename__ = 'town_types'

    code: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    schools: Mapped[list['Schools']] = relationship('Schools', back_populates='town_type')


class Schools(Base):
    __tablename__ = 'schools'

    code: Mapped[int] = mapped_column(Integer, primary_key=True)
    vpr_code: Mapped[int] = mapped_column(Integer, nullable=True)
    law_address: Mapped[str] = mapped_column(String(150), nullable=False)
    short_name: Mapped[str] = mapped_column(String(150), nullable=False)
    kind_code: Mapped[int] = mapped_column(ForeignKey('school_kinds.code', name="school-kind"), nullable=False)
    area_id: Mapped[int] = mapped_column(ForeignKey('areas.code', name="school-area"), nullable=False)
    property_id: Mapped[int] = mapped_column(ForeignKey('school_properties.code', name="school-property"), nullable=False)
    town_type_id: Mapped[int] = mapped_column(ForeignKey('town_types.code', name="school-townType"), nullable=False)

    kind: Mapped['SchoolKinds'] = relationship('SchoolKinds', back_populates='schools')
    area: Mapped['Areas'] = relationship('Areas', back_populates='schools')
    property: Mapped['SchoolProperties'] = relationship('SchoolProperties', back_populates='schools')
    town_type: Mapped['TownTypes'] = relationship('TownTypes', back_populates='schools')
    students: Mapped[list['Students']] = relationship('Students', back_populates='school')
    school_groups_schools: Mapped[list['SchoolGroupsSchools']] = relationship('SchoolGroupsSchools', back_populates='school')
    users: Mapped[list["User"]] = relationship("User", back_populates="school")


class SchoolGroups(Base):
    __tablename__ = 'school_groups'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    school_groups_schools: Mapped[list['SchoolGroupsSchools']] = relationship('SchoolGroupsSchools', back_populates='school_group')


class SchoolGroupsSchools(Base):
    __tablename__ = 'school_groups_schools'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    school_id: Mapped[int] = mapped_column(ForeignKey('schools.code', name="SGS-schools"), nullable=False)
    school_group_id: Mapped[int] = mapped_column(ForeignKey('school_groups.id', name="SGS-grouos"), nullable=False)

    school: Mapped['Schools'] = relationship('Schools', back_populates='school_groups_schools')
    school_group: Mapped['SchoolGroups'] = relationship('SchoolGroups', back_populates='school_groups_schools')


class TemplateFolders(Base):
    __tablename__ = 'template_folders'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=func.gen_random_uuid(), server_default="gen_random_uuid()")
    creator_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('auth_user.id', name="folder-creator"), nullable=False)
    name: Mapped[str] = mapped_column(String(63), nullable=False)
    permission_level: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    is_common: Mapped[bool] = mapped_column(Boolean, nullable=False)
    parent_folder_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('template_folders.id', name="folder-parent"), nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default='false')
    deleted_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    creator: Mapped['User'] = relationship('User', back_populates='template_folders')
    parent_folder: Mapped['TemplateFolders'] = relationship('TemplateFolders', remote_side=[id], back_populates='child_folders')
    child_folders: Mapped[list['TemplateFolders']] = relationship('TemplateFolders', back_populates='parent_folder')
    templates: Mapped[list['Templates']] = relationship('Templates', back_populates='folder')
    pinned_folders: Mapped[list['UserPinnedFolders']] = relationship('UserPinnedFolders', back_populates='folder')


class Templates(Base):
    __tablename__ = 'templates'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=func.gen_random_uuid(), server_default="gen_random_uuid()")
    folder_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('template_folders.id', name="template-folder"), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    params: Mapped[dict] = mapped_column(JSON, nullable=False)
    permission_level: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    is_common: Mapped[bool] = mapped_column(Boolean, nullable=False)
    type: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0, server_default='0')
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default='false')
    deleted_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    folder: Mapped['TemplateFolders'] = relationship('TemplateFolders', back_populates='templates')
    pinned_templates: Mapped[list['UserPinnedTemplates']] = relationship('UserPinnedTemplates', back_populates='template')


class UserPinnedFolders(Base):
    __tablename__ = 'user_pinned_folders'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=func.gen_random_uuid(), server_default='gen_random_uuid()')
    folder_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('template_folders.id', name="UPF-folder"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('auth_user.id', name="UPF-user"), nullable=False)
    is_pinned: Mapped[bool] = mapped_column(Boolean, nullable=False)

    folder: Mapped['TemplateFolders'] = relationship('TemplateFolders', back_populates='pinned_folders')
    user: Mapped['User'] = relationship('User', back_populates='pinned_folders')
    pinned_templates: Mapped['UserPinnedTemplates'] = relationship('UserPinnedTemplates', back_populates='user_folder')


class UserPinnedTemplates(Base):
    __tablename__ = 'user_pinned_templates'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=func.gen_random_uuid(), server_default='gen_random_uuid()')
    user_folder_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('user_pinned_folders.id', name="UPT-folder"), nullable=False)
    template_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('templates.id', name="UPT-user"), nullable=False)

    user_folder: Mapped['UserPinnedFolders'] = relationship('UserPinnedFolders', back_populates='pinned_templates')
    template: Mapped['Templates'] = relationship('Templates', back_populates='pinned_templates')


class SuperSubject(Base):
    __tablename__ = "super_subject"

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    subjects: Mapped[list['Subjects']] = relationship('Subjects', back_populates="super_subject")
    competencies: Mapped[list['Competencies']] = relationship('Competencies', back_populates="super_subject")
    users: Mapped[list['User']] = relationship('User', back_populates="super_subject")


class Subjects(Base):
    __tablename__ = 'subjects'

    code: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    super_subject_id: Mapped[int] = mapped_column(ForeignKey('super_subject.id', name="subject-superSubject"), nullable=True)

    super_subject: Mapped['SuperSubject'] = relationship('SuperSubject', back_populates="subjects")
    test_schemes: Mapped[list['TestSchemes']] = relationship('TestSchemes', back_populates="subject")


class ExamTypes(Base):
    __tablename__ = 'exam_types'

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(15), nullable=False)

    test_schemes: Mapped[list['TestSchemes']] = relationship('TestSchemes', back_populates="exam_type")


class TestSchemes(Base):
    __test__ = False
    __tablename__ = 'test_schemes'
    
    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True, autoincrement=True)
    exam_type_id: Mapped[int] = mapped_column(ForeignKey('exam_types.id', name="ETS-examType"), nullable=False)
    subject_id: Mapped[int] = mapped_column(ForeignKey('subjects.code', name="ETS-subject"), nullable=False)
    exam_year: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    grade: Mapped[int] = mapped_column(SmallInteger, nullable=False)

    exam_results: Mapped[list['ExamResults']] = relationship('ExamResults', back_populates='test_scheme')
    planned_exams: Mapped[list['PlannedExams']] = relationship('PlannedExams', back_populates='schema')
    work_plans: Mapped[list['WorkPlans']] = relationship('WorkPlans', back_populates='test_scheme')
    exam_type: Mapped['ExamTypes'] = relationship('ExamTypes', back_populates="test_schemes")
    subject: Mapped['Subjects'] = relationship('Subjects', back_populates="test_schemes")
    
    __table_args__ = (
        UniqueConstraint("exam_type_id", "subject_id", "exam_year", "grade", name='uniq_ETS'),
    )


class User(SQLAlchemyBaseUserTableUUID, Base):
    __tablename__ = "auth_user"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=func.gen_random_uuid(), server_default="gen_random_uuid()")
    super_subject_id: Mapped[int] = mapped_column(ForeignKey("super_subject.id", name="user-subject"), nullable=True)
    area_id: Mapped[int] = mapped_column(ForeignKey("areas.code", name="user-area"), nullable=True)
    school_id: Mapped[int] = mapped_column(ForeignKey("schools.code", name="user-school"), nullable=True)
    first_name: Mapped[str] = mapped_column(String(127), nullable=False)
    last_name: Mapped[str] = mapped_column(String(127), nullable=False)
    middle_name: Mapped[str] = mapped_column(String(127), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(127), nullable=False)
    access_level: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default='true')
    is_superuser: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default='false')

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        server_default="CURRENT_TIMESTAMP",
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
    force_change_password: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default='true')
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default='false')
    deleted_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    area: Mapped["Areas"] = relationship("Areas", back_populates="users")
    school: Mapped["Schools"] = relationship("Schools", back_populates="users")
    template_folders: Mapped[list['TemplateFolders']] = relationship('TemplateFolders', back_populates='creator')
    pinned_folders: Mapped[list['UserPinnedFolders']] = relationship('UserPinnedFolders', back_populates='user')
    super_subject: Mapped["SuperSubject"] = relationship("SuperSubject", back_populates="users")


class Competencies(Base):
    __tablename__ = 'competencies'

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(10), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    section_id: Mapped[int] = mapped_column(ForeignKey('competencies.id', name="competencies-competencies"), nullable=True)
    super_subject_id: Mapped[int] = mapped_column(ForeignKey('super_subject.id', name="competencies-superSubject"), nullable=False)
    skill: Mapped[str] = mapped_column(Text, nullable=True)

    section: Mapped['Competencies'] = relationship('Competencies', remote_side=[id], back_populates='subcompetencies')
    subcompetencies: Mapped[list['Competencies']] = relationship('Competencies', back_populates='section')
    super_subject: Mapped['SuperSubject'] = relationship('SuperSubject', back_populates='competencies')
    work_plans_competencies: Mapped[list['WorkPlansCompetencies']] = relationship('WorkPlansCompetencies', back_populates='competency')


class Difficuelties(Base):
    __tablename__ = 'difficuelties'

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=True)
    code: Mapped[str] = mapped_column(String(1), nullable=False)

    work_plans: Mapped[list['WorkPlans']] = relationship('WorkPlans', back_populates='difficulty')


class WorkPlans(Base):
    __tablename__ = 'work_plans'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    schema_id: Mapped[int] = mapped_column(ForeignKey('test_schemes.id', name="workPlan-difficulty"), nullable=False)
    difficulty_id: Mapped[int] = mapped_column(ForeignKey('difficuelties.id', name="workPlan-schema"), nullable=False)
    task_number_in_part: Mapped[int] = mapped_column(SmallInteger, nullable=True)
    part: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    task_number: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    criterion: Mapped[str] = mapped_column(String(5), nullable=True)
    skill: Mapped[str] = mapped_column(Text, nullable=False)
    max_points: Mapped[int] = mapped_column(SmallInteger, nullable=False)

    test_scheme: Mapped['TestSchemes'] = relationship('TestSchemes', back_populates='work_plans')
    work_plans_competencies: Mapped[list['WorkPlansCompetencies']] = relationship('WorkPlansCompetencies', back_populates='work_plan')
    difficulty: Mapped['Difficuelties'] = relationship('Difficuelties', back_populates='work_plans')
    
    __table_args__ = (
        UniqueConstraint("schema_id", "task_number_in_part", "part", name='uniq_workPlans'),
    )


class WorkPlansCompetencies(Base):
    __tablename__ = 'work_plans_competencies'

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True, autoincrement=True)
    work_plan_id: Mapped[int] = mapped_column(ForeignKey('work_plans.id', name="WPC-workPlan"), nullable=False)
    competencies_id: Mapped[int] = mapped_column(ForeignKey('competencies.id', name="WPC-competencies"), nullable=False)

    work_plan: Mapped['WorkPlans'] = relationship('WorkPlans', back_populates='work_plans_competencies')
    competency: Mapped['Competencies'] = relationship('Competencies', back_populates='work_plans_competencies')
    
    __table_args__ = (
        UniqueConstraint("competencies_id", "work_plan_id", name='uniq_workplanCompet'),
    )
