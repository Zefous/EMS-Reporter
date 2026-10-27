"""Comprehensive unit tests for EMS Reporter models, storage, and logic."""

import os
import tempfile
import pytest
from pathlib import Path

from app.models import ReportField, FieldType, DepartmentTab, ReporterConfig
from app.storage import ConfigManager, ReportGenerator
from app.templates import create_default_config


def test_numeric_field_calculation():
    """Verify numeric field calculations and badge format text: '(1 шт - 5 б)'."""
    field = ReportField(
        id="num-1",
        name="Участие в мероприятии",
        field_type=FieldType.NUMERIC,
        points_per_unit=5.0,
        manual_count=1
    )
    assert field.get_count() == 1
    assert field.calculate_points() == 5.0
    assert field.format_status_text() == "(1 шт - 5 б)"

    field.manual_count = 3
    assert field.get_count() == 3
    assert field.calculate_points() == 15.0
    assert field.format_status_text() == "(3 шт - 15 б)"


def test_folder_field_scanning():
    """Verify folder field screenshot scanning and badge format text: '(13 шт - 26 б)'."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        folder_path = Path(tmp_dir)
        # Create 13 dummy screenshot files
        for i in range(13):
            (folder_path / f"screenshot_{i:02d}.png").write_text("fake image data")

        # Also create a non-image file that should be ignored by default filter
        (folder_path / "notes.txt").write_text("some text")

        field = ReportField(
            id="fld-1",
            name="ПМП день (Город)",
            field_type=FieldType.FOLDER,
            folder_path=str(folder_path),
            points_per_unit=2.0
        )

        assert field.get_count() == 13
        assert field.calculate_points() == 26.0
        assert field.format_status_text() == "(13 шт - 26 б)"


def test_default_config_structure():
    """Verify default config contains PM, DI, PSED, HAD and all 11 Paramedic fields."""
    config = create_default_config()
    codes = [t.code for t in config.tabs]
    assert "PM" in codes
    assert "DI" in codes
    assert "PSED" in codes
    assert "HAD" in codes

    pm_tab = next(t for t in config.tabs if t.code == "PM")
    assert len(pm_tab.fields) == 11

    # Check required items exist
    field_names = [f.name for f in pm_tab.fields]
    assert any("Реанимация в городе (день)" in name for name in field_names)
    assert any("Реанимация в городе (ночь)" in name for name in field_names)
    assert any("Реанимация за городом (день)" in name for name in field_names)
    assert any("Реанимация за городом (ночь)" in name for name in field_names)
    assert any("Выдача таблеток" in name for name in field_names)
    assert any("Вакцинация в городе" in name for name in field_names)
    assert any("Вакцинация за городом" in name for name in field_names)
    assert any("Отменённые вызовы" in name for name in field_names)
    assert any("Участие в мероприятии" in name for name in field_names)
    assert any("Счастливый вызов" in name for name in field_names)
    assert any("Выдача комплектов мед. справок" in name for name in field_names)


def test_config_save_load_and_export():
    """Verify saving, loading, exporting and importing configuration."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        cfg_file = Path(tmp_dir) / "test_config.json"
        mgr = ConfigManager(str(cfg_file))
        config = create_default_config()
        config.player_name = "Dr. House"
        config.player_static = "#77777"
        config.rank = "Chief Physician"

        # Save & load
        mgr.save(config)
        assert cfg_file.exists()

        loaded = mgr.load()
        assert loaded.player_name == "Dr. House"
        assert loaded.player_static == "#77777"
        assert loaded.rank == "Chief Physician"
        assert len(loaded.tabs) == len(config.tabs)

        # Export & Import
        export_file = Path(tmp_dir) / "exported_preset.json"
        ConfigManager.export_to_file(loaded, str(export_file))
        assert export_file.exists()

        imported = ConfigManager.import_from_file(str(export_file))
        assert imported.player_name == "Dr. House"
        assert len(imported.tabs) == len(loaded.tabs)


def test_report_generation():
    """Verify markdown report generation contains player info, tabs, and totals."""
    config = create_default_config()
    config.player_name = "Kirill EMS"
    config.player_static = "#9999"
    config.rank = "Paramedic Lead"

    # Set some counts
    pm_tab = next(t for t in config.tabs if t.code == "PM")
    pm_tab.fields[8].manual_count = 2  # Участие в мероприятии (5 б/ед = 10 б)
    pm_tab.fields[9].manual_count = 1  # Счастливый вызов (10 б/ед = 10 б)

    report_md = ReportGenerator.generate_markdown_report(config)
    assert "Kirill EMS" in report_md
    assert "#9999" in report_md
    assert "Paramedic Lead" in report_md
    assert "Paramedic (PM)" in report_md
    assert "Участие в мероприятии" in report_md
    assert "ИТОГО" in report_md
    assert "20" in report_md  # 10 + 10 points
