from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio, json, os
from dotenv import load_dotenv
from services.bot import BotService
from services.telegram import TelegramService
from models.database import init_db

load_dotenv()
app = FastAPI(title="SC Trading AI", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
bot_service = BotService()
telegram = TelegramService()

class ConnectionManager:
    def __init__(self): self.active = []
    async def connect(self, ws): await ws.accept(); self.active.append(ws)
    def disconnect(self, ws):
        if ws in self.active: self.active.remove(ws)
    async def broadcast(self, data):
        dead = []
        for ws in self.active:
            try: await ws.send_json(data)
            except: dead.append(ws)
        for ws in dead: self.disconnect(ws)

manager = ConnectionManager()

@app.on_event("startup")
async def startup():
    await init_db()
    asyncio.create_task(bot_service.scheduler(manager))
    asyncio.create_task(telegram.listener(bot_service, manager))
    print("SC Trading AI started!")

@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await manager.connect(ws)
    await ws.send_json({"type":"connected","msg":"SC Trading AI connected!"})
    try:
        while True:
            data = await ws.receive_text()
            msg = json.loads(data)
            if msg.get("type") == "scan":
                asyncio.create_task(bot_service.run_scan(manager))
    except WebSocketDisconnect:
        manager.disconnect(ws)

@app.get("/")
async def root(): return {"name":"SC Trading AI","version":"2.0","status":"online"}

@app.get("/api/state")
async def get_state(): return bot_service.get_state()

@app.post("/api/scan")
async def scan(): asyncio.create_task(bot_service.run_scan(manager)); return {"ok": True}

@app.post("/api/stop")
async def stop(): bot_service.state["running"] = False; return {"ok": True}

@app.post("/api/auto")
async def auto():
    bot_service.state["auto_trade"] = not bot_service.state["auto_trade"]
    return {"auto": bot_service.state["auto_trade"]}

@app.post("/api/trade/{ticker}/{action}")
async def trade(ticker: str, action: str, qty: int = 1):
    asyncio.create_task(bot_service.execute_trade(ticker, action, qty))
    return {"ok": True}

@app.get("/api/signals")
async def signals(): return bot_service.state["signals"]

@app.get("/api/portfolio")
async def portfolio(): return {"portfolio": bot_service.state["portfolio"], "balance": bot_service.state["balance"], "pnl": bot_service.state["pnl"]}

@app.get("/api/trades")
async def trades(): return bot_service.state["trades"]

@app.get("/api/congress")
async def congress(): return bot_service.state["congress_signals"]
