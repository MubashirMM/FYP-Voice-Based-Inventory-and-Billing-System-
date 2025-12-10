import React from 'react'
import { Menu, Bell, User, LogOut } from 'lucide-react'

function Header({ toggleSidebar, toggleTheme, isDarkMode }) {
  const handleLogout = () => {
    if (window.confirm('Are you sure you want to logout?')) {
      localStorage.setItem('ims_auth', '0')
      localStorage.removeItem('ims_current_user')
      window.location.reload()
    }
  }

  const getCurrentUser = () => {
    try {
      const user = localStorage.getItem('ims_current_user')
      if (user) {
        return JSON.parse(user)
      }
    } catch (e) {}
    return null
  }

  const currentUser = getCurrentUser()

  return (
    <header className="fixed top-0 left-0 right-0 z-40 bg-white dark:bg-gray-800 shadow-md">
      <div className="flex items-center justify-between px-4 py-3">
        <div className="flex items-center gap-4">
          <button
            onClick={toggleSidebar}
            className="lg:hidden p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
          >
            <Menu className="w-6 h-6 text-gray-700 dark:text-gray-200" />
          </button>
          <h1 className="text-xl md:text-2xl font-bold text-primary dark:text-blue-400">
            AI Voice Billing
          </h1>
        </div>

        <div className="flex items-center gap-3">
          {currentUser && (
            <span className="hidden sm:block text-sm text-gray-600 dark:text-gray-400">
              Welcome, <span className="font-semibold">{currentUser.username}</span>
            </span>
          )}
          
          <button
            onClick={toggleTheme}
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
          >
            {isDarkMode ? '🌙' : '☀️'}
          </button>
          
          <button className="relative p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700">
            <Bell className="w-5 h-5 text-gray-700 dark:text-gray-200" />
            <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
          </button>

          <button 
            onClick={handleLogout}
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
            title="Logout"
          >
            <LogOut className="w-5 h-5 text-gray-700 dark:text-gray-200" />
          </button>
        </div>
      </div>
    </header>
  )
}

export default Header
