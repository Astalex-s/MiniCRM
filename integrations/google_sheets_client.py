"""
Модуль для CRUD-операций с Google Таблицами через Google API.
Подключение через сервисный аккаунт. Готов к импорту в любое приложение.

Явные функции:
  Чтение: read_entire_table, read_entire_sheet, read_range, read_row, read_column
  Запись/добавление: append_rows, write_range, write_cell, insert_rows, insert_columns
  Изменение: update_range (перезапись диапазона)
  Удаление: clear_range, clear_sheet, clear_entire_table, delete_rows, delete_columns
  Листы: get_sheet_titles, get_sheet_id, create_sheet, delete_sheet
"""

from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Загрузка .env из корня проекта
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def get_config_from_env() -> dict[str, str | None]:
    """
    Читает конфигурацию из .env (уже загружен при импорте модуля).
    Возвращает словарь для передачи в GoogleSheetsClient:
      spreadsheet_id — GOOGLE_SPREADSHEET_ID (обязателен),
      credentials_path — GOOGLE_CREDENTIALS_PATH или CREDENTIALS_PATH (опционально).
    Пример: client = GoogleSheetsClient(**get_config_from_env())
    """
    import os

    spreadsheet_id = os.environ.get("GOOGLE_SPREADSHEET_ID")
    credentials_path = (
        os.environ.get("GOOGLE_CREDENTIALS_PATH")
        or os.environ.get("CREDENTIALS_PATH")
        or None
    )
    return {
        "spreadsheet_id": spreadsheet_id or "",
        "credentials_path": credentials_path,
    }


def _sheet_range_str(sheet_name: str, range_name: str) -> str:
    """Формирует строку диапазона 'Лист'!A1:B2 с учётом кавычек в названии листа."""
    if " " in sheet_name or "'" in sheet_name:
        safe_title = "'" + sheet_name.replace("'", "''") + "'"
    else:
        safe_title = sheet_name
    return f"{safe_title}!{range_name}" if range_name else safe_title


