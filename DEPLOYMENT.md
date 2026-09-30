# 🚀 VocaGuide Production Deployment Guide

This guide covers complete, step-by-step production deployment for **VocaGuide** across **GitHub**, **Render** (Backend), **Vercel** (Frontend), and **Supabase** (Database & Document Knowledge Vault).

---

## 📋 Architecture & Service Roles

| Component | Platform | Role | Public / Secret |
| :--- | :--- | :--- | :--- |
| **Code Repository** | **GitHub** | Source control & CI/CD triggers | Public or Private repo |
| **Backend API** | **Render** | FastAPI server, LLM orchestration, Supabase RAG, PDF/text processing | Private internal secrets, public API URL |
| **Frontend UI** | **Vercel** | React + Vite single-page application | Public client bundle |
| **Knowledge Base** | **Supabase** | PostgreSQL database, Full-text Search (FTS), RLS, Document vault | Secured by Supabase anon key / RLS |

---

## Step 1: Push Code to GitHub

1. **Verify Git Status and Clean Untracked Secrets:**
   ```bash
   git status
   ```
   *Ensure that `.env`, `node_modules/`, and `.db` files are ignored.*

2. **Stage and Commit:**
   ```bash
   git add .
   git commit -m "feat: production ready vocaguide with supabase rag and cloud deployment config"
   ```

3. **Link to your GitHub Repository:**
   Create a new empty repository on [GitHub](https://github.com/new) (e.g. `vocaguide-ai-campus-assistant`).
   ```bash
   git remote add origin https://github.com/<YOUR-USERNAME>/<YOUR-REPO-NAME>.git
   git branch -M main
   git push -u origin main
   ```

---

## Step 2: Supabase Setup & Verification

1. Go to [Supabase Dashboard](https://supabase.com/dashboard) and select or create your project.
2. Under **Project Settings -> API**, copy:
   - **Project URL** (e.g. `https://your-project.supabase.co`)
   - **anon / public key** (safe for client/backend queries under RLS)
3. Ensure the schema tables exist:
   - `public.users`
   - `public.college_documents`
   - `public.knowledge_chunks` (with `fts` tsvector generated column & GIN index)
   - `public.conversation_sessions`
   - `public.reminders`
   - Stored procedure: `search_college_knowledge(search_query text, match_count int)`
4. Note down your `SUPABASE_URL` and `SUPABASE_KEY`.

---

## Step 3: Deploy Backend on Render

1. Log into [Render](https://dashboard.render.com/).
2. Click **New +** $\rightarrow$ **Web Service**.
3. Select **Build and deploy from a Git repository** and connect your GitHub repo.
4. Configure the Web Service settings:

| Field | Setting / Value |
| :--- | :--- |
| **Name** | `vocaguide-api` |
| **Region** | Oregon (US West) or closest to your users |
| **Branch** | `main` |
| **Root Directory** | Leave blank (root of repo) |
| **Runtime** | `Python 3` *(Preferred)* or `Docker` |
| **Build Command** | `pip install --upgrade pip && pip install -r requirements.txt` |
| **Start Command** | `uvicorn backend.main:app --host 0.0.0.0 --port $PORT` |
| **Instance Type** | Free |

5. Under **Advanced $\rightarrow$ Health Check Path**, set:
   ```
   /health
   ```

6. Add the following **Environment Variables** in the Render Dashboard:

| Key | Value | Notes |
| :--- | :--- | :--- |
| `AI_PROVIDER` | `demo` *(or `gemini` / `openai` / `groq`)* | Defaults to offline grounded engine if keys omitted |
| `CORS_ORIGINS` | `*` *(or your Vercel URL)* | Allows Vercel frontend to query the API |
| `SUPABASE_URL` | `https://your-project.supabase.co` | Your live Supabase project URL |
| `SUPABASE_KEY` | `eyJhbGci...` | Supabase API key |
| `GEMINI_API_KEY` | *(Optional)* | Google AI Gemini API Key |
| `OPENAI_API_KEY` | *(Optional)* | OpenAI API Key |
| `GROQ_API_KEY` | *(Optional)* | Groq Cloud API Key |
*(Note: Render dynamically sets `$PORT`. Do NOT manually define `PORT` unless using custom port bindings.)*

7. Click **Create Web Service**. Wait for the build and deployment to finish.
8. Copy your live Render URL (e.g. `https://vocaguide-api.onrender.com`).
9. Verify by opening `https://vocaguide-api.onrender.com/health` in your browser. It should return:
   ```json
   {"status": "healthy", "service": "vocaguide-api", "version": "1.0.0", "provider": "demo"}
   ```

---

## Step 4: Deploy Frontend on Vercel

1. Log into [Vercel](https://vercel.com/dashboard).
2. Click **Add New...** $\rightarrow$ **Project**.
3. Import your GitHub repository.
4. In the **Configure Project** screen:
   - **Framework Preset:** `Vite`
   - **Root Directory:** Click "Edit" and choose `frontend`
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
5. Expand **Environment Variables** and add:

| Key | Value |
| :--- | :--- |
| `VITE_API_URL` | `https://vocaguide-api.onrender.com` *(Replace with your live Render backend URL without trailing slash)* |

6. Click **Deploy**.
7. In ~60 seconds, Vercel will generate your live production URL (e.g. `https://vocaguide.vercel.app`).
8. Open your live Vercel URL in your browser:
   - Try a voice or text question: *"When is the physics exam?"*
   - Try a follow-up: *"Where is it?"*
   - Click **Docs Vault** in the header to view or upload college documents directly into Supabase.

---

## Step 5: Post-Deployment Verification Checklist

- [ ] **Render Health Check:** `https://<YOUR-RENDER-URL>/health` returns `{"status": "healthy"}`.
- [ ] **Supabase Status:** Header in VocaGuide shows `Supabase: Connected`.
- [ ] **CORS Verification:** No CORS errors in browser dev tools console when sending chat messages.
- [ ] **RAG Grounding:** Asking *"What is the attendance condonation policy?"* retrieves and cites `[college_rules_and_handbook.txt]`.
- [ ] **Anti-Hallucination Guardrail:** Asking *"Can I fly drones over the student cafeteria roof?"* responds with: *"I could not find verified information regarding this question in the official college documents, handbook, or timetable."*
- [ ] **Voice Input & Barge-in:** Clicking the microphone activates browser speech recognition; speaking while AI is talking immediately silences audio.
- [ ] **Document Management:** Admin can upload a PDF or TXT notice, view indexed chunks, and delete documents in real-time.
