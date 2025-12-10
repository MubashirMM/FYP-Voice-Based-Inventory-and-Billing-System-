import React, { useState } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import Header from './components/Header'
import Sidebar from './components/Sidebar'
import Dashboard from './pages/Dashboard'
import VoiceBilling from './pages/VoiceBilling'
import Inventory from './pages/Inventory'
import UdharKhata from './pages/UdharKhata'
import Reports from './pages/Reports'
import Settings from './pages/Settings'
import Login from './pages/Login'
import Register from './pages/Register'

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(() => {
    try { return localStorage.getItem('ims_auth') === '1' } catch (e) { return false }
  })
  const [showRegister, setShowRegister] = useState(false)
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)
  const [isDarkMode, setIsDarkMode] = useState(() => {
    try { return localStorage.getItem('ims_theme') === 'dark' } catch (e) { return false }
  })

  const toggleSidebar = () => setIsSidebarOpen(!isSidebarOpen)
  const toggleTheme = () => setIsDarkMode(!isDarkMode)

  React.useEffect(() => {
    try { localStorage.setItem('ims_theme', isDarkMode ? 'dark' : 'light') } catch (e) {}
  }, [isDarkMode])

  React.useEffect(() => {
    try { localStorage.setItem('ims_auth', isAuthenticated ? '1' : '0') } catch (e) {}
  }, [isAuthenticated])

  if (!isAuthenticated) {
    if (showRegister) {
      return (
        <Register 
          onBackToLogin={() => setShowRegister(false)}
          onRegisterSuccess={() => setShowRegister(false)}
        />
      )
    }
    return (
      <Login 
        onLogin={() => setIsAuthenticated(true)} 
        onRegisterClick={() => setShowRegister(true)}
      />
    )
  }

  return (
    <Router>
      <div className={isDarkMode ? 'dark' : ''}>
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
          <Header toggleSidebar={toggleSidebar} toggleTheme={toggleTheme} isDarkMode={isDarkMode} />
          <Sidebar isOpen={isSidebarOpen} toggleSidebar={toggleSidebar} />
          
          <main className="lg:ml-64 pt-16 p-4 md:p-6">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/voice-billing" element={<VoiceBilling />} />
              <Route path="/inventory" element={<Inventory />} />
              <Route path="/udhar" element={<UdharKhata />} />
              <Route path="/reports" element={<Reports />} />
              <Route path="/settings" element={<Settings toggleTheme={toggleTheme} isDarkMode={isDarkMode} />} />
              <Route path="*" element={<Navigate to="/" />} />
            </Routes>
          </main>
        </div>
      </div>
    </Router>
  )
}

export default App
