import React, { useState } from 'react'
import { Search, Plus, Edit, Trash2, Filter } from 'lucide-react'

function Inventory() {
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('all')
  const [showAddModal, setShowAddModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [editingItem, setEditingItem] = useState(null)
  const [items, setItems] = useState([
    { id: 1, name: 'Sugar (Cheeni)', category: 'Groceries', stock: 45, unit: 'kg', price: 100 },
    { id: 2, name: 'Rice (Chawal)', category: 'Groceries', stock: 80, unit: 'kg', price: 200 },
    { id: 3, name: 'Tea (Chai)', category: 'Beverages', stock: 35, unit: 'packets', price: 150 },
    { id: 4, name: 'Cooking Oil', category: 'Groceries', stock: 25, unit: 'liter', price: 400 },
    { id: 5, name: 'Flour (Atta)', category: 'Groceries', stock: 60, unit: 'kg', price: 100 },
    { id: 6, name: 'Milk Powder', category: 'Dairy', stock: 8, unit: 'packets', price: 850 },
    { id: 7, name: 'Soap', category: 'Personal Care', stock: 40, unit: 'pieces', price: 80 },
    { id: 8, name: 'Shampoo', category: 'Personal Care', stock: 22, unit: 'bottles', price: 250 },
    { id: 9, name: 'Biscuits', category: 'Snacks', stock: 50, unit: 'packets', price: 60 },
    { id: 10, name: 'Salt (Namak)', category: 'Groceries', stock: 30, unit: 'kg', price: 40 },
  ])

  const categories = ['all', 'Groceries', 'Beverages', 'Dairy', 'Personal Care', 'Snacks']

  // New item form state
  const [newName, setNewName] = useState('')
  const [newCategory, setNewCategory] = useState('Groceries')
  const [newStock, setNewStock] = useState(0)
  const [newUnit, setNewUnit] = useState('kg')
  const [newPrice, setNewPrice] = useState(0)

  const filteredItems = items.filter(item => {
    const matchesSearch = item.name.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesCategory = selectedCategory === 'all' || item.category === selectedCategory
    return matchesSearch && matchesCategory
  })

  const handleDelete = (id) => {
    if (window.confirm('Are you sure you want to delete this item?')) {
      setItems(items.filter(item => item.id !== id))
    }
  }

  const getStockStatus = (stock) => {
    if (stock < 10) return { text: 'Critical', color: 'text-red-600 bg-red-100' }
    if (stock < 20) return { text: 'Low', color: 'text-yellow-600 bg-yellow-100' }
    return { text: 'Good', color: 'text-green-600 bg-green-100' }
  }

  // load items from localStorage
  React.useEffect(() => {
    try {
      const raw = localStorage.getItem('ims_items')
      if (raw) setItems(JSON.parse(raw))
    } catch (e) {
      // ignore
    }
  }, [])

  // persist items
  React.useEffect(() => {
    try {
      localStorage.setItem('ims_items', JSON.stringify(items))
    } catch (e) {}
  }, [items])

  const handleAddItem = (e) => {
    e.preventDefault()
    const item = {
      id: Date.now(),
      name: newName || 'Unnamed Item',
      category: newCategory,
      stock: Number(newStock) || 0,
      unit: newUnit || 'pcs',
      price: Number(newPrice) || 0,
    }
    setItems([item, ...items])
    setShowAddModal(false)
    // reset form
    setNewName('')
    setNewCategory('Groceries')
    setNewStock(0)
    setNewUnit('kg')
    setNewPrice(0)
  }

  const handleEditClick = (item) => {
    setEditingItem(item)
    setNewName(item.name)
    setNewCategory(item.category)
    setNewStock(item.stock)
    setNewUnit(item.unit)
    setNewPrice(item.price)
    setShowEditModal(true)
  }

  const handleEditItem = (e) => {
    e.preventDefault()
    const updatedItems = items.map(item => 
      item.id === editingItem.id 
        ? {
            ...item,
            name: newName || 'Unnamed Item',
            category: newCategory,
            stock: Number(newStock) || 0,
            unit: newUnit || 'pcs',
            price: Number(newPrice) || 0,
          }
        : item
    )
    setItems(updatedItems)
    setShowEditModal(false)
    setEditingItem(null)
    // reset form
    setNewName('')
    setNewCategory('Groceries')
    setNewStock(0)
    setNewUnit('kg')
    setNewPrice(0)
  }

  return (
    <div className="space-y-6">
      {/* Sticky Header with Title and Add Button */}
      <div className="sticky top-16 z-20 bg-gray-50 dark:bg-gray-900 py-4 -mx-4 px-4 md:-mx-6 md:px-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <h1 className="text-2xl md:text-3xl font-bold text-gray-800 dark:text-white">Inventory</h1>
          <button
            onClick={() => setShowAddModal(true)}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg font-semibold hover:bg-blue-700 transition-colors flex items-center gap-2 justify-center shadow-lg"
          >
            <Plus className="w-5 h-5" />
            Add New Item
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-4">
        <div className="flex flex-col md:flex-row gap-4">
          {/* Search */}
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input
              type="text"
              placeholder="Search items..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
            />
          </div>

          {/* Category Filter */}
          <div className="relative">
            <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="pl-10 pr-8 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white appearance-none cursor-pointer"
            >
              {categories.map(cat => (
                <option key={cat} value={cat}>
                  {cat === 'all' ? 'All Categories' : cat}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Inventory Table */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-700">
              <tr>
                <th className="text-left py-4 px-6 text-gray-700 dark:text-gray-300 font-semibold">#</th>
                <th className="text-left py-4 px-6 text-gray-700 dark:text-gray-300 font-semibold">Item Name</th>
                <th className="text-left py-4 px-6 text-gray-700 dark:text-gray-300 font-semibold">Category</th>
                <th className="text-left py-4 px-6 text-gray-700 dark:text-gray-300 font-semibold">Stock</th>
                <th className="text-left py-4 px-6 text-gray-700 dark:text-gray-300 font-semibold">Price</th>
                <th className="text-left py-4 px-6 text-gray-700 dark:text-gray-300 font-semibold">Status</th>
                <th className="text-left py-4 px-6 text-gray-700 dark:text-gray-300 font-semibold">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredItems.length === 0 ? (
                <tr>
                  <td colSpan="7" className="text-center py-12 text-gray-500 dark:text-gray-400">
                    No items found
                  </td>
                </tr>
              ) : (
                filteredItems.map((item, index) => {
                  const status = getStockStatus(item.stock)
                  return (
                    <tr key={item.id} className="border-t dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700">
                      <td className="py-4 px-6 text-gray-800 dark:text-white">{index + 1}</td>
                      <td className="py-4 px-6 text-gray-800 dark:text-white font-medium">{item.name}</td>
                      <td className="py-4 px-6 text-gray-600 dark:text-gray-400">{item.category}</td>
                      <td className="py-4 px-6 text-gray-800 dark:text-white">
                        {item.stock} {item.unit}
                      </td>
                      <td className="py-4 px-6 text-gray-800 dark:text-white">₨ {item.price}</td>
                      <td className="py-4 px-6">
                        <span className={`px-3 py-1 rounded-full text-xs font-semibold ${status.color}`}>
                          {status.text}
                        </span>
                      </td>
                      <td className="py-4 px-6">
                        <div className="flex items-center gap-2">
                          <button 
                            onClick={() => handleEditClick(item)}
                            className="text-blue-600 hover:text-blue-700 p-2 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition-colors"
                          >
                            <Edit className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => handleDelete(item.id)}
                            className="text-red-600 hover:text-red-700 p-2 hover:bg-red-50 rounded-lg transition-colors"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  )
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add Item Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl max-w-md w-full p-6">
            <h2 className="text-2xl font-bold text-gray-800 dark:text-white mb-4">Add New Item</h2>
            <form className="space-y-4" onSubmit={handleAddItem}>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Item Name
                </label>
                <input
                  type="text"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  placeholder="e.g., Sugar"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Category
                </label>
                <select value={newCategory} onChange={(e) => setNewCategory(e.target.value)} className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white">
                  {categories.filter(c => c !== 'all').map(cat => (
                    <option key={cat} value={cat}>{cat}</option>
                  ))}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Stock
                  </label>
                  <input
                    type="number"
                    value={newStock}
                    onChange={(e) => setNewStock(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                    placeholder="0"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Unit
                  </label>
                  <input
                    type="text"
                    value={newUnit}
                    onChange={(e) => setNewUnit(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                    placeholder="kg/ltr/pcs"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Unit Price (₨)
                </label>
                <input
                  type="number"
                  value={newPrice}
                  onChange={(e) => setNewPrice(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  placeholder="0"
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
                  // onSubmit={}
                  
                >
                  Add Item
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Item Modal */}
      {showEditModal && editingItem && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl max-w-md w-full p-6">
            <h2 className="text-2xl font-bold text-gray-800 dark:text-white mb-4">Edit Item</h2>
            <form className="space-y-4" onSubmit={handleEditItem}>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Item Name
                </label>
                <input
                  type="text"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  placeholder="e.g., Sugar"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Category
                </label>
                <select value={newCategory} onChange={(e) => setNewCategory(e.target.value)} className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white">
                  {categories.filter(c => c !== 'all').map(cat => (
                    <option key={cat} value={cat}>{cat}</option>
                  ))}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Stock
                  </label>
                  <input
                    type="number"
                    value={newStock}
                    onChange={(e) => setNewStock(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                    placeholder="0"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Unit
                  </label>
                  <input
                    type="text"
                    value={newUnit}
                    onChange={(e) => setNewUnit(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                    placeholder="kg/ltr/pcs"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Unit Price (₨)
                </label>
                <input
                  type="number"
                  value={newPrice}
                  onChange={(e) => setNewPrice(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  placeholder="0"
                />
              </div>
              <div className="flex gap-4 pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setShowEditModal(false)
                    setEditingItem(null)
                    setNewName('')
                    setNewCategory('Groceries')
                    setNewStock(0)
                    setNewUnit('kg')
                    setNewPrice(0)
                  }}
                  className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
                >
                  Update Item
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Floating Action Button (visible on mobile/when scrolled) */}
      <button
        onClick={() => setShowAddModal(true)}
        className="fixed bottom-6 right-6 bg-blue-600 text-white p-4 rounded-full shadow-2xl hover:bg-blue-700 transition-all hover:scale-110 z-30 lg:hidden"
        title="Add New Item"
      >
        <Plus className="w-6 h-6" />
      </button>
    </div>
  )
}

export default Inventory
