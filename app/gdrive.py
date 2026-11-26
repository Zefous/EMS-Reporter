"""Google Drive API v3 integration with DPAPI token encryption and incremental sync."""

from __future__ import annotations

import ctypes
import ctypes.wintypes
import hashlib
import json
import mimetypes
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

SCOPES = ["https://www.googleapis.com/auth/drive.file"]
REPORT_FOLDER_PROP_KEY = "ems_reporter_type"
REPORT_FOLDER_PROP_VAL = "report_folder"


def get_app_data_dir() -> Path:
    """Return local user data directory for storing encrypted Google Drive tokens."""
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        d = Path(base) / "EMS_Reporter"
    else:
        d = Path.home() / ".local" / "share" / "EMS_Reporter"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_token_path() -> Path:
    """Return path to the encrypted Google Drive token file."""
    return get_app_data_dir() / "gdrive_token.dat"


def find_client_secrets(custom_path: Optional[str] = None) -> Optional[Path]:
    """Locate client_secrets.json in user directory, app directory, or PyInstaller bundle."""
    candidates: List[Path] = []
    if custom_path:
        candidates.append(Path(custom_path))

    if getattr(sys, "frozen", False):
        candidates.append(Path(sys.executable).parent / "client_secrets.json")
    else:
        candidates.append(Path.cwd() / "client_secrets.json")

    candidates.append(get_app_data_dir() / "client_secrets.json")

    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        candidates.append(Path(sys._MEIPASS) / "client_secrets.json")

    for p in candidates:
        if p.is_file():
            return p
    return None


# --- Windows DPAPI encryption helpers ---

class _DATA_BLOB(ctypes.Structure):
    _fields_ = [
        ("cbData", ctypes.wintypes.DWORD),
        ("pbData", ctypes.POINTER(ctypes.c_char)),
    ]


def protect_data(raw: bytes) -> bytes:
    """Encrypt bytes using Windows DPAPI (CryptProtectData). Falls back to raw on non-Windows."""
    if sys.platform != "win32" or not raw:
        return raw
    try:
        crypt32 = ctypes.windll.crypt32
        kernel32 = ctypes.windll.kernel32
        buf = ctypes.create_string_buffer(raw, len(raw))
        blob_in = _DATA_BLOB(len(raw), buf)
        blob_out = _DATA_BLOB()
        if crypt32.CryptProtectData(
            ctypes.byref(blob_in),
            "EMS_Reporter_GDrive_Token",
            None,
            None,
            None,
            0,
            ctypes.byref(blob_out),
        ):
            try:
                return ctypes.string_at(blob_out.pbData, blob_out.cbData)
            finally:
                kernel32.LocalFree(blob_out.pbData)
    except Exception:
        pass
    return raw


def unprotect_data(enc: bytes) -> bytes:
    """Decrypt bytes using Windows DPAPI (CryptUnprotectData). Falls back to raw on non-Windows."""
    if sys.platform != "win32" or not enc:
        return enc
    try:
        crypt32 = ctypes.windll.crypt32
        kernel32 = ctypes.windll.kernel32
        buf = ctypes.create_string_buffer(enc, len(enc))
        blob_in = _DATA_BLOB(len(enc), buf)
        blob_out = _DATA_BLOB()
        if crypt32.CryptUnprotectData(
            ctypes.byref(blob_in),
            None,
            None,
            None,
            None,
            0,
            ctypes.byref(blob_out),
        ):
            try:
                return ctypes.string_at(blob_out.pbData, blob_out.cbData)
            finally:
                kernel32.LocalFree(blob_out.pbData)
    except Exception:
        pass
    return enc


def compute_md5(file_path: Path) -> str:
    """Compute MD5 hex digest of a local file."""
    h = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


@dataclass
class SyncPlan:
    """Result of comparing local image files against remote Google Drive folder contents."""
    to_upload: List[Path] = field(default_factory=list)
    already_synced: List[Path] = field(default_factory=list)
    orphaned_remote: List[Dict[str, Any]] = field(default_factory=list)


