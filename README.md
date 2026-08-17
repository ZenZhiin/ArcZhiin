# ArcZhiin — Full-Stack AI Assistant

> A private, always-on AI assistant by **ZenZhiin** — voice control, smart home integration, GPU-accelerated local AI, and a futuristic dashboard.

## Architecture

```
Desktop Hub (Ryzen 7 + GTX 1070 Ti + Linux)
├── FastAPI Backend (AI Brain + Voice Pipeline)
├── Ollama (CUDA GPU-accelerated LLMs)
├── Home Assistant (Docker)
├── SQLite + sqlite-vec (Memory)
└── React Dashboard (served via Nginx)
```

## Quick Start (Mac Development)

```bash
# 1. Set up Python environment
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Copy environment config
cp .env.example .env
# Edit .env with your API keys

# 3. Start backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 4. Start frontend (separate terminal)
cd frontend
npm install
npm run dev
```

## Project Structure

```
arczhiin/
├── backend/          # FastAPI Python backend
│   ├── main.py       # App entrypoint
│   ├── config.py     # Settings & env loading
│   ├── api/routes/   # WebSocket & REST endpoints
│   ├── core/         # LLM router, agent, memory
│   ├── voice/        # Wake word, VAD, STT, TTS
│   ├── integrations/ # Home Assistant, calendar
│   └── db/           # SQLite schemas & migrations
├── frontend/         # React 19 + Vite + TypeScript
├── docker/           # Dockerfiles & nginx config
└── scripts/          # Setup & deployment scripts
```

## Tech Stack

- **Backend**: Python 3.11+ / FastAPI / LiteLLM / Ollama
- **Frontend**: React 19 / Vite / TypeScript / Tailwind / Zustand
- **Database**: SQLite (WAL) + sqlite-vec
- **Voice**: openWakeWord / Silero VAD / faster-whisper / Piper TTS
- **Smart Home**: Home Assistant via WebSocket + MCP
- **LLM**: Gemini (primary) → Ollama GPU (fallback) → Gemini Pro (complex)

## License

Private — ZenZhiin Venture
