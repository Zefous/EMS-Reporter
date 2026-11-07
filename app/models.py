"""Data models for EMS Reporter."""

from __future__ import annotations

import os
from enum import Enum
from pathlib import Path
from typing import List, Optional, Union
from pydantic import BaseModel, Field


class FieldType(str, Enum):
    """Type of field inside a department tab."""
    FOLDER = "folder"                      # Counts screenshots in a directory
    NUMERIC = "numeric"                    # Manual numeric input (spinbox)
    LINKS = "links"                        # Simple links (points awarded per link)
    LINKS_WITH_TASKS = "links_with_tasks"  # Links with task counts (points awarded per task)


class DiscordLinkItem(BaseModel):
    """Single Discord link entry with a count of completed tasks."""
    url: str = Field(default="", description="Discord message URL")
    count: int = Field(default=1, ge=1, description="Number of completed tasks for this link")


class ReportField(BaseModel):
    """Single item / counter inside an EMS tab."""
    id: str = Field(description="Unique identifier for the field")
    name: str = Field(description="Field display name, e.g. 'ПМП день (Город)'")
    field_type: FieldType = Field(default=FieldType.FOLDER, description="Type: folder, numeric, links, or links_with_tasks")
    folder_path: str = Field(default="", description="Path to folder containing screenshots (for folder type)")
    points_per_unit: float = Field(default=1.0, description="Points awarded per screenshot, unit, link, or task")
    manual_count: int = Field(default=0, ge=0, description="Current value for numeric fields")
    
    # Storage for simple links (plain strings)
    simple_links: List[str] = Field(default_factory=list, description="List of simple URLs for FieldType.LINKS")

    # Storage for links with tasks (DiscordLinkItem)
    links: List[Union[str, DiscordLinkItem]] = Field(
        default_factory=list,
        description="List of message links or DiscordLinkItem for FieldType.LINKS_WITH_TASKS"
    )

    # Batch / Threshold calculation for folder fields
    batch_mode_enabled: bool = Field(default=False, description="Enable batch/threshold calculation")
    batch_size: int = Field(default=4, ge=1, description="Number of screenshots required for one batch")
    batch_points: float = Field(default=30.0, ge=0.0, description="Points awarded per complete batch")

    cloud_link: str = Field(default="", description="Optional cloud storage link (e.g. Google Drive folder, Imgur album)")
    filter_extensions: List[str] = Field(
        default_factory=lambda: [".png", ".jpg", ".jpeg", ".bmp", ".webp"],
        description="Allowed image file extensions for folder scanning (empty = all files)"
    )

    def get_clean_simple_links(self) -> List[str]:
        """Return non-empty trimmed links for simple links field."""
        # Support migration if links were previously stored in self.links
        source = self.simple_links if self.simple_links else [
            (it.url if isinstance(it, DiscordLinkItem) else it) for it in self.links
        ]
        return [lnk.strip() for lnk in source if lnk and str(lnk).strip()]

    def get_discord_link_items(self) -> List[DiscordLinkItem]:
        """Normalize links into DiscordLinkItem list with valid non-empty URLs."""
        res: List[DiscordLinkItem] = []
        for item in self.links:
            if isinstance(item, DiscordLinkItem):
                clean_url = item.url.strip()
                if clean_url:
                    res.append(DiscordLinkItem(url=clean_url, count=max(1, int(item.count))))
            elif isinstance(item, str):
                s = item.strip()
                if s:
                    res.append(DiscordLinkItem(url=s, count=1))
        # If links was empty but simple_links had items
        if not res and self.simple_links:
            for s in self.simple_links:
                if s.strip():
                    res.append(DiscordLinkItem(url=s.strip(), count=1))
        return res

    def to_template(self) -> ReportField:
        """Return a clean copy of the field without paths, counts, links, or cloud urls."""
        data = self.model_dump()
        data["folder_path"] = ""
        data["manual_count"] = 0
        data["simple_links"] = []
        data["links"] = []
        data["cloud_link"] = ""
        return ReportField.model_validate(data)

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
        """Get the total completed item/link/task count."""
        if self.field_type == FieldType.FOLDER:
            return self.count_files()
        elif self.field_type == FieldType.LINKS:
            return len(self.get_clean_simple_links())
        elif self.field_type == FieldType.LINKS_WITH_TASKS:
            items = self.get_discord_link_items()
            return sum(item.count for item in items)
        return max(0, int(self.manual_count))

    def calculate_points(self) -> float:
        """Calculate total points for this field."""
        if self.field_type == FieldType.FOLDER:
            count = self.count_files()
            if self.batch_mode_enabled and self.batch_size > 0:
                batches = count // self.batch_size
                return round(batches * self.batch_points, 2)
            return round(count * self.points_per_unit, 2)
        elif self.field_type == FieldType.LINKS:
            return round(len(self.get_clean_simple_links()) * self.points_per_unit, 2)
        elif self.field_type == FieldType.LINKS_WITH_TASKS:
            items = self.get_discord_link_items()
            total_tasks = sum(item.count for item in items)
            return round(total_tasks * self.points_per_unit, 2)
        else:
            return round(self.get_count() * self.points_per_unit, 2)

    def format_status_text(self) -> str:
        """Return formatted badge text, e.g. '(13 шт - 26 б)'."""
        count = self.get_count()
        pts = self.calculate_points()
        pts_str = f"{int(pts)}" if pts.is_integer() else f"{pts:.1f}"
        return f"({count} шт - {pts_str} б)"

    def format_report_entry(self, join_with_newline: bool = True) -> str:
        """Format field value for report. If points are 0, return '-'."""
        if self.calculate_points() == 0:
            return "-"

        status = self.format_status_text()
        if self.field_type == FieldType.LINKS:
            clean = self.get_clean_simple_links()
            if not clean:
                return "-"
            if len(clean) == 1:
                return f"{clean[0]} {status}"
            else:
                sep = "\n" if join_with_newline else " "
                return f"{sep.join(clean)}{sep}{status}"
        elif self.field_type == FieldType.LINKS_WITH_TASKS:
            items = self.get_discord_link_items()
            if not items:
                return "-"

            lines = []
            for item in items:
                link_pts = round(item.count * self.points_per_unit, 2)
                link_pts_str = f"{int(link_pts)}" if link_pts.is_integer() else f"{link_pts:.1f}"
                lines.append(f"{item.url} ({item.count} шт - {link_pts_str} б)")

            lines.append(status)
            sep = "\n" if join_with_newline else " "
            return sep.join(lines)
        else:
            link = self.cloud_link.strip() if self.cloud_link else ""
            if link:
                return f"{link} {status}"
            return status


