"""Data models for EMS Reporter."""

from __future__ import annotations

import os
from enum import Enum
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field


class FieldType(str, Enum):
    """Type of field inside a department tab."""
    FOLDER = "folder"      # Counts screenshots in a directory
    NUMERIC = "numeric"    # Manual numeric input (spinbox)
    LINKS = "links"        # Counts message / proof links (Discord, etc.)


class ReportField(BaseModel):
    """Single item / counter inside an EMS department tab."""
    id: str = Field(description="Unique identifier for the field")
    name: str = Field(description="Field display name, e.g. 'ПМП день (Город)'")
    field_type: FieldType = Field(default=FieldType.FOLDER, description="Type: folder, numeric, or links")
    folder_path: str = Field(default="", description="Path to folder containing screenshots (for folder type)")
    points_per_unit: float = Field(default=1.0, description="Points awarded per screenshot, unit, or link")
    manual_count: int = Field(default=0, ge=0, description="Current value for numeric fields")
    links: List[str] = Field(default_factory=list, description="List of message links (for links type)")
    cloud_link: str = Field(default="", description="Optional cloud storage link (e.g. Google Drive folder, Imgur album)")
    filter_extensions: List[str] = Field(
        default_factory=lambda: [".png", ".jpg", ".jpeg", ".bmp", ".webp"],
        description="Allowed image file extensions for folder scanning (empty = all files)"
    )

    def get_clean_links(self) -> List[str]:
        """Return non-empty trimmed links."""
        return [lnk.strip() for lnk in self.links if lnk and lnk.strip()]

    def count_files(self) -> int:
        """Count matching files in folder if folder_path exists."""
        if self.field_type != FieldType.FOLDER:
            return self.manual_count

        if not self.folder_path or not os.path.exists(self.folder_path):
            return 0

        path = Path(self.folder_path)
        if not path.is_dir():
            return 0

        valid_exts = {ext.lower() for ext in self.filter_extensions} if self.filter_extensions else None
        count = 0
        try:
            with os.scandir(path) as it:
                for entry in it:
                    if entry.is_file():
                        if valid_exts is None:
                            count += 1
                        else:
                            _, ext = os.path.splitext(entry.name)
                            if ext.lower() in valid_exts:
                                count += 1
        except (PermissionError, OSError):
            return 0
        return count

    def get_count(self) -> int:
        """Get the item count (files in folder, manual numeric value, or number of links)."""
        if self.field_type == FieldType.FOLDER:
            return self.count_files()
        elif self.field_type == FieldType.LINKS:
            return len(self.get_clean_links())
        return max(0, int(self.manual_count))

    def calculate_points(self) -> float:
        """Calculate total points for this field."""
        count = self.get_count()
        return round(count * self.points_per_unit, 2)

    def format_status_text(self) -> str:
        """Return formatted badge text, e.g. '(13 шт - 26 б)'."""
        count = self.get_count()
        pts = self.calculate_points()
        # Format points nicely: 26 instead of 26.0 if whole number
        pts_str = f"{int(pts)}" if pts.is_integer() else f"{pts:.1f}"
        return f"({count} шт - {pts_str} б)"

    def format_report_entry(self, join_with_newline: bool = True) -> str:
        """Format field value for report, e.g. 'https://... (10 шт - 20 б)' or '(6 шт - 18 б)'."""
        status = self.format_status_text()
        if self.field_type == FieldType.LINKS:
            clean = self.get_clean_links()
            if not clean:
                return status
            if len(clean) == 1:
                return f"{clean[0]} {status}"
            else:
                sep = "\n" if join_with_newline else " "
                return f"{sep.join(clean)}{sep}{status}"
        else:
            link = self.cloud_link.strip() if self.cloud_link else ""
            if link:
                return f"{link} {status}"
            return status


class DepartmentTab(BaseModel):
    """Tab representing a department (PM, DI, PSED, HAD, etc.) or custom group."""
    id: str = Field(description="Unique identifier for the tab")
    title: str = Field(description="Display title, e.g. 'Paramedic (PM)'")
    code: str = Field(default="", description="Short code, e.g. 'PM', 'DI', 'PSED', 'HAD'")
    description: str = Field(default="", description="Short description or notes")
    fields: List[ReportField] = Field(default_factory=list, description="Fields inside this tab")

    def total_count(self) -> int:
        """Sum of all item counts in this tab."""
        return sum(f.get_count() for f in self.fields)

    def total_points(self) -> float:
        """Sum of all points in this tab."""
        return round(sum(f.calculate_points() for f in self.fields), 2)


class ReporterConfig(BaseModel):
    """Complete application configuration containing tabs, presets, and metadata."""
    app_title: str = Field(default="EMS Reporter - Majestic RP")
    player_name: str = Field(default="", description="Name of player (e.g. John Doe | 12345)")
    player_static: str = Field(default="", description="Static ID / passport (e.g. #12345)")
    rank: str = Field(default="", description="Current rank/position in EMS")
    auto_refresh_seconds: int = Field(default=5, ge=0, description="Auto folder scan interval (0 = off)")
    active_tab_id: Optional[str] = Field(default=None, description="Last selected tab ID")
    tabs: List[DepartmentTab] = Field(default_factory=list, description="List of configured department tabs")

    def grand_total_count(self) -> int:
        """Sum of counts across all tabs."""
        return sum(t.total_count() for t in self.tabs)

    def grand_total_points(self) -> float:
        """Sum of points across all tabs."""
        return round(sum(t.total_points() for t in self.tabs), 2)
