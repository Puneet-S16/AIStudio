# 🚀 Autonomous AI Web Studio

An enterprise-grade, multi-agent AI platform that autonomously designs, builds, tests, and deploys production-ready, multi-page web applications from a single text prompt.

Built for the **Scaler School of Tech Hackathon**.

![AI Studio Overview](https://img.shields.io/badge/Status-Production_Ready-success)
![Python 3.14+](https://img.shields.io/badge/Python-3.14%2B-blue)
![LangGraph](https://img.shields.io/badge/Orchestration-LangGraph-orange)
![Groq](https://img.shields.io/badge/Inference-Groq_LPU-purple)

---

## 🌟 The Vision
Current AI code generators spit out flat, boring, single-page HTML files that require heavy human intervention. 

**Autonomous AI Web Studio** solves this by utilizing a sophisticated Multi-Agent orchestration pipeline that acts as an entire software agency. It enforces "God-Tier" design tokens (Tailwind glassmorphism, Unsplash imagery, CSS animations) to generate jaw-dropping, deeply nested, multi-page React/Tailwind applications, visually tests them, and deploys them to GitHub—all with zero human intervention.

## ✨ Core Features

- **🧠 Multi-Agent Architecture (LangGraph):**
  - **Ideator:** Acts as the Senior UX/UI Architect. Generates deep-scrolling, massive JSON layouts with complex component hierarchies.
  - **Builder:** Acts as the Elite Frontend Engineer. Translates the plan into 300+ line, multi-file codebases using advanced Tailwind CSS, custom keyframes, and rich placeholder imagery.
  - **Reviewer:** Acts as QA. Uses a headless **Playwright** browser to visually test the local server output, capturing console errors and forcing the Builder to fix them before showing the user.
- **🖥️ Enterprise Real-Time IDE:** A Vercel-inspired dark-mode UI with live WebSocket streaming, simulated terminal logs, and a dynamic file explorer.
- **🛡️ Zero-Hallucination Context:** A "New Project" system that actively sanitizes file paths and clears the LangGraph memory state to prevent context pollution between generations.
- **🚀 1-Click GitHub Deploy:** Recursively packages the generated multi-file workspace and asynchronously deploys it to a live GitHub Pages repository using `PyGithub`.
- **📊 Omium Tracing:** Deep observability and workflow tracing integrated via the Omium SDK to capture agent decisions and tool calls.

---

## 🛠️ Tech Stack

- **Backend:** FastAPI, Python, WebSockets
- **AI Orchestration:** LangChain, LangGraph
- **Inference:** Groq API (Llama-3.3-70B / Qwen-32B) for ultra-low latency generation
- **QA Automation:** Playwright (Headless Browser)
- **Deployment:** PyGithub API
- **Frontend:** HTML5, Tailwind CSS, Vanilla JS, Monaco Editor
- **Observability:** Omium SDK

---

## 📦 Local Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Puneet-S16/AIStudio.git
   cd AIStudio
   ```

2. **Set up the virtual environment:**
   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # Windows
   # source venv/bin/activate  # Mac/Linux
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

4. **Environment Variables:**
   Create a `.env` file in the root directory:
   ```env
   GROQ_API_KEY=your_groq_api_key
   GITHUB_TOKEN=your_github_personal_access_token
   ```

5. **Run the Server:**
   ```bash
   .\run.ps1
   # OR
   python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
   ```

6. **Open the Studio:**
   Navigate to `http://127.0.0.1:8000` in your browser.

---

## 📸 Demo & Traces

- **Omium Trace Workflow:** The entire agent pipeline is instrumented with the Omium SDK. Every generation triggers a trace that logs agent handoffs, API latency, and code output states.

---

*Designed and engineered with strict quality constraints. No "Lorem Ipsum" allowed.*