class GoogleSheetsClient:
    """
    Клиент для работы с Google Таблицами.
    Явные методы: чтение всей таблицы/листа/диапазона, добавление строк, запись, изменение, удаление, управление листами.
    """

    def __init__(
        self,
        spreadsheet_id: str,
        credentials_path: str | Path | None = None,
    ) -> None:
        """
        Args:
            spreadsheet_id: ID таблицы (из URL: .../d/SPREADSHEET_ID/...).
            credentials_path: Путь к JSON-ключу сервисного аккаунта.
                Если None — ищется файл *excel-factory*.json в папке с модулем.
        """
        self.spreadsheet_id = spreadsheet_id
        self._credentials_path = self._resolve_credentials_path(credentials_path)
        self._service = self._build_service()

    def _resolve_credentials_path(self, path: str | Path | None) -> Path:
        if path is not None:
            return Path(path)
        import os
        env_path = os.environ.get("GOOGLE_CREDENTIALS_PATH") or os.environ.get("CREDENTIALS_PATH")
        if env_path:
            return Path(env_path)
        cwd = Path(__file__).resolve().parent
        for f in cwd.glob("*excel-factory*.json"):
            return f
        config_dir = cwd.parent / "config"
        for f in config_dir.glob("*excel-factory*.json"):
            return f
        raise FileNotFoundError(
            "Не найден JSON-ключ сервисного аккаунта. "
            "Укажите credentials_path явно или положите файл *excel-factory*.json в папку config/ или integrations/."
        )

    def _build_service(self):
        creds = Credentials.from_service_account_file(
            str(self._credentials_path),
            scopes=SCOPES,
        )
        return build("sheets", "v4", credentials=creds)

    # ——— Метаданные и листы ———

    def get_spreadsheet_metadata(self) -> dict[str, Any]:
        """Возвращает полные метаданные таблицы (листы, свойства, и т.д.)."""
        return (
            self._service.spreadsheets()
            .get(spreadsheetId=self.spreadsheet_id)
            .execute()
        )

    def get_sheet_titles(self) -> list[str]:
        """Список названий всех листов таблицы."""
        meta = self.get_spreadsheet_metadata()
        return [s["properties"]["title"] for s in meta.get("sheets", [])]

    def get_sheet_id(self, sheet_name: str) -> int:
        """Возвращает ID листа (sheetId) по его названию. Нужен для batchUpdate."""
        meta = self.get_spreadsheet_metadata()
        for s in meta.get("sheets", []):
            if s["properties"]["title"] == sheet_name:
                return s["properties"]["sheetId"]
        raise KeyError(f"Лист с названием '{sheet_name}' не найден.")

    # ——— ЧТЕНИЕ ДАННЫХ ———

    def read_entire_table(self) -> dict[str, list[list[Any]]]:
        """
        Читает все заполненные ячейки со всех листов таблицы.
        Возвращает: {название_листа: [[строка1], [строка2], ...]}.
        """
        titles = self.get_sheet_titles()
        out: dict[str, list[list[Any]]] = {}
        for title in titles:
            range_str = _sheet_range_str(title, "")
            try:
                result = (
                    self._service.spreadsheets()
                    .values()
                    .get(spreadsheetId=self.spreadsheet_id, range=range_str)
                    .execute()
                )
                out[title] = result.get("values", [])
            except HttpError:
                out[title] = []
        return out

    def read_entire_sheet(self, sheet_name: str | None = None) -> list[list[Any]]:
        """
        Читает все заполненные ячейки одного листа.
        sheet_name: название листа; если None — первый лист.
        """
        name = sheet_name or self.get_sheet_titles()[0]
        range_str = _sheet_range_str(name, "")
        try:
            result = (
                self._service.spreadsheets()
                .values()
                .get(spreadsheetId=self.spreadsheet_id, range=range_str)
                .execute()
            )
            return result.get("values", [])
        except HttpError as e:
            raise RuntimeError(f"Ошибка чтения листа '{name}': {e}") from e

    def read_range(
        self,
        range_name: str,
        sheet_name: str | None = None,
    ) -> list[list[Any]]:
        """
        Читает диапазон ячеек в A1-нотации.
        range_name: например "A1:D10", "A:B", "1:5".
        sheet_name: лист; если None — диапазон задаётся в range_name с листом при необходимости.
        """
        if sheet_name:
            range_str = _sheet_range_str(sheet_name, range_name)
        else:
            range_str = range_name
        try:
            result = (
                self._service.spreadsheets()
                .values()
                .get(spreadsheetId=self.spreadsheet_id, range=range_str)
                .execute()
            )
            return result.get("values", [])
        except HttpError as e:
            raise RuntimeError(f"Ошибка чтения диапазона {range_str}: {e}") from e

    def read_row(
        self,
        row_index: int,
        sheet_name: str | None = None,
        start_column: int = 1,
        end_column: int | None = None,
    ) -> list[Any]:
        """
        Читает одну строку по индексу (1-based).
        start_column, end_column: номера столбцов (1-based); end_column=None — до последней заполненной.
        """
        name = sheet_name or self.get_sheet_titles()[0]

        def _col_letter(n: int) -> str:
            s = ""
            while n > 0:
                n, r = divmod(n - 1, 26)
                s = chr(65 + r) + s
            return s

        start_letter = _col_letter(start_column)
        if end_column is not None:
            range_name = f"{start_letter}{row_index}:{_col_letter(end_column)}{row_index}"
        else:
            range_name = f"{start_letter}{row_index}"
        rows = self.read_range(range_name, sheet_name=name)
        if not rows:
            return []
        return rows[0]

    def read_column(
        self,
        column_letter: str,
        sheet_name: str | None = None,
        start_row: int = 1,
        end_row: int | None = None,
    ) -> list[Any]:
        """
        Читает один столбец по букве (A, B, ..., Z, AA, ...).
        start_row, end_row: номера строк (1-based); end_row=None — до последней заполненной.
        """
        name = sheet_name or self.get_sheet_titles()[0]
        if end_row is not None:
            range_name = f"{column_letter}{start_row}:{column_letter}{end_row}"
        else:
            range_name = f"{column_letter}{start_row}"
        rows = self.read_range(range_name, sheet_name=name)
        return [row[0] if row else None for row in rows]

    # ——— ЗАПИСЬ И ДОБАВЛЕНИЕ ДАННЫХ ———

    def append_rows(
        self,
        values: list[list[Any]],
        sheet_name: str | None = None,
        value_input_option: str = "USER_ENTERED",
    ) -> dict[str, Any]:
        """
        Добавляет строки в конец листа (без перезаписи существующих).
        values: список строк; каждая строка — список значений ячеек.
        value_input_option: "RAW" (как есть) или "USER_ENTERED" (формулы/форматы интерпретируются).
        """
        name = sheet_name or self.get_sheet_titles()[0]
        range_str = _sheet_range_str(name, "")
        body = {"values": values}
        return (
            self._service.spreadsheets()
            .values()
            .append(
                spreadsheetId=self.spreadsheet_id,
                range=range_str,
                valueInputOption=value_input_option,
                insertDataOption="INSERT_ROWS",
                body=body,
            )
            .execute()
        )

    def write_range(
        self,
        range_name: str,
        values: list[list[Any]],
        sheet_name: str | None = None,
        value_input_option: str = "USER_ENTERED",
    ) -> dict[str, Any]:
        """
        Записывает (перезаписывает) значения в диапазон.
        range_name: A1-нотация, например "A1:D5".
        """
        if sheet_name:
            range_str = _sheet_range_str(sheet_name, range_name)
        else:
            range_str = range_name
        body = {"values": values}
        return (
            self._service.spreadsheets()
            .values()
            .update(
                spreadsheetId=self.spreadsheet_id,
                range=range_str,
                valueInputOption=value_input_option,
                body=body,
            )
            .execute()
        )

    def write_cell(
        self,
        cell: str,
        value: Any,
        sheet_name: str | None = None,
        value_input_option: str = "USER_ENTERED",
    ) -> dict[str, Any]:
        """Записывает значение в одну ячейку (A1-нотация, например "B3")."""
        return self.write_range(
            range_name=cell,
            values=[[value]],
            sheet_name=sheet_name,
            value_input_option=value_input_option,
        )

    def update_range(
        self,
        range_name: str,
        values: list[list[Any]],
        sheet_name: str | None = None,
        value_input_option: str = "USER_ENTERED",
    ) -> dict[str, Any]:
        """Алиас для write_range: изменение данных в указанном диапазоне (перезапись)."""
        return self.write_range(
            range_name=range_name,
            values=values,
            sheet_name=sheet_name,
            value_input_option=value_input_option,
        )

    def insert_rows(
        self,
        sheet_name: str | None = None,
        start_index: int = 0,
        count: int = 1,
    ) -> dict[str, Any]:
        """
        Вставляет пустые строки (сдвигает существующие вниз).
        start_index: 0-based индекс строки, с которой вставить.
        count: сколько строк вставить.
        """
        name = sheet_name or self.get_sheet_titles()[0]
        sheet_id = self.get_sheet_id(name)
        body = {
            "requests": [
                {
                    "insertDimension": {
                        "range": {
                            "sheetId": sheet_id,
                            "dimension": "ROWS",
                            "startIndex": start_index,
                            "endIndex": start_index + count,
                        }
                    }
                }
            ]
        }
        return (
            self._service.spreadsheets()
            .batchUpdate(spreadsheetId=self.spreadsheet_id, body=body)
            .execute()
        )

    def insert_columns(
        self,
        sheet_name: str | None = None,
        start_index: int = 0,
        count: int = 1,
    ) -> dict[str, Any]:
        """
        Вставляет пустые столбцы (сдвигает существующие вправо).
        start_index: 0-based индекс столбца.
        """
        name = sheet_name or self.get_sheet_titles()[0]
        sheet_id = self.get_sheet_id(name)
        body = {
            "requests": [
                {
                    "insertDimension": {
                        "range": {
                            "sheetId": sheet_id,
                            "dimension": "COLUMNS",
                            "startIndex": start_index,
                            "endIndex": start_index + count,
                        }
                    }
                }
            ]
        }
        return (
            self._service.spreadsheets()
            .batchUpdate(spreadsheetId=self.spreadsheet_id, body=body)
            .execute()
        )

    # ——— УДАЛЕНИЕ ДАННЫХ ———

    def clear_range(
        self,
        range_name: str,
        sheet_name: str | None = None,
    ) -> dict[str, Any]:
        """Очищает содержимое и форматирование в указанном диапазоне (A1-нотация)."""
        if sheet_name:
            range_str = _sheet_range_str(sheet_name, range_name)
        else:
            range_str = range_name
        return (
            self._service.spreadsheets()
            .values()
            .clear(spreadsheetId=self.spreadsheet_id, range=range_str)
            .execute()
        )

    def clear_sheet(self, sheet_name: str | None = None) -> dict[str, Any]:
        """Очищает весь лист (все ячейки с данными)."""
        name = sheet_name or self.get_sheet_titles()[0]
        range_str = _sheet_range_str(name, "")
        return (
            self._service.spreadsheets()
            .values()
            .clear(spreadsheetId=self.spreadsheet_id, range=range_str)
            .execute()
        )

    def clear_entire_table(self) -> dict[str, list[dict[str, Any]]]:
        """Очищает все листы таблицы. Возвращает результат clear по каждому листу."""
        titles = self.get_sheet_titles()
        results: dict[str, list[dict[str, Any]]] = {}
        for title in titles:
            try:
                r = self.clear_sheet(sheet_name=title)
                results[title] = [r]
            except HttpError as e:
                results[title] = [{"error": str(e)}]
        return results

    def delete_rows(
        self,
        sheet_name: str | None = None,
        start_index: int = 0,
        count: int = 1,
    ) -> dict[str, Any]:
        """
        Удаляет строки (сдвигает следующие вверх).
        start_index: 0-based индекс первой удаляемой строки.
        count: сколько строк удалить.
        """
        name = sheet_name or self.get_sheet_titles()[0]
        sheet_id = self.get_sheet_id(name)
        body = {
            "requests": [
                {
                    "deleteDimension": {
                        "range": {
                            "sheetId": sheet_id,
                            "dimension": "ROWS",
                            "startIndex": start_index,
                            "endIndex": start_index + count,
                        }
                    }
                }
            ]
        }
        return (
            self._service.spreadsheets()
            .batchUpdate(spreadsheetId=self.spreadsheet_id, body=body)
            .execute()
        )

    def delete_columns(
        self,
        sheet_name: str | None = None,
        start_index: int = 0,
        count: int = 1,
    ) -> dict[str, Any]:
        """Удаляет столбцы (сдвигает следующие влево). start_index — 0-based."""
        name = sheet_name or self.get_sheet_titles()[0]
        sheet_id = self.get_sheet_id(name)
        body = {
            "requests": [
                {
                    "deleteDimension": {
                        "range": {
                            "sheetId": sheet_id,
                            "dimension": "COLUMNS",
                            "startIndex": start_index,
                            "endIndex": start_index + count,
                        }
                    }
                }
            ]
        }
        return (
            self._service.spreadsheets()
            .batchUpdate(spreadsheetId=self.spreadsheet_id, body=body)
            .execute()
        )

    # ——— УПРАВЛЕНИЕ ЛИСТАМИ ———

    def create_sheet(
        self,
        title: str,
        rows: int = 1000,
        cols: int = 26,
    ) -> dict[str, Any]:
        """Создаёт новый лист с указанным названием и размером (строки × столбцы)."""
        body = {
            "requests": [
                {
                    "addSheet": {
                        "properties": {
                            "title": title,
                            "gridProperties": {
                                "rowCount": rows,
                                "columnCount": cols,
                            },
                        }
                    }
                }
            ]
        }
        return (
            self._service.spreadsheets()
            .batchUpdate(spreadsheetId=self.spreadsheet_id, body=body)
            .execute()
        )

    def delete_sheet(self, sheet_name: str | None = None, sheet_id: int | None = None) -> dict[str, Any]:
        """
        Удаляет лист. Укажите sheet_name или sheet_id (ID из метаданных).
        Хотя бы один лист в таблице должен остаться.
        """
        if sheet_id is None:
            if sheet_name is None:
                raise ValueError("Укажите sheet_name или sheet_id.")
            sheet_id = self.get_sheet_id(sheet_name)
        body = {
            "requests": [{"deleteSheet": {"sheetId": sheet_id}}]
        }
        return (
            self._service.spreadsheets()
            .batchUpdate(spreadsheetId=self.spreadsheet_id, body=body)
            .execute()
        )

    # ——— ФОРМАТИРОВАНИЕ (для отчётов, документов) ———

    def merge_cells(
        self,
        sheet_name: str | None = None,
        start_row: int = 0,
        end_row: int = 1,
        start_column: int = 0,
        end_column: int = 1,
    ) -> dict[str, Any]:
        """
        Объединяет ячейки в прямоугольный диапазон.
        Индексы 0-based: start_row, end_row (исключающий), start_column, end_column (исключающий).
        """
        name = sheet_name or self.get_sheet_titles()[0]
        sheet_id = self.get_sheet_id(name)
        body = {
            "requests": [
                {
                    "mergeCells": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": start_row,
                            "endRowIndex": end_row,
                            "startColumnIndex": start_column,
                            "endColumnIndex": end_column,
                        },
                        "mergeType": "MERGE_ALL",
                    }
                }
            ]
        }
        return (
            self._service.spreadsheets()
            .batchUpdate(spreadsheetId=self.spreadsheet_id, body=body)
            .execute()
        )

    def format_range_bold(
        self,
        sheet_name: str | None = None,
        start_row: int = 0,
        end_row: int = 1,
        start_column: int = 0,
        end_column: int = 1,
    ) -> dict[str, Any]:
        """Делает текст в диапазоне жирным. Индексы 0-based (end — исключающий)."""
        name = sheet_name or self.get_sheet_titles()[0]
        sheet_id = self.get_sheet_id(name)
        body = {
            "requests": [
                {
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": start_row,
                            "endRowIndex": end_row,
                            "startColumnIndex": start_column,
                            "endColumnIndex": end_column,
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "textFormat": {"bold": True},
                            }
                        },
                        "fields": "userEnteredFormat.textFormat.bold",
                    }
                }
            ]
        }
        return (
            self._service.spreadsheets()
            .batchUpdate(spreadsheetId=self.spreadsheet_id, body=body)
            .execute()
        )

    def format_range_header(
        self,
        sheet_name: str | None = None,
        start_row: int = 0,
        end_row: int = 1,
        start_column: int = 0,
        end_column: int = 1,
    ) -> dict[str, Any]:
        """Форматирует диапазон как заголовок таблицы: жирный, серый фон, выравнивание по центру."""
        return self.format_range_header_colored(
            sheet_name, start_row, end_row, start_column, end_column,
            red=0.9, green=0.9, blue=0.9,
            text_red=0, text_green=0, text_blue=0,
        )

    def format_range_header_colored(
        self,
        sheet_name: str | None = None,
        start_row: int = 0,
        end_row: int = 1,
        start_column: int = 0,
        end_column: int = 1,
        *,
        red: float = 0.1,
        green: float = 0.35,
        blue: float = 0.2,
        text_red: float = 1,
        text_green: float = 1,
        text_blue: float = 1,
    ) -> dict[str, Any]:
        """Заголовок таблицы с произвольным фоном и цветом текста (0–1). По умолчанию — тёмно‑зелёный фон, белый текст."""
        name = sheet_name or self.get_sheet_titles()[0]
        sheet_id = self.get_sheet_id(name)
        body = {
            "requests": [
                {
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": start_row,
                            "endRowIndex": end_row,
                            "startColumnIndex": start_column,
                            "endColumnIndex": end_column,
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "backgroundColor": {"red": red, "green": green, "blue": blue},
                                "horizontalAlignment": "CENTER",
                                "textFormat": {
                                    "bold": True,
                                    "fontSize": 11,
                                    "foregroundColor": {"red": text_red, "green": text_green, "blue": text_blue},
                                },
                            }
                        },
                        "fields": "userEnteredFormat(backgroundColor,horizontalAlignment,textFormat)",
                    }
                }
            ]
        }
        return (
            self._service.spreadsheets()
            .batchUpdate(spreadsheetId=self.spreadsheet_id, body=body)
            .execute()
        )

    def format_range_background(
        self,
        sheet_name: str | None = None,
        start_row: int = 0,
        end_row: int = 1,
        start_column: int = 0,
        end_column: int = 1,
        red: float = 1,
        green: float = 1,
        blue: float = 1,
    ) -> dict[str, Any]:
        """Заливает диапазон цветом (RGB 0–1). Индексы 0-based, end — исключающий."""
        name = sheet_name or self.get_sheet_titles()[0]
        sheet_id = self.get_sheet_id(name)
        body = {
            "requests": [
                {
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": start_row,
                            "endRowIndex": end_row,
                            "startColumnIndex": start_column,
                            "endColumnIndex": end_column,
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "backgroundColor": {"red": red, "green": green, "blue": blue},
                            }
                        },
                        "fields": "userEnteredFormat.backgroundColor",
                    }
                }
            ]
        }
        return (
            self._service.spreadsheets()
            .batchUpdate(spreadsheetId=self.spreadsheet_id, body=body)
            .execute()
        )

    def format_report_table(
        self,
        sheet_name: str | None = None,
        num_rows: int = 1,
        num_cols: int = 1,
    ) -> dict[str, Any]:
        """
        Форматирование отчёта: заголовок (жирный, фон, по центру), границы таблицы,
        перенос текста в ячейках данных, автоширина столбцов.
        num_rows, num_cols — количество строк и столбцов (включая заголовок). Индексы 0-based, end — исключающий.
        """
        name = sheet_name or self.get_sheet_titles()[0]
        sheet_id = self.get_sheet_id(name)
        requests = []

        # 1. Заголовок (первая строка): жирный, серый фон, по центру
        requests.append({
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": 0,
                    "endRowIndex": 1,
                    "startColumnIndex": 0,
                    "endColumnIndex": num_cols,
                },
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {"red": 0.85, "green": 0.85, "blue": 0.85},
                        "horizontalAlignment": "CENTER",
                        "verticalAlignment": "MIDDLE",
                        "wrapStrategy": "WRAP",
                        "textFormat": {"bold": True, "fontSize": 11},
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,horizontalAlignment,verticalAlignment,wrapStrategy,textFormat)",
            }
        })

        # 2. Границы всей таблицы
        requests.append({
            "updateBorders": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": 0,
                    "endRowIndex": num_rows,
                    "startColumnIndex": 0,
                    "endColumnIndex": num_cols,
                },
                "top": {"style": "SOLID", "width": 1, "color": {"red": 0.6, "green": 0.6, "blue": 0.6}},
                "bottom": {"style": "SOLID", "width": 1, "color": {"red": 0.6, "green": 0.6, "blue": 0.6}},
                "left": {"style": "SOLID", "width": 1, "color": {"red": 0.6, "green": 0.6, "blue": 0.6}},
                "right": {"style": "SOLID", "width": 1, "color": {"red": 0.6, "green": 0.6, "blue": 0.6}},
                "innerHorizontal": {"style": "SOLID", "width": 1, "color": {"red": 0.8, "green": 0.8, "blue": 0.8}},
                "innerVertical": {"style": "SOLID", "width": 1, "color": {"red": 0.8, "green": 0.8, "blue": 0.8}},
            }
        })

        # 3. Перенос текста и выравнивание для области данных (строки 1..num_rows)
        if num_rows > 1:
            requests.append({
                "repeatCell": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": 1,
                        "endRowIndex": num_rows,
                        "startColumnIndex": 0,
                        "endColumnIndex": num_cols,
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "wrapStrategy": "WRAP",
                            "verticalAlignment": "TOP",
                        }
                    },
                    "fields": "userEnteredFormat(wrapStrategy,verticalAlignment)",
                }
            })

        # 4. Автоширина столбцов
        requests.append({
            "autoResizeDimensions": {
                "dimensions": {
                    "sheetId": sheet_id,
                    "dimension": "COLUMNS",
                    "startIndex": 0,
                    "endIndex": num_cols,
                }
            }
        })

        body = {"requests": requests}
        return (
            self._service.spreadsheets()
            .batchUpdate(spreadsheetId=self.spreadsheet_id, body=body)
            .execute()
        )

    def rename_sheet(
        self,
        new_title: str,
        sheet_name: str | None = None,
        sheet_id: int | None = None,
    ) -> dict[str, Any]:
        """Переименовывает лист. Укажите sheet_name или sheet_id, и новый заголовок new_title."""
        if sheet_id is None:
            name = sheet_name or self.get_sheet_titles()[0]
            sheet_id = self.get_sheet_id(name)
        body = {
            "requests": [
                {
                    "updateSheetProperties": {
                        "properties": {"sheetId": sheet_id, "title": new_title},
                        "fields": "title",
                    }
                }
            ]
        }
        return (
            self._service.spreadsheets()
            .batchUpdate(spreadsheetId=self.spreadsheet_id, body=body)
            .execute()
        )

    # ——— Обратная совместимость (алиасы) ———

    def get_sheet_metadata(self) -> dict[str, Any]:
        """Алиас для get_spreadsheet_metadata()."""
        return self.get_spreadsheet_metadata()

    def read_all_cells(self) -> dict[str, list[list[Any]]]:
        """Алиас для read_entire_table()."""
        return self.read_entire_table()

    def read_all_cells_flat(self) -> list[list[Any]]:
        """Читает все ячейки первого листа. Алиас для read_entire_sheet(None)."""
        return self.read_entire_sheet(sheet_name=None)

    def append_values(
        self,
        values: list[list[Any]],
        sheet_name: str | None = None,
        range_name: str | None = None,
        value_input_option: str = "USER_ENTERED",
    ) -> dict[str, Any]:
        """Алиас для append_rows() (range_name игнорируется — добавление в конец)."""
        return self.append_rows(
            values=values,
            sheet_name=sheet_name,
            value_input_option=value_input_option,
        )


