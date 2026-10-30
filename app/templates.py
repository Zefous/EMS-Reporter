"""Default template generator for Majestic GTA V RP EMS departments."""

import uuid
from app.models import ReporterConfig, DepartmentTab


def create_default_config() -> ReporterConfig:
    """Generate default configuration for EMS departments with empty fields."""
    
    # 1. Paramedic (PM)
    pm_tab = DepartmentTab(
        id=str(uuid.uuid4()),
        title="Paramedic (PM)",
        code="PM",
        description="Скорая медицинская помощь (выезды, ПМП, реанимации, вызовы)",
        fields=[]
    )

    # 2. Department of Internship (DI)
    di_tab = DepartmentTab(
        id=str(uuid.uuid4()),
        title="Department of Internship (DI)",
        code="DI",
        description="Обучение персонала, экзамены, лекции",
        fields=[]
    )

    # 3. Psychological and Sanitary-Epidemiological Department (PSED)
    psed_tab = DepartmentTab(
        id=str(uuid.uuid4()),
        title="Psychological & Sanitary (PSED)",
        code="PSED",
        description="Санитарные проверки, справки о здоровье, психологическая помощь",
        fields=[]
    )

    # 4. Hospital Administration Department (HAD)
    had_tab = DepartmentTab(
        id=str(uuid.uuid4()),
        title="Hospital Administration (HAD)",
        code="HAD",
        description="Администрация больницы, контроль за порядком и составом",
        fields=[]
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
