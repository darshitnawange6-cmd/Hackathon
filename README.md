# 🎙️ VocaGuide – AI Voice-Powered Campus Assistant

[![Hackathon Ready](https://img.shields.io/badge/Hackathon-Presentation%20Ready-brightgreen)](#)
[![Theme](https://img.shields.io/badge/Theme-Voice%20%26%20Conversational%20Intelligence-blue)](#)
[![Backend](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&logoColor=white)](#)
[![Frontend](https://img.shields.io/badge/React%2018-Vite%20%2B%20Tailwind%20CSS-61DAFB?logo=react&logoColor=black)](#)
[![Database](https://img.shields.io/badge/Supabase-PostgreSQL%20%2B%20Vector%20FTS-3ECF8E?logo=supabase&logoColor=white)](#)
[![Deployment](https://img.shields.io/badge/Cloud-Render%20%2B%20Vercel-purple)](#)

> **VocaGuide** is a commercial-grade, voice-first campus intelligence assistant engineered for university students. Powered by conversational speech recognition, multi-turn conversational context, hybrid document RAG (Supabase + local vector fallback), strict anti-hallucination guardrails, and real-time audio visualization, VocaGuide eliminates campus navigation friction through natural, spoken dialogue.

---

## 📌 Problem Statement

College students face daily friction navigating academic life:
- **Fragmented Portals:** Class schedules, midterm dates, exam rules, and professor contacts are scattered across disparate learning management systems, buried 20-page PDF handbooks, and outdated noticeboards.
- **Lost Context:** Traditional campus chatbots operate as rigid single-turn FAQs—they cannot understand conversational context (e.g. asking *"Where is it?"* or *"What do I need to bring?"* fails because the bot forgets the subject).
- **Audio Clumsiness:** Standard assistants cannot handle speech interruptions; when the assistant speaks, students have to wait for the entire audio prompt to finish before correcting or redirecting the bot.
- **Unreliable Hallucinations:** Generic AI models invent exam dates, office hours, and grading policies, causing severe academic risk for students.

---

## 💡 The VocaGuide Solution

VocaGuide delivers an end-to-end voice companion tailored specifically for higher education:
1. **Conversational Memory & Pronoun Resolution:** Resolves pronouns (*"it"*, *"that"*, *"there"*) and multi-turn inquiries with zero cognitive load.
2. **Instant Voice Barge-In / Interruption:** If the AI is speaking aloud and the student begins talking, audio output immediately terminates and transitions into active listening with zero delay.
3. **Hybrid RAG Grounding with Source Citations:** Ingests official PDF handbooks, notices, and syllabi into Supabase vector full-text search with instant citation cards (Document Name, Category, Date, Section).
4. **Automated Student Action Tools:** Synthesizes natural language commands directly into database study actions (setting exam reminders, viewing daily class timetables).
5. **Zero-Key Resilience Fallback:** Operates with 100% presentation uptime locally even if cloud AI APIs or internet connectivity are unavailable.

---

## 🏗️ System Architecture

```
                             ┌─────────────────────────────────┐
                             │  VocaGuide Web Client (React 18)│
                             │  Vite • Tailwind CSS • Canvas   │
                             └────────────────┬────────────────┘
                                              │
                    ┌─────────────────────────┴─────────────────────────┐
                    │ Web Speech API (STT)      Web Speech Synth (TTS)  │
                    │      [Voice Barge-In / Interruption Engine]       │
                    └─────────────────────────┬─────────────────────────┘
                                              │ HTTP / SSE Stream
                                              ▼
                             ┌─────────────────────────────────┐
                             │     FastAPI Backend Server      │
                             │   (Python 3.10+ / Port 8000)    │
                             └────────────────┬────────────────┘
                                              │
         ┌─────────────────────────┬──────────┴──────────┬─────────────────────────┐
         ▼                         ▼                     ▼                         ▼
┌──────────────────┐     ┌──────────────────┐  ┌───────────────────┐    ┌─────────────────────┐
│ Intent & Entity  │     │  Action Registry │  │ Context & Session │    │ Hybrid RAG Engine   │
│  Classification  │     │ - create_reminder│  │  Memory Manager   │    │ - Supabase Postgres │
│  (11 Enums)      │     │ - show_timetable │  │ (Supabase/SQLite) │    │ - TF-IDF Fallback   │
└────────┬─────────┘     │ - show_exams     │  └─────────┬─────────┘    │ - Anti-Hallucinate  │
         │               └─────────┬────────┘            │              └──────────┬──────────┘
         │                         │                     │                         │
         └─────────────────────────┼─────────────────────┴─────────────────────────┘
                                   │
                                   ▼
                    ┌───────────────────────────────┐
                    │  Unified Conversational Core  │
                    │  ┌──────────────────────────┐ │
                    │  │ Grounded Offline Engine  │ │  (Tier 2 Fallback)
                    │  ├──────────────────────────┤ │
                    │  │ Gemini / OpenAI / Groq   │ │  (Tier 1 Cloud)
                    │  ├──────────────────────────┤ │
                    │  │ Predefined Safe Response │ │  (Tier 3 Resilience)
                    │  └──────────────────────────┘ │
                    └───────────────────────────────┘
```

---

## ✨ Key Features

- **5-State Audio Waveform HUD:** Visual states for `LISTENING`, `THINKING`, `SPEAKING`, `IDLE`, and `ERROR` with pulsing microphone animations.
- **Judge / Developer Dashboard:** Real-time telemetry inspector displaying detected intent, STT/RAG/AI latencies, session context state, executed actions, and system health (toggle with `Ctrl+D` or `F2`).
- **Real-Time SSE Token Streaming:** Progressive token streaming delivers typewriter-style conversational feedback.
- **Transparent Source Citations:** Visual cards on every message showing exact document names, sections, and dates.
- **Admin Document Vault:** Upload official PDFs and TXT files directly to Supabase with automatic chunking and vector indexing.
- **Dual Persistence:** Automatically mirrors reminders and session context across Supabase PostgreSQL and local SQLite databases.
- **Commercial Responsive Layout:** Tailored dark-mode UI optimized across desktop monitors, tablets, and mobile devices.

---

## 🛠️ Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | React 18, Vite, Tailwind CSS, Lucide Icons, Canvas Confetti |
| **Audio & Voice** | Web Speech Recognition API, SpeechSynthesis, Custom Waveform Canvas |
| **Backend** | Python 3.10+, FastAPI, Uvicorn, Pydantic, HTTPX |
| **RAG & Search** | Supabase (PostgreSQL with `tsvector` FTS), Scikit-Learn TF-IDF, PyPDF |
| **AI Providers** | Google Gemini (1.5 Flash), OpenAI (GPT-4o mini), Groq, Grounded Core Engine |
| **Storage & Persistence**| Supabase PostgreSQL, SQLite 3 (dual-storage architecture) |
| **Hosting & Cloud** | Vercel (Frontend), Render (Backend), Supabase Cloud |

---

## 🎯 Official Hackathon Demo Flow (4 Steps)

To demonstrate the full conversational intelligence and context inheritance live:

1. **Step 1: Exam Inquiry**
   - **User Spoken Input:** `"When is my Physics exam?"`
   - **System:** Speech recognition $\rightarrow$ Intent `EXAM_QUERY` $\rightarrow$ Knowledge retrieval $\rightarrow$ Grounds date: **Monday, Oct 12, 2026 at 9:00 AM - 12:00 PM** $\rightarrow$ Text-to-speech response with source citations.
2. **Step 2: Pronoun Location Follow-up**
   - **User Spoken Input:** `"Where is it?"`
   - **System:** Resolves pronoun *"it"* to the active Physics exam $\rightarrow$ Intent `LOCATION_QUERY` $\rightarrow$ Answers: **Hall B-204, Science Block, 2nd Floor**.
3. **Step 3: Exam Requirements Follow-up**
   - **User Spoken Input:** `"What do I need to bring?"`
   - **System:** Continues context $\rightarrow$ Retrieves exam equipment rules: **Hall Ticket, Student ID Card, Casio fx-991EX non-programmable calculator**.
4. **Step 4: Contextual Reminder Creation**
   - **User Spoken Input:** `"Remind me tomorrow."`
   - **System:** Inherits subject `"Physics exam"` $\rightarrow$ Intent `REMINDER_CREATE` $\rightarrow$ Executes `create_reminder` action $\rightarrow$ Persists to database and confirms: *"Reminder set: 'Physics exam' for Tomorrow."*

> 💡 *Presenter Tip:* Click the **"🎯 Demo: Physics Exam"** button in Quick Actions or open **"Demo Scenarios"** in the top header to run this sequence with a single click.

---

## 🚀 Local Setup Instructions

### 1. Prerequisites
- Python 3.10 or higher
- Node.js 18 or higher & npm

### 2. Backend Installation & Run
```bash
# Clone the repository
git clone <your-repository-url>
cd Hackathon

# Install backend dependencies
pip install -r backend/requirements.txt

# Copy environment variables
cp .env.example .env

# Run FastAPI backend (Port 8000)
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

### 3. Frontend Installation & Run
```bash
# In a separate terminal
cd frontend
npm install
npm run dev
```

Visit **`http://localhost:5173`** in your browser.

---

## 🔐 Environment Variables

Create a `.env` file in the project root:

```ini
# Application Mode
APP_ENV=development
PORT=8000

# AI Provider Selection: 'demo', 'gemini', 'openai', or 'groq'
AI_PROVIDER=demo
GEMINI_API_KEY=
OPENAI_API_KEY=
GROQ_API_KEY=

# Supabase Cloud Database & RAG (Optional - falls back to local SQLite)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-service-key

# Client Safe Public Variables (Frontend)
VITE_API_URL=http://localhost:8000
```

> 🛡️ *Security Notice:* Secret keys and database credentials are strictly read on the backend server. The Vite frontend never bundles or exposes private API keys.

---

## ☁️ Deployment

- **Backend (Render):** Blueprint file [`render.yaml`](render.yaml) and [`Procfile`](Procfile) are included. The health check is available at `/health` and `/api/health`.
- **Frontend (Vercel):** Single-page application rewrites are configured in [`frontend/vercel.json`](frontend/vercel.json).
- Detailed cloud deployment instructions are documented in [`DEPLOYMENT.md`](DEPLOYMENT.md).

---

## ⚠️ Known Limitations & Assumptions

1. **Web Speech API Browser Compatibility:** Voice recognition (STT) requires Chromium-based browsers (Google Chrome, Microsoft Edge, Brave) or Safari with microphone permissions enabled. Firefox supports Speech Synthesis (TTS) but has limited native SpeechRecognition support. Text input works universally across all browsers.
2. **Microphone Permissions:** In local development, the browser will prompt for microphone permission on first use. In production, HTTPS is required for persistent microphone access.
3. **Sample Campus Scope:** The included dataset models the *Nexus Institute of Technology* (Fall 2026). Custom college documents can be uploaded on-the-fly via the **Docs Vault** modal.
#   H a c k a t h o n  
 