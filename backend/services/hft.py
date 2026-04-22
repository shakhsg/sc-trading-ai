import asyncio, os, time, random
from datetime import datetime
from collections import deque

class HFTService:
    def __init__(self):
        self.state = {
            "running": False,
            "latency_ms": 0,
            "avg_latency": 0,
            "max_latency": 0,
            "rate_limited": False,
            "rate_limit_threshold": 150,
            "trades_count": 0,
            "trades_per_min": 0,
            "pnl": 0.0,
            "pnl_history": [],
            "gaps_found": 0,
            "heartbeat": True,
            "last_heartbeat": datetime.now().strftime("%H:%M:%S"),
            "system_status": "READY",
            "latency_history": [],
        }
        self.latency_samples = deque(maxlen=100)
        self.trade_timestamps = deque(maxlen=1000)

    def measure_latency(self):
        start = time.time()
        try:
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            s.connect(("127.0.0.1", int(os.getenv("IB_PORT", "7497"))))
            s.close()
        except: pass
        return round((time.time() - start) * 1000, 2)

    def check_rate_limit(self):
        lat = self.state["latency_ms"]
        threshold = self.state["rate_limit_threshold"]
        self.state["rate_limited"] = lat > threshold
        if self.state["rate_limited"]: self.state["system_status"] = "RATE LIMITED"
        elif lat > threshold * 0.7: self.state["system_status"] = "WARNING"
        else: self.state["system_status"] = "OPTIMAL"

    def get_state(self): return self.state

    async def heartbeat_loop(self, manager):
        tick = 0
        while self.state["running"]:
            try:
                await asyncio.sleep(1)
                tick += 1
                lat = self.measure_latency()
                self.latency_samples.append(lat)
                self.state["latency_ms"] = lat
                if len(self.state["latency_history"]) > 60:
                    self.state["latency_history"].pop(0)
                self.state["latency_history"].append({"t": tick, "v": lat})
                if self.latency_samples:
                    self.state["avg_latency"] = round(sum(self.latency_samples)/len(self.latency_samples), 2)
                    self.state["max_latency"] = round(max(self.latency_samples), 2)
                self.check_rate_limit()
                self.state["heartbeat"] = not self.state["heartbeat"]
                self.state["last_heartbeat"] = datetime.now().strftime("%H:%M:%S")
                await manager.broadcast({
                    "type": "hft_heartbeat",
                    "latency": lat,
                    "avg_latency": self.state["avg_latency"],
                    "max_latency": self.state["max_latency"],
                    "rate_limited": self.state["rate_limited"],
                    "status": self.state["system_status"],
                    "trades_per_min": self.state["trades_per_min"],
                    "pnl": self.state["pnl"],
                    "tick": tick,
                    "heartbeat": self.state["heartbeat"],
                    "last_heartbeat": self.state["last_heartbeat"],
                    "rate_limit_threshold": self.state["rate_limit_threshold"],
                    "latency_history": self.state["latency_history"][-20:]
                })
            except Exception as e:
                await asyncio.sleep(2)

    async def simulate_activity_stream(self, manager):
        actions = ["BUY","SELL","SCAN","CHECK","MONITOR","ANALYZE","EXECUTE"]
        stocks = ["AAPL","MSFT","NVDA","META","GOOGL","AMZN","V","JNJ","KO","PLTR"]
        count = 0
        pnl = 0.0
        while self.state["running"]:
            try:
                await asyncio.sleep(0.05)
                count += 1
                stock = random.choice(stocks)
                action = random.choice(actions)
                price = round(random.uniform(50, 700), 2)
                lat = round(random.uniform(0.5, 15), 2)
                profit = round(random.uniform(-0.5, 1.2), 4)
                pnl += profit
                self.state["trades_count"] = count
                self.state["pnl"] = round(pnl, 4)
                self.trade_timestamps.append(time.time())
                now = time.time()
                recent = [t for t in self.trade_timestamps if now - t < 60]
                self.state["trades_per_min"] = len(recent)
                await manager.broadcast({
                    "type": "hft_log",
                    "id": count,
                    "time": datetime.now().strftime("%H:%M:%S.%f")[:-3],
                    "action": action,
                    "symbol": stock,
                    "price": price,
                    "latency": lat,
                    "profit": profit,
                    "pnl": round(pnl, 4),
                    "status": "OK" if lat < 10 else "SLOW",
                    "count": count
                })
            except Exception as e:
                await asyncio.sleep(0.1)

    async def start(self, manager):
        if self.state["running"]: return
        self.state["running"] = True
        asyncio.create_task(self.heartbeat_loop(manager))
        asyncio.create_task(self.simulate_activity_stream(manager))

    async def stop(self):
        self.state["running"] = False
