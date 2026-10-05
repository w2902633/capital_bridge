import os
import sys
import time
import threading
import json

BASE = r"C:\Capital\SKDLLPythonTester"
if BASE not in sys.path:
    sys.path.insert(0, BASE)
from SKDLLPython import SK

USER = os.environ.get("CAPITAL_USER_ID", "")
PASSWORD = os.environ.get("CAPITAL_PASSWORD", "")
AUTHORITY = int(os.environ.get("CAPITAL_AUTHORITY", "0"))

ready = threading.Event()
ticks = []
quotes = []
lock = threading.Lock()

def msg(code):
    try: return SK.GetMessage(code)
    except Exception: return str(code)

def on_reply(login_id, message):
    print("[REPLY]", str(message).encode("ascii","backslashreplace").decode("ascii"), flush=True)

def on_connection(login_id, code):
    t = msg(code)
    print("[CONNECTION]", t, flush=True)
    if "STOCKS_READY" in t:
        ready.set()

def on_quote(market_no, stock_no):
    with lock: quotes.append((market_no, stock_no))
    print("[QUOTE]", market_no, stock_no, flush=True)

def on_tick(market_no, stock_no, ptr, date, time_hms, time_micro, bid, ask, close, qty, simulate):
    row = {"market_no":market_no,"stock_no":stock_no,"ptr":ptr,"date":date,"time":time_hms,
           "bid_raw":bid,"ask_raw":ask,"close_raw":close,"qty":qty,"simulate":simulate}
    with lock: ticks.append(row)
    print("[TICK]", json.dumps(row, ensure_ascii=True), flush=True)

SK.OnReplyMessage(on_reply)
SK.OnConnection(on_connection)
SK.OnNotifyQuoteLONG(on_quote)
SK.OnNotifyTicksLONG(on_tick)

def init_worker():
    login = SK.Login(USER, PASSWORD, AUTHORITY)
    print("[LOGIN]", msg(login.Code), flush=True)
    if login.Code != 0: return
    rc = SK.ManageServerConnection(USER, 0, 1)
    print("[CONNECT]", msg(rc), flush=True)
    if rc != 0: return
    ready.wait(15)
    for m in [2,7,13,0,1]:
        try:
            rc = SK.LoadCommodity(m)
            print("[LOAD]", m, msg(rc), flush=True)
        except Exception as e:
            print("[LOAD_EXC]", m, repr(e), flush=True)
        time.sleep(0.3)

t = threading.Thread(target=init_worker)
t.start(); t.join()
print("[INIT_DONE]", flush=True)
time.sleep(1)

symbols = ["6488","PBF00","QEF00","OWF00","LXF00","PBF01","QEF01","TX00","MTX00"]

def req(item, sym):
    print("[REQ_START]", item, sym, flush=True)
    try:
        a = SK.SKQuoteLib_RequestTicks(item, sym)
        print("[REQ_TICKS]", item, sym, msg(a), flush=True)
    except Exception as e:
        print("[REQ_TICKS_EXC]", item, sym, repr(e), flush=True)
    try:
        b = SK.SKQuoteLib_RequestStocks(sym)
        print("[REQ_STOCKS]", sym, msg(b), flush=True)
    except Exception as e:
        print("[REQ_STOCKS_EXC]", sym, repr(e), flush=True)

for i,sym in enumerate(symbols, start=1):
    rt = threading.Thread(target=req, args=(i,sym))
    rt.start(); rt.join()
    time.sleep(1.0)

time.sleep(10)
print("[SUMMARY_TICKS]", sorted(set(x["stock_no"] for x in ticks)), flush=True)
print("[SUMMARY_QUOTES]", sorted(set(x[1] for x in quotes)), flush=True)
