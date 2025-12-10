import React, { useState } from 'react'
import { Plus, Filter, Clock, CheckCircle, XCircle } from 'lucide-react'

function UdharKhata() {
  const [filter, setFilter] = useState('all')
  const [showAddModal, setShowAddModal] = useState(false)
  const [customers, setCustomers] = useState([
    { id: 1, name: 'Ahmed Ali', amount: 5000, dueDate: '2025-10-25', paid: false },
    { id: 2, name: 'Fatima Khan', amount: 3200, dueDate: '2025-10-22', paid: false },
    { id: 3, name: 'Hassan Sheikh', amount: 7500, dueDate: '2025-10-30', paid: false },
    { id: 4, name: 'Ayesha Malik', amount: 2000, dueDate: '2025-10-20', paid: true },
    { id: 5, name: 'Bilal Ahmad', amount: 4800, dueDate: '2025-10-28', paid: false },
    { id: 6, name: 'Zainab Hussain', amount: 1500, dueDate: '2025-10-19', paid: true },
    { id: 7, name: 'Imran Raza', amount: 6200, dueDate: '2025-11-05', paid: false },
    { id: 8, name: 'Sana Iqbal', amount: 3900, dueDate: '2025-10-24', paid: false },
  ])

  // Add form state
  const [newCustomerName, setNewCustomerName] = React.useState('')
  const [newAmount, setNewAmount] = React.useState(0)
  const [newDueDate, setNewDueDate] = React.useState('')

  const filteredCustomers = customers.filter(customer => {
    if (filter === 'all') return true
    if (filter === 'paid') return customer.paid
    if (filter === 'unpaid') return !customer.paid
    return true
  })

  React.useEffect(() => {
    try {
      const raw = localStorage.getItem('ims_udhar')
      if (raw) setCustomers(JSON.parse(raw))
    } catch (e) {}
  }, [])

  React.useEffect(() => {
    try { localStorage.setItem('ims_udhar', JSON.stringify(customers)) } catch (e) {}
  }, [customers])

  const handleAddEntry = (e) => {
    e.preventDefault()
    const entry = {
      id: Date.now(),
      name: newCustomerName || 'Unnamed',
      amount: Number(newAmount) || 0,
      dueDate: newDueDate || new Date().toISOString().slice(0,10),
      paid: false,
    }
    setCustomers([entry, ...customers])
    setShowAddModal(false)
    setNewCustomerName('')
    setNewAmount(0)
    setNewDueDate('')
  }

  const totalUnpaid = customers
    .filter(c => !c.paid)
    .reduce((sum, c) => sum + c.amount, 0)

  const totalPaid = customers
    .filter(c => c.paid)
    .reduce((sum, c) => sum + c.amount, 0)

  const togglePaidStatus = (id) => {
    setCustomers(customers.map(customer => 
      customer.id === id ? { ...customer, paid: !customer.paid } : customer
    ))
  }

  const isOverdue = (dueDate) => {
    return new Date(dueDate) < new Date()
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <h1 className="text-2xl md:text-3xl font-bold text-gray-800 dark:text-white">Udhar Khata</h1>
        <button
          onClick={() => setShowAddModal(true)}
          className="bg-blue-600 text-white px-6 py-2 rounded-lg font-semibold hover:bg-blue-700 transition-colors flex items-center gap-2 justify-center"
        >
          <Plus className="w-5 h-5" />
          Add New Entry
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-3 bg-red-100 dark:bg-red-900 rounded-lg">
              <XCircle className="w-6 h-6 text-red-600 dark:text-red-400" />
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Total Unpaid</p>
              <p className="text-2xl font-bold text-red-600">₨ {totalUnpaid.toLocaleString()}</p>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-3 bg-green-100 dark:bg-green-900 rounded-lg">
              <CheckCircle className="w-6 h-6 text-green-600 dark:text-green-400" />
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Total Paid</p>
              <p className="text-2xl font-bold text-green-600">₨ {totalPaid.toLocaleString()}</p>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-3 bg-blue-100 dark:bg-blue-900 rounded-lg">
              <Clock className="w-6 h-6 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Total Customers</p>
              <p className="text-2xl font-bold text-gray-800 dark:text-white">{customers.length}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Filter Buttons */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-4">
        <div className="flex items-center gap-2">
          <Filter className="w-5 h-5 text-gray-600 dark:text-gray-400" />
          <span className="text-gray-700 dark:text-gray-300 font-medium mr-2">Filter:</span>
          <div className="flex gap-2 flex-wrap">
            {['all', 'unpaid', 'paid'].map(f => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  filter === f
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                }`}
              >
                {f.charAt(0).toUpperCase() + f.slice(1)}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Customers List */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filteredCustomers.length === 0 ? (
          <div className="col-span-2 bg-white dark:bg-gray-800 rounded-xl shadow-md p-12 text-center">
            <p className="text-gray-500 dark:text-gray-400">No customers found</p>
          </div>
        ) : (
          filteredCustomers.map(customer => {
            const overdue = isOverdue(customer.dueDate) && !customer.paid
            return (
              <div
                key={customer.id}
                className={`bg-white dark:bg-gray-800 rounded-xl shadow-md p-6 border-l-4 ${
                  customer.paid
                    ? 'border-green-500'
                    : overdue
                    ? 'border-red-500'
                    : 'border-yellow-500'
                }`}
              >
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-800 dark:text-white mb-1">
                      {customer.name}
                    </h3>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">
                      ₨ {customer.amount.toLocaleString()}
                    </p>
                  </div>
                  <button
                    onClick={() => togglePaidStatus(customer.id)}
                    className={`p-2 rounded-full ${
                      customer.paid
                        ? 'bg-green-100 text-green-600'
                        : 'bg-gray-100 text-gray-400 hover:bg-green-100 hover:text-green-600'
                    } transition-colors`}
                  >
                    <CheckCircle className="w-6 h-6" />
                  </button>
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                    <Clock className="w-4 h-4" />
                    <span>Due: {new Date(customer.dueDate).toLocaleDateString()}</span>
                  </div>
                  <span
                    className={`text-xs font-semibold px-3 py-1 rounded-full ${
                      customer.paid
                        ? 'bg-green-100 text-green-800'
                        : overdue
                        ? 'bg-red-100 text-red-800'
                        : 'bg-yellow-100 text-yellow-800'
                    }`}
                  >
                    {customer.paid ? 'PAID' : overdue ? 'OVERDUE' : 'PENDING'}
                  </span>
                </div>
              </div>
            )
          })
        )}
      </div>

      {/* Add Entry Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl max-w-md w-full p-6">
            <h2 className="text-2xl font-bold text-gray-800 dark:text-white mb-4">Add New Udhar Entry</h2>
            <form className="space-y-4" onSubmit={handleAddEntry}>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Customer Name
                </label>
                <input
                  type="text"
                  value={newCustomerName}
                  onChange={(e) => setNewCustomerName(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  placeholder="e.g., Ahmed Ali"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Amount (₨)
                </label>
                <input
                  type="number"
                  value={newAmount}
                  onChange={(e) => setNewAmount(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  placeholder="0"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Due Date
                </label>
                <input
                  type="date"
                  value={newDueDate}
                  onChange={(e) => setNewDueDate(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                />
              </div>
              <div className="flex gap-4 pt-4">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Add Entry
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default UdharKhata
