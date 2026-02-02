export function BsModal({ show, onClose, title, children }) {
  if (!show) return null
  return (
    <>
      <div className="modal-backdrop fade show" onClick={onClose} aria-hidden="true" />
      <div
        className="modal fade show"
        style={{ display: 'block' }}
        onClick={onClose}
        tabIndex={-1}
        aria-modal="true"
      >
        <div className="modal-dialog modal-dialog-centered" onClick={(e) => e.stopPropagation()}>
          <div className="modal-content shadow">
            <div className="modal-header border-0 pb-0">
              <h5 className="modal-title fw-semibold">{title}</h5>
              <button type="button" className="btn-close" onClick={onClose} aria-label="Закрыть" />
            </div>
            <div className="modal-body pt-2">{children}</div>
          </div>
        </div>
      </div>
    </>
  )
}
