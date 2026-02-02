"""
Клиент API локального бэкенда CRM.
Запросы к http://127.0.0.1:8000 через urllib (без доп. зависимостей).
"""
import json
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

BASE_URL = "http://127.0.0.1:8000"


def _request(
    method: str,
    path: str,
    data: Optional[Dict[str, Any]] = None,
) -> Optional[Any]:
    url = BASE_URL.rstrip("/") + "/" + path.lstrip("/")
    req_data = None
    if data is not None:
        req_data = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=req_data, method=method)
    req.add_header("Content-Type", "application/json")
    if data is not None:
        req.add_header("Content-Length", str(len(req_data)))
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body) if body else None
    except urllib.error.HTTPError as e:
        try:
            err_body = e.read().decode("utf-8")
            err = json.loads(err_body)
            detail = err.get("detail", err_body)
        except Exception:
            detail = str(e)
        raise RuntimeError(detail)
    except urllib.error.URLError as e:
        raise RuntimeError(f"Сервер недоступен: {e.reason}")
    except Exception as e:
        raise RuntimeError(str(e))


def get(path: str) -> Optional[Any]:
    return _request("GET", path)


def post(path: str, data: Dict[str, Any]) -> Optional[Any]:
    return _request("POST", path, data)


def patch(path: str, data: Dict[str, Any]) -> Optional[Any]:
    return _request("PATCH", path, data)


def delete(path: str) -> Optional[Any]:
    return _request("DELETE", path)


# ---------- Клиенты ----------

def client_list(status: Optional[str] = None, limit: int = 200, offset: int = 0) -> List[Dict]:
    q = f"limit={limit}&offset={offset}"
    if status:
        q += f"&status={status}"
    r = get(f"clients?{q}")
    return r if isinstance(r, list) else []


def client_search(q: str, limit: int = 100) -> List[Dict]:
    from urllib.parse import quote
    r = get(f"clients/search?q={quote(q)}&limit={limit}")
    return r if isinstance(r, list) else []


def client_get(client_id: int) -> Optional[Dict]:
    return get(f"clients/{client_id}")


def client_create(payload: Dict[str, Any]) -> Dict:
    r = post("clients", payload)
    return r or {}


def client_update(client_id: int, payload: Dict[str, Any]) -> Dict:
    r = patch(f"clients/{client_id}", payload)
    return r or {}


def client_delete(client_id: int) -> None:
    delete(f"clients/{client_id}")


def client_archive(client_id: int) -> Dict:
    r = post(f"clients/{client_id}/archive", {})
    return r or {}


# ---------- Сделки ----------

def deal_list(
    client_id: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = 200,
    offset: int = 0,
) -> List[Dict]:
    q = f"limit={limit}&offset={offset}"
    if client_id is not None:
        q += f"&client_id={client_id}"
    if status:
        q += f"&status={status}"
    r = get(f"deals?{q}")
    return r if isinstance(r, list) else []


def deal_search(q: str, limit: int = 100) -> List[Dict]:
    from urllib.parse import quote
    r = get(f"deals/search?q={quote(q)}&limit={limit}")
    return r if isinstance(r, list) else []


def deal_get(deal_id: int) -> Optional[Dict]:
    return get(f"deals/{deal_id}")


def deal_create(payload: Dict[str, Any]) -> Dict:
    r = post("deals", payload)
    return r or {}


def deal_update(deal_id: int, payload: Dict[str, Any]) -> Dict:
    r = patch(f"deals/{deal_id}", payload)
    return r or {}


def deal_delete(deal_id: int) -> None:
    delete(f"deals/{deal_id}")


# ---------- Задачи ----------

def task_list(
    client_id: Optional[int] = None,
    deal_id: Optional[int] = None,
    is_completed: Optional[bool] = None,
    limit: int = 200,
    offset: int = 0,
) -> List[Dict]:
    q = f"limit={limit}&offset={offset}"
    if client_id is not None:
        q += f"&client_id={client_id}"
    if deal_id is not None:
        q += f"&deal_id={deal_id}"
    if is_completed is not None:
        q += f"&is_completed={str(is_completed).lower()}"
    r = get(f"tasks?{q}")
    return r if isinstance(r, list) else []


def task_get(task_id: int) -> Optional[Dict]:
    return get(f"tasks/{task_id}")


def task_create(payload: Dict[str, Any]) -> Dict:
    r = post("tasks", payload)
    return r or {}


def task_update(task_id: int, payload: Dict[str, Any]) -> Dict:
    r = patch(f"tasks/{task_id}", payload)
    return r or {}


def task_delete(task_id: int) -> None:
    delete(f"tasks/{task_id}")


def task_set_completed(task_id: int, completed: bool) -> Dict:
    r = post(f"tasks/{task_id}/complete?completed={str(completed).lower()}", {})
    return r or {}
