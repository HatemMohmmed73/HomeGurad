# HomeGuard: Per-Device Behavioral Firewall for Smart Homes

![HomeGuard Logo](https://via.placeholder.com/150x150?text=HomeGuard)

**A Final Year Project - Fall 2025**

Cybersecurity + AI + Web Development

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Installation](#installation)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Project Structure](#project-structure)
- [Team](#team)

---

## 🌟 Overview

HomeGuard is an **affordable, on-premises smart home security gateway** that runs on a Raspberry Pi. It uses **per-device behavioral modeling** with machine learning to detect anomalies in IoT device traffic and provides **explainable alerts** in plain language for non-technical users.

### Problem Statement

- Existing home gateways treat all devices uniformly
- Lack of per-device visibility and adaptive protection
- Non-technical users struggle with complex security alerts
- Compromised IoT devices can exploit allowed network channels

### Solution

HomeGuard provides:
- ✅ Real-time traffic monitoring with Zeek
- ✅ ML-based anomaly detection (Isolation Forest)
- ✅ Per-device behavioral profiling
- ✅ Automatic firewall blocking (nftables)
- ✅ User-friendly web dashboard with plain-language explanations

---

## 🚀 Features

### 1. **Device Monitoring**
- Real-time traffic analysis for all connected IoT devices
- Per-device statistics (bytes sent/received, packet counts)
- Connection status tracking (Active, Idle, Blocked, Offline)

### 2. **Behavioral Analysis**
- Machine learning-based anomaly detection
- Per-device behavioral scoring
- Isolation Forest algorithm for unsupervised learning

### 3. **Security Enforcement**
- Automatic device blocking on anomaly detection
- Manual block/unblock controls
- nftables integration for firewall rules

### 4. **Real-time Alerts**
- WebSocket-powered live notifications
- Severity-based alert classification (Critical, High, Medium, Low)
- Explainable alerts in plain language

### 5. **User Dashboard**
- Modern React-based interface
- Device overview with visual indicators
- Alert management and history
- System settings and configuration

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend (React)                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │Dashboard │  │ Devices  │  │  Alerts  │  │ Settings │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└────────────────────────┬────────────────────────────────────┘
                         │ REST API + WebSocket
┌────────────────────────▼────────────────────────────────────┐
│                    Backend (FastAPI)                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │   Auth   │  │ Devices  │  │  Alerts  │  │ ML Model │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│  ┌──────────┐  ┌──────────────────────────────────────┐   │
│  │ Firewall │  │     WebSocket Manager                 │   │
│  └──────────┘  └──────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                    Data Layer (MongoDB)                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Devices  │  │  Alerts  │  │  Users   │  │ Settings │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│              Network Layer (Raspberry Pi)                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐     │
│  │   Zeek   │  │ nftables │  │   IoT Devices        │     │
│  └──────────┘  └──────────┘  └──────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern, fast Python web framework
- **Python 3.11+** - Core programming language
- **Motor** - Async MongoDB driver
- **Scikit-learn** - Machine learning (Isolation Forest)
- **Pandas/NumPy** - Data processing
- **Zeek** - Network traffic analysis
- **nftables** - Linux firewall

### Frontend
- **React 18** - UI library
- **TypeScript** - Type-safe JavaScript
- **Tailwind CSS** - Utility-first CSS framework
- **Recharts** - Data visualization
- **Zustand** - State management
- **Socket.IO** - WebSocket client
- **Axios** - HTTP client
- **Vite** - Build tool

### Database
- **MongoDB** - NoSQL database for flexible schema

### DevOps
- **Docker & Docker Compose** - Containerization
- **Nginx** - Web server and reverse proxy

---

## 📦 Installation

### Prerequisites

- **Raspberry Pi 4** (4GB+ RAM recommended) or any Linux system
- **Docker & Docker Compose** installed
- **Git** installed

### Quick Start with Docker

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/homeguard.git
cd homeguard/dashboard
```

2. **Create environment file**
```bash
cp backend/.env.example backend/.env
# Edit backend/.env with your settings
```

3. **Build and run with Docker Compose**
```bash
docker-compose up -d
```

4. **Access the dashboard**
```
Frontend: http://localhost:3000
Backend API: http://localhost:8000
API Docs: http://localhost:8000/docs
```

5. **Default credentials**
```
Email: admin@homeguard.local
Password: admin123
```
Only this administrator account is available. All user registration features and the customer dashboard have been removed so the entire system runs with a single secure admin login.

### Manual Installation

#### Backend

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Run MongoDB (if not using Docker)
# Ensure MongoDB is running on localhost:27017

# Run the backend
python main.py
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build
```

---

## 🎯 Usage

### 1. **Register/Login**
- Navigate to `http://localhost:3000`
- Login with default credentials or create a new account

### 2. **Monitor Devices**
- View all connected IoT devices on the Dashboard
- Check device status, traffic, and behavioral scores
- Click on a device for detailed information

### 3. **Manage Alerts**
- View all security alerts in the Alerts page
- Filter by severity, date, or device
- Acknowledge alerts after review

### 4. **Configure Settings**
- Adjust anomaly detection threshold
- Enable/disable automatic blocking
- Configure notification preferences
- Retrain the ML model

### 5. **Block/Unblock Devices**
- Manually block suspicious devices
- Automatic blocking based on anomaly detection
- View blocked device list

---

## 📚 API Documentation

### Authentication

**POST** `/api/auth/login`
```json
{
  "email": "admin@homeguard.local",
  "password": "admin123"
}
```

**GET** `/api/auth/me`
- Requires: Bearer Token

### Devices

**GET** `/api/devices`
- Get all devices

**GET** `/api/devices/{device_id}`
- Get device details

**POST** `/api/devices/{device_id}/block`
- Block a device

**POST** `/api/devices/{device_id}/unblock`
- Unblock a device

### Alerts

**GET** `/api/alerts?severity={severity}&days={days}`
- Get alerts with filters

**PATCH** `/api/alerts/{alert_id}/acknowledge`
- Acknowledge an alert

**GET** `/api/alerts/stats/summary`
- Get alert statistics

### ML Model

**GET** `/api/model/status`
- Get model status and metrics

**POST** `/api/model/inference`
- Run anomaly detection

**POST** `/api/model/retrain`
- Trigger model retraining

### Settings

**GET** `/api/settings`
- Get system settings

**POST** `/api/settings`
- Update settings

For full API documentation, visit: `http://localhost:8000/docs`

---

## 📁 Project Structure

```
dashboard/
├── backend/
│   ├── api/
│   │   └── routes/
│   │       ├── auth.py
│   │       ├── devices.py
│   │       ├── alerts.py
│   │       ├── model.py
│   │       └── settings_api.py
│   ├── core/
│   │   ├── security.py
│   │   ├── websocket_manager.py
│   │   └── firewall.py
│   ├── database/
│   │   ├── mongodb.py
│   │   └── models.py
│   ├── ml/
│   │   └── anomaly_detector.py
│   ├── config.py
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Layout.tsx
│   │   │   ├── DeviceCard.tsx
│   │   │   └── StatsCard.tsx
│   │   ├── pages/
│   │   │   ├── Login.tsx
│   │   │   ├── Dashboard.tsx
│   │   │   ├── DeviceDetail.tsx
│   │   │   ├── Alerts.tsx
│   │   │   └── Settings.tsx
│   │   ├── services/
│   │   │   ├── api.ts
│   │   │   └── websocket.ts
│   │   ├── store/
│   │   │   └── authStore.ts
│   │   ├── types/
│   │   │   └── index.ts
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   ├── Dockerfile
│   └── nginx.conf
└── docker-compose.yml
```

---

## 👥 Team

**Students:**
- Hatem Mohammed Al-burtaman (s134189@student.squ.edu.om)
- Alazhar Mohammed Alabri (s134783@student.squ.edu.om)
- Ali Abdullah Alkamzari (s135215@student.squ.edu.om)
- Adnan Mohammed Alsiyabi (s133658@student.squ.edu.om)

**Supervisor:**
- Dr. Abdelhamid Abdessalem (ahamid@squ.edu.om)

**Institution:** Sultan Qaboos University

**Submission Date:** October 2, 2025

---

## 📝 License

This project is part of a Final Year Project at Sultan Qaboos University.

---

## 🙏 Acknowledgments

- Sultan Qaboos University for providing resources and guidance
- Dr. Abdelhamid Abdessalem for supervision and mentorship
- IoT-23 and Bot-IoT datasets for training data

---

## 📧 Contact

For questions or issues, please contact the team via email or create an issue on GitHub.

---

**HomeGuard** © 2025 - Securing Your Smart Home, One Device at a Time 🏠🔒