# ——— Точка входа ———

def main() -> None:
    """
    Точка входа: подключение к таблице, запись данных (с комментариями), затем чтение и вывод.
    """
    import os
    import sys

    # —— Конфигурация: ID таблицы из .env, переменной окружения или аргумента ——
    spreadsheet_id = (
        os.environ.get("GOOGLE_SPREADSHEET_ID")
        or (sys.argv[1] if len(sys.argv) > 1 else None)
    )
    if not spreadsheet_id:
        print(
            "Укажите ID таблицы в .env (GOOGLE_SPREADSHEET_ID=...),\n"
            "  или: GOOGLE_SPREADSHEET_ID=... python google_sheets_client.py\n"
            "  или: python google_sheets_client.py SPREADSHEET_ID",
            file=sys.stderr,
        )
        sys.exit(1)

    credentials_path = (
        os.environ.get("GOOGLE_CREDENTIALS_PATH")
        or os.environ.get("CREDENTIALS_PATH")
        or None
    )

    client = GoogleSheetsClient(
        spreadsheet_id=spreadsheet_id,
        credentials_path=credentials_path,
    )

    # —— Запись в таблицу: 10 строк × 8 столбцов (тестовые данные) ——
    sheet_name = client.get_sheet_titles()[0] if client.get_sheet_titles() else None
    if not sheet_name:
        print("В таблице нет листов. Создайте лист вручную или через client.create_sheet(...).", file=sys.stderr)
        sys.exit(1)

    # Тестовые данные: заголовок + 9 строк (итого 10 строк), 8 столбцов
    test_data_10x8 = [
        # Строка 1 — заголовки
        ["№", "Название", "Категория", "Цена", "Кол-во", "Дата", "Статус", "Примечание"],
        # Строки 2–10 — данные (9 строк)
        [1, "Ноутбук X1", "Техника", 89900, 2, "2025-01-15", "Доставлен", "Оплачен"],
        [2, "Мышь беспроводная", "Аксессуары", 1200, 5, "2025-01-16", "В пути", ""],
        [3, "Клавиатура", "Аксессуары", 3500, 3, "2025-01-17", "Ожидает", "Склад А"],
        [4, "Монитор 27\"", "Техника", 25000, 1, "2025-01-18", "Доставлен", ""],
        [5, "Веб-камера", "Техника", 4500, 4, "2025-01-19", "В пути", ""],
        [6, "Коврик для мыши", "Аксессуары", 399, 10, "2025-01-20", "Доставлен", "Серия Pro"],
        [7, "USB‑хаб", "Аксессуары", 1890, 2, "2025-01-21", "Ожидает", ""],
        [8, "Наушники", "Аксессуары", 5200, 1, "2025-01-22", "Доставлен", "С шумоподавлением"],
        [9, "Блок питания", "Техника", 3200, 2, "2025-01-23", "В пути", ""],
    ]

    client.write_range(
        range_name="A1:H10",
        values=test_data_10x8,
        sheet_name=sheet_name,
        value_input_option="USER_ENTERED",
    )
    print("Записано 10 строк × 8 столбцов в диапазон A1:H10")

    # —— Чтение всей таблицы и вывод в консоль для проверки ——
    print("-" * 60)
    print("Листы:", client.get_sheet_titles())
    print("-" * 60)
    all_data = client.read_entire_table()
    for name, rows in all_data.items():
        print(f"\n--- Лист: {name} ---")
        if not rows:
            print("  (пусто)")
            continue
        for row in rows:
            print(row)


if __name__ == "__main__":
    main()
