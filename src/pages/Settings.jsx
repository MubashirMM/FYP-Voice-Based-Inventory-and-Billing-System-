import React, { useState } from 'react'
import { Settings as SettingsIcon, Mic, Globe, Moon, Sun, User, Users } from 'lucide-react'

function Settings({ toggleTheme, isDarkMode }) {
  const [language, setLanguage] = useState('english')
  const [voiceModel, setVoiceModel] = useState('standard')
  const [shopkeepers, setShopkeepers] = useState([
    { id: 1, name: 'Ahmed Ali', role: 'Owner', email: 'ahmed@shop.com', active: true },
    { id: 2, name: 'Fatima Khan', role: 'Manager', email: 'fatima@shop.com', active: true },
    { id: 3, name: 'Hassan Sheikh', role: 'Staff', email: 'hassan@shop.com', active: false },
  ])

  return (
    <div className="space-y-6">
      <h1 className="text-2xl md:text-3xl font-bold text-gray-800 dark:text-white">Settings</h1>

      {/* Theme Settings */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6">
        <div className="flex items-center gap-3 mb-4">
          {isDarkMode ? <Moon className="w-6 h-6 text-blue-600" /> : <Sun className="w-6 h-6 text-yellow-600" />}
          <h2 className="text-xl font-semibold text-gray-800 dark:text-white">Appearance</h2>
        </div>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Theme Mode
            </label>
            <div className="flex gap-4">
              <button
                onClick={() => !isDarkMode && toggleTheme()}
                className={`flex-1 py-3 px-4 rounded-lg border-2 transition-colors ${
                  !isDarkMode
                    ? 'border-blue-600 bg-blue-50 dark:bg-blue-900/20'
                    : 'border-gray-300 dark:border-gray-600 hover:border-blue-400'
                }`}
              >
                <Sun className="w-6 h-6 mx-auto mb-2" />
                <p className="text-center font-medium">Light</p>
              </button>
              <button
                onClick={() => isDarkMode && toggleTheme()}
                className={`flex-1 py-3 px-4 rounded-lg border-2 transition-colors ${
                  isDarkMode
                    ? 'border-blue-600 bg-blue-50 dark:bg-blue-900/20'
                    : 'border-gray-300 dark:border-gray-600 hover:border-blue-400'
                }`}
              >
                <Moon className="w-6 h-6 mx-auto mb-2" />
                <p className="text-center font-medium">Dark</p>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Voice Model Settings */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6">
        <div className="flex items-center gap-3 mb-4">
          <Mic className="w-6 h-6 text-blue-600" />
          <h2 className="text-xl font-semibold text-gray-800 dark:text-white">Voice Recognition</h2>
        </div>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Voice Model
            </label>
            <select
              value={voiceModel}
              onChange={(e) => setVoiceModel(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
            >
              <option value="standard">Standard (Recommended)</option>
              <option value="advanced">Advanced (More Accurate)</option>
              <option value="fast">Fast (Quick Response)</option>
              <option value="multilingual">Multilingual (Urdu + English)</option>
            </select>
          </div>

          <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <div>
              <p className="font-medium text-gray-800 dark:text-white">Enable Voice Commands</p>
              <p className="text-sm text-gray-600 dark:text-gray-400">Allow voice input for billing</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" defaultChecked className="sr-only peer" />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-600 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
            </label>
          </div>

          <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <div>
              <p className="font-medium text-gray-800 dark:text-white">Auto-detect Language</p>
              <p className="text-sm text-gray-600 dark:text-gray-400">Automatically switch between Urdu and English</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" defaultChecked className="sr-only peer" />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-600 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
            </label>
          </div>
        </div>
      </div>

      {/* Language Settings */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6">
        <div className="flex items-center gap-3 mb-4">
          <Globe className="w-6 h-6 text-blue-600" />
          <h2 className="text-xl font-semibold text-gray-800 dark:text-white">Language</h2>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Display Language
          </label>
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
          >
            <option value="english">English</option>
            <option value="urdu">اردو (Urdu)</option>
            <option value="both">Both (Bilingual)</option>
          </select>
        </div>
      </div>

      {/* User Management */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <Users className="w-6 h-6 text-blue-600" />
            <h2 className="text-xl font-semibold text-gray-800 dark:text-white">User Management</h2>
          </div>
          <button className="bg-blue-600 text-white px-4 py-2 rounded-lg font-semibold hover:bg-blue-700 transition-colors text-sm">
            Add User
          </button>
        </div>

        <div className="space-y-3">
          {shopkeepers.map(shopkeeper => (
            <div
              key={shopkeeper.id}
              className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg"
            >
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center">
                  <User className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                </div>
                <div>
                  <p className="font-medium text-gray-800 dark:text-white">{shopkeeper.name}</p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">{shopkeeper.email}</p>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <span className="px-3 py-1 rounded-full text-xs font-semibold bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300">
                  {shopkeeper.role}
                </span>
                <span
                  className={`w-3 h-3 rounded-full ${
                    shopkeeper.active ? 'bg-green-500' : 'bg-gray-400'
                  }`}
                  title={shopkeeper.active ? 'Active' : 'Inactive'}
                ></span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* About Section */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6">
        <div className="flex items-center gap-3 mb-4">
          <SettingsIcon className="w-6 h-6 text-blue-600" />
          <h2 className="text-xl font-semibold text-gray-800 dark:text-white">About</h2>
        </div>
        <div className="space-y-2 text-gray-600 dark:text-gray-400">
          <p><strong className="text-gray-800 dark:text-white">Version:</strong> 1.0.0</p>
          <p><strong className="text-gray-800 dark:text-white">Built with:</strong> React + Tailwind CSS</p>
          <p><strong className="text-gray-800 dark:text-white">Purpose:</strong> AI Voice Billing & Inventory Management</p>
          <p className="mt-4 text-sm">
            This is a demo frontend application. Voice recognition and backend integration will be added in production.
          </p>
        </div>
      </div>
    </div>
  )
}

export default Settings
