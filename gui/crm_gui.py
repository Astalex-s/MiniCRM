"""
Визуальный интерфейс мини-CRM на Tkinter.
Запросы к локальному бэкенду (http://127.0.0.1:8000).
Таблицы, окна редактирования, поиск.
"""
import sys
from pathlib import Path

# Корень проекта в path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tkinter import Tk, Toplevel, Frame, Label, Entry, Button, ttk, messagebox, StringVar, BooleanVar
from tkinter import scrolledtext

from gui import api


def _err(msg):
    messagebox.showerror("Ошибка", msg)


def _ok(msg):
    messagebox.showinfo("OK", msg)


# ---------- Общие виджеты ----------

class SearchBar(Frame):
    def __init__(self, parent, on_search, placeholder="Поиск..."):
        super().__init__(parent)
        self.var = StringVar()
        self.on_search = on_search
        Label(self, text="Поиск:").pack(side="left", padx=(0, 4))
        e = Entry(self, textvariable=self.var, width=25)
        e.pack(side="left", padx=(0, 4))
        e.bind("<Return>", lambda e: on_search())
        Button(self, text="Найти", command=on_search).pack(side="left", padx=(0, 8))
        Button(self, text="Сброс", command=self._reset).pack(side="left")

    def _reset(self):
        self.var.set("")
        self.on_search()

    def get(self):
        return self.var.get().strip()


# ---------- Клиенты ----------

CLIENT_COLS = ("id", "name", "email", "phone", "status", "notes")
CLIENT_HEADERS = ("ID", "Имя", "Email", "Телефон", "Статус", "Заметки")


class ClientEditWindow(Toplevel):
    def __init__(self, parent, client=None, on_saved=None):
        super().__init__(parent)
        self.client = client
        self.on_saved = on_saved
        self.title("Редактирование клиента" if client else "Новый клиент")
        self.geometry("420x280")
        self.resizable(True, True)
        f = Frame(self, padx=12, pady=12)
        f.pack(fill="both", expand=True)
        Label(f, text="Имя *").grid(row=0, column=0, sticky="w", pady=2)
        self.name_var = StringVar(value=(client.get("name") or "") if client else "")
        Entry(f, textvariable=self.name_var, width=40).grid(row=0, column=1, sticky="ew", pady=2, padx=(8, 0))
        Label(f, text="Email").grid(row=1, column=0, sticky="w", pady=2)
        self.email_var = StringVar(value=(client.get("email") or "") if client else "")
        Entry(f, textvariable=self.email_var, width=40).grid(row=1, column=1, sticky="ew", pady=2, padx=(8, 0))
        Label(f, text="Телефон").grid(row=2, column=0, sticky="w", pady=2)
        self.phone_var = StringVar(value=(client.get("phone") or "") if client else "")
        Entry(f, textvariable=self.phone_var, width=40).grid(row=2, column=1, sticky="ew", pady=2, padx=(8, 0))
        Label(f, text="Статус").grid(row=3, column=0, sticky="w", pady=2)
        self.status_var = StringVar(value=(client.get("status") or "active") if client else "active")
        ttk.Combobox(f, textvariable=self.status_var, values=("active", "archived"), width=18, state="readonly").grid(
            row=3, column=1, sticky="w", pady=2, padx=(8, 0)
        )
        Label(f, text="Заметки").grid(row=4, column=0, sticky="nw", pady=2)
        self.notes_var = StringVar(value=(client.get("notes") or "") if client else "")
        st = scrolledtext.ScrolledText(f, width=40, height=4, wrap="word")
        st.grid(row=4, column=1, sticky="ew", pady=2, padx=(8, 0))
        st.insert("1.0", self.notes_var.get())
        self.notes_widget = st
        f.columnconfigure(1, weight=1)
        btn_f = Frame(self)
        btn_f.pack(fill="x", padx=12, pady=8)
        Button(btn_f, text="Сохранить", command=self._save).pack(side="right", padx=4)
        Button(btn_f, text="Отмена", command=self.destroy).pack(side="right")

    def _save(self):
        name = self.name_var.get().strip()
        if not name:
            _err("Укажите имя клиента.")
            return
        payload = {
            "name": name,
            "email": self.email_var.get().strip() or None,
            "phone": self.phone_var.get().strip() or None,
            "status": self.status_var.get(),
            "notes": self.notes_widget.get("1.0", "end").strip() or None,
        }
        try:
            if self.client:
                api.client_update(self.client["id"], payload)
                _ok("Клиент обновлён.")
            else:
                api.client_create(payload)
                _ok("Клиент создан.")
            if self.on_saved:
                self.on_saved()
            self.destroy()
        except Exception as e:
            _err(str(e))


