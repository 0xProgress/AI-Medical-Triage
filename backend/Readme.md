# 🏥 AI Medical Triage System

An open-source, privacy-first medical triage system that uses conversational AI to assess symptoms, rank potential conditions, and generate downloadable health reports—without storing any user data on the server.

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green.svg)](https://fastapi.tiangolo.com/)
[![Qwen](https://img.shields.io/badge/Qwen-2.5-orange.svg)](https://huggingface.co/Qwen)

---

## 📖 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [API Documentation](#api-documentation)
- [Environment Variables](#environment-variables)
- [Database](#database)
- [Contributing](#contributing)
- [License](#license)

---

## 📋 Overview

**AI Medical Triage** addresses healthcare access gaps in low-resource regions by providing a free, accessible first line of medical guidance. The system:

- 🗣️ **Converses** with users about their symptoms
- 🧠 **Analyzes** symptoms using Qwen AI
- 📊 **Matches** against an evidence-based medical database (Symcat)
- ❓ **Asks** intelligent follow-up questions to narrow down conditions
- 📄 **Generates** downloadable PDF reports with clinical reasoning
- 🔒 **Stores zero user data** on the server (privacy-first)

> ⚠️ **DISCLAIMER:** This system is for **informational purposes only**. It is **NOT a substitute** for professional medical advice, diagnosis, or treatment. Always consult a licensed healthcare provider for medical concerns.

---

## ✨ Features

### Core Features
| Feature | Description |
|---------|-------------|
| **Multi-Turn Conversation** | Dynamic symptom assessment with intelligent follow-up questions |
| **Evidence-Based Matching** | 100+ diseases, 230+ symptoms from Symcat database |
| **Red Flag Detection** | AI-powered identification of urgent symptoms |
| **Privacy-First Design** | No data stored server-side; sessions auto-delete after 1 hour |
| **PDF Reports** | Downloadable reports with clinical reasoning and disclaimers |
| **Open-Source Transparency** | Full codebase and database available for audit |

### Technical Features
- 🚀 FastAPI backend with async support
- 🤖 Qwen AI integration via Hugging Face
- 📊 SQLite database with JSON export
- 🌙 Dark/Light theme support
- 📱 Fully responsive design (mobile-first)

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER (Browser)                             │
└─────────────────────────┬───────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    FRONTEND (React/Vite)                            │
│                    - UI for users                                  │
│                    - Sends requests to AI layer                    │
└─────────────────────────┬───────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    AI MIDDLEWARE (Triage Engine)                   │
│                    - Symptom extraction via Qwen                   │
│                    - Database query & disease ranking              │
│                    - Follow-up question generation                 │
│                    - Session management                            │
└─────────────────────────┬───────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    BACKEND (FastAPI + SQLite)                      │
│                    - REST API endpoints                            │
│                    - Symcat medical database (100 diseases)        │
│                    - PDF report generation                         │
│                    - Session cleanup (1-hour auto-delete)          │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | React, TypeScript, Vite, Tailwind CSS | UI, state management, API calls |
| **AI Model** | Qwen/Qwen2.5-7B-Instruct (via Hugging Face) | Symptom extraction, reasoning, follow-ups |
| **Backend** | FastAPI, Python 3.11+ | API endpoints, business logic, sessions |
| **Database** | SQLite (with JSON export) | 100 diseases, 230 symptoms, mappings |
| **Reports** | ReportLab | PDF report generation |
| **Hosting** | Vercel (frontend), Railway/Render (backend) | Free-tier deployment |

---

## 📁 Project Structure

```
AI-Medical-Triage/
│
├── README.md                 # This file
├── LICENSE                   # Apache 2.0 License
├── CONTRIBUTING.md           # Contribution guidelines
│
├── backend/                  # FastAPI backend (separate branch: backend)
│   ├── main.py               # Entry point
│   ├── config.py             # Configuration
│   ├── requirements.txt      # Python dependencies
│   ├── models/               # Pydantic schemas, Qwen client
│   ├── database/             # SQLite queries, build script
│   ├── ai/                   # Triage engine, reasoning
│   ├── routes/               # API endpoints (/chat, /report)
│   ├── services/             # Report generation
│   └── data/                 # symcat.db, symcat_simplified.json
│
├── frontend/                 # React frontend (separate branch: frontend)
│   ├── public/               # Static assets, favicons
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── lib/              # API client
│   │   ├── store/            # Zustand state management
│   │   └── types/            # TypeScript definitions
│   ├── package.json          # Dependencies
│   └── vite.config.ts        # Vite configuration
│
└── docs/                     # Documentation
    ├── ARCHITECTURE.md       # Technical deep-dive
    ├── API.md                # API reference
    ├── DEPLOYMENT.md         # Deployment guide
    └── DATA_SOURCES.md       # Data sources and licensing
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Hugging Face API token ([Get one here](https://huggingface.co/settings/tokens))

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/your-org/AI-Medical-Triage.git
cd AI-Medical-Triage
```

### 2️⃣ Backend Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
cd backend
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your Hugging Face API token

# Build the database
python -m database.build_db

# Start the server
PYTHONPATH=. python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 3️⃣ Frontend Setup

```bash
cd frontend
npm install

# Set up environment variables
echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1" > .env.local

# Start development server
npm run dev
```

### 4️⃣ Open in Browser

- Frontend: `http://localhost:5173` (or `http://localhost:3000`)
- Backend API: `http://localhost:8000/api/v1/health`
- API Docs: `http://localhost:8000/docs`

---

## 📡 API Documentation

### Chat Endpoint

**POST** `/api/v1/chat`

```json
{
  "session_id": null,
  "message": "I have a sore throat and fever",
  "conversation_history": []
}
```

**Response:**
```json
{
  "session_id": "uuid",
  "message": "Based on your symptoms...",
  "conditions": [...],
  "red_flags": [],
  "is_complete": false,
  "turn": 1
}
```

### Report Endpoint

**POST** `/api/v1/report`

```json
{
  "session_id": "uuid"
}
```

**Response:**
```json
{
  "report_url": "/downloads/report_xxx.pdf",
  "download_url": "/downloads/report_xxx.pdf",
  "generated_at": "2026-06-22T12:00:00"
}
```

### Session Endpoint

**GET** `/api/v1/session/{session_id}`

**Response:** Full session data including conversation, symptoms, and conditions.

### Health Check

**GET** `/api/v1/health`

```json
{
  "status": "healthy",
  "version": "0.1.0",
  "timestamp": "2026-06-22T12:00:00"
}
```

---

## 🔧 Environment Variables

### Backend (`.env`)

```env
# API Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=false

# Hugging Face AI
HF_API_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
HF_MODEL=Qwen/Qwen2.5-7B-Instruct
HF_API_URL=https://router.huggingface.co/v1/chat/completions

# Session Management
SESSION_TIMEOUT=3600
MAX_TURNS=20

# CORS
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
```

### Frontend (`.env.local`)

```env
PUBLIC_API_URL=http://localhost:8000/api/v1
```

---

## 💾 Database

The database is built from the Symcat medical dataset and includes:

| Table | Records |
|-------|---------|
| **Diseases** | 100 unique conditions |
| **Symptoms** | 230+ symptoms |
| **Disease-Symptoms Mapping** | Many-to-many relationships |

### Build Database

```bash
cd backend
python -m database.build_db
```

This creates:
- `data/symcat.db` (SQLite database)
- `data/symcat_simplified.json` (Human-readable JSON export)

---

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md).

### Development Branches

| Branch | Purpose |
|--------|---------|
| `main` | Documentation only |
| `backend` | FastAPI backend code |
| `frontend` | React frontend code |

### Pull Request Process

1. Fork the repository
2. Create a feature branch (`feature/amazing-feature`)
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

---

## 📄 License

This project is licensed under the Apache License, Version 2.0 - see the [LICENSE](LICENSE) file for details.

### Data Sources

| Dataset | License |
|---------|---------|
| **Symcat** | Open-source, permissive |
| **UMLS** | NIH, free for research |
| **Qwen Model** | Apache 2.0 |

---

## 🙏 Acknowledgments

- [Symcat](https://www.symcat.com/) for the symptom-disease database
- [Qwen](https://huggingface.co/Qwen) for the open-weight LLM
- [Hugging Face](https://huggingface.co/) for the Inference API

---

## ⚠️ Disclaimer

**IMPORTANT:** This software is for **informational and educational purposes only**. It is **not** a substitute for professional medical advice, diagnosis, or treatment. Always seek the advice of your physician or other qualified health provider with any questions you may have regarding a medical condition. Never disregard professional medical advice or delay in seeking it because of something you have read on this system.

**In case of emergency, call your local emergency services immediately.**

---

## 📞 Contact

- **GitHub Issues:** [Report a bug](https://github.com/your-org/AI-Medical-Triage/issues)
- **Discord:** [Join our community](https://discord.gg/your-invite)
- **Email:** support@your-project.org

---

*Built with ❤️ for accessible healthcare.*