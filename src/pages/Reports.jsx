import React, { useState } from 'react'
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { Calendar, TrendingUp } from 'lucide-react'

function Reports() {
  const [dateRange, setDateRange] = useState('week')
  const [category, setCategory] = useState('all')

  // Mock data for charts
  const salesTrendData = [
    { date: 'Mon', sales: 12000 },
    { date: 'Tue', sales: 19000 },
    { date: 'Wed', sales: 15000 },
    { date: 'Thu', sales: 22000 },
    { date: 'Fri', sales: 28000 },
    { date: 'Sat', sales: 35000 },
    { date: 'Sun', sales: 30000 },
  ]

  const itemFrequencyData = [
    { item: 'Sugar', count: 45 },
    { item: 'Rice', count: 38 },
    { item: 'Tea', count: 35 },
    { item: 'Oil', count: 28 },
    { item: 'Flour', count: 25 },
    { item: 'Milk', count: 20 },
  ]

  const salesSummary = [
    { product: 'Sugar (Cheeni)', quantity: '45 kg', totalSale: 4500, profit: 900 },
    { product: 'Rice (Chawal)', quantity: '38 kg', totalSale: 7600, profit: 1520 },
    { product: 'Tea (Chai)', quantity: '35 packets', totalSale: 5250, profit: 1050 },
    { product: 'Cooking Oil', quantity: '28 ltr', totalSale: 11200, profit: 2240 },
    { product: 'Flour (Atta)', quantity: '25 kg', totalSale: 2500, profit: 500 },
    { product: 'Milk Powder', quantity: '20 packets', totalSale: 17000, profit: 3400 },
  ]

  return (
    <div className="space-y-6">
      <h1 className="text-2xl md:text-3xl font-bold text-gray-800 dark:text-white">Reports & Analytics</h1>

      {/* Filters */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-4">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Date Range
            </label>
            <div className="relative">
              <Calendar className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <select
                value={dateRange}
                onChange={(e) => setDateRange(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
              >
                <option value="today">Today</option>
                <option value="week">This Week</option>
                <option value="month">This Month</option>
                <option value="year">This Year</option>
              </select>
            </div>
          </div>

          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Category
            </label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
            >
              <option value="all">All Categories</option>
              <option value="groceries">Groceries</option>
              <option value="beverages">Beverages</option>
              <option value="dairy">Dairy</option>
              <option value="personal-care">Personal Care</option>
            </select>
          </div>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl shadow-md p-6 text-white">
          <p className="text-sm opacity-90 mb-1">Total Revenue</p>
          <p className="text-3xl font-bold">₨ 48,050</p>
          <p className="text-sm mt-2 opacity-90">+15% from last week</p>
        </div>
        <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-xl shadow-md p-6 text-white">
          <p className="text-sm opacity-90 mb-1">Total Profit</p>
          <p className="text-3xl font-bold">₨ 9,610</p>
          <p className="text-sm mt-2 opacity-90">+12% from last week</p>
        </div>
        <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl shadow-md p-6 text-white">
          <p className="text-sm opacity-90 mb-1">Total Transactions</p>
          <p className="text-3xl font-bold">186</p>
          <p className="text-sm mt-2 opacity-90">+8% from last week</p>
        </div>
        <div className="bg-gradient-to-br from-orange-500 to-orange-600 rounded-xl shadow-md p-6 text-white">
          <p className="text-sm opacity-90 mb-1">Avg. Transaction</p>
          <p className="text-3xl font-bold">₨ 258</p>
          <p className="text-sm mt-2 opacity-90">+5% from last week</p>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Sales Trend Chart */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6">
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp className="w-5 h-5 text-blue-600" />
            <h2 className="text-xl font-semibold text-gray-800 dark:text-white">Daily Sales Trend</h2>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={salesTrendData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.1} />
              <XAxis dataKey="date" stroke="#6B7280" />
              <YAxis stroke="#6B7280" />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#1F2937', 
                  border: 'none', 
                  borderRadius: '8px',
                  color: '#fff'
                }} 
              />
              <Line type="monotone" dataKey="sales" stroke="#3B82F6" strokeWidth={3} dot={{ fill: '#3B82F6' }} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Item Frequency Chart */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-800 dark:text-white mb-4">Item Frequency</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={itemFrequencyData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.1} />
              <XAxis dataKey="item" stroke="#6B7280" />
              <YAxis stroke="#6B7280" />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#1F2937', 
                  border: 'none', 
                  borderRadius: '8px',
                  color: '#fff'
                }} 
              />
              <Bar dataKey="count" fill="#10B981" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Sales Summary Table */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md overflow-hidden">
        <div className="p-6 border-b dark:border-gray-700">
          <h2 className="text-xl font-semibold text-gray-800 dark:text-white">Sales Summary</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-700">
              <tr>
                <th className="text-left py-4 px-6 text-gray-700 dark:text-gray-300 font-semibold">#</th>
                <th className="text-left py-4 px-6 text-gray-700 dark:text-gray-300 font-semibold">Product</th>
                <th className="text-left py-4 px-6 text-gray-700 dark:text-gray-300 font-semibold">Quantity</th>
                <th className="text-left py-4 px-6 text-gray-700 dark:text-gray-300 font-semibold">Total Sale</th>
                <th className="text-left py-4 px-6 text-gray-700 dark:text-gray-300 font-semibold">Profit</th>
              </tr>
            </thead>
            <tbody>
              {salesSummary.map((item, index) => (
                <tr key={index} className="border-t dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700">
                  <td className="py-4 px-6 text-gray-800 dark:text-white">{index + 1}</td>
                  <td className="py-4 px-6 text-gray-800 dark:text-white font-medium">{item.product}</td>
                  <td className="py-4 px-6 text-gray-600 dark:text-gray-400">{item.quantity}</td>
                  <td className="py-4 px-6 text-gray-800 dark:text-white">₨ {item.totalSale.toLocaleString()}</td>
                  <td className="py-4 px-6 text-green-600 font-semibold">₨ {item.profit.toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
            <tfoot className="bg-gray-50 dark:bg-gray-700 font-bold">
              <tr>
                <td colSpan="3" className="py-4 px-6 text-gray-800 dark:text-white text-right">TOTAL:</td>
                <td className="py-4 px-6 text-gray-800 dark:text-white">
                  ₨ {salesSummary.reduce((sum, item) => sum + item.totalSale, 0).toLocaleString()}
                </td>
                <td className="py-4 px-6 text-green-600">
                  ₨ {salesSummary.reduce((sum, item) => sum + item.profit, 0).toLocaleString()}
                </td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>
    </div>
  )
}

export default Reports
