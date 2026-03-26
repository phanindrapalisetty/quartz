import React, { useEffect, useState } from 'react'
import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { Database, LogOut, Table2 } from 'lucide-react'
import api from '../lib/api'
import { clearSession } from '../lib/session'

export default function Layout() {
  const [user, setUser] = useState(null)
  const location = useLocation()
  const navigate = useNavigate()

  useEffect(() => {
    api.get('/auth/me').then((r) => setUser(r.data)).catch(() => {})
  }, [])

  function logout() {
    api.delete('/auth/logout').finally(() => {
      clearSession()
      navigate('/')
    })
  }

  function navLink(to, Icon, label) {
    const active = location.pathname === to
    return (
      <Link
        to={to}
        className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
          active
            ? 'bg-[#E8F4F7] text-[#0D2E37]'
            : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
        }`}
      >
        <Icon size={14} />
        {label}
      </Link>
    )
  }

  return (
    <div className="min-h-screen flex flex-col">
      <nav className="bg-white border-b border-gray-200 px-5 h-13 flex items-center justify-between shrink-0" style={{ height: 52 }}>
        <div className="flex items-center gap-5">
          <span className="font-bold text-[#0D2E37] text-base tracking-tight select-none">
            Quartz
          </span>
          <div className="flex items-center gap-0.5">
            {navLink('/load',  Database, 'Load')}
            {navLink('/query', Table2,   'Query')}
          </div>
        </div>

        {user && (
          <div className="flex items-center gap-3">
            <div className="w-7 h-7 rounded-full bg-[#E8F4F7] flex items-center justify-center text-xs font-semibold text-[#0D2E37] shrink-0">
              {user.name?.[0]?.toUpperCase() ?? user.email?.[0]?.toUpperCase() ?? '?'}
            </div>
            <span className="text-sm text-gray-600 hidden sm:block">{user.email}</span>
            <button
              onClick={logout}
              title="Logout"
              className="p-1.5 text-gray-400 hover:text-gray-700 hover:bg-gray-100 rounded transition-colors"
            >
              <LogOut size={15} />
            </button>
          </div>
        )}
      </nav>

      <main className="flex-1 flex flex-col overflow-hidden">
        <Outlet />
      </main>
    </div>
  )
}
