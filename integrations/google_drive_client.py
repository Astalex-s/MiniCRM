"""
Модуль для CRUD-операций с Google Drive через Google Drive API.

Два режима аутентификации:
  1. Сервисный аккаунт (JSON-ключ *excel-factory*.json или из ENV) — класс GoogleDriveClient:
     Чтение: list_files, get_file, get_file_metadata
     Создание: create_file
     Удаление: delete_file
     Важно: у сервисного аккаунта свой отдельный Drive (часто пустой). Ваши личные файлы
     там не видны, если вы не открыли к ним доступ для email сервисного аккаунта.

  2. OAuth2 от имени пользователя (client_secret JSON в папке проекта) — класс GoogleDriveUserClient:
     Список файлов: list_files  — видит ваш «Мой диск».
     Создание: create_google_doc, create_google_sheet
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from dotenv import load_dotenv
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from google.oauth2.credentials import Credentials as UserCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Загрузка .env из корня проекта
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)

# Скоупы для Drive API
SCOPES_DRIVE = ["https://www.googleapis.com/auth/drive"]
# Для OAuth2 пользователя: Drive + создание файлов в любой папке
SCOPES_DRIVE_USER = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/drive.file",
]

# MIME-типы Google-приложений
MIME_GOOGLE_DOC = "application/vnd.google-apps.document"
MIME_GOOGLE_SHEET = "application/vnd.google-apps.spreadsheet"


def get_drive_config_from_env() -> Dict[str, Optional[str]]:
    """
    Читает конфигурацию Drive из .env.
    Возвращает словарь: credentials_path, folder_id (опционально).
    """
    import os

    credentials_path = (
        os.environ.get("GOOGLE_CREDENTIALS_PATH")
        or os.environ.get("CREDENTIALS_PATH")
        or None
    )
    folder_id = os.environ.get("GOOGLE_DRIVE_FOLDER_ID") or None
    return {
        "credentials_path": credentials_path,
        "folder_id": folder_id,
    }


# ——— Сервисный аккаунт: CRUD по файлам Drive ———


class GoogleDriveClient:
    """
    Клиент для работы с Google Drive через сервисный аккаунт.
    CRUD: список файлов, чтение метаданных/контента, создание, удаление.
    """

    def __init__(self, credentials_path: Optional[Union[str, Path]] = None) -> None:
        """
        Args:
            credentials_path: Путь к JSON-ключу сервисного аккаунта.
                Если None — берётся из ENV (GOOGLE_CREDENTIALS_PATH / CREDENTIALS_PATH)
                или ищется файл *excel-factory*.json в папке с модулем.
        """
        self._credentials_path = self._resolve_credentials_path(credentials_path)
        self._service = self._build_service()

    def _resolve_credentials_path(self, path: Optional[Union[str, Path]]) -> Path:
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
            "Укажите credentials_path явно, задайте GOOGLE_CREDENTIALS_PATH в .env "
            "или положите файл *excel-factory*.json в папку config/ или integrations/."
        )

    def _build_service(self):
        creds = ServiceAccountCredentials.from_service_account_file(
            str(self._credentials_path),
            scopes=SCOPES_DRIVE,
        )
        return build("drive", "v3", credentials=creds)

    def list_files(
        self,
        folder_id: Optional[str] = None,
        page_size: int = 100,
        order_by: str = "name",
    ) -> List[Dict[str, Any]]:
        """
        Возвращает список файлов и папок в указанной папке (или в корне Drive).

        Args:
            folder_id: ID папки в Drive. None или "root" — корень Drive сервисного аккаунта.
            page_size: Максимум записей в ответе (по умолчанию 100).
            order_by: Сортировка, например "name", "modifiedTime desc".

        Returns:
            Список словарей с полями id, name, mimeType, modifiedTime и др.
        """
        q = "trashed = false"
        if folder_id and folder_id != "root":
            q += f" and '{folder_id}' in parents"
        else:
            q += " and 'root' in parents"

        result = (
            self._service.files()
            .list(
                q=q,
                pageSize=page_size,
                fields="nextPageToken, files(id, name, mimeType, modifiedTime, size, webViewLink)",
                orderBy=order_by,
            )
            .execute()
        )
        return result.get("files", [])

    def get_folder_id_by_name(
        self,
        folder_name: str,
        parent_id: Optional[str] = None,
    ) -> Optional[str]:
        """
        Ищет папку по имени. Если parent_id не задан — по всему Drive (в т.ч. во вложенных папках).
        Возвращает ID первой найденной папки или None.
        """
        q = "trashed = false and mimeType = 'application/vnd.google-apps.folder' and name = '{}'".format(
            folder_name.replace("'", "\\'")
        )
        if parent_id and parent_id != "root":
            q += f" and '{parent_id}' in parents"
        # если parent_id не задан — не фильтруем по родителю: ищем по всему Drive
        result = (
            self._service.files()
            .list(q=q, pageSize=1, fields="files(id, name)")
            .execute()
        )
        files = result.get("files", [])
        return files[0]["id"] if files else None

    def get_file_metadata(self, file_id: str) -> Dict[str, Any]:
        """Возвращает метаданные файла по ID."""
        return (
            self._service.files()
            .get(fileId=file_id, fields="id, name, mimeType, size, modifiedTime, webViewLink, parents")
            .execute()
        )

    def get_file(self, file_id: str, alt: str = "media") -> Any:
        """
        Скачивает содержимое файла (для бинарных/экспорта).
        Для Google Doc/Sheet лучше использовать export с mimeType.
        """
        return (
            self._service.files()
            .get_media(fileId=file_id)
            .execute()
        )

    def create_file(
        self,
        name: str,
        mime_type: str,
        folder_id: Optional[str] = None,
        body_extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Создаёт файл (или пустой Google Doc/Sheet) в указанной папке или в корне.

        Args:
            name: Имя файла.
            mime_type: MIME-тип, например MIME_GOOGLE_DOC, MIME_GOOGLE_SHEET или application/octet-stream.
            folder_id: ID папки; None — корень Drive.
            body_extra: Дополнительные поля для body (например description).

        Returns:
            Объект созданного файла (id, name, mimeType, webViewLink и др.).
        """
        body: Dict[str, Any] = {"name": name, "mimeType": mime_type}
        if folder_id and folder_id != "root":
            body["parents"] = [folder_id]
        if body_extra:
            body.update(body_extra)
        return self._service.files().create(body=body, fields="id, name, mimeType, webViewLink").execute()

    def delete_file(self, file_id: str) -> None:
        """Удаляет файл по ID (перемещает в корзину). Безвозвратное удаление — через emptyTrash или delete с supportsAllDrives."""
        self._service.files().delete(fileId=file_id).execute()