def plan_sync(local_files: List[Path], remote_files: List[Dict[str, Any]]) -> SyncPlan:
    """Compare local files with remote files by name + md5Checksum (or size).

    - Files already present in remote with matching md5 (or size if md5 missing) are skipped.
    - New or modified local files are scheduled for upload.
    - Remote files whose names no longer exist locally are marked as orphaned_remote.
    """
    plan = SyncPlan()
    remote_by_name: Dict[str, List[Dict[str, Any]]] = {}
    for rf in remote_files:
        name = rf.get("name", "")
        remote_by_name.setdefault(name, []).append(rf)

    local_names = {p.name for p in local_files}

    for lp in local_files:
        candidates = remote_by_name.get(lp.name, [])
        if not candidates:
            plan.to_upload.append(lp)
            continue

        local_md5 = compute_md5(lp)
        local_size = str(lp.stat().st_size)
        matched = False
        for rf in candidates:
            r_md5 = rf.get("md5Checksum")
            r_size = str(rf.get("size", ""))
            if r_md5 and r_md5 == local_md5:
                matched = True
                break
            if not r_md5 and r_size == local_size:
                matched = True
                break

        if matched:
            plan.already_synced.append(lp)
        else:
            plan.to_upload.append(lp)

    for rf in remote_files:
        if rf.get("name", "") not in local_names:
            plan.orphaned_remote.append(rf)

    return plan


def _escape_query_val(val: str) -> str:
    return val.replace("\\", "\\\\").replace("'", "\\'")


