"""Comprehensive unit tests for EMS Reporter models, storage, and logic."""

import os
import tempfile
import pytest
from pathlib import Path

from app.models import ReportField, FieldType, DepartmentTab, ReporterConfig, DiscordLinkItem
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


def test_folder_batch_threshold_calculation():
    """Verify batch threshold scoring (e.g. 8 screenshots = 60 pts, 7 = 30 pts with batch_size=4, batch_points=30)."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        folder_path = Path(tmp_dir)
        for i in range(8):
            (folder_path / f"img_{i}.png").write_text("data")

        field = ReportField(
            id="fld-batch",
            name="ПМП за городом",
            field_type=FieldType.FOLDER,
            folder_path=str(folder_path),
            points_per_unit=2.0,
            batch_mode_enabled=True,
            batch_size=4,
            batch_points=30.0
        )

        # 8 screenshots // 4 = 2 batches * 30 = 60 points
        assert field.get_count() == 8
        assert field.calculate_points() == 60.0
        assert field.format_status_text() == "(8 шт - 60 б)"

        # Remove 1 screenshot -> 7 screenshots // 4 = 1 batch * 30 = 30 points (remainder 3 ignored)
        (folder_path / "img_7.png").unlink()
        assert field.get_count() == 7
        assert field.calculate_points() == 30.0
        assert field.format_status_text() == "(7 шт - 30 б)"

        # If batch_mode is disabled, counts normally (7 * 2 = 14)
        field.batch_mode_enabled = False
        assert field.calculate_points() == 14.0
        assert field.format_status_text() == "(7 шт - 14 б)"


def test_simple_links_field_calculation_and_report():
    """Verify FieldType.LINKS counts simple links (points awarded per link)."""
    f = ReportField(
        id="simple-lnk-1",
        name="Аудиты в Discord",
        field_type=FieldType.LINKS,
        points_per_unit=5.0,
        simple_links=[
            "https://discord.com/channels/1/2/1",
            "   ",  # Ignored
            "https://discord.com/channels/1/2/2",
            "https://discord.com/channels/1/2/3"
        ]
    )

    assert f.get_count() == 3
    assert f.calculate_points() == 15.0
    assert f.format_status_text() == "(3 шт - 15 б)"

    entry_nl = f.format_report_entry(join_with_newline=True)
    assert "https://discord.com/channels/1/2/1" in entry_nl
    assert "https://discord.com/channels/1/2/3" in entry_nl
    assert "(3 шт - 15 б)" in entry_nl


def test_links_with_tasks_calculation_and_report():
    """Verify FieldType.LINKS_WITH_TASKS counts tasks per link and formats report accurately."""
    f = ReportField(
        id="task-lnk-1",
        name="Отчёт в Discord с задачами",
        field_type=FieldType.LINKS_WITH_TASKS,
        points_per_unit=3.0,
        links=[
            DiscordLinkItem(url="https://discord.com/channels/1/2/1", count=3),
            DiscordLinkItem(url="https://discord.com/channels/1/2/2", count=2),
            DiscordLinkItem(url="https://discord.com/channels/1/2/3", count=5),
        ]
    )

    # Total tasks = 3 + 2 + 5 = 10
    assert f.get_count() == 10
    # Total points = 10 * 3 = 30
    assert f.calculate_points() == 30.0
    assert f.format_status_text() == "(10 шт - 30 б)"

    # Format report entry
    report_entry = f.format_report_entry(join_with_newline=True)
    expected_lines = [
        "https://discord.com/channels/1/2/1 (3 шт - 9 б)",
        "https://discord.com/channels/1/2/2 (2 шт - 6 б)",
        "https://discord.com/channels/1/2/3 (5 шт - 15 б)",
        "(10 шт - 30 б)"
    ]
    for line in expected_lines:
        assert line in report_entry


def test_default_config_is_completely_clean():
    """Verify default config starts with NO tabs at all."""
    config = create_default_config()
    assert len(config.tabs) == 0


def test_config_save_load_and_export():
    """Verify saving, loading, exporting and importing configuration."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        cfg_file = Path(tmp_dir) / "test_config.json"
        mgr = ConfigManager(str(cfg_file))
        config = create_default_config()
        config.player_name = "Dr. House"
        config.player_static = "77777"
        config.tabs.append(DepartmentTab(id="tab-1", title="Главная", fields=[]))

        # Save & load
        mgr.save(config)
        assert cfg_file.exists()

        loaded = mgr.load()
        assert loaded.player_name == "Dr. House"
        assert loaded.player_static == "77777"
        assert len(loaded.tabs) == 1

        # Export & Import
        export_file = Path(tmp_dir) / "exported_preset.json"
        ConfigManager.export_to_file(loaded, str(export_file))
        assert export_file.exists()

        imported = ConfigManager.import_from_file(str(export_file))
        assert imported.player_name == "Dr. House"
        assert len(imported.tabs) == 1


def test_plain_report_generation():
    """Verify plain text report matches user required format with separate fields."""
    config = create_default_config()
    config.player_name = "Jason Mitsui"
    config.player_static = "206277"

    tab = DepartmentTab(id="t1", title="Paramedic (PM)", fields=[
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
    ])

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
