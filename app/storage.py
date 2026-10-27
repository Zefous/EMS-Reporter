"""Configuration storage and report generation utilities."""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.models import ReporterConfig, DepartmentTab, ReportField, FieldType
from app.templates import create_default_config

DEFAULT_CONFIG_FILENAME = "ems_config.json"


class ConfigManager:
    """Manages loading, saving, importing, and exporting config files."""

    def __init__(self, filepath: Optional[str] = None):
        if filepath is None:
            # Place ems_config.json in the current working directory or user folder
            self.filepath = Path(DEFAULT_CONFIG_FILENAME).resolve()
        else:
            self.filepath = Path(filepath).resolve()

    def load(self) -> ReporterConfig:
        """Load configuration from file, or create default if not found or invalid."""
        if not self.filepath.exists():
            config = create_default_config()
            self.save(config)
            return config

        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            return ReporterConfig.model_validate(data)
        except Exception:
            # Fallback to default if file was corrupted
            config = create_default_config()
            return config

    def save(self, config: ReporterConfig, target_path: Optional[str] = None) -> None:
        """Save configuration to JSON file."""
        dest = Path(target_path).resolve() if target_path else self.filepath
        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, "w", encoding="utf-8") as f:
            json.dump(config.model_dump(mode="json"), f, ensure_ascii=False, indent=2)

    @staticmethod
    def export_to_file(config: ReporterConfig, path: str) -> None:
        """Export config to specified path for sharing with other users."""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(config.model_dump(mode="json"), f, ensure_ascii=False, indent=2)

    @staticmethod
    def import_from_file(path: str) -> ReporterConfig:
        """Import config from a shared file."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return ReporterConfig.model_validate(data)


class ReportGenerator:
    """Generates formatted reports for Majestic RP."""

    @staticmethod
    def generate_plain_report(config: ReporterConfig, tab: DepartmentTab) -> str:
        """Generate plain text report for the active department tab.

        Format:
        Имя Фамилия | статик
        "Jason Mitsui | 206277"
        Название поля 1
        "ссылка (10 шт - 20 б)"
        ...
        Общее количество баллов
        "38"
        """
        lines = []

        # 1. Player Info Header
        name = config.player_name.strip() if config.player_name else ""
        static = config.player_static.strip() if config.player_static else ""
        if name and static:
            player_info = f"{name} | {static}"
        elif name:
            player_info = name
        elif static:
            player_info = static
        else:
            player_info = "Имя Фамилия | статик"

        lines.append("Имя Фамилия | статик")
        lines.append(player_info)

        # 2. Fields in the active tab
        for field in tab.fields:
            lines.append(field.name)
            entry = field.format_report_entry()
            lines.append(entry)

        # 3. Total points for the active tab
        tot_pts = tab.total_points()
        pts_str = f"{int(tot_pts)}" if tot_pts.is_integer() else f"{tot_pts:.1f}"
        lines.append("Общее количество баллов")
        lines.append(pts_str)

        return "\n".join(lines)

    @staticmethod
    def generate_markdown_report(config: ReporterConfig, active_tab_only: bool = False, current_tab_id: Optional[str] = None) -> str:
        """Generate formatted report with Discord/Forum markdown formatting."""
        lines = []
        now_str = datetime.now().strftime("%d.%m.%Y %H:%M")
        
        lines.append("```md")
        lines.append("═" * 46)
        lines.append("🚑 ОТЧЁТ О ПРОДЕЛАННОЙ РАБОТЕ EMS | MAJESTIC RP 🚑")
        lines.append("═" * 46)
        
        if config.player_name:
            lines.append(f"• Имя Фамилия: {config.player_name}")
        if config.player_static:
            lines.append(f"• Статический ID: {config.player_static}")
        if config.rank:
            lines.append(f"• Должность / Ранг: {config.rank}")
        lines.append(f"• Дата формирования: {now_str}")
        lines.append("═" * 46)
        lines.append("```")
        lines.append("")

        tabs_to_include = config.tabs
        if active_tab_only and current_tab_id:
            tabs_to_include = [t for t in config.tabs if t.id == current_tab_id]

        total_pts = 0.0
        total_items = 0

        for tab in tabs_to_include:
            tab_pts = tab.total_points()
            tab_count = tab.total_count()
            total_pts += tab_pts
            total_items += tab_count

            pts_str = f"{int(tab_pts)}" if tab_pts.is_integer() else f"{tab_pts:.1f}"

            lines.append(f"### 📋 {tab.title} — {tab_count} шт. ({pts_str} б.)")
            if tab.description:
                lines.append(f"> *{tab.description}*")
            lines.append("")

            if not tab.fields:
                lines.append("_В этом отделе пока нет полей._")
                lines.append("")
                continue

            for idx, field in enumerate(tab.fields, 1):
                count = field.get_count()
                pts = field.calculate_points()
                f_pts_str = f"{int(pts)}" if pts.is_integer() else f"{pts:.1f}"
                unit_pts = f"{int(field.points_per_unit)}" if field.points_per_unit.is_integer() else f"{field.points_per_unit:.1f}"

                status = f"**{count} шт.** — **{f_pts_str} б.** ({unit_pts} б/ед)"
                type_badge = "📁" if field.field_type == FieldType.FOLDER else "🔢"
                lines.append(f"{idx}. {type_badge} {field.name}: {status}")

            lines.append("")

        grand_pts_str = f"{int(total_pts)}" if total_pts.is_integer() else f"{total_pts:.1f}"
        lines.append("```")
        lines.append(f"ИТОГО: {total_items} выполненных действий | Всего баллов: {grand_pts_str} б.")
        lines.append("```")

        return "\n".join(lines)
