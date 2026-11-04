"""Default configuration generator for EMS Reporter."""

from app.models import ReporterConfig


def create_default_config() -> ReporterConfig:
    """Generate clean default configuration without pre-created tabs."""
    return ReporterConfig(
        app_title="EMS Reporter - Majestic GTA V RP",
        player_name="",
        player_static="",
        auto_refresh_seconds=5,
        active_tab_id=None,
        tabs=[]
    )
