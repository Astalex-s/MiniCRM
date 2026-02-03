import { useState, useEffect } from 'react'
import { api, formatExportError } from '../api'
import { BsModal } from './BsModal'
import { Pagination } from './Pagination'
import { ReportsModal } from './ReportsModal'

const PER_PAGE = 10

/** Фильтр по дате: дата записи (created_at) в формате YYYY-MM-DD входит в [dateFrom, dateTo]. */
function filterByDateRange(items, dateFrom, dateTo, dateField = 'created_at') {
  if (!dateFrom && !dateTo) return items
  return items.filter((item) => {
    const raw = item[dateField] || ''
    const d = String(raw).slice(0, 10)
    if (dateFrom && d < dateFrom) return false
    if (dateTo && d > dateTo) return false
    return true
  })
}

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
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')

  const load = async () => {
    setLoading(true)
    setError(null)
    try {
      const params = { limit: 200 }
      if (statusFilter) params.status = statusFilter
      const data = search
        ? await api.clients.search(search)
        : await api.clients.list(params)
      setList(Array.isArray(data) ? data : [])
      setPage(1)
    } catch (e) {
      setError(e.message)
      setList([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [search, statusFilter])

  let filteredList = filterByDateRange(list, dateFrom, dateTo)
  if (statusFilter && search) filteredList = filteredList.filter((r) => r.status === statusFilter)
  const totalPages = Math.max(1, Math.ceil(filteredList.length / PER_PAGE))
  const safePage = Math.min(page, totalPages)
  const visibleList = filteredList.slice((safePage - 1) * PER_PAGE, safePage * PER_PAGE)

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
        <div className="d-flex flex-wrap align-items-center gap-3 mt-2 pt-2 border-top">
          <span className="text-muted small">Фильтры:</span>
          <select className="form-select form-select-sm" style={{ width: 'auto' }} value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
            <option value="">Все статусы</option>
            <option value="active">Активные</option>
            <option value="archived">В архиве</option>
          </select>
          <label className="d-flex align-items-center gap-1 small text-muted">
            Создано с
            <input type="date" className="form-control form-control-sm" style={{ width: 'auto' }} value={dateFrom} onChange={(e) => { setDateFrom(e.target.value); setPage(1) }} />
          </label>
          <label className="d-flex align-items-center gap-1 small text-muted">
            по
            <input type="date" className="form-control form-control-sm" style={{ width: 'auto' }} value={dateTo} onChange={(e) => { setDateTo(e.target.value); setPage(1) }} />
          </label>
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
          ) : filteredList.length === 0 ? (
            <div className="text-center py-5 text-muted">
              <p className="mt-2 mb-0">Нет записей по выбранным фильтрам</p>
            </div>
          ) : (
            <>
            <table className="table table-hover table-striped align-middle mb-0">
              <thead className="table-light">
                <tr>
                  <th>ID</th><th>Имя</th><th>Email</th><th>Телефон</th><th>Статус</th><th>Заметки</th><th style={{ width: '180px' }}></th>
                </tr>
              </thead>
              <tbody>
                {visibleList.map((r) => (
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
            <Pagination
              total={filteredList.length}
              perPage={PER_PAGE}
              currentPage={safePage}
              onPageChange={setPage}
            />
            </>
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
