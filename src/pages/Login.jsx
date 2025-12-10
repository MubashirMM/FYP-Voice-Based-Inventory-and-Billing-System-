import React, { useState } from 'react'
import { Mic, LogIn, Eye, EyeOff } from 'lucide-react'

function Login({ onLogin, onRegisterClick }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    setError('')

    if (!username || !password) {
      setError('Please enter both username and password')
      return
    }

    // Get registered users
    let users = []
    try {
      const storedUsers = localStorage.getItem('ims_users')
      if (storedUsers) {
        users = JSON.parse(storedUsers)
      }
    } catch (e) {
      users = []
    }

    // Check credentials
    const user = users.find(u => u.username === username && u.password === password)
    
    if (user) {
      // Store current user
      localStorage.setItem('ims_current_user', JSON.stringify(user))
      onLogin()
    } else {
      setError('Invalid username or password')
    }
  }

  const handleVoiceLogin = () => {
    alert('Voice login simulation - This would use voice recognition in production')
    onLogin()
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">AI Voice Billing</h1>
          <p className="text-gray-600">Inventory Management System</p>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Username
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Enter username"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Password
            </label>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent pr-10"
                placeholder="Enter password"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700"
              >
                {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            className="w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors flex items-center justify-center gap-2"
          >
            <LogIn className="w-5 h-5" />
            Login
          </button>
        </form>

        <div className="mt-6">
          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-300"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-white text-gray-500">Or</span>
            </div>
          </div>

          <button
            onClick={handleVoiceLogin}
            className="mt-4 w-full bg-green-600 text-white py-3 rounded-lg font-semibold hover:bg-green-700 transition-colors flex items-center justify-center gap-2"
          >
            <Mic className="w-5 h-5" />
            Login with Voice
          </button>
        </div>

        <p className="mt-6 text-center text-sm text-gray-600">
          Don't have an account?{' '}
          <button
            onClick={onRegisterClick}
            className="text-blue-600 hover:text-blue-700 font-semibold"
          >
            Register here
          </button>
        </p>

        <p className="mt-4 text-center text-xs text-gray-500">
          Demo: Register first or use voice login
        </p>
      </div>
    </div>
  )
}

export default Login