class GoogleDriveClient:
    """Wrapper around Google Drive API v3 for EMS Reporter."""

    def __init__(self, service: Any = None, token_path: Optional[Path] = None):
        self._service = service
        self.token_path = token_path or get_token_path()
        self._creds = None

    def load_credentials(self):
        """Load and refresh saved OAuth credentials if available."""
        if self._service is not None:
            return None

        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request

        if not self.token_path.is_file():
            return None

        try:
            raw_bytes = self.token_path.read_bytes()
            decrypted = unprotect_data(raw_bytes)
            info = json.loads(decrypted.decode("utf-8"))
            creds = Credentials.from_authorized_user_info(info, SCOPES)
        except Exception:
            return None

        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                self._save_credentials(creds)
            except Exception:
                return None

        if creds and creds.valid:
            self._creds = creds
            return creds
        return None

    def _save_credentials(self, creds) -> None:
        self.token_path.parent.mkdir(parents=True, exist_ok=True)
        raw = creds.to_json().encode("utf-8")
        self.token_path.write_bytes(protect_data(raw))

    def is_authenticated(self) -> bool:
        if self._service is not None:
            return True
        return self.load_credentials() is not None

    def authenticate(self, client_secrets_path: Optional[str] = None) -> Optional[Dict[str, str]]:
        """Run OAuth 2.0 browser flow and save encrypted token."""
        from google_auth_oauthlib.flow import InstalledAppFlow

        secrets_file = find_client_secrets(client_secrets_path)
        if not secrets_file:
            raise FileNotFoundError(
                "Файл client_secrets.json не найден.\n"
                "Положите client_secrets.json рядом с программой или укажите его вручную."
            )

        flow = InstalledAppFlow.from_client_secrets_file(str(secrets_file), SCOPES)
        creds = flow.run_local_server(port=0)
        self._creds = creds
        self._save_credentials(creds)
        self._service = None
        return self.get_user_info()

    def logout(self) -> None:
        """Remove saved token and reset service."""
        self._creds = None
        self._service = None
        if self.token_path.is_file():
            try:
                self.token_path.unlink()
            except OSError:
                pass

    @property
    def service(self):
        if self._service is not None:
            return self._service
        creds = self._creds or self.load_credentials()
        if not creds:
            raise RuntimeError("Не выполнена авторизация в Google Диске.")
        from googleapiclient.discovery import build
        self._service = build("drive", "v3", credentials=creds, cache_discovery=False)
        return self._service

    def get_user_info(self) -> Optional[Dict[str, str]]:
        """Return authenticated user's displayName and emailAddress."""
        try:
            res = self.service.about().get(fields="user(displayName,emailAddress)").execute()
            return res.get("user")
        except Exception:
            return None

    def list_report_folders(self) -> List[Dict[str, Any]]:
        """List report folders previously created by EMS Reporter, newest first."""
        q = (
            "mimeType = 'application/vnd.google-apps.folder' "
            "and trashed = false "
            f"and appProperties has {{ key='{REPORT_FOLDER_PROP_KEY}' and value='{REPORT_FOLDER_PROP_VAL}' }}"
        )
        res = self.service.files().list(
            q=q,
            spaces="drive",
            fields="files(id, name, webViewLink, modifiedTime)",
            orderBy="modifiedTime desc",
            pageSize=100,
        ).execute()
        return res.get("files", [])

    def create_unique_report_folder(self, base_name: str) -> Dict[str, Any]:
        """Create a new report folder; if base_name exists, append (2), (3), etc."""
        existing = self.list_report_folders()
        existing_names = {f.get("name", "") for f in existing}

        candidate = base_name.strip() or "Отчёт EMS"
        if candidate in existing_names:
            idx = 2
            while f"{candidate} ({idx})" in existing_names:
                idx += 1
            candidate = f"{candidate} ({idx})"

        metadata = {
            "name": candidate,
            "mimeType": "application/vnd.google-apps.folder",
            "appProperties": {REPORT_FOLDER_PROP_KEY: REPORT_FOLDER_PROP_VAL},
        }
        folder = self.service.files().create(
            body=metadata,
            fields="id, name, webViewLink",
        ).execute()
        return folder

    def get_or_create_subfolder(self, parent_id: str, folder_name: str) -> Dict[str, Any]:
        """Find or create a field subfolder inside parent_id and ensure link-sharing is enabled."""
        escaped_name = _escape_query_val(folder_name)
        escaped_parent = _escape_query_val(parent_id)
        q = (
            f"name = '{escaped_name}' "
            f"and '{escaped_parent}' in parents "
            "and mimeType = 'application/vnd.google-apps.folder' "
            "and trashed = false"
        )
        res = self.service.files().list(
            q=q,
            spaces="drive",
            fields="files(id, name, webViewLink)",
            pageSize=10,
        ).execute()
        files = res.get("files", [])
        if files:
            folder = files[0]
        else:
            metadata = {
                "name": folder_name,
                "mimeType": "application/vnd.google-apps.folder",
                "parents": [parent_id],
            }
            folder = self.service.files().create(
                body=metadata,
                fields="id, name, webViewLink",
            ).execute()
            self.ensure_anyone_reader_permission(folder["id"])

        if not folder.get("webViewLink"):
            folder["webViewLink"] = f"https://drive.google.com/drive/folders/{folder['id']}"
        return folder

    def ensure_anyone_reader_permission(self, file_id: str) -> None:
        """Grant 'anyone with the link can view' permission on a folder."""
        try:
            self.service.permissions().create(
                fileId=file_id,
                body={"type": "anyone", "role": "reader"},
                fields="id",
            ).execute()
        except Exception:
            pass

    def list_files_in_folder(self, folder_id: str) -> List[Dict[str, Any]]:
        """List all non-trashed files inside a Google Drive folder."""
        escaped_parent = _escape_query_val(folder_id)
        q = (
            f"'{escaped_parent}' in parents "
            "and mimeType != 'application/vnd.google-apps.folder' "
            "and trashed = false"
        )
        all_files: List[Dict[str, Any]] = []
        page_token: Optional[str] = None
        while True:
            res = self.service.files().list(
                q=q,
                spaces="drive",
                fields="nextPageToken, files(id, name, size, md5Checksum)",
                pageSize=200,
                pageToken=page_token,
            ).execute()
            all_files.extend(res.get("files", []))
            page_token = res.get("nextPageToken")
            if not page_token:
                break
        return all_files

    def upload_file(self, parent_id: str, file_path: Path) -> Dict[str, Any]:
        """Upload a local file into parent_id on Google Drive."""
        from googleapiclient.http import MediaFileUpload

        mime_type, _ = mimetypes.guess_type(str(file_path))
        if not mime_type:
            mime_type = "application/octet-stream"

        metadata = {
            "name": file_path.name,
            "parents": [parent_id],
        }
        media = MediaFileUpload(str(file_path), mimetype=mime_type, resumable=True)
        return self.service.files().create(
            body=metadata,
            media_body=media,
            fields="id, name, webViewLink",
        ).execute()

    def delete_file(self, file_id: str) -> None:
        """Delete a file from Google Drive."""
        self.service.files().delete(fileId=file_id).execute()
