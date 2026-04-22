import asyncio, os, httpx

class TelegramService:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_TOKEN","")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID","")
        self.base = "https://api.telegram.org/bot"+self.token

    async def send(self, msg, chat_id=None):
        cid = chat_id or self.chat_id
        try:
            async with httpx.AsyncClient(timeout=8) as client:
                await client.post(self.base+"/sendMessage",
                    data={"chat_id":cid,"text":msg,"parse_mode":"HTML"})
        except: pass

    async def listener(self, bot_service, manager):
        offset = None
        await self.send("<b>SC Trading AI (QuantBot v2) Online!</b>"+chr(10)+"Type /help to control")
        while True:
            try:
                async with httpx.AsyncClient(timeout=30) as client:
                    params = {"timeout":25}
                    if offset: params["offset"] = offset
                    r = await client.get(self.base+"/getUpdates", params=params)
                    for u in r.json().get("result",[]):
                        offset = u["update_id"] + 1
                        msg = u.get("message",{})
                        cid = msg.get("chat",{}).get("id")
                        txt = msg.get("text","")
                        if cid and txt.startswith("/"):
                            asyncio.create_task(self.handle(cid, txt, bot_service, manager))
            except: await asyncio.sleep(5)

    async def handle(self, cid, txt, bot, manager):
        parts = txt.strip().split()
        cmd = parts[0].lower()
        nl = chr(10)
        if cmd in ["/help","/start"]:
            await self.send("<b>SC Trading AI Commands</b>"+nl+nl+"/scan - Run AI scan"+nl+"/portfolio - Your holdings"+nl+"/signals - AI signals"+nl+"/congress - Capitol Trades"+nl+"/balance - Account balance"+nl+"/buy AAPL - Buy 1 share"+nl+"/sell MSFT - Sell 1 share"+nl+"/auto - Toggle auto trading"+nl+"/status - Bot status", cid)
        elif cmd=="/scan":
            await self.send("Starting scan...", cid)
            asyncio.create_task(bot.run_scan(manager))
        elif cmd=="/portfolio":
            p = bot.state["portfolio"]
            if not p: await self.send("No positions.", cid); return
            msg = "<b>Holdings</b>"+nl+nl
            for pos in p:
                s="+" if pos["pnl"]>=0 else ""
                msg += "<b>"+pos["ticker"]+"</b> "+str(pos["qty"])+" shares"+nl+"avg $"+str(pos["avg"])+" | now $"+str(pos["current"])+nl+"P&L: "+s+"$"+str(pos["pnl"])+" ("+s+str(pos["pct"])+"%)"+nl+nl
            await self.send(msg, cid)
        elif cmd=="/signals":
            sigs=bot.state["signals"]
            if not sigs: await self.send("No signals. Use /scan!", cid); return
            msg="<b>AI Signals</b>"+nl+nl
            for s in sigs:
                e="green" if s["signal"]=="BUY" else "red" if s["signal"]=="SELL" else "yellow"
                msg+="<b>"+s["ticker"]+"</b> $"+str(s["price"])+" - "+s["signal"]+" ("+str(s["confidence"])+"%)"+nl
            await self.send(msg, cid)
        elif cmd=="/congress":
            cs=bot.state["congress_signals"]
            if not cs: await self.send("No Congress signals.", cid); return
            msg="<b>Capitol Trades</b>"+nl+nl
            for c in cs[:10]:
                msg+="<b>"+c["ticker"]+"</b> - "+c["politician"]+nl+c["type"]+" - "+c["date"]+nl+nl
            await self.send(msg, cid)
        elif cmd=="/balance":
            s="+" if bot.state["pnl"]>=0 else ""
            await self.send("<b>Account</b>"+nl+"Balance: <b>$"+str(bot.state["balance"])+"</b>"+nl+"P&L: <b>"+s+"$"+str(bot.state["pnl"])+"</b>"+nl+"Positions: "+str(len(bot.state["portfolio"])), cid)
        elif cmd=="/buy":
            if len(parts)<2: await self.send("Usage: /buy AAPL", cid); return
            t=parts[1].upper()
            await self.send("Buying "+t+"...", cid)
            asyncio.create_task(bot.execute_trade(t,"BUY"))
        elif cmd=="/sell":
            if len(parts)<2: await self.send("Usage: /sell AAPL", cid); return
            t=parts[1].upper()
            await self.send("Selling "+t+"...", cid)
            asyncio.create_task(bot.execute_trade(t,"SELL"))
        elif cmd=="/auto":
            bot.state["auto_trade"]=not bot.state["auto_trade"]
            s="ON" if bot.state["auto_trade"] else "OFF"
            await self.send("Auto trading: <b>"+s+"</b>", cid)
        elif cmd=="/status":
            await self.send("<b>QuantBot Status</b>"+nl+"Status: "+("Scanning" if bot.state["running"] else "Idle")+nl+"Auto: "+("ON" if bot.state["auto_trade"] else "OFF")+nl+"Last Scan: "+bot.state["last_scan"]+nl+"AI Calls: "+str(bot.state["calls"])+nl+"Signals: "+str(len(bot.state["signals"]))+nl+"Positions: "+str(len(bot.state["portfolio"])), cid)
        else:
            await self.send("Unknown. Type /help", cid)
