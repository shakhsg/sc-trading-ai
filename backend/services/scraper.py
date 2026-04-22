import httpx
from bs4 import BeautifulSoup

class CapitolTradesScraper:
    async def get_signals(self):
        try:
            headers = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
            async with httpx.AsyncClient(timeout=15) as client:
                r = await client.get(
                    "https://www.quiverquant.com/congresstrading/",
                    headers=headers)
                soup = BeautifulSoup(r.text, "html.parser")
                trades = []
                rows = soup.select("table tr")
                for row in rows[1:30]:
                    try:
                        cols = row.select("td")
                        if len(cols) < 4: continue
                        ticker = cols[1].get_text(strip=True).upper()
                        politician = cols[0].get_text(strip=True)
                        trade_type = cols[2].get_text(strip=True).lower()
                        date = cols[3].get_text(strip=True)
                        if not ticker or len(ticker) > 6: continue
                        if "purchase" in trade_type or "buy" in trade_type:
                            trades.append({"ticker":ticker,"politician":politician,"type":"bought","date":date})
                    except: continue
                return trades
        except Exception as e:
            print("Scraper error:", e)
            return []
