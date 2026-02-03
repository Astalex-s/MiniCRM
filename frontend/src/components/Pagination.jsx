/**
 * Пагинация: кнопки «Предыдущая» / «Следующая» и подпись «Страница X из Y» (всего N записей).
 * perPage — записей на странице, total — всего записей, currentPage — текущая (1-based), onPageChange(page).
 */
export function Pagination({ total, perPage, currentPage, onPageChange }) {
  const totalPages = Math.max(1, Math.ceil(total / perPage))
  const page = Math.min(Math.max(1, currentPage), totalPages)
  const from = total === 0 ? 0 : (page - 1) * perPage + 1
  const to = Math.min(page * perPage, total)

  return (
    <nav className="d-flex align-items-center justify-content-between flex-wrap gap-2 py-2 px-3 border-top bg-light" aria-label="Пагинация">
      <span className="text-muted small">
        {total === 0 ? 'Нет записей' : `Показано ${from}–${to} из ${total}`}
      </span>
      <div className="d-flex align-items-center gap-1">
        <button
          type="button"
          className="btn btn-sm btn-outline-secondary"
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}
          aria-label="Предыдущая страница"
        >
          <i className="bi bi-chevron-left" />
        </button>
        <span className="px-2 small text-nowrap">
          Страница {page} из {totalPages}
        </span>
        <button
          type="button"
          className="btn btn-sm btn-outline-secondary"
          disabled={page >= totalPages}
          onClick={() => onPageChange(page + 1)}
          aria-label="Следующая страница"
        >
          <i className="bi bi-chevron-right" />
        </button>
      </div>
    </nav>
  )
}
