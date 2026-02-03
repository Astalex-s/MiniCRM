import { useState, useEffect } from 'react'
import { api, formatExportError } from '../api'
import { BsModal } from './BsModal'
import { ReportsModal } from './ReportsModal'

const statusBadge = (s) => {
  const cls = s === 'active' ? 'bg-success' : 'bg-secondary'
  return <span className={`badge ${cls}`}>{s}</span>
}

export function ClientsSection() {
  const [list, setList] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [search, setSearch] = useState('')
  const [modal, setModal] = useState(null)
  const [formError, setFormError] = useState('')
  const [exportLoading, setExportLoading] = useState(false)
  const [exportResult, setExportResult] = useState(null)
  const [reportsModalOpen, setReportsModalOpen] = useState(false)

  const load = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = search
        ? await api.clients.search(search)
        : await api.clients.list({ limit: 200 })
      setList(Array.isArray(data) ? data : [])
    } catch (e) {
      setError(e.message)
      setList([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [search])

  const openCreate = () => {
    setModal({ type: 'create', data: { name: '', email: '', phone: '', status: 'active', notes: '' } })
    setFormError('')
  }
  const openEdit = (row) => {
    setModal({ type: 'edit', id: row.id, data: { name: row.name, email: row.email || '', phone: row.phone || '', status: row.status, notes: row.notes || '' } })
    setFormError('')
  }
  const closeModal = () => setModal(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setFormError('')
    const fd = new FormData(e.target)
    const data = { name: fd.get('name').trim(), email: fd.get('email')?.trim() || null, phone: fd.get('phone')?.trim() || null, status: fd.get('status'), notes: fd.get('notes')?.trim() || null }
    if (!data.name) { setFormError('Укажите имя'); return }
    try {
      if (modal.type === 'create') await api.clients.create(data)
      else await api.clients.update(modal.id, data)
      closeModal()
      load()
    } catch (err) {
      setFormError(err.message)
    }
  }

  const archive = async (id) => {
    if (!confirm('Архивировать клиента?')) return
    try {
      await api.clients.archive(id)
      load()
    } catch (e) {
      setError(e.message)
    }
  }
  const remove = async (id) => {
    if (!confirm('Удалить клиента навсегда?')) return
    try {
      await api.clients.delete(id)
      load()
    } catch (e) {
      setError(e.message)
    }
  }

  const runExport = async () => {
    setExportResult(null)
    setExportLoading(true)
    try {
      const res = await api.export.clients()
      setExportResult(res)
    } catch (e) {
      setExportResult({ error: e.message })
    } finally {
      setExportLoading(false)
    }
  }

  return (
    <div className="card">
      <div className="card-header bg-white py-3 d-flex flex-wrap align-items-center gap-2 justify-content-between">
        <div className="d-flex flex-wrap align-items-center gap-2">
          <button type="button" className="btn btn-primary" onClick={openCreate}>
            <i className="bi bi-plus-lg me-1"></i>Добавить
          </button>
          <button type="button" className="btn btn-outline-secondary" onClick={load}>
            <i className="bi bi-arrow-clockwise me-1"></i>Обновить
          </button>
          <div className="input-group" style={{ width: '220px' }}>
            <span className="input-group-text bg-white"><i className="bi bi-search text-muted"></i></span>
            <input
              type="search"
              className="form-control"
              placeholder="Поиск..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <button type="button" className="btn btn-success" onClick={runExport} disabled={exportLoading} title="Выгрузить таблицу в Google Таблицы">
            {exportLoading ? <span className="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true" /> : <i className="bi bi-file-earmark-spreadsheet me-1"></i>}
            Выгрузить отчёт
          </button>
          <button type="button" className="btn btn-outline-primary" onClick={() => setReportsModalOpen(true)} title="Все отчёты по клиентам в Google Drive">
            <i className="bi bi-folder2-open me-1"></i>Мои отчёты
          </button>
        </div>
      </div>
      {exportResult && (
        <div className={`alert m-3 mb-0 ${exportResult.error ? 'alert-danger' : 'alert-success'} alert-dismissible fade show`} role="alert">
          {exportResult.error ? (
            formatExportError(exportResult.error)
          ) : (
            <>
              Отчёт «{exportResult.title}» создан.{' '}
              <a href={exportResult.webViewLink} target="_blank" rel="noopener noreferrer">Открыть таблицу</a>
            </>
          )}
          <button type="button" className="btn-close" onClick={() => setExportResult(null)} aria-label="Закрыть" />
        </div>
      )}
      <div className="card-body p-0">
        {error && (
          <div className="alert alert-danger alert-dismissible fade show m-3 mb-0" role="alert">
            {error}
            <button type="button" className="btn-close" onClick={() => setError(null)} aria-label="Закрыть" />
          </div>
        )}
        <div className="table-responsive">
          {loading ? (
            <div className="text-center py-5 text-muted">
              <div className="spinner-border" role="status"><span className="visually-hidden">Загрузка...</span></div>
              <p className="mt-2 mb-0">Загрузка...</p>
            </div>
          ) : list.length === 0 ? (
            <div className="text-center py-5 text-muted">
              <i className="bi bi-people display-4"></i>
              <p className="mt-2 mb-0">Нет клиентов</p>
            </div>
          ) : (
            <table className="table table-hover table-striped align-middle mb-0">
              <thead className="table-light">
                <tr>
                  <th>ID</th><th>Имя</th><th>Email</th><th>Телефон</th><th>Статус</th><th>Заметки</th><th style={{ width: '180px' }}></th>
                </tr>
              </thead>
              <tbody>
                {list.map((r) => (
                  <tr key={r.id}>
                    <td><span className="text-muted">#{r.id}</span></td>
                    <td><strong>{r.name}</strong></td>
                    <td>{r.email || '—'}</td>
                    <td>{r.phone || '—'}</td>
                    <td>{statusBadge(r.status)}</td>
                    <td className="text-muted small">{(r.notes || '').slice(0, 40)}{(r.notes || '').length > 40 ? '…' : ''}</td>
                    <td>
                      <div className="btn-group btn-group-sm">
                        <button type="button" className="btn btn-outline-primary" onClick={() => openEdit(r)} title="Изменить">
                          <i className="bi bi-pencil"></i>
                        </button>
                        {r.status === 'active' && (
                          <button type="button" className="btn btn-outline-warning" onClick={() => archive(r.id)} title="В архив">
                            <i className="bi bi-archive"></i>
                          </button>
                        )}
                        <button type="button" className="btn btn-outline-danger" onClick={() => remove(r.id)} title="Удалить">
                          <i className="bi bi-trash"></i>
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      <BsModal show={!!modal} onClose={closeModal} title={modal?.type === 'create' ? 'Новый клиент' : 'Редактирование клиента'}>
        {formError && <div className="alert alert-danger py-2">{formError}</div>}
        <form onSubmit={handleSubmit}>
          <div className="mb-3">
            <label className="form-label">Имя *</label>
            <input name="name" className="form-control" defaultValue={modal?.data?.name} required />
          </div>
          <div className="mb-3">
            <label className="form-label">Email</label>
            <input name="email" type="email" className="form-control" defaultValue={modal?.data?.email} />
          </div>
          <div className="mb-3">
            <label className="form-label">Телефон</label>
            <input name="phone" className="form-control" defaultValue={modal?.data?.phone} />
          </div>
          <div className="mb-3">
            <label className="form-label">Статус</label>
            <select name="status" className="form-select" defaultValue={modal?.data?.status}>
              <option value="active">Активный</option>
              <option value="archived">Архив</option>
            </select>
          </div>
          <div className="mb-4">
            <label className="form-label">Заметки</label>
            <textarea name="notes" className="form-control" rows={3} defaultValue={modal?.data?.notes} />
          </div>
          <div className="d-flex justify-content-end gap-2">
            <button type="button" className="btn btn-secondary" onClick={closeModal}>Отмена</button>
            <button type="submit" className="btn btn-primary">Сохранить</button>
          </div>
        </form>
      </BsModal>
      <ReportsModal show={reportsModalOpen} onClose={() => setReportsModalOpen(false)} section="clients" sectionLabel="Клиенты" />
    </div>
  )
}
