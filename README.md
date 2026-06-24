# 🏥 AI Medical Triage

> **Privacy-first, open-source conversational AI for initial medical triage**

[![Live Demo](https://img.shields.io/badge/demo-live-brightgreen)](https://ai-medical-triage-dab8.onrender.com)
[![Backend API](https://img.shields.io/badge/api-online-blue)](https://ai-medical-triage-bk.onrender.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)

## 🌟 Overview

AI Medical Triage is a **privacy-first, open-source** conversational AI system that helps users understand their symptoms and identify potential conditions before seeking professional medical care.

### Key Features

- 💬 **Multi-turn Conversational AI** - Smart clarifying questions to narrow down conditions
- 🏥 **Evidence-Based Matching** - Symptoms matched against a comprehensive medical database
- 📄 **Downloadable Health Reports** - Users own their health data with PDF reports
- 🔒 **Privacy First** - Zero server-side data logging, sessions auto-delete
- 🌍 **Open Source** - Fully auditable code, deployable anywhere
- 🚨 **Red Flag Alerts** - Immediate warnings for life-threatening symptoms

### Live Demo

🌐 **Frontend:** https://ai-medical-triage-dab8.onrender.com
🔗 **Backend API:** https://ai-medical-triage-bk.onrender.com
📚 **API Docs:** https://ai-medical-triage-bk.onrender.com/docs

---

## 📋 Table of Contents

- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Quick Start](#quick-start)
- [Deployment](#deployment)
- [API Reference](#api-reference)
- [Database Schema](#database-schema)
- [Contributing](#contributing)
- [Known Issues](#known-issues)
- [License](#license)

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Browser                           │
│                    (React + Tailwind CSS)                      │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTPS
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Frontend (Render)                         │
│                  Static React Application                      │
│                  https://ai-medical-triage-dab8.onrender.com    │
└────────────────────────────┬────────────────────────────────────┘
                             │ API Calls
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Backend (Render)                         │
│                       FastAPI + Qwen AI                        │
│                   https://ai-medical-triage-bk.onrender.com     │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │  FastAPI    │  │   Qwen AI   │  │   SQLite Database       │ │
│  │  Endpoints  │◄─│  (7B Model) │  │   (40+ MB, 1000+        │ │
│  └─────────────┘  └─────────────┘  │    diseases, 400+       │ │
│                                     │    symptoms)            │ │
│                                     └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🛠 Technology Stack

### Frontend
| Technology | Purpose |
|------------|---------|
| React 18 | UI Framework |
| TypeScript | Type Safety |
| Tailwind CSS | Styling |
| Vite | Build Tool |
| Zustand | State Management |

### Backend
| Technology | Purpose |
|------------|---------|
| FastAPI | API Framework |
| Qwen 2.5-7B | AI Model (via Hugging Face) |
| SQLite | Database |
| Pandas | Data Processing |
| WeasyPrint | PDF Generation |

### Deployment
| Service | Purpose |
|---------|---------|
| Render | Backend & Frontend Hosting |
| Hugging Face | Qwen Model Hosting |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/0xProgress/AI-Medical-Triage.git
cd AI-Medical-Triage
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Build the database (first time only)
python -c "from database.build_db import DatabaseBuilder; DatabaseBuilder().build()"

# Run the server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create environment file
echo "VITE_API_URL=http://localhost:8000/api/v1" > .env

# Run development server
npm run dev
```

### 4. Open in Browser

- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

---

## 🚢 Deployment

### Backend (Render)

1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Configure:

| Setting | Value |
|---------|-------|
| **Environment** | Python 3 |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn main:app --host 0.0.0.0 --port 10000` |
| **Root Directory** | `backend` |

4. Add Environment Variables:

```env
PYTHON_VERSION=3.11.8
HF_HOME=/data
```

### Frontend (Render Static Site)

1. Create a new Static Site on Render
2. Connect your GitHub repository
3. Configure:

| Setting | Value |
|---------|-------|
| **Build Command** | `npm install && npm run build` |
| **Publish Directory** | `dist` |
| **Root Directory** | `frontend` |

4. Add Environment Variables:

```env
VITE_API_URL=https://your-backend-url.onrender.com/api/v1
```

### Hugging Face Spaces (Alternative)

```bash
# Clone the Space
git clone https://huggingface.co/spaces/your-username/medtriage-frontend

# Copy built files
cp -r frontend/dist/* medtriage-frontend/

# Push
cd medtriage-frontend
git add .
git commit -m "Deploy"
git push
```

---

## 📚 API Reference

### Base URL
```
https://ai-medical-triage-bk.onrender.com/api/v1
```

### Endpoints

#### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "timestamp": "2026-06-24T12:00:00"
}
```

#### Chat
```http
POST /chat
```

**Request:**
```json
{
  "session_id": "optional-uuid",
  "message": "I have a cough and fever",
  "history": []
}
```

**Response:**
```json
{
  "session_id": "uuid",
  "message": "Based on your symptoms...",
  "conditions": [
    {
      "name": "acute bronchospasm",
      "description": "...",
      "match_score": 4,
      "match_percentage": 18.18,
      "urgency": "high",
      "precautions": ["..."],
      "medications": ["..."],
      "diet": ["..."],
      "workouts": ["..."]
    }
  ],
  "follow_up_question": "Is the cough productive or dry?",
  "red_flags": [],
  "is_complete": false,
  "turn": 1,
  "max_turns_reached": false
}
```

#### Generate Report
```http
POST /report
```

**Request:**
```json
{
  "session_id": "your-session-id"
}
```

**Response:**
```json
{
  "report_url": "/downloads/report_xxxxx.pdf",
  "download_url": "/downloads/report_xxxxx.pdf",
  "generated_at": "2026-06-24T12:00:00"
}
```

#### Get Session
```http
GET /session/{session_id}
```

---

## 📊 Database Schema

### Diseases Table
```sql
CREATE TABLE diseases (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE,
    description TEXT,
    precautions TEXT,      -- JSON array
    medications TEXT,      -- JSON array
    diet TEXT,            -- JSON array
    workouts TEXT,        -- JSON array
    symptom_count INTEGER
);
```

### Symptoms Table
```sql
CREATE TABLE symptoms (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE
);
```

### Disease-Symptoms Relationship
```sql
CREATE TABLE disease_symptoms (
    disease_id INTEGER,
    symptom_id INTEGER,
    PRIMARY KEY (disease_id, symptom_id),
    FOREIGN KEY (disease_id) REFERENCES diseases(id),
    FOREIGN KEY (symptom_id) REFERENCES symptoms(id)
);
```

---

## 🤝 Contributing

### Development Workflow

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

### Commit Convention

```
feat: Add new feature
fix: Bug fix
docs: Documentation update
style: Code style update
refactor: Code refactoring
test: Test updates
chore: Build/package updates
```

### Coding Standards

- **Python**: PEP 8
- **TypeScript**: ESLint + Prettier
- **Commits**: Conventional Commits

---

## 🐛 Known Issues (To Fix Later)

### 1. Report Download 404
**Issue:** The PDF report is generated but the download URL returns 404
**File:** `backend/services/report_generator.py`
**Fix Needed:** Ensure the StaticFiles mount is serving the reports directory correctly
**Priority:** Medium


---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Qwen Team** for the open-source AI model
- **Symcat** for the medical database
- **Hugging Face** for model hosting
- **Render** for free hosting

---

## 📞 Contact & Community

- **GitHub Issues:** [Report a bug](https://github.com/0xProgress/AI-Medical-Triage/issues)
- **Email:** progressuwhuseba@gmail.com

---

## ⚠️ Disclaimer

> **This is NOT a substitute for professional medical advice.**
>
> Always consult a licensed healthcare provider for medical decisions. This tool is for informational purposes only and should not be used for self-diagnosis or treatment.
>
> In case of emergency, call your local emergency number immediately.

---

## 🌟 Support the Project

If you find this project helpful, please consider:

- ⭐ Starring the repository
- 🐛 Reporting issues
- 🔧 Contributing code
- 💰 Sponsoring development

---

**Built with ❤️ for healthcare accessibility**