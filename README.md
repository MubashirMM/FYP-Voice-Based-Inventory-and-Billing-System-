🛒 AI-Powered Grocery Shop Management System (Urdu Voice Enabled)
📌 Project Overview

Developed a full-stack AI-powered Grocery Shop Management System specifically designed for Urdu-speaking grocery store owners in Pakistan.

The system digitizes daily shop operations including:

Inventory/Stock Management
Billing & Invoice Generation
Udhaar (Customer Credit) Management
Sales Reporting & Forecasting
AI-based Urdu Voice Command Interaction

The application integrates speech recognition and natural language processing to allow shop owners to manage operations using Urdu voice commands.

🎯 Key Features
🔐 Authentication & User Management
Secure user signup and login
Password reset via email
JWT-based authentication
Email notifications for important actions
Session handling and protected APIs
📦 Stock Management
Add, update, delete, and search inventory items
Low stock alert system with automated email notifications
Unit conversion support (kg, grams, liters, custom units)
Real-time inventory tracking
💳 Udhaar (Credit) Management
Customer udhaar account handling
Payment history tracking
Persistent udhaar records
Credit summary and balance calculation
🧾 Billing System
Dynamic bill generation
Printable/downloadable invoices
Immutable billing history records
Automated stock deduction after billing
📊 Reports & Forecasting
Sales analytics and reporting
Historical business analysis
Business forecasting insights
Performance trend tracking
🎤 AI-Powered Urdu Voice Assistant

Integrated an Urdu voice-command system enabling users to operate the application hands-free.

AI Pipeline
🎙️ Speech-to-Text

Used:

Whisper Turbo
Experimented with Whisper Small fine-tuning for Urdu speech improvement
🧠 Natural Language Processing

Used:

LLaMA-based LLM for command understanding and entity extraction
🎯 Supported Voice Operations

Voice interaction integrated with:

Stock Management
Billing System
Udhaar Item Management
Udhaar Handling

The system converts Urdu speech into structured actionable commands for backend execution.

🏗️ Software Architecture

Implemented using a Layered Monolithic Architecture for maintainability and scalability.

Backend Architecture (FastAPI)

Structured into:

Models Layer
Schemas Layer
CRUD Layer
API/Router Layer
Services Layer
Utility Layer
Utility Components
Voice processing utilities
Unit conversion utilities
Email services
Query optimization helpers
Frontend

Built using:

React.js
Tailwind CSS

Features:

Responsive UI
Urdu-friendly navigation
Minimal and easy-to-use interface
🗄️ Database Design

Used PostgreSQL with normalized relational schema including:

Users
Stock
Bills
Udhaar Records
Transactions
Bill History
☁️ Deployment & Infrastructure

Deployed on AWS cloud infrastructure for scalable production-ready hosting.

Implemented:

CI/CD pipeline support
Dockerized deployment approach
Logging and monitoring integration
🧪 Testing & Quality Assurance

Implemented comprehensive functional and non-functional testing strategies.

✅ Functional Testing
🔹 Unit Testing

Tools Used:

Pytest

Tested:

CRUD operations
Business logic
Utility functions
Validation logic
🔹 API & Integration Testing

Tools Used:

FastAPI TestClient
Pytest

Validated:

API endpoints
Authentication flows
Database integration
Error handling
🔹 System Testing

Tools Used:

Playwright

Automated end-to-end testing for:

User workflows
Billing process
Stock operations
Authentication flow
Voice-triggered operations
🔹 User Acceptance Testing (UAT)

Performed manual usability testing with non-technical users.

Results:

Users were able to navigate the system with minimal guidance
Easy workflow understanding
Improved usability for Urdu-speaking shopkeepers
🔐 Non-Functional Testing
🛡️ Security Testing

Tools Used:

OWASP ZAP
Gitleaks

Security checks included:

Credential leakage scanning
API vulnerability assessment
OWASP security validation
Authentication and authorization testing
⚡ Performance Testing

Tools Used:

Locust
Concurrent User Testing

Tested with:

20 concurrent users
100 concurrent users
🚀 Performance Optimizations
🔹 Authentication API Optimization
Before Optimization
Registration/Login Response Time:
60–68 seconds under load
Optimizations Applied
Query optimization
Reduced unnecessary database queries
LRU caching implementation
Improved session handling
Better indexing strategies
After Optimization
Registration API:
~1–2 seconds
Login API:
~500–700 ms
🔹 Stock CRUD Performance Optimization
Before Optimization
High latency under concurrent load
Improvements
Query optimization
Efficient database access patterns
Reduced redundant commits
Optimized CRUD execution flow
Final Performance
Most stock operations completed within milliseconds to ~1 second under load
📈 Scalability & Reliability

The system was tested for:

Concurrent user handling
API stability
Response consistency
Database reliability

Performance remained stable during multi-user load simulations.

🌐 Compatibility & Usability

Compatible with:

Google Chrome
Microsoft Edge
Firefox
Modern Chromium browsers

Designed with:

Responsive layouts
Minimal learning curve
Urdu-first accessibility approach
🚀 Tech Stack
Frontend
React.js
Tailwind CSS
Backend
FastAPI
Python
AI Integration
Whisper Turbo
LLaMA-based LLM
Database
PostgreSQL
Testing
Pytest
FastAPI TestClient
Playwright
Locust
OWASP ZAP
Gitleaks
Deployment
AWS
📂 Core Modules
Authentication Module
Inventory Management Module
Billing System
Udhaar Management
Reporting & Forecasting
Urdu Voice Command System
📈 Future Enhancements
Multi-user role management (Cashier/Admin/Manager)
Mobile application support
Advanced analytics dashboard
Offline-first functionality
Real-time voice assistant improvements
Fine-tuned Urdu speech models
📜 Conclusion

This project demonstrates the integration of modern full-stack development, AI-powered voice interaction, cloud deployment, security testing, and performance optimization into a real-world business solution tailored for local Pakistani markets.

The system successfully improves operational efficiency for small grocery stores through automation, Urdu voice accessibility, and scalable architecture.
