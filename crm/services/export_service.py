"""
Экспорт данных CRM в Google Таблицы: создание файла, запись данных, форматирование отчёта.
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..config import ROOT, SECTION_PREFIXES
from .google_settings import read_google_settings


def _col_letter(n: int) -> str:
    """Номер столбца (1-based) в букву A, B, ..., Z, AA, ..."""
    s = ""
    while n > 0:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s or "A"


def _resolve_creds_path(path: Optional[str]) -> Optional[str]:
    if not path or Path(path).is_absolute():
        return path
    return str(ROOT / path.replace("\\", "/"))


def _get_service_account_email(credentials_path: str) -> str:
    p = Path(credentials_path)
    if not p.is_absolute():
        p = ROOT / credentials_path.replace("\\", "/")
    data = json.loads(p.read_text(encoding="utf-8"))
    return data.get("client_email") or ""


def export_to_google_sheet(
    title: str,
    headers: List[str],
    rows: List[List[Any]],
    folder_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Создаёт Google Таблицу (OAuth пользователя при наличии client_secret),
    записывает данные и применяет форматирование отчёта (заголовок, границы, автоширина).
    """
    from integrations.google_drive_client import GoogleDriveClient, GoogleDriveUserClient, MIME_GOOGLE_SHEET
    from integrations.google_sheets_client import GoogleSheetsClient

    settings = read_google_settings()
    creds_path = _resolve_creds_path(settings.get("credentials_path"))
    client_secret_path = _resolve_creds_path(settings.get("client_secret_path"))
    fid = folder_id or settings.get("folder_id")

    title_with_ts = f"{title} {datetime.now().strftime('%Y-%m-%d %H-%M-%S')}"

    if client_secret_path:
        drive_user = GoogleDriveUserClient(client_secret_path=client_secret_path)
        meta = drive_user.create_google_sheet(title=title_with_ts, folder_id=fid or None)
        spreadsheet_id = meta["id"]
        web_view_link = meta.get("webViewLink", "")
        if creds_path:
            sa_email = _get_service_account_email(creds_path)
            if sa_email:
                drive_user.share_file_with_email(spreadsheet_id, sa_email, role="writer")
    else:
        drive = GoogleDriveClient(credentials_path=creds_path)
        meta = drive.create_file(title_with_ts, MIME_GOOGLE_SHEET, folder_id=fid or None)
        spreadsheet_id = meta["id"]
        web_view_link = meta.get("webViewLink", "")

    sheets = GoogleSheetsClient(spreadsheet_id=spreadsheet_id, credentials_path=creds_path)
    sheet_name = sheets.get_sheet_titles()[0]
    values = [headers] + [[str(c) for c in row] for row in rows]
    num_rows, num_cols = len(values), len(headers)
    range_name = f"A1:{_col_letter(num_cols)}{num_rows}"

    sheets.write_range(
        range_name=range_name,
        values=values,
        sheet_name=sheet_name,
        value_input_option="USER_ENTERED",
    )
    sheets.format_report_table(sheet_name=sheet_name, num_rows=num_rows, num_cols=num_cols)

    return {"spreadsheet_id": spreadsheet_id, "webViewLink": web_view_link, "title": title_with_ts}


def list_export_files(section: str) -> List[Dict[str, Any]]:
    """Список отчётов в папке Drive по разделу (clients/deals/tasks)."""
    from integrations.google_drive_client import GoogleDriveClient, GoogleDriveUserClient

    settings = read_google_settings()
    creds_path = _resolve_creds_path(settings.get("credentials_path"))
    client_secret_path = _resolve_creds_path(settings.get("client_secret_path"))
    fid = settings.get("folder_id")
    prefix = SECTION_PREFIXES.get(section)
    if not prefix:
        return []

    if client_secret_path:
        client = GoogleDriveUserClient(client_secret_path=client_secret_path)
    else:
        client = GoogleDriveClient(credentials_path=creds_path)

    q = "trashed = false and mimeType = 'application/vnd.google-apps.spreadsheet'"
    if fid and fid != "root":
        q += f" and '{fid}' in parents"
    else:
        q += " and 'root' in parents"

    result = (
        client._service.files()
        .list(
            q=q,
            pageSize=100,
            orderBy="modifiedTime desc",
            fields="nextPageToken, files(id, name, mimeType, modifiedTime, webViewLink)",
        )
        .execute()
    )
    files = result.get("files", [])
    out = [f for f in files if (f.get("name") or "").startswith(prefix)]
    return [
        {"id": f["id"], "name": f["name"], "webViewLink": f.get("webViewLink", ""), "modifiedTime": f.get("modifiedTime", "")}
        for f in out
    ]
