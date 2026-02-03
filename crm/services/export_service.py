"""
Экспорт данных CRM в Google Таблицы: создание файла, запись данных, форматирование отчёта.
Сводный блок вверху: период, статусы, всего записей. Шапка таблицы — тёмно-зелёная, статусы — цветом.
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..config import ROOT, SECTION_PREFIXES
from .google_settings import read_google_settings

# Цвета для статусов в отчётах (RGB 0–1): для передачи в format_report_table
STATUS_COLORS_CLIENTS = {"active": (0.2, 0.7, 0.4), "archived": (0.6, 0.6, 0.6)}
STATUS_COLORS_DEALS = {
    "draft": (0.6, 0.6, 0.6),
    "in_progress": (0.35, 0.55, 0.9),
    "won": (0.2, 0.7, 0.4),
    "lost": (0.9, 0.35, 0.3),
}
STATUS_COLORS_TASKS = {"Да": (0.2, 0.7, 0.4), "Нет": (0.75, 0.75, 0.75)}


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


def _parse_date(s: Any) -> Optional[datetime]:
    """Извлекает дату из строки created_at (ISO или только дата)."""
    if not s:
        return None
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except Exception:
        return None


def _pad_row(row: List[Any], num_cols: int) -> List[Any]:
    """Дополняет строку пустыми ячейками до num_cols."""
    return list(row) + [""] * max(0, num_cols - len(row))


def _build_summary_block(section: str, rows_data: List[Dict[str, Any]], num_cols: int) -> List[List[Any]]:
    """
    Сводка: период, статусы (для сделок — по ячейкам + суммы по статусам), всего записей.
    """
    if not rows_data:
        return [
            _pad_row(["Сводка отчёта"], num_cols),
            _pad_row(["Период:", "—", "—"], num_cols),
            _pad_row(["Статусы:", "—"], num_cols),
            _pad_row(["Всего записей:", 0], num_cols),
        ]

    dates = []
    for r in rows_data:
        t = _parse_date(r.get("created_at"))
        if t:
            dates.append(t)
    date_min = min(dates).strftime("%Y-%m-%d") if dates else "—"
    date_max = max(dates).strftime("%Y-%m-%d") if dates else "—"

    if section == "clients":
        from collections import Counter
        statuses = Counter(r.get("status") or "" for r in rows_data)
        status_line = ", ".join(f"{k}: {v}" for k, v in sorted(statuses.items()) if v)
        if not status_line:
            status_line = "—"
        summary = [
            _pad_row(["Сводка отчёта"], num_cols),
            _pad_row(["Период:", date_min, date_max], num_cols),
            _pad_row(["Статусы:", status_line], num_cols),
            _pad_row(["Всего записей:", len(rows_data)], num_cols),
        ]
    elif section == "deals":
        from collections import defaultdict
        labels = {"draft": "Черновик", "in_progress": "В работе", "won": "Выиграно", "lost": "Проиграно"}
        order = ["draft", "in_progress", "won", "lost"]
        counts = defaultdict(int)
        sums = defaultdict(float)
        for r in rows_data:
            st = r.get("status") or "draft"
            counts[st] += 1
            amt = r.get("amount")
            if amt is not None:
                try:
                    sums[st] += float(amt)
                except (TypeError, ValueError):
                    pass
        summary = [
            _pad_row(["Сводка по сделкам"], num_cols),
            _pad_row(["Период:", date_min, date_max], num_cols),
            _pad_row(["Статус"] + [labels.get(k, k) for k in order], num_cols),
            _pad_row(["Кол-во"] + [counts[k] for k in order], num_cols),
            _pad_row(["Сумма"] + [round(sums[k], 2) for k in order], num_cols),
            _pad_row(["Всего записей:", len(rows_data)], num_cols),
        ]
    elif section == "tasks":
        done = sum(1 for r in rows_data if r.get("is_completed"))
        summary = [
            _pad_row(["Сводка отчёта"], num_cols),
            _pad_row(["Период:", date_min, date_max], num_cols),
            _pad_row(["Выполнено:", done, "Не выполнено:", len(rows_data) - done], num_cols),
            _pad_row(["Всего записей:", len(rows_data)], num_cols),
        ]
    else:
        summary = [
            _pad_row(["Сводка отчёта"], num_cols),
            _pad_row(["Период:", date_min, date_max], num_cols),
            _pad_row(["Всего записей:", len(rows_data)], num_cols),
        ]
    return summary


def export_to_google_sheet(
    title: str,
    headers: List[str],
    rows: List[List[Any]],
    folder_id: Optional[str] = None,
    section: Optional[str] = None,
    rows_data: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Создаёт Google Таблицу, записывает данные и форматирует отчёт.
    section: "clients" | "deals" | "tasks" — для сводки и подсветки статусов.
    rows_data: сырые данные (list of dict) для сводки по датам и статусам; при section без rows_data сводка по датам из rows не строится.
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
    num_cols = len(headers)
    data_rows = [[str(c) for c in row] for row in rows]

    # Первая строка — название отчёта (объединяем столбцы, синий фон, жирный курсив)
    report_title = title
    title_row = [report_title] + [""] * (num_cols - 1)

    if section and num_cols:
        summary_block = _build_summary_block(section, rows_data or [], num_cols)
        empty_row = [""] * num_cols
        table_part = [headers] + data_rows
        values = [title_row] + summary_block + [empty_row] + table_part
    else:
        values = [title_row, [""] * num_cols] + [headers] + data_rows

    data_start_row = len(values) - len(data_rows) - 1  # строка заголовка таблицы (0-based)
    num_data_rows = 1 + len(data_rows)
    total_rows = len(values)
    summary_rows = data_start_row - 2 if section else 0  # между title и пустой строкой
    range_name = f"A1:{_col_letter(num_cols)}{total_rows}"

    sheets.write_range(
        range_name=range_name,
        values=values,
        sheet_name=sheet_name,
        value_input_option="USER_ENTERED",
    )

    # Столбец статуса: после добавления столбца № — клиенты/сделки 6-й (индекс 5), задачи 7-й (индекс 6)
    status_col_index = None
    status_colors = None
    if section == "clients":
        status_col_index = 5
        status_colors = STATUS_COLORS_CLIENTS
    elif section == "deals":
        status_col_index = 5
        status_colors = STATUS_COLORS_DEALS
    elif section == "tasks":
        status_col_index = 6
        status_colors = STATUS_COLORS_TASKS

    sheets.format_report_table(
        sheet_name=sheet_name,
        num_rows=num_data_rows,
        num_cols=num_cols,
        data_start_row=data_start_row,
        summary_rows=summary_rows,
        title_row_index=0,
        report_title=report_title,
        status_col_index=status_col_index,
        status_colors=status_colors,
        data_rows_values=[headers] + data_rows if status_colors else None,
        status_text_color=True,
    )

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
