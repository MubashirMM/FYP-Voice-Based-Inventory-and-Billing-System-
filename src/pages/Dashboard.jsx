import React from 'react'
import { Link } from 'react-router-dom'
import { TrendingUp, Package, AlertTriangle, Mic, Book, BarChart } from 'lucide-react'

function Dashboard() {
  const stats = [
    { title: 'Today Sales', value: '₨ 45,230', change: '+12%', color: 'blue', icon: TrendingUp },
    { title: 'Total Items', value: '284', change: '+5', color: 'green', icon: Package },
    { title: 'Low Stock', value: '12', change: 'Alert', color: 'red', icon: AlertTriangle },
    { title: 'Udhar Amount', value: '₨ 23,500', change: '15 people', color: 'yellow', icon: Book },
  ]

  const topItems = [
    { name: 'Sugar (Cheeni)', sold: 45, unit: 'kg', revenue: '₨ 4,500' },
    { name: 'Rice (Chawal)', sold: 30, unit: 'kg', revenue: '₨ 6,000' },
    { name: 'Tea (Chai)', sold: 25, unit: 'packets', revenue: '₨ 3,750' },
    { name: 'Cooking Oil', sold: 20, unit: 'ltr', revenue: '₨ 8,000' },
    { name: 'Flour (Atta)', sold: 18, unit: 'kg', revenue: '₨ 1,800' },
  ]

  const lowStockItems = [
    { name: 'Sugar (Cheeni)', stock: 5, unit: 'kg', status: 'critical' },
    { name: 'Milk Powder', stock: 8, unit: 'packets', status: 'low' },
    { name: 'Soap', stock: 10, unit: 'pieces', status: 'low' },
  ]

  const shortcuts = [
    { name: 'Voice Billing', path: '/voice-billing', icon: Mic, color: 'bg-blue-500' },
    { name: 'Inventory', path: '/inventory', icon: Package, color: 'bg-green-500' },
    { name: 'Udhar Khata', path: '/udhar', icon: Book, color: 'bg-yellow-500' },
    { name: 'Reports', path: '/reports', icon: BarChart, color: 'bg-purple-500' },
  ]

  return (
    <div className="space-y-6">
      <h1 className="text-2xl md:text-3xl font-bold text-gray-800 dark:text-white">Dashboard</h1>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat) => (
          <div
            key={stat.title}
            className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6 hover:shadow-lg transition-shadow"
          >
            <div className="flex items-center justify-between mb-4">
              <div className={`p-3 rounded-lg bg-${stat.color}-100 dark:bg-${stat.color}-900`}>
                <stat.icon className={`w-6 h-6 text-${stat.color}-600 dark:text-${stat.color}-400`} />
              </div>
              <span className={`text-sm font-medium text-${stat.color}-600`}>{stat.change}</span>
            </div>
            <h3 className="text-gray-600 dark:text-gray-400 text-sm mb-1">{stat.title}</h3>
            <p className="text-2xl font-bold text-gray-800 dark:text-white">{stat.value}</p>
          </div>
        ))}
      </div>

      {/* Shortcuts */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6">
        <h2 className="text-xl font-semibold text-gray-800 dark:text-white mb-4">Quick Actions</h2>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {shortcuts.map((shortcut) => (
            <Link
              key={shortcut.path}
              to={shortcut.path}
              className="flex flex-col items-center p-4 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            >
              <div className={`${shortcut.color} p-4 rounded-full mb-3`}>
                <shortcut.icon className="w-6 h-6 text-white" />
              </div>
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300 text-center">
                {shortcut.name}
              </span>
            </Link>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Sold Items */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-800 dark:text-white mb-4">
            Top Selling Items
          </h2>
          <div className="space-y-3">
            {topItems.map((item, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg"
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-primary text-white rounded-full flex items-center justify-center font-bold">
                    {index + 1}
                  </div>
                  <div>
                    <p className="font-medium text-gray-800 dark:text-white">{item.name}</p>
                    <p className="text-sm text-gray-500">
                      {item.sold} {item.unit} sold
                    </p>
                  </div>
                </div>
                <span className="font-semibold text-green-600">{item.revenue}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Low Stock Alerts */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-800 dark:text-white mb-4 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-red-500" />
            Low Stock Alerts
          </h2>
          <div className="space-y-3">
            {lowStockItems.map((item, index) => (
              <div
                key={index}
                className={`p-4 rounded-lg border-l-4 ${
                  item.status === 'critical'
                    ? 'bg-red-50 border-red-500 dark:bg-red-900/20'
                    : 'bg-yellow-50 border-yellow-500 dark:bg-yellow-900/20'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-gray-800 dark:text-white">{item.name}</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Only {item.stock} {item.unit} left
                    </p>
                  </div>
                  <span
                    className={`text-xs font-semibold px-3 py-1 rounded-full ${
                      item.status === 'critical'
                        ? 'bg-red-200 text-red-800'
                        : 'bg-yellow-200 text-yellow-800'
                    }`}
                  >
                    {item.status.toUpperCase()}
                  </span>
                </div>
              </div>
            ))}
            <Link
              to="/inventory"
              className="block text-center py-2 text-blue-600 hover:text-blue-700 font-medium"
            >
              View All Inventory →
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Dashboard
