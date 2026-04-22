import asyncio, os, threading
from datetime import datetime
from groq import Groq
import nest_asyncio
nest_asyncio.apply()

STOCKS = ["AAPL","MSFT","GOOGL","AMZN","META","NVDA","V","JNJ","KO","PLTR"]

class BotService:
    def __init__(self):
        self.state = {
            "running": False, "signals": [], "log": [], "trades": [],
            "portfolio": [], "balance": 0, "pnl": 0, "calls": 0,
            "auto_trade": False, "last_scan": "Never", "congress_signals": []
        }

    def log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        entry = "["+ts+"] "+msg
        self.state["log"].insert(0, entry)
        if len(self.state["log"]) > 100: self.state["log"].pop()
        print(entry)

    def get_state(self): return self.state

    def _run_ib_sync(self, func):
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(func())
        finally:
            loop.close()

    def get_price_sync(self, ticker):
        try:
            from ib_insync import IB, Stock
            ib = IB()
            ib.connect(os.getenv("IB_HOST","127.0.0.1"), int(os.getenv("IB_PORT","7497")), clientId=10)
            contract = Stock(ticker, "SMART", "USD")
            bars = ib.reqHistoricalData(contract, endDateTime="", durationStr="1 D",
                barSizeSetting="1 hour", whatToShow="TRADES", useRTH=True)
            price = round(bars[-1].close, 3) if bars else None
            ib.disconnect()
            return price
        except: return None

    def get_candles_sync(self, ticker):
        try:
            from ib_insync import IB, Stock
            ib = IB()
            ib.connect(os.getenv("IB_HOST","127.0.0.1"), int(os.getenv("IB_PORT","7497")), clientId=11)
            contract = Stock(ticker, "SMART", "USD")
            bars = ib.reqHistoricalData(contract, endDateTime="", durationStr="5 D",
                barSizeSetting="1 hour", whatToShow="TRADES", useRTH=True)
            out = []
            for b in bars:
                ts_str = str(b.date)
                try:
                    if " " in ts_str:
                        ts = int(datetime.strptime(ts_str[:16], "%Y-%m-%d %H:%M").timestamp())
                    else:
                        ts = int(datetime.strptime(ts_str, "%Y-%m-%d").timestamp())
                    out.append({"time":ts,"open":round(b.open,4),"high":round(b.high,4),"low":round(b.low,4),"close":round(b.close,4)})
                except: pass
            ib.disconnect()
            return out
        except: return []

    def get_portfolio_sync(self):
        try:
            from ib_insync import IB
            ib = IB()
            ib.connect(os.getenv("IB_HOST","127.0.0.1"), int(os.getenv("IB_PORT","7497")), clientId=12)
            positions = ib.positions()
            account_vals = ib.accountValues()
            portfolio = []
            for p in positions:
                t=p.contract.symbol; q=p.position; avg=round(p.avgCost,3)
                cur = self.get_price_sync(t) or avg
                pnl=round((cur-avg)*q,2); pct=round(((cur-avg)/avg)*100,2) if avg else 0
                portfolio.append({"ticker":t,"qty":int(q),"avg":avg,"current":cur,"pnl":pnl,"pct":pct,"value":round(cur*q,2)})
            bal = 0
            for v in account_vals:
                if v.tag=="NetLiquidation" and v.currency=="USD": bal=round(float(v.value),2)
            ib.disconnect()
            return portfolio, bal
        except Exception as e:
            self.log("Portfolio error: "+str(e))
            return [], 0

    def execute_trade_sync(self, ticker, action, qty=1):
        try:
            from ib_insync import IB, Stock, MarketOrder
            ib = IB()
            ib.connect(os.getenv("IB_HOST","127.0.0.1"), int(os.getenv("IB_PORT","7497")), clientId=13)
            contract = Stock(ticker, "SMART", "USD")
            ib.placeOrder(contract, MarketOrder(action, qty))
            ib.sleep(2)
            price = self.get_price_sync(ticker) or 0
            msg = action+" "+str(qty)+"x "+ticker+" @$"+str(price)
            self.log(msg)
            trade = {"action":action,"ticker":ticker,"qty":qty,"time":datetime.now().strftime("%H:%M:%S"),"price":price}
            self.state["trades"].insert(0, trade)
            ib.disconnect()
            return True
        except Exception as e:
            self.log("Trade error: "+str(e))
            return False

    async def execute_trade(self, ticker, action, qty=1):
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self.execute_trade_sync, ticker, action, qty)
        return result

    def _scan_thread(self, manager, loop):
        try:
            self.log("Getting portfolio...")
            portfolio, bal = self.get_portfolio_sync()
            self.state["portfolio"] = portfolio
            self.state["balance"] = bal
            self.state["pnl"] = round(sum(p["pnl"] for p in portfolio), 2)

            try:
                from services.scraper import CapitolTradesScraper
                import asyncio as aio
                new_loop = aio.new_event_loop()
                congress = new_loop.run_until_complete(CapitolTradesScraper().get_signals())
                new_loop.close()
                self.state["congress_signals"] = congress
                self.log("Found "+str(len(congress))+" Congress trades!")
            except Exception as e:
                self.log("Scraper: "+str(e))
                congress = []

            client = Groq(api_key=os.getenv("GROQ_API_KEY",""))
            new_signals = []

            for ticker in STOCKS:
                try:
                    price = self.get_price_sync(ticker)
                    if not price:
                        self.log("No price for "+ticker)
                        continue
                    candles = self.get_candles_sync(ticker)
                    self.log("Analyzing "+ticker+" $"+str(price)+"...")

                    congress_ctx = ""
                    for c in congress:
                        if c.get("ticker") == ticker:
                            congress_ctx = " Congress: "+c.get("politician","")+" recently bought."

                    nl = chr(10)
                    prompt = ticker+" stock $"+str(price)+"."+congress_ctx+nl+"SIGNAL: BUY or SELL or HOLD"+nl+"REASON: one sentence"+nl+"CONFIDENCE: 1-100"
                    resp = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role":"user","content":prompt}])
                    analysis = resp.choices[0].message.content
                    self.state["calls"] += 1

                    signal = "HOLD"
                    confidence = 50
                    if "SIGNAL: BUY" in analysis: signal = "BUY"
                    elif "SIGNAL: SELL" in analysis: signal = "SELL"
                    for line in analysis.split(nl):
                        if "CONFIDENCE:" in line:
                            try: confidence = min(100,max(0,int("".join(filter(str.isdigit,line)))))
                            except: pass

                    sig = {"ticker":ticker,"price":price,"signal":signal,"analysis":analysis,"confidence":confidence,"candles":candles,"congress":congress_ctx.strip()}
                    new_signals.append(sig)
                    self.log(ticker+": "+signal+" "+str(confidence)+"%")

                    if loop and manager:
                        asyncio.run_coroutine_threadsafe(manager.broadcast({"type":"signal","data":sig}), loop)

                    if self.state["auto_trade"] and signal == "BUY":
                        self.execute_trade_sync(ticker, "BUY")

                except Exception as e:
                    self.log("Error "+ticker+": "+str(e))

            self.state["signals"] = new_signals
            self.log("Scan done! "+str(len(new_signals))+" signals.")

            if loop and manager:
                asyncio.run_coroutine_threadsafe(manager.broadcast({
                    "type":"scan_complete","signals":new_signals,
                    "portfolio":self.state["portfolio"],"balance":self.state["balance"],
                    "pnl":self.state["pnl"],"calls":self.state["calls"],
                    "last_scan":self.state["last_scan"]
                }), loop)

        except Exception as e:
            self.log("Scan error: "+str(e))
        finally:
            self.state["running"] = False
            if loop and manager:
                asyncio.run_coroutine_threadsafe(manager.broadcast({"type":"status","running":False}), loop)

    async def run_scan(self, manager=None):
        if self.state["running"]: return
        self.state["running"] = True
        self.state["last_scan"] = datetime.now().strftime("%H:%M:%S")
        if manager:
            await manager.broadcast({"type":"status","running":True,"last_scan":self.state["last_scan"]})
        loop = asyncio.get_event_loop()
        t = threading.Thread(target=self._scan_thread, args=(manager, loop), daemon=True)
        t.start()

    async def scheduler(self, manager):
        while True:
            await asyncio.sleep(15*60)
            if not self.state["running"]:
                await self.run_scan(manager)
