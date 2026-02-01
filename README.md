# EXCELIO — Google Таблицы: клиент и генератор отчётов

Проект состоит из двух частей:

1. **`google_sheets_client.py`** — модуль для работы с Google Таблицами (CRUD, форматирование). Подключение через сервисный аккаунт. Можно подключать в любые приложения и использовать со **сторонними данными** (API 1С, свои БД, CSV и т.д.).
2. **`report_app.py`** — десктопное приложение на Tkinter: форма (период, тип отчёта, подразделение, исполнитель и др.) и запись **симулированного** отчёта в таблицу с оформлением.

---

## Требования

- Python 3.10+
- JSON-ключ сервисного аккаунта Google (Google Cloud Console)

## Установка

```bash
pip install -r requirements.txt
```

## Настройка

1. **Сервисный аккаунт**  
   В [Google Cloud Console](https://console.cloud.google.com/) создайте сервисный аккаунт, включите **Google Sheets API**, скачайте JSON-ключ и положите его в папку проекта. Модуль ищет файл по маске `*excel-factory*.json`.

2. **Доступ к таблице**  
   В Google Таблице: «Настройки доступа» → добавьте email из JSON (`client_email`) с правами «Редактор» или «Читатель».

3. **ID таблицы**  
   В URL: `https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit` — это и есть ID.

4. **Файл `.env`** (рекомендуется):

   ```
   GOOGLE_SPREADSHEET_ID=ваш_id_таблицы
   GOOGLE_CREDENTIALS_PATH=путь/к/ключу.json
   ```

   `GOOGLE_CREDENTIALS_PATH` можно не указывать — тогда используется авто-поиск `*excel-factory*.json`. При импорте `google_sheets_client` загружает `.env` автоматически.

---

## Запуск скрипта и генератора

### Скрипт `google_sheets_client.py` (точка входа)

Читает всю таблицу и выводит данные в консоль:

```bash
# ID из .env
python google_sheets_client.py

# или через переменную окружения / аргумент
set GOOGLE_SPREADSHEET_ID=ваш_id
python google_sheets_client.py
# или: python google_sheets_client.py ваш_id
```

### Генератор отчётов `report_app.py`

Окно с полями: период (дата с / по), тип отчёта, подразделение, исполнитель, номер отчёта, получатель, примечание. По кнопке «Сформировать отчёт» генерируются **тестовые** данные и записываются в первый лист таблицы с оформлением (переименование листа, тёмно-зелёная шапка, раскраска статусов).

```bash
python report_app.py
```

Перед запуском в `.env` должен быть указан `GOOGLE_SPREADSHEET_ID`.

---

## Работа со сторонними данными через `google_sheets_client.py`

Модуль рассчитан на то, чтобы подключать его в свои скрипты и передавать туда **уже готовые** данные: из API 1С, своей БД, CSV, парсеров и т.д. Формат данных — список строк, каждая строка — список значений ячеек: `list[list[Any]]`.

### Общая схема

1. Получить данные из внешнего источника (1С, API, БД, файл).
2. Преобразовать в `list[list]` (заголовок + строки).
3. Создать `GoogleSheetsClient`, записать данные через `write_range` / `append_rows`.
4. При необходимости оформить лист: `merge_cells`, `format_range_header_colored`, `rename_sheet` и т.д.

### Пример: автоотчёт из API 1С

Допустим, 1С отдаёт отчёт по REST (JSON). Нужно выгрузить его в Google Таблицу.

```python
import requests
from google_sheets_client import GoogleSheetsClient, get_config_from_env

# 1) Получить данные из 1С (пример: эндпоинт и заголовки авторизации у вас свои)
response = requests.get(
    "https://your-1c-server/odata/standard.odata/Report_Sales",
    headers={"Authorization": "Bearer YOUR_TOKEN"},
    params={"$format": "json"}
)
data = response.json()

# 2) Преобразовать в строки для таблицы: заголовок + данные
rows = []
if "value" in data:
    items = data["value"]
    if items:
        # Заголовок — ключи первого элемента
        headers = list(items[0].keys())
        rows.append(headers)
        for item in items:
            rows.append([item.get(h, "") for h in headers])

# Если 1С отдаёт уже плоский список списков:
# rows = [["№", "Дата", "Сумма", ...]] + list_of_rows

# 3) Подключение к таблице и запись
cfg = get_config_from_env()
client = GoogleSheetsClient(
    spreadsheet_id=cfg["spreadsheet_id"],
    credentials_path=cfg.get("credentials_path"),
)
sheet_name = client.get_sheet_titles()[0]

# Очистить старые данные (опционально) или писать в новый лист
# client.clear_sheet(sheet_name)

# Записать: заголовок в A1, данные — с A2
if rows:
    client.write_range("A1", rows, sheet_name=sheet_name)
    # Опционально: оформить шапку (тёмно-зелёный фон, белый текст)
    num_cols = len(rows[0])
    client.format_range_header_colored(
        sheet_name,
        start_row=0, end_row=1, start_column=0, end_column=num_cols,
        red=0.1, green=0.35, blue=0.2,
        text_red=1, text_green=1, text_blue=1,
    )
```

### Пример: запись по диапазонам и добавление строк

```python
from google_sheets_client import GoogleSheetsClient, get_config_from_env

cfg = get_config_from_env()
client = GoogleSheetsClient(
    spreadsheet_id=cfg["spreadsheet_id"],
    credentials_path=cfg.get("credentials_path"),
)
sheet = client.get_sheet_titles()[0]

# Заголовок
client.write_range("A1:F1", [["Дата", "Документ", "Сумма", "Контрагент", "Статус", "Комментарий"]], sheet_name=sheet)
client.format_range_header_colored(sheet, 0, 1, 0, 6, red=0.1, green=0.35, blue=0.2, text_red=1, text_green=1, text_blue=1)

# Данные из вашего источника (например, список словарей из 1С)
external_rows = [
    ["01.02.2025", "Реализация 001", 15000, "ООО Рога", "Проведён", ""],
    ["02.02.2025", "Реализация 002", 23000, "ИП Копыта", "Проведён", ""],
]
client.append_rows(external_rows, sheet_name=sheet)
```

### Пример: свой скрипт с конфигом из кода

Если не используете `.env`, передайте ID таблицы и путь к ключу явно:

```python
from google_sheets_client import GoogleSheetsClient

client = GoogleSheetsClient(
    spreadsheet_id="ваш_id_таблицы",
    credentials_path="путь/к/ключу.json",  # или None для авто-поиска *excel-factory*.json
)

# Чтение
data = client.read_entire_sheet(sheet_name="Лист1")

# Запись сторонних данных (например, из CSV или БД)
my_rows = [["Колонка1", "Колонка2"], ["значение1", "значение2"]]
client.write_range("A1", my_rows, sheet_name="Лист1")

# Добавить строки в конец
client.append_rows([["ещё", "строка"]], sheet_name="Лист1")
```

---

## API класса `GoogleSheetsClient`

### Метаданные и листы

| Метод | Описание |
|-------|----------|
| `get_spreadsheet_metadata()` | Полные метаданные таблицы |
| `get_sheet_titles()` | Список названий листов |
| `get_sheet_id(sheet_name)` | ID листа по имени |
| `rename_sheet(new_title, sheet_name=None, sheet_id=None)` | Переименовать лист |
| `create_sheet(title, rows=1000, cols=26)` | Создать лист |
| `delete_sheet(sheet_name=None, sheet_id=None)` | Удалить лист |

### Чтение

| Метод | Описание |
|-------|----------|
| `read_entire_table()` | Все ячейки со всех листов: `{лист: [[ряд], ...]}` |
| `read_entire_sheet(sheet_name=None)` | Все ячейки одного листа |
| `read_range(range_name, sheet_name=None)` | Диапазон в A1-нотации |
| `read_row(row_index, sheet_name=None, ...)` | Одна строка по индексу (1-based) |
| `read_column(column_letter, sheet_name=None, ...)` | Один столбец по букве |

### Запись и вставка

| Метод | Описание |
|-------|----------|
| `write_range(range_name, values, sheet_name=None, ...)` | Записать/перезаписать диапазон |
| `write_cell(cell, value, sheet_name=None, ...)` | Одна ячейка |
| `append_rows(values, sheet_name=None, ...)` | Добавить строки в конец листа |
| `update_range(...)` | Алиас для `write_range` |
| `insert_rows(sheet_name=None, start_index=0, count=1)` | Вставить пустые строки |
| `insert_columns(sheet_name=None, start_index=0, count=1)` | Вставить пустые столбцы |

### Удаление и очистка

| Метод | Описание |
|-------|----------|
| `clear_range(range_name, sheet_name=None)` | Очистить диапазон |
| `clear_sheet(sheet_name=None)` | Очистить весь лист |
| `clear_entire_table()` | Очистить все листы |
| `delete_rows(sheet_name=None, start_index=0, count=1)` | Удалить строки |
| `delete_columns(sheet_name=None, start_index=0, count=1)` | Удалить столбцы |

### Форматирование

| Метод | Описание |
|-------|----------|
| `merge_cells(sheet_name, start_row, end_row, start_column, end_column)` | Объединить ячейки (0-based) |
| `format_range_bold(...)` | Жирный текст в диапазоне |
| `format_range_header(...)` | Заголовок: серый фон, жирный, по центру |
| `format_range_header_colored(..., red, green, blue, text_red, text_green, text_blue)` | Заголовок с произвольным фоном и цветом текста (0–1) |
| `format_range_background(..., red, green, blue)` | Заливка диапазона цветом (0–1) |

Все индексы в методах форматирования и слияния — **0-based**, `end_row` / `end_column` — **исключающие**.

---

## Структура проекта

```
EXCELIO/
├── google_sheets_client.py   # Клиент Google Таблиц (CRUD, форматирование)
├── report_app.py             # Генератор отчётов (Tkinter, тестовые данные)
├── requirements.txt
├── .env                      # GOOGLE_SPREADSHEET_ID, GOOGLE_CREDENTIALS_PATH
├── excel-factory-*.json      # JSON-ключ сервисного аккаунта
└── README.md
```

---

## Лицензия

Используйте в своих проектах по необходимости.