# ——— OAuth2: создание Google Документов и Таблиц от имени пользователя ———


def _resolve_client_secret_path(path: Optional[Union[str, Path]] = None) -> Path:
    """Путь к client_secret JSON (OAuth2). Из аргумента, ENV или *client_secret*.json в папке модуля."""
    if path is not None:
        return Path(path)
    import os

    env_path = os.environ.get("GOOGLE_CLIENT_SECRET_PATH")
    if env_path:
        return Path(env_path)
    cwd = Path(__file__).resolve().parent
    for f in cwd.glob("*client_secret*.json"):
        return f
    config_dir = cwd.parent / "config"
    for f in config_dir.glob("*client_secret*.json"):
        return f
    raise FileNotFoundError(
        "Не найден client_secret JSON для OAuth2. "
        "Укажите client_secret_path явно, задайте GOOGLE_CLIENT_SECRET_PATH в .env "
        "или положите файл *client_secret*.json в папку config/ или integrations/."
    )


def _get_user_credentials(
    client_secret_path: Union[str, Path],
    token_path: Optional[Union[str, Path]] = None,
    scopes: Optional[List[str]] = None,
) -> UserCredentials:
    """
    Возвращает учётные данные пользователя через OAuth2.
    При первом запуске открывает браузер для входа; токен сохраняется в token_path.
    """
    client_secret_path = Path(client_secret_path)
    if token_path is None:
        token_path = client_secret_path.parent / "token_drive_user.json"
    else:
        token_path = Path(token_path)

    scopes = scopes or SCOPES_DRIVE_USER
    creds = None

    if token_path.exists():
        try:
            creds = UserCredentials.from_authorized_user_file(str(token_path), scopes)
        except Exception:
            pass

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(client_secret_path), scopes)
            creds = flow.run_local_server(port=0)
        with open(token_path, "w") as f:
            f.write(creds.to_json())

    return creds


