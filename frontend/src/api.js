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

/** Понятное сообщение для ошибок экспорта в Google. */
export function formatExportError(message) {
  if (!message || typeof message !== 'string') return message
  if (/storageQuotaExceeded|storage.?quota|quota.?exceeded/i.test(message)) {
    return 'Квота хранилища Google Drive превышена. Освободите место в Drive или используйте другой аккаунт.'
  }
  if (/учётных данных не найден|credentials|\.env/i.test(message)) {
    return 'Файл учётных данных не найден. Задайте GOOGLE_CREDENTIALS_PATH или GOOGLE_CLIENT_SECRET_PATH в .env.'
  }
  return message
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
    /** Список выгруженных отчётов по разделу (clients | deals | tasks) */
    listFiles: (section) => request('GET', `/export/files?section=${encodeURIComponent(section)}`),
  },
  // Настройки Google (сохраняются в файл на сервере)
  settings: {
    getGoogle: () => request('GET', '/settings/google'),
    saveGoogle: (data) => request('POST', '/settings/google', data),
    /** Загрузить JSON конфигурации в config/, вернёт { path } */
    uploadGoogleFile: (file, target) => {
      const form = new FormData()
      form.append('file', file)
      return fetch(`${API_BASE}/settings/google/upload?target=${encodeURIComponent(target)}`, {
        method: 'POST',
        body: form,
      }).then((res) => {
        if (!res.ok) return res.json().then((err) => { throw new Error(err.detail || res.statusText) })
        return res.json()
      })
    },
  },
}
