import { useState, useEffect } from 'react'
import { api } from '../api'
import { BsModal } from './BsModal'

const dealStatusBadge = (s) => {
  const map = { draft: 'bg-secondary', in_progress: 'bg-info', won: 'bg-success', lost: 'bg-danger' }
  return <span className={`badge ${map[s] || 'bg-secondary'}`}>{s}</span>
}

export function DealsSection() {
  const [list, setList] = useState([])
  const [clientsList, setClientsList] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [search, setSearch] = useState('')
  const [modal, setModal] = useState(null)
  const [formError, setFormError] = useState('')

  const loadClients = async () => {
    try {
      const data = await api.clients.list({ limit: 500 })
      setClientsList(Array.isArray(data) ? data : [])
    } catch {
      setClientsList([])
    }
  }

  const load = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = search ? await api.deals.search(search) : await api.deals.list({ limit: 200 })
      setList(Array.isArray(data) ? data : [])
    } catch (e) {
      setError(e.message)
      setList([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [search])
  useEffect(() => { loadClients() }, [])

  const getClientName = (clientId) => clientsList.find((c) => c.id === clientId)?.name || null

  const openCreate = () => {
    setModal({ type: 'create', data: { title: '', client_id: '', amount: '', status: 'draft', notes: '' } })
    setFormError('')
  }
  const openEdit = (row) => {
    setModal({ type: 'edit', id: row.id, data: { title: row.title, client_id: row.client_id ?? '', amount: row.amount ?? '', status: row.status, notes: row.notes || '' } })
    setFormError('')
  }
  const closeModal = () => setModal(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setFormError('')
    const fd = new FormData(e.target)
    const clientId = fd.get('client_id')?.trim()
    const amount = fd.get('amount')?.trim()
    const data = {
      title: fd.get('title').trim(),
      client_id: clientId ? parseInt(clientId, 10) : null,
      amount: amount ? parseFloat(amount) : null,
      status: fd.get('status'),
      notes: fd.get('notes')?.trim() || null,
    }
    if (!data.title) { setFormError('Укажите название'); return }
    try {
      if (modal.type === 'create') await api.deals.create(data)
      else await api.deals.update(modal.id, data)
      closeModal()
      load()
    } catch (err) {
      setFormError(err.message)
    }
  }

  const remove = async (id) => {
    if (!confirm('Удалить сделку?')) return
    try {
      await api.deals.delete(id)
      load()
    } catch (e) {
      setError(e.message)
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
            <input type="search" className="form-control" placeholder="Поиск..." value={search} onChange={(e) => setSearch(e.target.value)} />
          </div>
        </div>
      </div>
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
              <i className="bi bi-briefcase display-4"></i>
              <p className="mt-2 mb-0">Нет сделок</p>
            </div>
          ) : (
            <table className="table table-hover table-striped align-middle mb-0">
              <thead className="table-light">
                <tr>
                  <th>ID</th><th>Название</th><th>Клиент</th><th>Сумма</th><th>Статус</th><th>Заметки</th><th style={{ width: '120px' }}></th>
                </tr>
              </thead>
              <tbody>
                {list.map((r) => (
                  <tr key={r.id}>
                    <td><span className="text-muted">#{r.id}</span></td>
                    <td><strong>{r.title}</strong></td>
                    <td>{getClientName(r.client_id) || (r.client_id != null ? `#${r.client_id}` : '—')}</td>
                    <td>{r.amount != null ? <span className="text-nowrap">{r.amount.toLocaleString('ru')}</span> : '—'}</td>
                    <td>{dealStatusBadge(r.status)}</td>
                    <td className="text-muted small">{(r.notes || '').slice(0, 40)}{(r.notes || '').length > 40 ? '…' : ''}</td>
                    <td>
                      <div className="btn-group btn-group-sm">
                        <button type="button" className="btn btn-outline-primary" onClick={() => openEdit(r)} title="Изменить">
                          <i className="bi bi-pencil"></i>
                        </button>
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

      <BsModal show={!!modal} onClose={closeModal} title={modal?.type === 'create' ? 'Новая сделка' : 'Редактирование сделки'}>
        {formError && <div className="alert alert-danger py-2">{formError}</div>}
        <form onSubmit={handleSubmit}>
          <div className="mb-3">
            <label className="form-label">Название *</label>
            <input name="title" className="form-control" defaultValue={modal?.data?.title} required />
          </div>
          <div className="mb-3">
            <label className="form-label">Клиент</label>
            <select name="client_id" className="form-select" defaultValue={modal?.data?.client_id ?? ''}>
              <option value="">Без клиента</option>
              {clientsList.map((c) => (
                <option key={c.id} value={c.id}>{c.name} (#{c.id})</option>
              ))}
            </select>
          </div>
          <div className="mb-3">
            <label className="form-label">Сумма</label>
            <input name="amount" type="number" step="any" className="form-control" defaultValue={modal?.data?.amount} />
          </div>
          <div className="mb-3">
            <label className="form-label">Статус</label>
            <select name="status" className="form-select" defaultValue={modal?.data?.status}>
              <option value="draft">Черновик</option>
              <option value="in_progress">В работе</option>
              <option value="won">Выиграна</option>
              <option value="lost">Проиграна</option>
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
    </div>
  )
}
