"""Update checking and in-place application updater for EMS Reporter."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from PySide6.QtCore import QThread, Signal

from app import __version__

DEFAULT_REPO = "Zefous/EMS-Reporter"


def parse_version(v_str: str) -> Tuple[int, ...]:
    """Parse version string like 'v1.1.0' or '1.2.3-beta' into integer tuple."""
    if not v_str:
        return (0, 0, 0)
    cleaned = v_str.strip().lstrip("vV")
    numbers = re.findall(r"\d+", cleaned)
    if not numbers:
        return (0, 0, 0)
    return tuple(int(n) for n in numbers)


def is_newer_version(current: str, remote: str) -> bool:
    """Return True if remote version is strictly newer than current version."""
    return parse_version(remote) > parse_version(current)


@dataclass
class ReleaseInfo:
    """Information about a GitHub release."""
    tag_name: str
    version: str
    name: str
    body: str
    html_url: str
    download_url: Optional[str]
    asset_name: Optional[str]
    asset_size: int


def fetch_latest_release(
    repo: str = DEFAULT_REPO,
    current_version: str = __version__,
    timeout: int = 6
) -> Optional[ReleaseInfo]:
    """Query GitHub API for the latest release. Returns ReleaseInfo or None."""
    api_url = f"https://api.github.com/repos/{repo}/releases/latest"
    req = urllib.request.Request(
        api_url,
        headers={
            "User-Agent": f"EMS-Reporter/{current_version}",
            "Accept": "application/vnd.github.v3+json",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        # 404 means no releases published yet on repo
        return None
    except (urllib.error.URLError, TimeoutError, OSError):
        return None
    except Exception:
        return None

    tag = data.get("tag_name", "")
    if not tag:
        return None

    # Check assets for executable
    assets = data.get("assets", [])
    download_url: Optional[str] = None
    asset_name: Optional[str] = None
    asset_size: int = 0

    # Prefer EMS_Reporter.exe or any .exe
    for a in assets:
        name = a.get("name", "")
        if name.lower() == "ems_reporter.exe":
            download_url = a.get("browser_download_url")
            asset_name = name
            asset_size = a.get("size", 0)
            break
        elif name.lower().endswith(".exe") and not download_url:
            download_url = a.get("browser_download_url")
            asset_name = name
            asset_size = a.get("size", 0)

    # Fallback to first asset if available
    if not download_url and assets:
        download_url = assets[0].get("browser_download_url")
        asset_name = assets[0].get("name", "")
        asset_size = assets[0].get("size", 0)

    clean_v = tag.lstrip("vV")

    return ReleaseInfo(
        tag_name=tag,
        version=clean_v,
        name=data.get("name", tag) or tag,
        body=data.get("body", "") or "Описание изменений отсутствует.",
        html_url=data.get("html_url", f"https://github.com/{repo}/releases"),
        download_url=download_url,
        asset_name=asset_name,
        asset_size=asset_size,
    )


class CheckUpdateThread(QThread):
    """Background worker thread to query GitHub releases API without freezing UI."""

    finished_check = Signal(object)  # Emits Optional[ReleaseInfo]

    def __init__(self, current_version: str = __version__, parent=None):
        super().__init__(parent)
        self.current_version = current_version

    def run(self):
        info = fetch_latest_release(current_version=self.current_version)
        self.finished_check.emit(info)


class DownloadUpdateThread(QThread):
    """Background worker thread to download new version asset with progress reporting."""

    progress = Signal(int, int, int)  # percent, downloaded_bytes, total_bytes
    finished_download = Signal(str)   # path to downloaded .update file
    failed = Signal(str)              # error message

    def __init__(self, download_url: str, dest_path: Path, parent=None):
        super().__init__(parent)
        self.download_url = download_url
        self.dest_path = dest_path

    def run(self):
        try:
            req = urllib.request.Request(
                self.download_url,
                headers={"User-Agent": f"EMS-Reporter/{__version__}"}
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                total_size = int(response.headers.get("content-length", 0))
                downloaded = 0
                chunk_size = 64 * 1024  # 64 KB

                self.dest_path.parent.mkdir(parents=True, exist_ok=True)
                with open(self.dest_path, "wb") as f:
                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = int((downloaded / total_size) * 100)
                        else:
                            percent = 0
                        self.progress.emit(percent, downloaded, total_size)

            self.finished_download.emit(str(self.dest_path))
        except Exception as e:
            self.failed.emit(str(e))


def apply_update_and_restart(update_file: str | Path) -> bool:
    """Seamlessly replace running executable with the updated file preserving original name."""
    update_path = Path(update_file).resolve()
    if not update_path.exists():
        return False

    is_frozen = getattr(sys, "frozen", False)
    target_exe = Path(sys.executable).resolve()

    if not is_frozen:
        # Development mode (running from python source)
        return False

    base_dir = target_exe.parent

    # Environment without PyInstaller temporary directory pointers
    clean_env = os.environ.copy()
    clean_env.pop("_MEIPASS", None)
    clean_env.pop("_MEIPASS2", None)

    if sys.platform == "win32":
        # Create a helper batch script to replace file and restart cleanly
        bat_path = base_dir / "_apply_update.bat"
        # Crucial: Unset _MEIPASS and _MEIPASS2 so the new instance does not look
        # into the old instance's deleted temporary directory!
        bat_content = (
            "@echo off\r\n"
            "setlocal\r\n"
            "set \"_MEIPASS=\"\r\n"
            "set \"_MEIPASS2=\"\r\n"
            f'cd /d "{str(base_dir)}"\r\n'
            ":wait_loop\r\n"
            "timeout /t 1 /nobreak >nul\r\n"
            f'move /y "{update_path.name}" "{target_exe.name}" >nul 2>nul\r\n'
            "if errorlevel 1 goto wait_loop\r\n"
            f'start "" "{target_exe.name}"\r\n'
            'del "%~f0" & exit\r\n'
        )

        try:
            with open(bat_path, "w", encoding="ascii") as f:
                f.write(bat_content)
        except Exception:
            pass

        if bat_path.exists():
            subprocess.Popen(
                ["cmd.exe", "/c", str(bat_path)],
                cwd=str(base_dir),
                env=clean_env,
                creationflags=0x08000000,  # CREATE_NO_WINDOW
            )
        else:
            cmd_script = (
                f'set "_MEIPASS=" & set "_MEIPASS2=" & '
                f':loop & timeout /t 1 /nobreak >nul & '
                f'move /y "{str(update_path)}" "{str(target_exe)}" >nul 2>nul & '
                f'if errorlevel 1 (goto loop) else (start "" "{str(target_exe)}")'
            )
            subprocess.Popen(
                f'cmd.exe /c "{cmd_script}"',
                shell=True,
                env=clean_env,
                creationflags=0x08000000,
            )
        return True
    else:
        # Linux / Unix replacement
        try:
            os.chmod(update_path, 0o755)
            shutil.move(update_path, target_exe)
            subprocess.Popen([str(target_exe)], env=clean_env)
            return True
        except Exception:
            return False
