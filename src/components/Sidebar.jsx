import React from 'react'
import { NavLink } from 'react-router-dom'
import { LayoutDashboard, Mic, Package, Book, BarChart3, Settings, X } from 'lucide-react'

function Sidebar({ isOpen, toggleSidebar }) {
  const navItems = [
    { name: 'Dashboard', path: '/', icon: LayoutDashboard },
    { name: 'Voice Billing', path: '/voice-billing', icon: Mic },
    { name: 'Inventory', path: '/inventory', icon: Package },
    { name: 'Udhar Khata', path: '/udhar', icon: Book },
    { name: 'Reports', path: '/reports', icon: BarChart3 },
    { name: 'Settings', path: '/settings', icon: Settings },
  ]

  return (
    <>
      {/* Mobile Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={toggleSidebar}
        ></div>
      )}

      {/* Sidebar */}
      <aside
        className={`fixed left-0 top-0 h-full w-64 bg-white dark:bg-gray-800 shadow-lg transform transition-transform duration-300 z-50 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        } lg:translate-x-0 lg:mt-16`}
      >
        <div className="flex items-center justify-between p-4 lg:hidden">
          <h2 className="text-xl font-bold text-primary">Menu</h2>
          <button onClick={toggleSidebar}>
            <X className="w-6 h-6 text-gray-700 dark:text-gray-200" />
          </button>
        </div>

        <nav className="mt-4 lg:mt-0">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              onClick={() => window.innerWidth < 1024 && toggleSidebar()}
              className={({ isActive }) =>
                `flex items-center gap-3 px-6 py-3 text-gray-700 dark:text-gray-200 hover:bg-blue-50 dark:hover:bg-gray-700 transition-colors ${
                  isActive ? 'bg-blue-100 dark:bg-gray-700 border-r-4 border-primary' : ''
                }`
              }
            >
              <item.icon className="w-5 h-5" />
              <span className="font-medium">{item.name}</span>
            </NavLink>
          ))}
        </nav>
      </aside>
    </>
  )
}

export default Sidebar
