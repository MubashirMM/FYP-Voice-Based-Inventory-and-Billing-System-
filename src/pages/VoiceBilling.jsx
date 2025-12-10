import React, { useState } from 'react'
import { Mic, MicOff, Plus, Trash2, ShoppingCart } from 'lucide-react'

function VoiceBilling() {
  const [isListening, setIsListening] = useState(false)
  const [transcript, setTranscript] = useState('')
  const [parsedItem, setParsedItem] = useState(null)
  const [billItems, setBillItems] = useState([])
  const [manualName, setManualName] = useState('')
  const [manualQty, setManualQty] = useState(1)
  const [manualPrice, setManualPrice] = useState(0)

  const mockVoiceCommands = [
    '2 kilo cheeni',
    '5 packet chai',
    '1 liter oil',
    '3 kilo atta',
  ]

  const handleVoiceInput = () => {
    if (!isListening) {
      setIsListening(true)
      // Simulate voice recognition with random command
      setTimeout(() => {
        const randomCommand = mockVoiceCommands[Math.floor(Math.random() * mockVoiceCommands.length)]
        setTranscript(randomCommand)
        parseCommand(randomCommand)
        setIsListening(false)
      }, 2000)
    }
  }

  const parseCommand = (command) => {
    // Simple parsing logic for demo
    const match = command.match(/(\d+)\s*(kilo|kg|packet|liter|litre|piece)\s*(.+)/)
    if (match) {
      const quantity = match[1]
      const unit = match[2]
      const itemName = match[3]
      
      const priceMap = {
        'cheeni': 100,
        'chai': 150,
        'oil': 400,
        'atta': 100,
        'sugar': 100,
        'tea': 150,
        'milk': 120,
      }

      const price = priceMap[itemName.toLowerCase()] || 50

      setParsedItem({
        name: itemName.charAt(0).toUpperCase() + itemName.slice(1),
        quantity: quantity,
        unit: unit,
        price: price,
        total: quantity * price
      })
    }
  }

  const addToBill = () => {
    if (parsedItem) {
      const item = { ...parsedItem, id: Date.now() }
      setBillItems([...billItems, item])
      setParsedItem(null)
      setTranscript('')
    }
  }

  const addManualItem = (e) => {
    e.preventDefault()
    const item = {
      id: Date.now(),
      name: manualName || 'Item',
      quantity: manualQty,
      unit: '',
      price: Number(manualPrice) || 0,
      total: (Number(manualQty) || 0) * (Number(manualPrice) || 0),
    }
    setBillItems([...billItems, item])
    setManualName('')
    setManualQty(1)
    setManualPrice(0)
  }

  const removeFromBill = (id) => {
    setBillItems(billItems.filter(item => item.id !== id))
  }

  const calculateTotal = () => {
    return billItems.reduce((sum, item) => sum + item.total, 0)
  }

  const generateBill = () => {
    if (billItems.length === 0) {
      alert('No items in bill!')
      return
    }
    alert(`Bill Generated!\nTotal: ₨ ${calculateTotal()}\n\nThis would print or save in production.`)
    setBillItems([])
  }

  // persist bill items
  React.useEffect(() => {
    try {
      const raw = localStorage.getItem('ims_bill')
      if (raw) setBillItems(JSON.parse(raw))
    } catch (e) {}
  }, [])

  React.useEffect(() => {
    try { localStorage.setItem('ims_bill', JSON.stringify(billItems)) } catch (e) {}
  }, [billItems])

  return (
    <div className="space-y-6">
      <h1 className="text-2xl md:text-3xl font-bold text-gray-800 dark:text-white">Voice Billing</h1>

      {/* Voice Input Section */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-8">
        <div className="flex flex-col items-center">
          <button
            onClick={handleVoiceInput}
            disabled={isListening}
            className={`mb-6 w-32 h-32 rounded-full flex items-center justify-center transition-all ${
              isListening
                ? 'bg-red-500 animate-pulse'
                : 'bg-blue-500 hover:bg-blue-600'
            } shadow-lg`}
          >
            {isListening ? (
              <MicOff className="w-16 h-16 text-white" />
            ) : (
              <Mic className="w-16 h-16 text-white" />
            )}
          </button>

          <p className="text-center text-gray-600 dark:text-gray-400 mb-4">
            {isListening ? 'Listening...' : 'Click microphone to speak'}
          </p>

          {/* Transcribed Text */}
          {transcript && (
            <div className="w-full max-w-2xl bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 mb-4">
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Transcribed:</p>
              <p className="text-lg font-medium text-gray-800 dark:text-white">{transcript}</p>
            </div>
          )}

          {/* Parsed Output */}
          {parsedItem && (
            <div className="w-full max-w-2xl bg-green-50 dark:bg-green-900/20 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-800 dark:text-white mb-4">Parsed Item:</h3>
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Item Name:</p>
                  <p className="text-lg font-semibold text-gray-800 dark:text-white">{parsedItem.name}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Quantity:</p>
                  <p className="text-lg font-semibold text-gray-800 dark:text-white">
                    {parsedItem.quantity} {parsedItem.unit}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Unit Price:</p>
                  <p className="text-lg font-semibold text-gray-800 dark:text-white">₨ {parsedItem.price}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Total:</p>
                  <p className="text-lg font-semibold text-green-600">₨ {parsedItem.total}</p>
                </div>
              </div>
              <button
                onClick={addToBill}
                className="w-full bg-green-600 text-white py-3 rounded-lg font-semibold hover:bg-green-700 transition-colors flex items-center justify-center gap-2"
              >
                <Plus className="w-5 h-5" />
                Add to Bill
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Current Bill */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6">
        <h2 className="text-xl font-semibold text-gray-800 dark:text-white mb-4 flex items-center gap-2">
          <ShoppingCart className="w-6 h-6" />
          Current Bill
        </h2>

        {billItems.length === 0 ? (
          <div className="text-center py-12 text-gray-500 dark:text-gray-400">
            <ShoppingCart className="w-16 h-16 mx-auto mb-4 opacity-50" />
            <p>No items added yet. Use voice command to add items.</p>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b dark:border-gray-700">
                    <th className="text-left py-3 px-4 text-gray-700 dark:text-gray-300 font-semibold">Item</th>
                    <th className="text-left py-3 px-4 text-gray-700 dark:text-gray-300 font-semibold">Qty</th>
                    <th className="text-left py-3 px-4 text-gray-700 dark:text-gray-300 font-semibold">Price</th>
                    <th className="text-left py-3 px-4 text-gray-700 dark:text-gray-300 font-semibold">Total</th>
                    <th className="text-left py-3 px-4 text-gray-700 dark:text-gray-300 font-semibold">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {billItems.map((item) => (
                    <tr key={item.id} className="border-b dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700">
                      <td className="py-3 px-4 text-gray-800 dark:text-white">{item.name}</td>
                      <td className="py-3 px-4 text-gray-800 dark:text-white">
                        {item.quantity} {item.unit}
                      </td>
                      <td className="py-3 px-4 text-gray-800 dark:text-white">₨ {item.price}</td>
                      <td className="py-3 px-4 text-gray-800 dark:text-white font-semibold">₨ {item.total}</td>
                      <td className="py-3 px-4">
                        <button
                          onClick={() => removeFromBill(item.id)}
                          className="text-red-600 hover:text-red-700"
                        >
                          <Trash2 className="w-5 h-5" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="mt-6 flex items-center justify-between border-t dark:border-gray-700 pt-4">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Total Items: {billItems.length}</p>
              </div>
              <div className="text-right">
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Grand Total:</p>
                <p className="text-3xl font-bold text-green-600">₨ {calculateTotal()}</p>
              </div>
            </div>

            <button
              onClick={generateBill}
              className="w-full mt-6 bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors"
            >
              Generate Bill
            </button>
          </>
        )}
      </div>
    </div>
  )
}

export default VoiceBilling
