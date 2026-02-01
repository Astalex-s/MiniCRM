"""
Простое приложение на Tkinter для генерации отчётов.
Ввод: период (дата с — дата по), тип отчёта, исполнитель.
Отчёт формируется с рандомными данными и записывается в Google Таблицу
в виде документа: заголовок, метаданные, таблица с форматированием.
"""

import random
from datetime import datetime, timedelta
from tkinter import Tk, Frame, Label, Entry, Button, ttk, messagebox, StringVar

# Конфигурация и клиент Google Таблиц
from google_sheets_client import GoogleSheetsClient, get_config_from_env


# Типы отчётов и структура данных для симуляции
REPORT_TYPES = [
    "Продажи по дням",
    "Закупки поставщиков",
    "Складские остатки",
    "Выручка по категориям",
    "Заявки клиентов",
]

# Короткие названия листов для переименования
REPORT_SHORT_NAMES = {
    "Продажи по дням": "Продажи",
    "Закупки поставщиков": "Закупки",
    "Складские остатки": "Склад",
    "Выручка по категориям": "Выручка",
    "Заявки клиентов": "Заявки",
}

# Подразделения
DEPARTMENTS = [
    "Отдел продаж",
    "Закупки",
    "Склад",
    "Бухгалтерия",
    "Маркетинг",
    "ИТ",
]

# Цвета для выделения статусов (RGB 0–1): светлые оттенки
STATUS_COLORS = {
    "Оплачен": (0.7, 1.0, 0.7),      # светло-зелёный
    "Доставлен": (0.7, 1.0, 0.7),
    "Выполнена": (0.7, 1.0, 0.7),
    "В пути": (1.0, 1.0, 0.75),      # светло-жёлтый
    "В работе": (1.0, 1.0, 0.75),
    "Ожидает": (1.0, 0.9, 0.8),      # светло-оранжевый
    "Новая": (1.0, 0.85, 0.85),      # светло-красный
}

# Заголовки таблицы по типам отчётов (колонки)
REPORT_HEADERS = {
    "Продажи по дням": ["№", "Дата", "Товар", "Кол-во", "Сумма", "Клиент", "Статус"],
    "Закупки поставщиков": ["№", "Поставщик", "Товар", "Кол-во", "Цена", "Сумма", "Дата поставки"],
    "Складские остатки": ["№", "Склад", "Товар", "Остаток", "Ед. изм.", "Резерв", "Дата учёта"],
    "Выручка по категориям": ["№", "Категория", "Выручка", "Доля %", "Заказов", "Средний чек"],
    "Заявки клиентов": ["№", "Дата", "Клиент", "Товар", "Кол-во", "Сумма", "Статус"],
}


