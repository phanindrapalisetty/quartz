import React, { useEffect, useState } from 'react'
import { Navigate, Route, Routes, useSearchParams } from 'react-router-dom'
import { getSessionId, setSessionId } from './lib/session'
import Layout from './components/Layout'
import Login from './pages/Login'
import Load from './pages/Load'
import Query from './pages/Query'

function SessionInit({ children }) {
  const [searchParams, setSearchParams] = useSearchParams()
  const [ready, setReady] = useState(false)

  useEffect(() => {
    const sid = searchParams.get('session_id')
    if (sid) {
      setSessionId(sid)
      setSearchParams({}, { replace: true })
    }
    setReady(true)
  }, [])

  if (!ready) return null
  return children
}

function Protected({ children }) {
  if (!getSessionId()) return <Navigate to="/" replace />
  return children
}

export default function App() {
  return (
    <SessionInit>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route element={<Layout />}>
          <Route path="/load"  element={<Protected><Load /></Protected>} />
          <Route path="/query" element={<Protected><Query /></Protected>} />
        </Route>
      </Routes>
    </SessionInit>
  )
}
