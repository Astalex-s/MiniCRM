import { useState, useEffect } from 'react'
import { api } from '../api'
import { BsModal } from './BsModal'

export function TasksSection() {
  const [list, setList] = useState([])
  const [clientsList, setClientsList] = useState([])
  const [dealsList, setDealsList] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [modal, setModal] = useState(null)
  const [formError, setFormError] = useState('')

  const loadClientsAndDeals = async () => {
    try {
      const [clients, deals] = await Promise.all([api.clients.list({ limit: 500 }), api.deals.list({ limit: 500 })])
      setClientsList(Array.isArray(clients) ? clients : [])
      setDealsList(Array.isArray(deals) ? deals : [])
    } catch {
      setClientsList([])
      setDealsList([])
    }
  }

  const load = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await api.tasks.list({ limit: 200 })
      setList(Array.isArray(data) ? data : [])
    } catch (e) {
      setError(e.message)
      setList([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])
  useEffect(() => { loadClientsAndDeals() }, [])

  const getClientName = (id) => clientsList.find((c) => c.id === id)?.name ?? null
  const getDealTitle = (id) => dealsList.find((d) => d.id === id)?.title ?? null

  const openCreate = () => {
    setModal({ type: 'create', data: { title: '', description: '', client_id: '', deal_id: '', is_completed: false, due_date: '' } })
    setFormError('')
  }
  const openEdit = (row) => {
    setModal({
      type: 'edit',
      id: row.id,
      data: {
        title: row.title,
        description: row.description || '',
        client_id: row.client_id ?? '',
        deal_id: row.deal_id ?? '',
        is_completed: row.is_completed,
        due_date: (row.due_date || '').slice(0, 10),
      },
    })
    setFormError('')
  }
  const closeModal = () => setModal(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setFormError('')
    const fd = new FormData(e.target)
    const clientId = fd.get('client_id')?.trim()
    const dealId = fd.get('deal_id')?.trim()
    const data = {
      title: fd.get('title').trim(),
      description: fd.get('description')?.trim() || null,
      client_id: clientId ? parseInt(clientId, 10) : null,
      deal_id: dealId ? parseInt(dealId, 10) : null,
      is_completed: fd.get('is_completed') === 'on',
      due_date: fd.get('due_date')?.trim() || null,
    }
    if (!data.title) { setFormError('Укажите название'); return }
    try {
      if (modal.type === 'create') await api.tasks.create(data)
      else await api.tasks.update(modal.id, data)
      closeModal()
      load()
    } catch (err) {
      setFormError(err.message)
    }
  }

  const toggleCompleted = async (id, current) => {
    try {
      await api.tasks.setCompleted(id, !current)
      load()
    } catch (e) {
      setError(e.message)
    }
  }
  const remove = async (id) => {
    if (!confirm('Удалить задачу?')) return
    try {
      await api.tasks.delete(id)
      load()
    } catch (e) {
      setError(e.message)
    }
  }

  return (
    <div className="card">
      <div className="card-header bg-white py-3 d-flex flex-wrap align-items-center gap-2">
        <button type="button" className="btn btn-primary" onClick={openCreate}>
          <i className="bi bi-plus-lg me-1"></i>Добавить
        </button>
        <button type="button" className="btn btn-outline-secondary" onClick={load}>
          <i className="bi bi-arrow-clockwise me-1"></i>Обновить
        </button>
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
              <i className="bi bi-check2-square display-4"></i>
              <p className="mt-2 mb-0">Нет задач</p>
            </div>
          ) : (
            <table className="table table-hover table-striped align-middle mb-0">
              <thead className="table-light">
                <tr>
                  <th>ID</th><th>Название</th><th>Клиент</th><th>Сделка</th><th>Выполнено</th><th>Срок</th><th style={{ width: '160px' }}></th>
                </tr>
              </thead>
              <tbody>
                {list.map((r) => (
                  <tr key={r.id} className={r.is_completed ? 'table-secondary' : ''}>
                    <td><span className="text-muted">#{r.id}</span></td>
                    <td><strong>{r.title}</strong></td>
                    <td>{getClientName(r.client_id) || (r.client_id != null ? `#${r.client_id}` : '—')}</td>
                    <td>{getDealTitle(r.deal_id) || (r.deal_id != null ? `#${r.deal_id}` : '—')}</td>
                    <td>
                      {r.is_completed ? (
                        <span className="badge bg-success"><i className="bi bi-check-lg me-1"></i>Да</span>
                      ) : (
                        <span className="badge bg-secondary">Нет</span>
                      )}
                    </td>
                    <td className="text-muted">{(r.due_date || '').slice(0, 10) || '—'}</td>
                    <td>
                      <div className="btn-group btn-group-sm">
                        <button
                          type="button"
                          className={r.is_completed ? 'btn btn-outline-secondary' : 'btn btn-outline-success'}
                          onClick={() => toggleCompleted(r.id, r.is_completed)}
                          title={r.is_completed ? 'Отменить выполнение' : 'Отметить выполненной'}
                        >
                          <i className={`bi ${r.is_completed ? 'bi-arrow-counterclockwise' : 'bi-check-lg'}`}></i>
                        </button>
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

      <BsModal show={!!modal} onClose={closeModal} title={modal?.type === 'create' ? 'Новая задача' : 'Редактирование задачи'}>
        {formError && <div className="alert alert-danger py-2">{formError}</div>}
        <form onSubmit={handleSubmit}>
          <div className="mb-3">
            <label className="form-label">Название *</label>
            <input name="title" className="form-control" defaultValue={modal?.data?.title} required />
          </div>
          <div className="mb-3">
            <label className="form-label">Описание</label>
            <textarea name="description" className="form-control" rows={2} defaultValue={modal?.data?.description} />
          </div>
          <div className="row g-2 mb-3">
            <div className="col-6">
              <label className="form-label">Клиент</label>
              <select name="client_id" className="form-select" defaultValue={modal?.data?.client_id ?? ''}>
                <option value="">Без клиента</option>
                {clientsList.map((c) => (
                  <option key={c.id} value={c.id}>{c.name} (#{c.id})</option>
                ))}
              </select>
            </div>
            <div className="col-6">
              <label className="form-label">Сделка</label>
              <select name="deal_id" className="form-select" defaultValue={modal?.data?.deal_id ?? ''}>
                <option value="">Без сделки</option>
                {dealsList.map((d) => (
                  <option key={d.id} value={d.id}>{d.title} (#{d.id})</option>
                ))}
              </select>
            </div>
          </div>
          <div className="mb-3">
            <label className="form-label">Срок</label>
            <input name="due_date" type="date" className="form-control" defaultValue={modal?.data?.due_date} />
          </div>
          <div className="mb-4">
            <div className="form-check">
              <input name="is_completed" type="checkbox" className="form-check-input" id="task-completed" defaultChecked={modal?.data?.is_completed} />
              <label className="form-check-label" htmlFor="task-completed">Выполнено</label>
            </div>
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