class GoogleDriveUserClient:
    """
    Клиент для создания Google Документов и Google Таблиц от имени пользователя (OAuth2).
    Файлы создаются в указанной папке в Drive пользователя.
    """

    def __init__(
        self,
        client_secret_path: Optional[Union[str, Path]] = None,
        token_path: Optional[Union[str, Path]] = None,
    ) -> None:
        """
        Args:
            client_secret_path: Путь к client_secret JSON (OAuth2). Если None — поиск *client_secret*.json в папке модуля или GOOGLE_CLIENT_SECRET_PATH в .env.
            token_path: Путь для сохранения токена (по умолчанию token_drive_user.json рядом с client_secret).
        """
        self._client_secret_path = _resolve_client_secret_path(client_secret_path)
        self._token_path = Path(token_path) if token_path else self._client_secret_path.parent / "token_drive_user.json"
        self._creds = _get_user_credentials(
            self._client_secret_path,
            token_path=self._token_path,
            scopes=SCOPES_DRIVE_USER,
        )
        self._service = build("drive", "v3", credentials=self._creds)

    def list_files(
        self,
        folder_id: Optional[str] = None,
        page_size: int = 100,
        order_by: str = "name",
    ) -> List[Dict[str, Any]]:
        """
        Список файлов и папок в Drive пользователя (OAuth2).
        folder_id: None или "root" — корень "Мой диск"; иначе ID папки.
        """
        q = "trashed = false"
        if folder_id and folder_id != "root":
            q += f" and '{folder_id}' in parents"
        else:
            q += " and 'root' in parents"
        result = (
            self._service.files()
            .list(
                q=q,
                pageSize=page_size,
                fields="nextPageToken, files(id, name, mimeType, modifiedTime, size, webViewLink)",
                orderBy=order_by,
            )
            .execute()
        )
        return result.get("files", [])

    def get_folder_id_by_name(
        self,
        folder_name: str,
        parent_id: Optional[str] = None,
    ) -> Optional[str]:
        """
        Ищет папку по имени в Drive пользователя. Если parent_id не задан — по всему «Мой диск»
        (в т.ч. во вложенных папках). Возвращает ID первой найденной папки или None.
        """
        q = "trashed = false and mimeType = 'application/vnd.google-apps.folder' and name = '{}'".format(
            folder_name.replace("'", "\\'")
        )
        if parent_id and parent_id != "root":
            q += f" and '{parent_id}' in parents"
        # если parent_id не задан — не фильтруем по родителю: ищем по всему Drive
        result = (
            self._service.files()
            .list(q=q, pageSize=1, fields="files(id, name)")
            .execute()
        )
        files = result.get("files", [])
        return files[0]["id"] if files else None

    def create_google_doc(
        self,
        title: str,
        folder_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Создаёт новый Google Документ в указанной папке от имени пользователя.

        Args:
            title: Название документа.
            folder_id: ID папки в Drive пользователя. None — корень "Мой диск".

        Returns:
            Метаданные созданного файла (id, name, webViewLink и др.).
        """
        body: Dict[str, Any] = {
            "name": title,
            "mimeType": MIME_GOOGLE_DOC,
        }
        if folder_id:
            body["parents"] = [folder_id]
        return self._service.files().create(body=body, fields="id, name, mimeType, webViewLink").execute()

    def create_google_sheet(
        self,
        title: str,
        folder_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Создаёт новую Google Таблицу в указанной папке от имени пользователя.

        Args:
            title: Название таблицы.
            folder_id: ID папки в Drive пользователя. None — корень "Мой диск".

        Returns:
            Метаданные созданного файла (id, name, webViewLink и др.).
        """
        body: Dict[str, Any] = {
            "name": title,
            "mimeType": MIME_GOOGLE_SHEET,
        }
        if folder_id:
            body["parents"] = [folder_id]
        return self._service.files().create(body=body, fields="id, name, mimeType, webViewLink").execute()


# ——— Точка входа: тест чтения списка файлов ———

def main() -> None:
    """
    Тестовый запуск: список файлов в Drive.
    По умолчанию — сервисный аккаунт (у него свой пустой Drive).
    С флагом --user — личный аккаунт (OAuth2): показываются ваши файлы.
    Папка: GOOGLE_DRIVE_FOLDER_ID в .env или корень.
    """
    import os
    import sys

    use_user_account = "--user" in sys.argv
    folder_name_from_env = os.environ.get("GOOGLE_DRIVE_FOLDER_NAME")
    folder_id_from_env = os.environ.get("GOOGLE_DRIVE_FOLDER_ID")

    if use_user_account:
        try:
            client = GoogleDriveUserClient()
        except FileNotFoundError as e:
            print(e, file=sys.stderr)
            sys.exit(1)
        print("Google Drive (личный аккаунт, OAuth2): список файлов.")
    else:
        credentials_path = (
            os.environ.get("GOOGLE_CREDENTIALS_PATH")
            or os.environ.get("CREDENTIALS_PATH")
            or None
        )
        try:
            client = GoogleDriveClient(credentials_path=credentials_path)
        except FileNotFoundError as e:
            print(e, file=sys.stderr)
            sys.exit(1)
        print("Google Drive (сервисный аккаунт): список файлов.")
        print("Подсказка: чтобы увидеть свои файлы, запустите с флагом --user")

    # Папка задаётся по названию (GOOGLE_DRIVE_FOLDER_NAME) или по ID (GOOGLE_DRIVE_FOLDER_ID)
    if folder_name_from_env:
        resolved_id = client.get_folder_id_by_name(folder_name_from_env)
        if resolved_id:
            folder_id = resolved_id
            print(f"Папка по названию '{folder_name_from_env}': ID={folder_id}")
        else:
            print(f"Папка с названием '{folder_name_from_env}' не найдена в корне Drive.", file=sys.stderr)
            sys.exit(1)
    elif folder_id_from_env:
        folder_id = folder_id_from_env
        print(f"Папка по ID: {folder_id}")
    else:
        folder_id = "root"
        print("Папка: корень Drive (root)")

    print("-" * 60)
    print("-" * 60)

    try:
        files = client.list_files(folder_id=folder_id)
    except HttpError as e:
        print(f"Ошибка API: {e}", file=sys.stderr)
        sys.exit(1)

    if not files:
        print("(папка пуста или нет доступа)")
    else:
        col_name_w = max(4, max((len(str(f.get("name", "—"))) for f in files), default=4))
        col_name_w = min(col_name_w, 50)
        col_type_w = 45
        col_id_w = 35
        sep = "+" + "-" * (col_name_w + 2) + "+" + "-" * (col_type_w + 2) + "+" + "-" * (col_id_w + 2) + "+"
        head = "| {:<{}} | {:<{}} | {:<{}} |".format(
            "Name", col_name_w, "Type", col_type_w, "ID", col_id_w
        )
        print(sep)
        print(head)
        print(sep)
        for f in files:
            name = (f.get("name") or "—")[:col_name_w]
            mime_type = (f.get("mimeType") or "—")[:col_type_w]
            file_id = (f.get("id") or "—")[:col_id_w]
            print("| {:<{}} | {:<{}} | {:<{}} |".format(
                name, col_name_w, mime_type, col_type_w, file_id, col_id_w
            ))
        print(sep)

    print("-" * 60)

    # Создание Google Таблицы в папке MiniCRM — всегда от имени пользователя (OAuth2),
    # чтобы файл учитывался в вашей квоте (15 ГБ), а не в квоте сервисного аккаунта.
    try:
        sheet_title = os.environ.get("GOOGLE_NEW_SHEET_TITLE", "Еещ кролик")
        create_client = client if use_user_account else GoogleDriveUserClient()
        if folder_name_from_env:
            folder_for_sheet = create_client.get_folder_id_by_name(folder_name_from_env)
        else:
            folder_for_sheet = folder_id if folder_id != "root" else None
        if folder_for_sheet:
            print(f"Создание таблицы в папке: {folder_name_from_env or folder_id}")
        drive2 = create_client.create_google_sheet(title=sheet_title, folder_id=folder_for_sheet)
        # Вывод созданного файла в виде таблички (Name, ID)
        col_w = 50
        id_w = 36
        sep_c = "+" + "-" * (col_w + 2) + "+" + "-" * (id_w + 2) + "+"
        print("Создан файл:")
        print(sep_c)
        print("| {:<{}} | {:<{}} |".format("Name", col_w, "ID", id_w))
        print(sep_c)
        name_val = (drive2.get("name") or "—")[:col_w]
        id_val = (drive2.get("id") or "—")[:id_w]
        print("| {:<{}} | {:<{}} |".format(name_val, col_w, id_val, id_w))
        print(sep_c)
        if drive2.get("webViewLink"):
            print("  Ссылка: {}".format(drive2["webViewLink"]))
    except HttpError as e:
        if e.resp.status == 403 and "storageQuotaExceeded" in str(e):
            print(
                "Ошибка создания таблицы: превышена квота хранилища Google Drive.\n"
                "Освободите место в drive.google.com (удалите файлы, очистите корзину)\n"
                "или проверьте хранилище в настройках аккаунта Google.",
                file=sys.stderr,
            )
        else:
            print(f"Ошибка создания таблицы: {e}", file=sys.stderr)

    print("Готово.")


if __name__ == "__main__":
    main()
