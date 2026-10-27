"""Default template generator for Majestic GTA V RP EMS departments."""

import uuid
from app.models import ReporterConfig, DepartmentTab, ReportField, FieldType


def create_default_config() -> ReporterConfig:
    """Generate the pre-filled default configuration for EMS departments."""
    
    # 1. Paramedic (PM) - Exact fields as requested by user
    pm_fields = [
        ReportField(
            id=str(uuid.uuid4()),
            name="Реанимация в городе (день)",
            field_type=FieldType.FOLDER,
            folder_path="",
            points_per_unit=2.0,
            manual_count=0
        ),
        ReportField(
            id=str(uuid.uuid4()),
            name="Реанимация в городе (ночь)",
            field_type=FieldType.FOLDER,
            folder_path="",
            points_per_unit=3.0,
            manual_count=0
        ),
        ReportField(
            id=str(uuid.uuid4()),
            name="Реанимация за городом (день)",
            field_type=FieldType.FOLDER,
            folder_path="",
            points_per_unit=3.0,
            manual_count=0
        ),
        ReportField(
            id=str(uuid.uuid4()),
            name="Реанимация за городом (ночь)",
            field_type=FieldType.FOLDER,
            folder_path="",
            points_per_unit=4.0,
            manual_count=0
        ),
        ReportField(
            id=str(uuid.uuid4()),
            name="Выдача таблеток",
            field_type=FieldType.FOLDER,
            folder_path="",
            points_per_unit=1.0,
            manual_count=0
        ),
        ReportField(
            id=str(uuid.uuid4()),
            name="Вакцинация в городе",
            field_type=FieldType.FOLDER,
            folder_path="",
            points_per_unit=2.0,
            manual_count=0
        ),
        ReportField(
            id=str(uuid.uuid4()),
            name="Вакцинация за городом",
            field_type=FieldType.FOLDER,
            folder_path="",
            points_per_unit=3.0,
            manual_count=0
        ),
        ReportField(
            id=str(uuid.uuid4()),
            name="Отменённые вызовы",
            field_type=FieldType.FOLDER,
            folder_path="",
            points_per_unit=1.0,
            manual_count=0
        ),
        ReportField(
            id=str(uuid.uuid4()),
            name="Участие в мероприятии",
            field_type=FieldType.NUMERIC,
            folder_path="",
            points_per_unit=5.0,
            manual_count=0
        ),
        ReportField(
            id=str(uuid.uuid4()),
            name="Счастливый вызов",
            field_type=FieldType.NUMERIC,
            folder_path="",
            points_per_unit=10.0,
            manual_count=0
        ),
        ReportField(
            id=str(uuid.uuid4()),
            name="Выдача комплектов мед. справок",
            field_type=FieldType.NUMERIC,
            folder_path="",
            points_per_unit=5.0,
            manual_count=0
        ),
    ]

    pm_tab = DepartmentTab(
        id=str(uuid.uuid4()),
        title="Paramedic (PM)",
        code="PM",
        description="Отдел скорой медицинской помощи (выезды, ПМП, реанимации, вызовы)",
        fields=pm_fields
    )

    # 2. Department of Internship (DI)
    di_fields = [
        ReportField(
            id=str(uuid.uuid4()),
            name="Принятие экзамена / практики у интерна",
            field_type=FieldType.FOLDER,
            folder_path="",
            points_per_unit=5.0,
            manual_count=0
        ),
        ReportField(
            id=str(uuid.uuid4()),
            name="Проведение лекции для интернов",
            field_type=FieldType.FOLDER,
            folder_path="",
            points_per_unit=4.0,
            manual_count=0
        ),
        ReportField(
            id=str(uuid.uuid4()),
            name="Помощь интерну на практике",
            field_type=FieldType.FOLDER,
            folder_path="",
            points_per_unit=3.0,
            manual_count=0
        ),
        ReportField(
            id=str(uuid.uuid4()),
            name="Принятый в интернатуру человек",
            field_type=FieldType.NUMERIC,
            folder_path="",
            points_per_unit=5.0,
            manual_count=0
        ),
        ReportField(
            id=str(uuid.uuid4()),
            name="Проведение собеседования в EMS",
            field_type=FieldType.NUMERIC,
            folder_path="",
            points_per_unit=3.0,
            manual_count=0
        ),
    ]

    di_tab = DepartmentTab(
        id=str(uuid.uuid4()),
        title="Department of Internship (DI)",
        code="DI",
        description="Отдел интернатуры и обучения персонала EMS",
        fields=di_fields
    )

    # 3. Psychological and Sanitary-Epidemiological Department (PSED)
    psed_fields = [
        ReportField(
            id=str(uuid.uuid4()),
            name="Выдача мед. справки о физ. здоровье",
            field_type=FieldType.FOLDER,
            folder_path="",
            points_per_unit=2.0,
            manual_count=0
        ),
        ReportField(
            id=str(uuid.uuid4()),
            name="Выдача мед. справки о псих. здоровье",
            field_type=FieldType.FOLDER,
            folder_path="",
            points_per_unit=3.0,
            manual_count=0
        ),
        ReportField(
            id=str(uuid.uuid4()),
            name="Проведение санитарной проверки гос. фракции",
            field_type=FieldType.FOLDER,
            folder_path="",
            points_per_unit=10.0,
            manual_count=0
        ),
        ReportField(
            id=str(uuid.uuid4()),
            name="Сеанс психологической помощи",
            field_type=FieldType.NUMERIC,
            folder_path="",
            points_per_unit=6.0,
            manual_count=0
        ),
        ReportField(
            id=str(uuid.uuid4()),
            name="Проверка состава на наркотические вещества",
            field_type=FieldType.NUMERIC,
            folder_path="",
            points_per_unit=5.0,
            manual_count=0
        ),
    ]

    psed_tab = DepartmentTab(
        id=str(uuid.uuid4()),
        title="Psychological & Sanitary (PSED)",
        code="PSED",
        description="Психологический и санитарно-эпидемиологический отдел",
        fields=psed_fields
    )

    # 4. Hospital Administration Department (HAD)
    had_fields = [
        ReportField(
            id=str(uuid.uuid4()),
            name="Контроль работы сотрудников в холле",
            field_type=FieldType.FOLDER,
            folder_path="",
            points_per_unit=3.0,
            manual_count=0
        ),
        ReportField(
            id=str(uuid.uuid4()),
            name="Патрулирование больницы и палат",
            field_type=FieldType.FOLDER,
            folder_path="",
            points_per_unit=2.0,
            manual_count=0
        ),
        ReportField(
            id=str(uuid.uuid4()),
            name="Организация строя / собрания",
            field_type=FieldType.NUMERIC,
            folder_path="",
            points_per_unit=5.0,
            manual_count=0
        ),
        ReportField(
            id=str(uuid.uuid4()),
            name="Выдача дисциплинарного взыскания / поощрения",
            field_type=FieldType.NUMERIC,
            folder_path="",
            points_per_unit=3.0,
            manual_count=0
        ),
    ]

    had_tab = DepartmentTab(
        id=str(uuid.uuid4()),
        title="Hospital Administration (HAD)",
        code="HAD",
        description="Администрация больницы, контроль за порядком и составом",
        fields=had_fields
    )

    config = ReporterConfig(
        app_title="EMS Reporter - Majestic GTA V RP",
        player_name="",
        player_static="",
        rank="Paramedic",
        auto_refresh_seconds=5,
        active_tab_id=pm_tab.id,
        tabs=[pm_tab, di_tab, psed_tab, had_tab]
    )

    return config
