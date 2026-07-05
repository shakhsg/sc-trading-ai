# SC Trading AI

Professional AI trading terminal — real-time stock signals, Telegram alerts, and an HFT monitor. FastAPI backend with WebSocket streaming + React/TypeScript dashboard.

## Architecture

```
backend/    FastAPI + WebSocket broadcast, signal engine, Telegram alerts
frontend/   React + TypeScript dashboard (TradingDashboard, HFTDashboard)
```

- **Backend** — FastAPI app (`backend/main.py`) that runs the bot service, streams live updates to all connected clients over WebSockets, and persists data with SQLite.
- **Frontend** — Create React App + TypeScript UI with real-time trading and HFT monitoring dashboards.
- **Alerts** — Telegram integration for signal notifications.

## Getting Started

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm start
```

Copy `frontend/.env.example` to `frontend/.env` and set your values. The backend reads its configuration (Telegram token, API keys) from environment variables via `.env` — never commit real credentials.

## Tech Stack

FastAPI · WebSockets · SQLite · React · TypeScript · Telegram Bot API

## License

MIT
