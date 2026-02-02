import { useState, useEffect } from 'react'
import { api } from '../api'
import { BsModal } from './BsModal'

export function GoogleSettingsModal({ show, onClose }) {
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [folderId, setFolderId] = useState('')
  const [credentialsPath, setCredentialsPath] = useState('')
  const [clientSecretPath, setClientSecretPath] = useState('')
  const [pasteError, setPasteError] = useState('')

  useEffect(() => {
    if (show) {
      setError('')
      setPasteError('')
      setLoading(true)
      api.settings
        .getGoogle()
        .then((data) => {
          setFolderId(data?.folder_id ?? '')
          setCredentialsPath(data?.credentials_path ?? '')
          setClientSecretPath(data?.client_secret_path ?? '')
        })
        .catch((e) => setError(e.message))
        .finally(() => setLoading(false))
    }
  }, [show])

  const handlePaste = async () => {
    setPasteError('')
    try {
      const text = await navigator.clipboard.readText()
      setFolderId(text)
    } catch (e) {
      setPasteError('Не удалось вставить из буфера. Разрешите доступ к буферу обмена или вставьте вручную (Ctrl+V).')
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSaving(true)
    try {
      await api.settings.saveGoogle({
        folder_id: folderId.trim() || null,
        credentials_path: credentialsPath.trim() || null,
        client_secret_path: clientSecretPath.trim() || null,
      })
      onClose()
    } catch (e) {
      setError(e.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <BsModal show={show} onClose={onClose} title="Настройки Google (экспорт отчётов)">
      {loading ? (
        <div className="text-center py-4 text-muted">
          <div className="spinner-border" role="status"><span className="visually-hidden">Загрузка...</span></div>
        </div>
      ) : (
        <form onSubmit={handleSubmit}>
          {error && <div className="alert alert-danger py-2">{error}</div>}
          <div className="mb-3">
            <label className="form-label">ID папки Google Drive для отчётов</label>
            <div className="input-group">
              <input
                type="text"
                className="form-control font-monospace"
                placeholder="Например: 1abc..."
                value={folderId}
                onChange={(e) => setFolderId(e.target.value)}
              />
              <button type="button" className="btn btn-outline-secondary" onClick={handlePaste} title="Вставить из буфера (Ctrl+V может не сработать в окне)">
                Вставить
              </button>
            </div>
            {pasteError && <div className="form-text text-danger">{pasteError}</div>}
            <div className="form-text">Откройте папку в Google Drive в браузере — ID есть в URL после /folders/</div>
          </div>
          <div className="mb-3">
            <label className="form-label">Путь к credentials (JSON), необязательно</label>
            <input
              type="text"
              className="form-control font-monospace"
              placeholder="config/credentials.json"
              value={credentialsPath}
              onChange={(e) => setCredentialsPath(e.target.value)}
            />
          </div>
          <div className="mb-4">
            <label className="form-label">Путь к client_secret (JSON), необязательно</label>
            <input
              type="text"
              className="form-control font-monospace"
              placeholder="config/client_secret.json"
              value={clientSecretPath}
              onChange={(e) => setClientSecretPath(e.target.value)}
            />
          </div>
          <div className="d-flex justify-content-end gap-2">
            <button type="button" className="btn btn-secondary" onClick={onClose}>Отмена</button>
            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? 'Сохранение…' : 'Сохранить'}
            </button>
          </div>
        </form>
      )}
    </BsModal>
  )
}
