import os
import sys
import time
import json

BASE = r"C:\Capital\SKDLLPythonTester"
if BASE not in sys.path:
    sys.path.insert(0, BASE)

from SKDLLPython import SK

USER = os.environ.get("CAPITAL_USER_ID", "")
PASSWORD = os.environ.get("CAPITAL_PASSWORD", "")
AUTHORITY = int(os.environ.get("CAPITAL_AUTHORITY", "0"))

events = []
quotes = []

def msg(code):
    try:
        return SK.GetMessage(code)
    except Exception:
        return str(code)

def on_reply(login_id, message):
    print("[OnReplyMessage]", message)

def on_connection(login_id, code):
    text = msg(code)
    events.append((code, text))
    print("[OnConnection]", text)

def on_quote(market_no, stock_no):
    try:
        s = SK.SKQuoteLib_GetStockByStockNo(market_no, stock_no)
        scale = 10 ** max(int(getattr(s, "nDecimal", 0)), 0)
        def px(v):
            return None if v is None else v / scale
        data = {
            "market_no": market_no,
            "stock_no": stock_no,
            "name": getattr(s, "strStockName", ""),
            "decimal": getattr(s, "nDecimal", None),
            "close": px(getattr(s, "nClose", None)),
            "bid": px(getattr(s, "nBid", None)),
            "ask": px(getattr(s, "nAsk", None)),
            "open": px(getattr(s, "nOpen", None)),
            "high": px(getattr(s, "nHigh", None)),
            "low": px(getattr(s, "nLow", None)),
            "tick_qty": getattr(s, "nTickQty", None),
            "total_qty": getattr(s, "nTQty", None),
            "future_oi": getattr(s, "nFutureOI", None),
            "trading_day": getattr(s, "nTradingDay", None),
            "deal_time": getattr(s, "nDealTime", None),
            "code": getattr(s, "nCode", None),
        }
        quotes.append(data)
        print("[QUOTE]", json.dumps(data, ensure_ascii=False))
    except Exception as e:
        print("[QUOTE_ERROR]", market_no, stock_no, repr(e))

SK.OnReplyMessage(on_reply)
SK.OnConnection(on_connection)
SK.OnNotifyQuoteLONG(on_quote)

if not USER or not PASSWORD:
    raise SystemExit("Missing CAPITAL_USER_ID or CAPITAL_PASSWORD in runner environment")

login = SK.Login(USER, PASSWORD, AUTHORITY)
print("[Login]", msg(login.Code))
if login.Code != 0:
    raise SystemExit(login.Code)

code = SK.ManageServerConnection(USER, 0, 1)
print("[Domestic quote connection]", msg(code))
if code != 0:
    raise SystemExit(code)

deadline = time.time() + 10
while time.time() < deadline:
    if any("STOCKS_READY" in text for _, text in events):
        break
    time.sleep(0.25)

markets = [0, 2, 7, 13]
for market in markets:
    try:
        code = SK.LoadCommodity(market)
        print(f"[LoadCommodity {market}]", msg(code))
    except Exception as e:
        print(f"[LoadCommodity {market}] EXCEPTION", repr(e))
    time.sleep(0.5)

# Control stock plus candidate futures codes observed/expected in this environment.
candidates = [
    "2327", "6488",
    "PBF10", "PBF", "QEF10", "QEF",
    "TMF", "MXF", "TXF", "TM0000"
]

for symbol in candidates:
    try:
        code = SK.SKQuoteLib_RequestStocks(symbol)
        print(f"[RequestStocks {symbol}]", msg(code))
        time.sleep(1.0)
    except Exception as e:
        print(f"[RequestStocks {symbol}] EXCEPTION", repr(e))

print("[SUMMARY]", json.dumps({
    "events": [text for _, text in events],
    "quote_count": len(quotes),
    "symbols_seen": sorted(set(q["stock_no"] for q in quotes)),
}, ensure_ascii=False))