class DepartmentTab(BaseModel):
    """Tab representing a department or custom group."""
    id: str = Field(description="Unique identifier for the tab")
    title: str = Field(description="Display title, e.g. 'Paramedic (PM)'")
    code: str = Field(default="", description="Optional code")
    description: str = Field(default="", description="Short description")
    fields: List[ReportField] = Field(default_factory=list, description="Fields inside this tab")

    def total_count(self) -> int:
        """Sum of all item counts in this tab."""
        return sum(f.get_count() for f in self.fields)

    def total_points(self) -> float:
        """Sum of all points in this tab."""
        return round(sum(f.calculate_points() for f in self.fields), 2)

    def to_template(self) -> DepartmentTab:
        """Return a clean copy of the tab with clean template fields."""
        return DepartmentTab(
            id=self.id,
            title=self.title,
            code=self.code,
            description=self.description,
            fields=[f.to_template() for f in self.fields]
        )

    def clone_with_new_ids(self) -> DepartmentTab:
        """Return a deep copy of tab and its fields with newly generated unique IDs (for appending)."""
        import uuid
        new_fields = []
        for f in self.fields:
            f_data = f.model_dump()
            f_data["id"] = str(uuid.uuid4())
            new_fields.append(ReportField.model_validate(f_data))
        return DepartmentTab(
            id=str(uuid.uuid4()),
            title=self.title,
            code=self.code,
            description=self.description,
            fields=new_fields
        )


class ReporterConfig(BaseModel):
    """Complete application configuration containing tabs and metadata."""
    app_title: str = Field(default="EMS Reporter - Majestic RP")
    player_name: str = Field(default="", description="Name of player (e.g. John Doe)")
    player_static: str = Field(default="", description="Static ID / passport (e.g. 12345)")
    auto_refresh_seconds: int = Field(default=5, ge=0, description="Auto folder scan interval (0 = off)")
    active_tab_id: Optional[str] = Field(default=None, description="Last selected tab ID")
    tabs: List[DepartmentTab] = Field(default_factory=list, description="List of configured tabs")

    def grand_total_count(self) -> int:
        """Sum of counts across all tabs."""
        return sum(t.total_count() for t in self.tabs)

    def grand_total_points(self) -> float:
        """Sum of points across all tabs."""
        return round(sum(t.total_points() for t in self.tabs), 2)

    def create_export_copy(
        self,
        as_template: bool = False,
        active_tab_only: bool = False,
        active_tab_id: Optional[str] = None
    ) -> ReporterConfig:
        """Generate configuration for export with chosen options."""
        if active_tab_only and active_tab_id:
            selected_tabs = [t for t in self.tabs if t.id == active_tab_id]
            if not selected_tabs and self.tabs:
                selected_tabs = [self.tabs[0]]
        else:
            selected_tabs = list(self.tabs)

        if as_template:
            exported_tabs = [t.to_template() for t in selected_tabs]
            return ReporterConfig(
                app_title=self.app_title,
                player_name="",
                player_static="",
                auto_refresh_seconds=self.auto_refresh_seconds,
                active_tab_id=exported_tabs[0].id if exported_tabs else None,
                tabs=exported_tabs
            )
        else:
            copied_tabs = [t.model_copy(deep=True) for t in selected_tabs]
            return ReporterConfig(
                app_title=self.app_title,
                player_name=self.player_name,
                player_static=self.player_static,
                auto_refresh_seconds=self.auto_refresh_seconds,
                active_tab_id=self.active_tab_id,
                tabs=copied_tabs
            )
