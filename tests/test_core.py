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


def test_cloud_link_format_report_entry():
    """Verify format_report_entry with and without cloud link."""
    # Without cloud link
    f1 = ReportField(
        id="f1",
        name="ПМП день (Город)",
        field_type=FieldType.NUMERIC,
        points_per_unit=3.0,
        manual_count=6
    )
    assert f1.format_report_entry() == "(6 шт - 18 б)"

    # With cloud link
    f2 = ReportField(
        id="f2",
        name="ПМП день (Город)",
        field_type=FieldType.NUMERIC,
        points_per_unit=2.0,
        manual_count=10,
        cloud_link="https://drive.google.com/drive/folders/test12345"
    )
    assert f2.format_report_entry() == "https://drive.google.com/drive/folders/test12345 (10 шт - 20 б)"


def test_default_config_has_empty_fields():
    """Verify default tabs exist (PM, DI, PSED, HAD) and have no pre-created fields."""
    config = create_default_config()
    codes = [t.code for t in config.tabs]
    assert "PM" in codes
    assert "DI" in codes
    assert "PSED" in codes
    assert "HAD" in codes

    for t in config.tabs:
        assert len(t.fields) == 0, f"Tab {t.title} should have 0 fields by default"


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


def test_plain_report_generation():
    """Verify plain text report matches user required format with separate fields."""
    config = create_default_config()
    config.player_name = "Jason Mitsui"
    config.player_static = "206277"

    tab = config.tabs[0]
    tab.fields = [
        ReportField(
            id="f1",
            name="ПМП день (Город)",
            field_type=FieldType.NUMERIC,
            points_per_unit=2.0,
            manual_count=10,
            cloud_link="https://drive.google.com/folder1"
        ),
        ReportField(
            id="f2",
            name="ПМП ночь (Город)",
            field_type=FieldType.NUMERIC,
            points_per_unit=3.0,
            manual_count=6,
            cloud_link=""
        ),
    ]

    report = ReportGenerator.generate_plain_report(config, tab)
    expected_lines = [
        "Имя Фамилия | статик",
        "Jason Mitsui | 206277",
        "ПМП день (Город)",
        "https://drive.google.com/folder1 (10 шт - 20 б)",
        "ПМП ночь (Город)",
        "(6 шт - 18 б)",
        "Общее количество баллов",
        "38"
    ]

    for expected in expected_lines:
        assert expected in report
