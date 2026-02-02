const API_BASE = '/api'

async function request(method, path, body = null) {
  const opts = { method, headers: {} }
  if (body) {
    opts.headers['Content-Type'] = 'application/json'
    opts.body = JSON.stringify(body)
  }
  const res = await fetch(`${API_BASE}${path}`, opts)
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  const text = await res.text()
  return text ? JSON.parse(text) : null
}

export const api = {
  // Клиенты
  clients: {
    list: (params = {}) => {
      const q = new URLSearchParams(params).toString()
      return request('GET', `/clients${q ? '?' + q : ''}`)
    },
    search: (q, limit = 100) => request('GET', `/clients/search?q=${encodeURIComponent(q)}&limit=${limit}`),
    get: (id) => request('GET', `/clients/${id}`),
    create: (data) => request('POST', '/clients', data),
    update: (id, data) => request('PATCH', `/clients/${id}`, data),
    delete: (id) => request('DELETE', `/clients/${id}`),
    archive: (id) => request('POST', `/clients/${id}/archive`, {}),
  },
  // Сделки
  deals: {
    list: (params = {}) => {
      const q = new URLSearchParams(params).toString()
      return request('GET', `/deals${q ? '?' + q : ''}`)
    },
    search: (q, limit = 100) => request('GET', `/deals/search?q=${encodeURIComponent(q)}&limit=${limit}`),
    get: (id) => request('GET', `/deals/${id}`),
    create: (data) => request('POST', '/deals', data),
    update: (id, data) => request('PATCH', `/deals/${id}`, data),
    delete: (id) => request('DELETE', `/deals/${id}`),
  },
  // Задачи
  tasks: {
    list: (params = {}) => {
      const q = new URLSearchParams(params).toString()
      return request('GET', `/tasks${q ? '?' + q : ''}`)
    },
    get: (id) => request('GET', `/tasks/${id}`),
    create: (data) => request('POST', '/tasks', data),
    update: (id, data) => request('PATCH', `/tasks/${id}`, data),
    delete: (id) => request('DELETE', `/tasks/${id}`),
    setCompleted: (id, completed) => request('POST', `/tasks/${id}/complete?completed=${completed}`, {}),
  },
  // Экспорт в Google Таблицы
  export: {
    clients: (folderId = null) => request('POST', '/export/clients', folderId != null ? { folder_id: folderId } : {}),
    deals: (folderId = null) => request('POST', '/export/deals', folderId != null ? { folder_id: folderId } : {}),
    tasks: (folderId = null) => request('POST', '/export/tasks', folderId != null ? { folder_id: folderId } : {}),
  },
  // Настройки Google (сохраняются в файл на сервере)
  settings: {
    getGoogle: () => request('GET', '/settings/google'),
    saveGoogle: (data) => request('POST', '/settings/google', data),
  },
}
