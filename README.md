# 🛒 Grocery Shop Management System (Urdu-Based Web Application)

## 📌 Overview
This project is a web-based Grocery Shop Management System designed specifically for Urdu-speaking users in the Pakistani market.

It enables small shop owners to digitally manage daily operations including:
- Stock management
- Billing
- Customer credit (Udhaar)

The system also includes AI-powered voice interaction, allowing users to operate the system using Urdu voice commands.

Built with a modern full-stack architecture:
- Frontend: React.js
- Backend: FastAPI
- AI Integration: Whisper Turbo + LLM

---

## 🎯 Key Features

### 🔐 Authentication & User Management
- User Signup & Login
- Password Reset via Email
- Email notifications on key actions

### 📦 Stock Management
- Add, update, delete stock items
- Track inventory levels
- Automated stock alert emails when inventory is low

### 💳 Udhaar (Credit) Management
- Manage customer credit accounts
- Track payment history
- Persistent Udhaar history records

### 🧾 Billing System
- Generate bills dynamically
- Download and print bills
- Maintain bill history (non-deletable records)

### 📊 Reports & Forecasting
- Sales reports generation
- Business insights and forecasting
- Historical data analysis

### 🎤 Voice Integration (AI-Powered)
- Urdu voice commands supported
- Speech-to-text using Whisper Turbo
- LLM-based command processing

Voice-enabled operations include:
- Stock management
- Billing
- Udhaar handling

---

## 🏗️ Architecture

This project follows a layered monolithic architecture for maintainability and scalability.

### Backend (FastAPI)
Structured into:
- Schemas – Data validation
- Models – Database structure
- CRUD Layer – Database operations
- API Layer – Route handling
- Services Layer – Business logic (e.g., email handling)
- Utilities – Helper functions (e.g., unit conversion, voice processing)

### Frontend
- Built with React.js
- Styled using Tailwind CSS
- Responsive and user-friendly UI for Urdu users

---

## 🧠 AI & Voice Processing
- Speech recognition using Whisper Turbo
- Natural language understanding using LLM
- Converts Urdu speech into actionable system commands

---

## 🔄 Unit Conversion Utility
- Supports predefined unit conversions (kg, grams, liters)
- Custom units can be added
- Conversion applies only to supported units

---

## 🗄️ Database
PostgreSQL is used for data storage with a structured relational schema including:
- Users
- Stock
- Bills
- Udhaar records

---

## ☁️ Deployment
- Deployed using AWS cloud services
- Designed for scalable, real-world usage

---

## 👤 Target User
- Single Admin User (Shop Owner)
- Designed for small grocery store management

---

## 🚀 Tech Stack

### Frontend
- React.js
- Tailwind CSS

### Backend
- FastAPI (Python)

### AI Integration
- Whisper Turbo (Speech-to-Text)
- LLM (Command Processing)

### Database
- MySQL

### Deployment
- AWS

---

## 📂 Core Modules
- Authentication Module
- Stock Management Module
- Udhaar Management Module
- Billing System
- Reporting & Forecasting
- Voice Command System

---

## 📈 Future Improvements
- Multi-user support (cashier, manager roles)
- Mobile application version
- Advanced analytics dashboard
- Offline support for low connectivity areas

---

## 📜 Conclusion
This project demonstrates a real-world, AI-integrated business solution tailored for local markets. It combines modern web development, cloud deployment, and AI capabilities to enhance usability and efficiency for small business owners.
