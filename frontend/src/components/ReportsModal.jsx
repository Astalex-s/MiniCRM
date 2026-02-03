import { useState, useEffect } from 'react'
import { api } from '../api'
import { BsModal } from './BsModal'

function formatDate(iso) {
  if (!iso) return '—'
  try {
    const d = new Date(iso)
    return d.toLocaleString('ru-RU', { dateStyle: 'short', timeStyle: 'short' })
  } catch {
    return iso
  }
}

export function ReportsModal({ show, onClose, section, sectionLabel }) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [files, setFiles] = useState([])

  useEffect(() => {
    if (show && section) {
      setError('')
      setLoading(true)
      api.export
        .listFiles(section)
        .then((data) => setFiles(Array.isArray(data?.files) ? data.files : []))
        .catch((e) => {
          setError(e.message)
          setFiles([])
        })
        .finally(() => setLoading(false))
    }
  }, [show, section])

  return (
    <BsModal show={show} onClose={onClose} title={`Отчёты: ${sectionLabel || section}`}>
      {error && <div className="alert alert-danger py-2">{error}</div>}
      {loading ? (
        <div className="text-center py-4 text-muted">
          <div className="spinner-border" role="status"><span className="visually-hidden">Загрузка...</span></div>
          <p className="mt-2 mb-0">Загрузка списка отчётов...</p>
        </div>
      ) : files.length === 0 ? (
        <p className="text-muted mb-0">Нет выгруженных отчётов по этому разделу.</p>
      ) : (
        <div className="list-group list-group-flush">
          {files.map((f) => (
            <div key={f.id} className="list-group-item d-flex align-items-center justify-content-between px-0">
              <div className="text-truncate me-2" title={f.name}>
                <span className="fw-medium">{f.name}</span>
                <br />
                <small className="text-muted">{formatDate(f.modifiedTime)}</small>
              </div>
              <a
                href={f.webViewLink}
                target="_blank"
                rel="noopener noreferrer"
                className="btn btn-sm btn-outline-primary text-nowrap"
              >
                Открыть
              </a>
            </div>
          ))}
        </div>
      )}
    </BsModal>
  )
}