def _parse_date(s: str) -> datetime | None:
    """Парсит дату из строки DD.MM.YYYY или YYYY-MM-DD."""
    s = (s or "").strip()
    if not s:
        return None
    for fmt in ("%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def _format_date(d: datetime) -> str:
    return d.strftime("%d.%m.%Y")


def _generate_random_report(report_type: str, date_from: datetime, date_to: datetime) -> list[list]:
    """Генерирует рандомные строки отчёта по типу и периоду."""
    headers = REPORT_HEADERS.get(report_type, ["№", "Данные"])
    rows = [headers]
    num_rows = random.randint(8, 15)
    days_range = max(1, (date_to - date_from).days)

    if report_type == "Продажи по дням":
        products = ["Ноутбук", "Мышь", "Клавиатура", "Монитор", "Веб-камера", "Наушники", "Коврик", "Хаб"]
        clients = ["ООО Ромашка", "ИП Иванов", "ООО Техно", "Физлицо", "ООО Склад"]
        for i in range(1, num_rows + 1):
            day_off = random.randint(0, days_range) if days_range else 0
            row_date = date_from + timedelta(days=day_off)
            qty = random.randint(1, 10)
            price = random.randint(500, 50000)
            rows.append([
                i,
                _format_date(row_date),
                random.choice(products),
                qty,
                qty * price,
                random.choice(clients),
                random.choice(["Оплачен", "В пути", "Ожидает"]),
            ])
    elif report_type == "Закупки поставщиков":
        suppliers = ["Поставщик А", "Поставщик Б", "Поставщик В"]
        products = ["Комплектующие", "Упаковка", "Материалы", "Оборудование"]
        for i in range(1, num_rows + 1):
            qty = random.randint(10, 500)
            price = round(random.uniform(10, 1000), 2)
            day_off = random.randint(0, days_range) if days_range else 0
            rows.append([
                i, random.choice(suppliers), random.choice(products),
                qty, price, round(qty * price, 2),
                _format_date(date_from + timedelta(days=day_off)),
            ])
    elif report_type == "Складские остатки":
        warehouses = ["Склад 1", "Склад 2", "Склад 3"]
        products = ["Товар A", "Товар B", "Товар C", "Товар D", "Товар E"]
        for i in range(1, num_rows + 1):
            rows.append([
                i, random.choice(warehouses), random.choice(products),
                random.randint(0, 1000), "шт.", random.randint(0, 100),
                _format_date(date_to),
            ])
    elif report_type == "Выручка по категориям":
        categories = ["Электроника", "Аксессуары", "Комплектующие", "Услуги", "Прочее"]
        total_rev = random.randint(500000, 5000000)
        for i, cat in enumerate(random.sample(categories, min(5, len(categories))), 1):
            rev = random.randint(50000, total_rev // 2)
            total_rev -= rev
            if total_rev < 0:
                total_rev = 0
            orders = random.randint(10, 200)
            rows.append([i, cat, rev, round(rev / (rev + total_rev) * 100 if (rev + total_rev) else 0, 1), orders, rev // max(1, orders)])
        num_rows = len(rows) - 1
    elif report_type == "Заявки клиентов":
        clients = ["Клиент 1", "Клиент 2", "ИП Петров", "ООО Заказ"]
        products = ["Товар X", "Товар Y", "Услуга Z"]
        for i in range(1, num_rows + 1):
            day_off = random.randint(0, days_range) if days_range else 0
            qty = random.randint(1, 20)
            price = random.randint(1000, 50000)
            rows.append([
                i, _format_date(date_from + timedelta(days=day_off)),
                random.choice(clients), random.choice(products), qty, qty * price,
                random.choice(["Новая", "В работе", "Выполнена"]),
            ])
    else:
        for i in range(1, num_rows + 1):
            rows.append([i] + [random.randint(1, 100) for _ in range(len(headers) - 1)])

    return rows


def _write_report_to_sheet(
    client: GoogleSheetsClient,
    report_type: str,
    date_from: datetime,
    date_to: datetime,
    executor: str,
    department: str = "",
    report_number: str = "",
    recipient: str = "",
    note: str = "",
    sheet_name: str | None = None,
) -> None:
    """
    Записывает отчёт в лист: переименование листа, заголовок, метаданные (в т.ч. подразделение, номер, получатель, примечание),
    таблица с тёмно-зелёной шапкой и раскраской столбца статусов.
    """
    name = sheet_name or (client.get_sheet_titles()[0] if client.get_sheet_titles() else None)
    if not name:
        raise ValueError("В таблице нет листов. Создайте лист вручную.")

    # Переименование листа в короткое название отчёта + дата
    short_name = REPORT_SHORT_NAMES.get(report_type, report_type[:20])
    sheet_title = f"{short_name} {date_to.strftime('%d.%m.%y')}"
    client.rename_sheet(new_title=sheet_title, sheet_name=name)
    name = sheet_title  # дальше работаем с уже переименованным листом

    num_cols = 8
    data_rows = _generate_random_report(report_type, date_from, date_to)
    num_cols = max(num_cols, len(data_rows[0]) if data_rows else 1)

    # Строка 0: заголовок отчёта (объединяем, жирный)
    title = f"Отчёт: {report_type} — период с {_format_date(date_from)} по {_format_date(date_to)}"
    client.write_range("A1", [[title]], sheet_name=name)
    client.merge_cells(name, start_row=0, end_row=1, start_column=0, end_column=num_cols)
    client.format_range_bold(name, start_row=0, end_row=1, start_column=0, end_column=num_cols)

    # Метаданные: период, исполнитель, подразделение, номер отчёта, получатель, примечание
    meta = [
        ["Период:", f"с {_format_date(date_from)} по {_format_date(date_to)}"],
        ["Исполнитель:", executor or "—"],
        ["Подразделение:", department or "—"],
        ["Номер отчёта:", report_number or "—"],
        ["Получатель:", recipient or "—"],
        ["Примечание:", note or "—"],
    ]
    client.write_range("A3:B8", meta, sheet_name=name)

    # Таблица: заголовки и данные
    data_start_row = 10
    header_row_0based = data_start_row - 1
    client.write_range(f"A{data_start_row}", data_rows, sheet_name=name)
    num_columns = len(data_rows[0]) if data_rows else 1
    # Шапка таблицы — тёмно-зелёный фон, белый жирный текст
    client.format_range_header_colored(
        name,
        start_row=header_row_0based,
        end_row=header_row_0based + 1,
        start_column=0,
        end_column=num_columns,
        red=0.1,
        green=0.35,
        blue=0.2,
        text_red=1,
        text_green=1,
        text_blue=1,
    )

    # Раскраска столбца «Статус» по значению (индекс 6 для Продажи/Заявки)
    headers = data_rows[0] if data_rows else []
    try:
        status_col = headers.index("Статус")
    except ValueError:
        status_col = None
    if status_col is not None:
        for i, row in enumerate(data_rows[1:]):
            # Строка данных: 1-based data_start_row + 1 + i → 0-based (data_start_row - 1) + 1 + i
            row_0based = (data_start_row - 1) + 1 + i
            status_val = (row[status_col] if len(row) > status_col else "").strip()
            color = STATUS_COLORS.get(status_val, (1, 1, 1))
            client.format_range_background(
                name,
                start_row=row_0based,
                end_row=row_0based + 1,
                start_column=status_col,
                end_column=status_col + 1,
                red=color[0],
                green=color[1],
                blue=color[2],
            )

    # Подпись в конце
    last_data_row_1based = data_start_row + len(data_rows) - 1
    client.write_range(f"A{last_data_row_1based + 2}", [["— Конец отчёта —"]], sheet_name=name)
    client.format_range_bold(
        name,
        start_row=last_data_row_1based + 1,
        end_row=last_data_row_1based + 2,
        start_column=0,
        end_column=1,
    )


def main():
    root = Tk()
    root.title("Формирование отчёта")
    root.geometry("480x380")
    root.resizable(True, True)

    # Переменные
    var_date_from = StringVar(value=datetime.now().replace(day=1).strftime("%d.%m.%Y"))
    var_date_to = StringVar(value=datetime.now().strftime("%d.%m.%Y"))
    var_report_type = StringVar(value=REPORT_TYPES[0])
    var_department = StringVar(value=DEPARTMENTS[0])
    var_executor = StringVar(value="")
    var_report_number = StringVar(value="")
    var_recipient = StringVar(value="")
    var_note = StringVar(value="")

    frame = Frame(root, padx=16, pady=16)
    frame.pack(fill="both", expand=True)

    row_idx = 0
    # Период
    Label(frame, text="Дата с:").grid(row=row_idx, column=0, sticky="e", padx=(0, 8), pady=4)
    Entry(frame, textvariable=var_date_from, width=18).grid(row=row_idx, column=1, sticky="w", pady=4)
    row_idx += 1
    Label(frame, text="Дата по:").grid(row=row_idx, column=0, sticky="e", padx=(0, 8), pady=4)
    Entry(frame, textvariable=var_date_to, width=18).grid(row=row_idx, column=1, sticky="w", pady=4)
    row_idx += 1

    # Тип отчёта — выпадающий список
    Label(frame, text="Тип отчёта:").grid(row=row_idx, column=0, sticky="e", padx=(0, 8), pady=4)
    combo_report = ttk.Combobox(frame, textvariable=var_report_type, values=REPORT_TYPES, state="readonly", width=26)
    combo_report.grid(row=row_idx, column=1, sticky="w", pady=4)
    row_idx += 1

    # Подразделение — выпадающий список
    Label(frame, text="Подразделение:").grid(row=row_idx, column=0, sticky="e", padx=(0, 8), pady=4)
    combo_dept = ttk.Combobox(frame, textvariable=var_department, values=DEPARTMENTS, state="readonly", width=26)
    combo_dept.grid(row=row_idx, column=1, sticky="w", pady=4)
    row_idx += 1

    # Исполнитель
    Label(frame, text="Исполнитель:").grid(row=row_idx, column=0, sticky="e", padx=(0, 8), pady=4)
    Entry(frame, textvariable=var_executor, width=28).grid(row=row_idx, column=1, sticky="w", pady=4)
    row_idx += 1

    # Номер отчёта
    Label(frame, text="Номер отчёта:").grid(row=row_idx, column=0, sticky="e", padx=(0, 8), pady=4)
    Entry(frame, textvariable=var_report_number, width=28).grid(row=row_idx, column=1, sticky="w", pady=4)
    row_idx += 1

    # Получатель
    Label(frame, text="Получатель:").grid(row=row_idx, column=0, sticky="e", padx=(0, 8), pady=4)
    Entry(frame, textvariable=var_recipient, width=28).grid(row=row_idx, column=1, sticky="w", pady=4)
    row_idx += 1

    # Примечание
    Label(frame, text="Примечание:").grid(row=row_idx, column=0, sticky="e", padx=(0, 8), pady=4)
    Entry(frame, textvariable=var_note, width=28).grid(row=row_idx, column=1, sticky="w", pady=4)
    row_idx += 1

    status_label = Label(frame, text="", fg="gray")
    status_label.grid(row=row_idx, column=0, columnspan=2, pady=12)
    row_idx += 1

    def on_generate():
        date_from = _parse_date(var_date_from.get())
        date_to = _parse_date(var_date_to.get())
        if not date_from:
            messagebox.showerror("Ошибка", "Введите корректную дату «с» (DD.MM.YYYY).")
            return
        if not date_to:
            messagebox.showerror("Ошибка", "Введите корректную дату «по» (DD.MM.YYYY).")
            return
        if date_from > date_to:
            messagebox.showerror("Ошибка", "Дата «с» не может быть позже даты «по».")
            return
        executor = var_executor.get().strip() or "Не указан"
        status_label.config(text="Формирование отчёта...", fg="blue")
        root.update()
        try:
            cfg = get_config_from_env()
            if not cfg.get("spreadsheet_id"):
                messagebox.showerror("Ошибка", "В .env не указан GOOGLE_SPREADSHEET_ID.")
                status_label.config(text="", fg="gray")
                return
            client = GoogleSheetsClient(
                spreadsheet_id=cfg["spreadsheet_id"],
                credentials_path=cfg.get("credentials_path"),
            )
            _write_report_to_sheet(
                client,
                report_type=var_report_type.get(),
                date_from=date_from,
                date_to=date_to,
                executor=executor,
                department=var_department.get().strip(),
                report_number=var_report_number.get().strip(),
                recipient=var_recipient.get().strip(),
                note=var_note.get().strip(),
            )
            status_label.config(text="Отчёт записан в Google Таблицу.", fg="green")
            messagebox.showinfo("Готово", "Отчёт успешно записан в таблицу.")
        except Exception as e:
            status_label.config(text="Ошибка записи.", fg="red")
            messagebox.showerror("Ошибка", str(e))

    Button(frame, text="Сформировать отчёт", command=on_generate).grid(row=row_idx, column=0, columnspan=2, pady=8)

    root.mainloop()


if __name__ == "__main__":
    main()