class ClientsTab(Frame):
    def __init__(self, parent):
        super().__init__(parent)
        toolbar = Frame(self)
        toolbar.pack(fill="x", pady=(0, 4))
        Button(toolbar, text="Добавить", command=self._add).pack(side="left", padx=2)
        Button(toolbar, text="Редактировать", command=self._edit).pack(side="left", padx=2)
        Button(toolbar, text="Архивировать", command=self._archive).pack(side="left", padx=2)
        Button(toolbar, text="Удалить", command=self._delete).pack(side="left", padx=2)
        Button(toolbar, text="Обновить", command=self._refresh).pack(side="left", padx=2)
        self.search_bar = SearchBar(self, self._refresh, "Поиск по клиентам...")
        self.search_bar.pack(fill="x", pady=4)
        self.tree = ttk.Treeview(self, columns=CLIENT_COLS, show="headings", height=18, selectmode="browse")
        for col, h in zip(CLIENT_COLS, CLIENT_HEADERS):
            self.tree.heading(col, text=h)
            self.tree.column(col, width=80 if col != "name" and col != "notes" else 120)
        self.tree.column("notes", width=180)
        sb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self._refresh()

    def _refresh(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        q = self.search_bar.get()
        try:
            if q:
                rows = api.client_search(q)
            else:
                rows = api.client_list()
        except Exception as e:
            _err(str(e))
            return
        for r in rows:
            self.tree.insert("", "end", values=(
                r.get("id"),
                r.get("name") or "",
                r.get("email") or "",
                r.get("phone") or "",
                r.get("status") or "",
                (r.get("notes") or "")[:50],
            ), iid=str(r.get("id")))

    def _selection(self):
        sel = self.tree.selection()
        if not sel:
            _err("Выберите клиента.")
            return None
        return self.tree.item(sel[0])["values"]

    def _add(self):
        ClientEditWindow(self, client=None, on_saved=self._refresh)

    def _edit(self):
        sel = self._selection()
        if sel is None:
            return
        cid = sel[0]
        try:
            client = api.client_get(cid)
        except Exception as e:
            _err(str(e))
            return
        if client:
            ClientEditWindow(self, client=client, on_saved=self._refresh)

    def _archive(self):
        sel = self._selection()
        if sel is None:
            return
        if not messagebox.askyesno("Подтверждение", "Архивировать выбранного клиента?"):
            return
        try:
            api.client_archive(sel[0])
            _ok("Клиент архивирован.")
            self._refresh()
        except Exception as e:
            _err(str(e))

    def _delete(self):
        sel = self._selection()
        if sel is None:
            return
        if not messagebox.askyesno("Подтверждение", "Удалить клиента навсегда?"):
            return
        try:
            api.client_delete(sel[0])
            _ok("Клиент удалён.")
            self._refresh()
        except Exception as e:
            _err(str(e))


# ---------- Сделки ----------

DEAL_COLS = ("id", "title", "client_id", "amount", "status", "notes")
DEAL_HEADERS = ("ID", "Название", "ID клиента", "Сумма", "Статус", "Заметки")


class DealEditWindow(Toplevel):
    def __init__(self, parent, deal=None, on_saved=None):
        super().__init__(parent)
        self.deal = deal
        self.on_saved = on_saved
        self.title("Редактирование сделки" if deal else "Новая сделка")
        self.geometry("440x260")
        f = Frame(self, padx=12, pady=12)
        f.pack(fill="both", expand=True)
        Label(f, text="Название *").grid(row=0, column=0, sticky="w", pady=2)
        self.title_var = StringVar(value=(deal.get("title") or "") if deal else "")
        Entry(f, textvariable=self.title_var, width=40).grid(row=0, column=1, sticky="ew", pady=2, padx=(8, 0))
        Label(f, text="ID клиента").grid(row=1, column=0, sticky="w", pady=2)
        self.client_id_var = StringVar(value=str(deal.get("client_id") or "") if deal else "")
        Entry(f, textvariable=self.client_id_var, width=12).grid(row=1, column=1, sticky="w", pady=2, padx=(8, 0))
        Label(f, text="Сумма").grid(row=2, column=0, sticky="w", pady=2)
        self.amount_var = StringVar(value=str(deal.get("amount") or "") if deal else "")
        Entry(f, textvariable=self.amount_var, width=12).grid(row=2, column=1, sticky="w", pady=2, padx=(8, 0))
        Label(f, text="Статус").grid(row=3, column=0, sticky="w", pady=2)
        self.status_var = StringVar(value=(deal.get("status") or "draft") if deal else "draft")
        ttk.Combobox(
            f, textvariable=self.status_var,
            values=("draft", "in_progress", "won", "lost"), width=18, state="readonly"
        ).grid(row=3, column=1, sticky="w", pady=2, padx=(8, 0))
        Label(f, text="Заметки").grid(row=4, column=0, sticky="nw", pady=2)
        self.notes_var = StringVar(value=(deal.get("notes") or "") if deal else "")
        st = scrolledtext.ScrolledText(f, width=40, height=3, wrap="word")
        st.grid(row=4, column=1, sticky="ew", pady=2, padx=(8, 0))
        st.insert("1.0", self.notes_var.get())
        self.notes_widget = st
        f.columnconfigure(1, weight=1)
        btn_f = Frame(self)
        btn_f.pack(fill="x", padx=12, pady=8)
        Button(btn_f, text="Сохранить", command=self._save).pack(side="right", padx=4)
        Button(btn_f, text="Отмена", command=self.destroy).pack(side="right")

    def _save(self):
        title = self.title_var.get().strip()
        if not title:
            _err("Укажите название сделки.")
            return
        try:
            cid = self.client_id_var.get().strip()
            client_id = int(cid) if cid else None
        except ValueError:
            _err("ID клиента должен быть числом или пустым.")
            return
        try:
            am = self.amount_var.get().strip()
            amount = float(am) if am else None
        except ValueError:
            _err("Сумма должна быть числом.")
            return
        payload = {
            "title": title,
            "client_id": client_id,
            "amount": amount,
            "status": self.status_var.get(),
            "notes": self.notes_widget.get("1.0", "end").strip() or None,
        }
        try:
            if self.deal:
                api.deal_update(self.deal["id"], payload)
                _ok("Сделка обновлена.")
            else:
                api.deal_create(payload)
                _ok("Сделка создана.")
            if self.on_saved:
                self.on_saved()
            self.destroy()
        except Exception as e:
            _err(str(e))


class DealsTab(Frame):
    def __init__(self, parent):
        super().__init__(parent)
        toolbar = Frame(self)
        toolbar.pack(fill="x", pady=(0, 4))
        Button(toolbar, text="Добавить", command=self._add).pack(side="left", padx=2)
        Button(toolbar, text="Редактировать", command=self._edit).pack(side="left", padx=2)
        Button(toolbar, text="Удалить", command=self._delete).pack(side="left", padx=2)
        Button(toolbar, text="Обновить", command=self._refresh).pack(side="left", padx=2)
        self.search_bar = SearchBar(self, self._refresh)
        self.search_bar.pack(fill="x", pady=4)
        self.tree = ttk.Treeview(self, columns=DEAL_COLS, show="headings", height=18, selectmode="browse")
        for col, h in zip(DEAL_COLS, DEAL_HEADERS):
            self.tree.heading(col, text=h)
            self.tree.column(col, width=70 if col != "title" and col != "notes" else 140)
        sb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self._refresh()

    def _refresh(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        q = self.search_bar.get()
        try:
            if q:
                rows = api.deal_search(q)
            else:
                rows = api.deal_list()
        except Exception as e:
            _err(str(e))
            return
        for r in rows:
            self.tree.insert("", "end", values=(
                r.get("id"),
                r.get("title") or "",
                r.get("client_id") or "",
                r.get("amount") or "",
                r.get("status") or "",
                (r.get("notes") or "")[:40],
            ), iid=str(r.get("id")))

    def _selection(self):
        sel = self.tree.selection()
        if not sel:
            _err("Выберите сделку.")
            return None
        return self.tree.item(sel[0])["values"]

    def _add(self):
        DealEditWindow(self, deal=None, on_saved=self._refresh)

    def _edit(self):
        sel = self._selection()
        if sel is None:
            return
        try:
            deal = api.deal_get(sel[0])
        except Exception as e:
            _err(str(e))
            return
        if deal:
            DealEditWindow(self, deal=deal, on_saved=self._refresh)

    def _delete(self):
        sel = self._selection()
        if sel is None:
            return
        if not messagebox.askyesno("Подтверждение", "Удалить сделку?"):
            return
        try:
            api.deal_delete(sel[0])
            _ok("Сделка удалена.")
            self._refresh()
        except Exception as e:
            _err(str(e))


# ---------- Задачи ----------

TASK_COLS = ("id", "title", "client_id", "deal_id", "is_completed", "due_date")
TASK_HEADERS = ("ID", "Название", "ID клиента", "ID сделки", "Выполнено", "Срок")


class TaskEditWindow(Toplevel):
    def __init__(self, parent, task=None, on_saved=None):
        super().__init__(parent)
        self.task = task
        self.on_saved = on_saved
        self.title("Редактирование задачи" if task else "Новая задача")
        self.geometry("440x280")
        f = Frame(self, padx=12, pady=12)
        f.pack(fill="both", expand=True)
        Label(f, text="Название *").grid(row=0, column=0, sticky="w", pady=2)
        self.title_var = StringVar(value=(task.get("title") or "") if task else "")
        Entry(f, textvariable=self.title_var, width=40).grid(row=0, column=1, sticky="ew", pady=2, padx=(8, 0))
        Label(f, text="Описание").grid(row=1, column=0, sticky="nw", pady=2)
        self.desc_var = StringVar(value=(task.get("description") or "") if task else "")
        st1 = scrolledtext.ScrolledText(f, width=40, height=2, wrap="word")
        st1.grid(row=1, column=1, sticky="ew", pady=2, padx=(8, 0))
        st1.insert("1.0", self.desc_var.get())
        self.desc_widget = st1
        Label(f, text="ID клиента").grid(row=2, column=0, sticky="w", pady=2)
        self.client_id_var = StringVar(value=str(task.get("client_id") or "") if task else "")
        Entry(f, textvariable=self.client_id_var, width=12).grid(row=2, column=1, sticky="w", pady=2, padx=(8, 0))
        Label(f, text="ID сделки").grid(row=3, column=0, sticky="w", pady=2)
        self.deal_id_var = StringVar(value=str(task.get("deal_id") or "") if task else "")
        Entry(f, textvariable=self.deal_id_var, width=12).grid(row=3, column=1, sticky="w", pady=2, padx=(8, 0))
        Label(f, text="Срок (YYYY-MM-DD)").grid(row=4, column=0, sticky="w", pady=2)
        self.due_var = StringVar(value=(task.get("due_date") or "")[:10] if task and task.get("due_date") else "")
        Entry(f, textvariable=self.due_var, width=12).grid(row=4, column=1, sticky="w", pady=2, padx=(8, 0))
        self.completed_var = BooleanVar(value=task.get("is_completed") if task else False)
        ttk.Checkbutton(f, text="Выполнено", variable=self.completed_var).grid(row=5, column=1, sticky="w", pady=2, padx=(8, 0))
        f.columnconfigure(1, weight=1)
        btn_f = Frame(self)
        btn_f.pack(fill="x", padx=12, pady=8)
        Button(btn_f, text="Сохранить", command=self._save).pack(side="right", padx=4)
        Button(btn_f, text="Отмена", command=self.destroy).pack(side="right")

    def _save(self):
        title = self.title_var.get().strip()
        if not title:
            _err("Укажите название задачи.")
            return
        try:
            cid = self.client_id_var.get().strip()
            client_id = int(cid) if cid else None
        except ValueError:
            _err("ID клиента — число или пусто.")
            return
        try:
            did = self.deal_id_var.get().strip()
            deal_id = int(did) if did else None
        except ValueError:
            _err("ID сделки — число или пусто.")
            return
        due = self.due_var.get().strip() or None
        payload = {
            "title": title,
            "description": self.desc_widget.get("1.0", "end").strip() or None,
            "client_id": client_id,
            "deal_id": deal_id,
            "is_completed": self.completed_var.get(),
            "due_date": due,
        }
        try:
            if self.task:
                api.task_update(self.task["id"], payload)
                _ok("Задача обновлена.")
            else:
                api.task_create(payload)
                _ok("Задача создана.")
            if self.on_saved:
                self.on_saved()
            self.destroy()
        except Exception as e:
            _err(str(e))


class TasksTab(Frame):
    def __init__(self, parent):
        super().__init__(parent)
        toolbar = Frame(self)
        toolbar.pack(fill="x", pady=(0, 4))
        Button(toolbar, text="Добавить", command=self._add).pack(side="left", padx=2)
        Button(toolbar, text="Редактировать", command=self._edit).pack(side="left", padx=2)
        Button(toolbar, text="Выполнено / Не выполнено", command=self._toggle_done).pack(side="left", padx=2)
        Button(toolbar, text="Удалить", command=self._delete).pack(side="left", padx=2)
        Button(toolbar, text="Обновить", command=self._refresh).pack(side="left", padx=2)
        self.tree = ttk.Treeview(self, columns=TASK_COLS, show="headings", height=18, selectmode="browse")
        for col, h in zip(TASK_COLS, TASK_HEADERS):
            self.tree.heading(col, text=h)
            self.tree.column(col, width=70 if col != "title" else 180)
        sb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self._refresh()

    def _refresh(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        try:
            rows = api.task_list()
        except Exception as e:
            _err(str(e))
            return
        for r in rows:
            due = r.get("due_date") or ""
            if len(due) > 10:
                due = due[:10]
            self.tree.insert("", "end", values=(
                r.get("id"),
                r.get("title") or "",
                r.get("client_id") or "",
                r.get("deal_id") or "",
                "Да" if r.get("is_completed") else "Нет",
                due,
            ), iid=str(r.get("id")))

    def _selection(self):
        sel = self.tree.selection()
        if not sel:
            _err("Выберите задачу.")
            return None
        return self.tree.item(sel[0])["values"]

    def _add(self):
        TaskEditWindow(self, task=None, on_saved=self._refresh)

    def _edit(self):
        sel = self._selection()
        if sel is None:
            return
        try:
            task = api.task_get(sel[0])
        except Exception as e:
            _err(str(e))
            return
        if task:
            TaskEditWindow(self, task=task, on_saved=self._refresh)

    def _toggle_done(self):
        sel = self._selection()
        if sel is None:
            return
        tid = sel[0]
        current = sel[4] == "Да"
        try:
            api.task_set_completed(tid, not current)
            _ok("Статус задачи обновлён.")
            self._refresh()
        except Exception as e:
            _err(str(e))

    def _delete(self):
        sel = self._selection()
        if sel is None:
            return
        if not messagebox.askyesno("Подтверждение", "Удалить задачу?"):
            return
        try:
            api.task_delete(sel[0])
            _ok("Задача удалена.")
            self._refresh()
        except Exception as e:
            _err(str(e))


# ---------- Главное окно ----------

def main():
    root = Tk()
    root.title("Мини-CRM")
    root.geometry("900x560")
    root.minsize(700, 400)
    nb = ttk.Notebook(root)
    nb.pack(fill="both", expand=True, padx=8, pady=8)
    nb.add(ClientsTab(nb), text="Клиенты")
    nb.add(DealsTab(nb), text="Сделки")
    nb.add(TasksTab(nb), text="Задачи")
    root.mainloop()


if __name__ == "__main__":
    main()
