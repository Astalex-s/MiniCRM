import { useState } from 'react'
import { ClientsSection } from './components/ClientsSection'
import { DealsSection } from './components/DealsSection'
import { TasksSection } from './components/TasksSection'
import { GoogleSettingsModal } from './components/GoogleSettingsModal'
import './App.css'

const TABS = [
  { id: 'clients', label: 'Клиенты', icon: 'people' },
  { id: 'deals', label: 'Сделки', icon: 'briefcase' },
  { id: 'tasks', label: 'Задачи', icon: 'check2-square' },
]

export default function App() {
  const [activeTab, setActiveTab] = useState('clients')
  const [menuOpen, setMenuOpen] = useState(false)
  const [googleSettingsOpen, setGoogleSettingsOpen] = useState(false)

  const onTabClick = (id) => {
    setActiveTab(id)
    setMenuOpen(false)
  }

  const currentTab = TABS.find((t) => t.id === activeTab)

  return (
    <div className="min-vh-100 bg-light">
      <nav className="navbar navbar-expand-lg navbar-dark bg-primary shadow-sm">
        <div className="container-fluid container-lg">
          <span className="navbar-brand fw-bold d-flex align-items-center gap-2">
            <i className="bi bi-grid-3x3-gap"></i>
            Мини-CRM
          </span>
          <span className="navbar-current d-lg-none d-flex align-items-center gap-2 text-white ms-auto me-2">
            <i className={`bi bi-${currentTab?.icon}`}></i>
            <span className="fw-medium">{currentTab?.label}</span>
          </span>
          <button
            type="button"
            className="navbar-toggler border-0 text-white"
            onClick={() => setMenuOpen(!menuOpen)}
            aria-expanded={menuOpen}
            aria-label="Открыть меню"
          >
            <i className={`bi ${menuOpen ? 'bi-x-lg' : 'bi-list'} fs-4`}></i>
          </button>
          <div className={`collapse navbar-collapse ${menuOpen ? 'show' : ''}`} id="navbarNav">
            <ul className="navbar-nav nav-pills ms-auto align-items-lg-center">
              <li className="nav-item">
                <button
                  type="button"
                  className="nav-link text-white"
                  onClick={() => { setGoogleSettingsOpen(true); setMenuOpen(false); }}
                >
                  <i className="bi bi-gear me-1"></i>Настройки Google
                </button>
              </li>
              {TABS.map(({ id, label, icon }) => (
                <li className="nav-item" key={id}>
                  <button
                    type="button"
                    className={`nav-link ${activeTab === id ? 'active' : 'text-white'}`}
                    onClick={() => onTabClick(id)}
                  >
                    <i className={`bi bi-${icon} me-1`}></i>
                    {label}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </nav>

      <main className="container-fluid container-lg py-4">
        {activeTab === 'clients' && <ClientsSection />}
        {activeTab === 'deals' && <DealsSection />}
        {activeTab === 'tasks' && <TasksSection />}
      </main>
      <GoogleSettingsModal show={googleSettingsOpen} onClose={() => setGoogleSettingsOpen(false)} />
    </div>
  )
}
