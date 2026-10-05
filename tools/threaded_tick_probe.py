import os
import sys
import time
import threading
import queue
import json

BASE = r"C:\Capital\SKDLLPythonTester"
if BASE not in sys.path:
    sys.path.insert(0, BASE)

from SKDLLPython import SK

USER = os.environ.get("CAPITAL_USER_ID", "")
PASSWORD = os.environ.get("CAPITAL_PASSWORD", "")
AUTHORITY = int(os.environ.get("CAPITAL_AUTHORITY", "0"))

events = []
ticks = []
quotes = []
best5_count = 0
ready = threading.Event()
lock = threading.Lock()

def msg(code):
    try:
        return SK.GetMessage(code)
    except Exception:
        return str(code)

def safe(v):
    try:
        return str(v).encode("ascii", "backslashreplace").decode("ascii")
    except Exception:
        return "<unprintable>"

def on_reply(login_id, message):
    print("[OnReplyMessage]", safe(message), flush=True)

def on_connection(login_id, code):
    text = msg(code)
    with lock:
        events.append(text)
    print("[OnConnection]", safe(text), "callback_tid=", threading.get_ident(), flush=True)
    if "STOCKS_READY" in text:
        ready.set()

def on_quote(market_no, stock_no):
    with lock:
        quotes.append((market_no, stock_no))
    print("[QUOTE]", market_no, safe(stock_no), "callback_tid=", threading.get_ident(), flush=True)

def on_tick(market_no, stock_no, ptr, date, time_hms, time_micro, bid, ask, close, qty, simulate):
    row = {
        "market_no": market_no,
        "stock_no": stock_no,
        "ptr": ptr,
        "date": date,
        "time": time_hms,
        "bid_raw": bid,
        "ask_raw": ask,
        "close_raw": close,
        "qty": qty,
        "simulate": simulate,
        "callback_tid": threading.get_ident(),
    }
    with lock:
        ticks.append(row)
    print("[TICK]", json.dumps(row, ensure_ascii=True), flush=True)

def on_best5(*args):
    global best5_count
    best5_count += 1
    if best5_count <= 3:
        print("[BEST5] callback_tid=", threading.get_ident(), "argc=", len(args), flush=True)

SK.OnReplyMessage(on_reply)
SK.OnConnection(on_connection)
SK.OnNotifyQuoteLONG(on_quote)
SK.OnNotifyTicksLONG(on_tick)
try:
    SK.OnNotifyBest5LONG(on_best5)
except Exception as e:
    print("[Best5 registration]", repr(e), flush=True)

if not USER or not PASSWORD:
    raise SystemExit("Missing CAPITAL credentials")

state = {}

def init_worker():
    print("[INIT_THREAD_START] tid=", threading.get_ident(), flush=True)
    login = SK.Login(USER, PASSWORD, AUTHORITY)
    state["login_code"] = login.Code
    print("[Login]", msg(login.Code), flush=True)
    if login.Code != 0:
        return
    rc = SK.ManageServerConnection(USER, 0, 1)
    state["conn_code"] = rc
    print("[ManageServerConnection]", msg(rc), flush=True)
    if rc != 0:
        return
    if not ready.wait(15):
        print("[INIT] STOCKS_READY timeout", flush=True)
    else:
        print("[INIT] STOCKS_READY observed", flush=True)
    for m in [2, 7, 13, 0, 1]:
        try:
            rc = SK.LoadCommodity(m)
            print(f"[LoadCommodity {m}] {msg(rc)}", flush=True)
        except Exception as e:
            print(f"[LoadCommodity {m}] EXCEPTION {safe(repr(e))}", flush=True)
        time.sleep(0.5)
    print("[INIT_THREAD_END] tid=", threading.get_ident(), flush=True)

init_t = threading.Thread(target=init_worker, name="capital-init")
init_t.start()
init_t.join()
print("[MAIN] init thread joined; control returned to main tid=", threading.get_ident(), flush=True)
time.sleep(1.0)

# Each subscription call runs in a fresh worker thread and returns before the next one.
candidates = [
    ("stock_control", "2327"),
    ("otc_control", "6488"),
    ("future_oct26", "PBFV6"),
    ("future_oct26", "QEFV6"),
    ("future_oct26", "OWFV6"),
    ("future_oct26", "LXFV6"),
    ("future_nov26", "PBFX6"),
    ("future_nov26", "QEFX6"),
    ("future_numeric_control", "PBF10"),
    ("future_numeric_control", "QEF10"),
]

results = []

def request_one(item_no, label, symbol):
    print(f"[REQ_THREAD_START] tid={threading.get_ident()} item={item_no} symbol={symbol}", flush=True)
    try:
        rc_tick = SK.SKQuoteLib_RequestTicks(item_no, symbol)
        print(f"[RequestTicks {item_no} {symbol}] {msg(rc_tick)}", flush=True)
    except Exception as e:
        rc_tick = None
        print(f"[RequestTicks {item_no} {symbol}] EXCEPTION {safe(repr(e))}", flush=True)
    try:
        rc_stock = SK.SKQuoteLib_RequestStocks(symbol)
        print(f"[RequestStocks {symbol}] {msg(rc_stock)}", flush=True)
    except Exception as e:
        rc_stock = None
        print(f"[RequestStocks {symbol}] EXCEPTION {safe(repr(e))}", flush=True)
    results.append((item_no, label, symbol, rc_tick, rc_stock))
    print(f"[REQ_THREAD_END] tid={threading.get_ident()} symbol={symbol}", flush=True)

for idx, (label, symbol) in enumerate(candidates):
    t = threading.Thread(target=request_one, args=(idx, label, symbol), name=f"req-{idx}")
    t.start()
    t.join()
    # Explicitly return control to OS/main between requests.
    time.sleep(1.5)

print("[MAIN] subscriptions issued; waiting for callbacks", flush=True)
deadline = time.time() + 12
while time.time() < deadline:
    time.sleep(0.25)

print("[SUMMARY] ticks=", len(ticks), "quotes=", len(quotes), "best5=", best5_count, flush=True)
print("[SUMMARY symbols ticks]", sorted(set(safe(x["stock_no"]) for x in ticks)), flush=True)
print("[SUMMARY symbols quotes]", sorted(set(safe(x[1]) for x in quotes)), flush=True)
for row in results:
    print("[RESULT]", row[0], row[1], row[2], msg(row[3]) if row[3] is not None else "EXC", msg(row[4]) if row[4] is not None else "EXC", flush=True)
