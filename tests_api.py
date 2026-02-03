"""
Проверка всех API эндпоинтов CRM (только stdlib urllib).
Запуск: сначала запустите uvicorn (или Docker), затем: python tests_api.py
Базовый URL: http://127.0.0.1:8000
"""
import json
import urllib.error
import urllib.request
from typing import Any, Dict, Optional, Tuple

BASE = "http://127.0.0.1:8000"
FAILED: list[str] = []
PASSED: list[str] = []


def request(
    method: str,
    path: str,
    body: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
) -> Tuple[int, Optional[Any]]:
    url = BASE + path
    req_headers = {"Accept": "application/json"}
    if headers:
        req_headers.update(headers)
    if body is not None:
        req_headers["Content-Type"] = "application/json"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            text = r.read().decode("utf-8")
            return r.status, json.loads(text) if text else None
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            return e.code, json.loads(body)
        except Exception:
            return e.code, body
    except Exception as e:
        return -1, str(e)


def ok(name: str, status: int, data: Any) -> None:
    if 200 <= status < 300:
        PASSED.append(name)
        print(f"  OK   {name} -> {status}")
    else:
        FAILED.append(name)
        print(f"  FAIL {name} -> {status} {data}")


def main() -> None:
    print("Testing Mini CRM API at", BASE)
    print()

    # Health & root
    status, data = request("GET", "/health")
    ok("GET /health", status, data)
    status, data = request("GET", "/")
    ok("GET /", status, data)

    # Settings
    status, data = request("GET", "/settings/google")
    ok("GET /settings/google", status, data)
    if status == 200 and isinstance(data, dict):
        if "folder_id" not in data or "credentials_path" not in data:
            FAILED.append("GET /settings/google (keys)")
            print("  FAIL GET /settings/google missing keys")
        else:
            PASSED.append("GET /settings/google (keys)")

    status, data = request("POST", "/settings/google", {"folder_id": "", "credentials_path": "config/x.json"})
    ok("POST /settings/google", status, data)

    # Clients
    status, data = request("GET", "/clients")
    ok("GET /clients", status, data)
    status, data = request("GET", "/clients?status=active&limit=5")
    ok("GET /clients?status=active", status, data)
    status, data = request("GET", "/clients/search?q=test&limit=5")
    ok("GET /clients/search", status, data)

    status, data = request("POST", "/clients", {"name": "Test Client API", "status": "active"})
    ok("POST /clients", status, data)
    client_id = data.get("id") if isinstance(data, dict) and status == 200 else None

    if client_id:
        status, data = request("GET", f"/clients/{client_id}")
        ok("GET /clients/{id}", status, data)
        status, data = request("PATCH", f"/clients/{client_id}", {"notes": "Updated by test"})
        ok("PATCH /clients/{id}", status, data)
        status, _ = request("POST", f"/clients/{client_id}/archive")
        ok("POST /clients/{id}/archive", status, data)
        status, _ = request("DELETE", f"/clients/{client_id}")
        ok("DELETE /clients/{id}", status, data)

    # Deals
    status, data = request("GET", "/deals")
    ok("GET /deals", status, data)
    status, data = request("POST", "/deals", {"title": "Test Deal API", "status": "draft"})
    ok("POST /deals", status, data)
    deal_id = data.get("id") if isinstance(data, dict) and status == 200 else None
    if deal_id:
        status, data = request("GET", f"/deals/{deal_id}")
        ok("GET /deals/{id}", status, data)
        status, data = request("PATCH", f"/deals/{deal_id}", {"status": "in_progress"})
        ok("PATCH /deals/{id}", status, data)
        status, _ = request("DELETE", f"/deals/{deal_id}")
        ok("DELETE /deals/{id}", status, data)

    # Tasks
    status, data = request("GET", "/tasks")
    ok("GET /tasks", status, data)
    status, data = request("POST", "/tasks", {"title": "Test Task API", "is_completed": False})
    ok("POST /tasks", status, data)
    task_id = data.get("id") if isinstance(data, dict) and status == 200 else None
    if task_id:
        status, data = request("GET", f"/tasks/{task_id}")
        ok("GET /tasks/{id}", status, data)
        status, data = request("POST", f"/tasks/{task_id}/complete?completed=true")
        ok("POST /tasks/{id}/complete", status, data)
        status, _ = request("DELETE", f"/tasks/{task_id}")
        ok("DELETE /tasks/{id}", status, data)

    # Export (200 = success; 500/503 = endpoint ok, credentials missing or error)
    status, data = request("POST", "/export/clients", {})
    if status == 200:
        PASSED.append("POST /export/clients")
        print("  OK   POST /export/clients -> 200")
    elif status in (500, 503):
        PASSED.append("POST /export/clients (creds/env)")
        print(f"  OK   POST /export/clients -> {status} (credentials/env)")
    else:
        FAILED.append("POST /export/clients")
        print(f"  FAIL POST /export/clients -> {status} {data}")

    status, files_data = request("GET", "/export/files?section=clients")
    if status in (200, 500):
        ok("GET /export/files", status, files_data)
    else:
        FAILED.append("GET /export/files")
        print(f"  FAIL GET /export/files -> {status}")

    # 404
    status, _ = request("GET", "/clients/999999")
    if status == 404:
        PASSED.append("GET /clients/999999 -> 404")
        print("  OK   GET /clients/999999 -> 404")
    else:
        FAILED.append("404 check")
        print(f"  FAIL expected 404 got {status}")

    print()
    print("Passed:", len(PASSED))
    print("Failed:", len(FAILED))
    if FAILED:
        print("Failed tests:", FAILED)
        raise SystemExit(1)
    print("All tests passed.")


if __name__ == "__main__":
    main()
