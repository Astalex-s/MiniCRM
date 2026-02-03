import { useState, useEffect, useRef } from 'react'
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
  const [uploadingCredentials, setUploadingCredentials] = useState(false)
  const [uploadingClientSecret, setUploadingClientSecret] = useState(false)
  const credentialsInputRef = useRef(null)
  const clientSecretInputRef = useRef(null)

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

  const handleFileSelect = async (target, file) => {
    if (!file || !file.name.toLowerCase().endsWith('.json')) {
      setError('Выберите файл с расширением .json')
      return
    }
    setError('')
    if (target === 'credentials') setUploadingCredentials(true)
    else setUploadingClientSecret(true)
    try {
      const res = await api.settings.uploadGoogleFile(file, target)
      if (res?.path) {
        if (target === 'credentials') setCredentialsPath(res.path)
        else setClientSecretPath(res.path)
      }
    } catch (e) {
      setError(e.message)
    } finally {
      if (target === 'credentials') setUploadingCredentials(false)
      else setUploadingClientSecret(false)
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
            <label className="form-label">Сервисный аккаунт (excel-factory.json)</label>
            <div className="input-group">
              <input
                type="text"
                className="form-control font-monospace"
                placeholder="config/excel-factory.json"
                value={credentialsPath}
                onChange={(e) => setCredentialsPath(e.target.value)}
              />
              <input
                ref={credentialsInputRef}
                type="file"
                accept=".json"
                className="d-none"
                onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFileSelect('credentials', f); e.target.value = '' }}
              />
              <button
                type="button"
                className="btn btn-outline-secondary"
                disabled={uploadingCredentials}
                onClick={() => credentialsInputRef.current?.click()}
              >
                {uploadingCredentials ? <span className="spinner-border spinner-border-sm" /> : 'Выбрать файл'}
              </button>
            </div>
            <div className="form-text">Укажите путь вручную или загрузите JSON — сохранится в config/</div>
          </div>
          <div className="mb-4">
            <label className="form-label">Client secret (JSON), для OAuth</label>
            <div className="input-group">
              <input
                type="text"
                className="form-control font-monospace"
                placeholder="config/client_secret.json"
                value={clientSecretPath}
                onChange={(e) => setClientSecretPath(e.target.value)}
              />
              <input
                ref={clientSecretInputRef}
                type="file"
                accept=".json"
                className="d-none"
                onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFileSelect('client_secret', f); e.target.value = '' }}
              />
              <button
                type="button"
                className="btn btn-outline-secondary"
                disabled={uploadingClientSecret}
                onClick={() => clientSecretInputRef.current?.click()}
              >
                {uploadingClientSecret ? <span className="spinner-border spinner-border-sm" /> : 'Выбрать файл'}
              </button>
            </div>
            <div className="form-text">Укажите путь вручную или загрузите JSON — сохранится в config/</div>
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
