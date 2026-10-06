import os, sys, time, json, threading, sqlite3, signal
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
from collections import defaultdict, deque
from datetime import datetime

BASE=r"C:\\Capital\\SKDLLPythonTester"
if BASE not in sys.path:
    sys.path.insert(0, BASE)
from SKDLLPython import SK

HOST="127.0.0.1"
PORT=int(os.environ.get("CAPITAL_BRIDGE_PORT","8877"))
USER=os.environ.get("CAPITAL_USER_ID","")
PASSWORD=os.environ.get("CAPITAL_PASSWORD","")
AUTH=int(os.environ.get("CAPITAL_AUTHORITY","0"))
SYMBOLS=[x.strip() for x in os.environ.get(
    "CAPITAL_BRIDGE_SYMBOLS",
    "PBF00,QEF00,DQF00,VBF00,CCF00,TM0000"
).split(",") if x.strip()]
DB_PATH=os.environ.get("CAPITAL_BRIDGE_DB", os.path.join(BASE,"capital_market_data.sqlite3"))

ready=threading.Event()
stop_evt=threading.Event()
lock=threading.RLock()
quotes={}
ticks=defaultdict(lambda: deque(maxlen=50000))
bars=defaultdict(lambda: defaultdict(dict))
started_at=time.time()

TF_SECONDS={"1m":60,"3m":180,"5m":300,"15m":900,"1h":3600}

def safe_msg(code):
    try:
        return SK.GetMessage(code)
    except Exception:
        return str(code)

def px(raw):
    if raw is None:
        return None
    # Current Taiwan stock/futures callbacks observed from this SKCOM bridge use x100 scaling.
    return raw / 100.0

def bar_bucket(ts, sec):
    return ts - (ts % sec)

def update_bars(symbol, epoch_s, price, qty):
    for tf,sec in TF_SECONDS.items():
        b=bar_bucket(epoch_s,sec)
        series=bars[symbol][tf]
        cur=series.get(b)
        if cur is None:
            series[b]={"t":b,"o":price,"h":price,"l":price,"c":price,"v":qty}
        else:
            cur["h"]=max(cur["h"],price)
            cur["l"]=min(cur["l"],price)
            cur["c"]=price
            cur["v"]+=qty
        if len(series)>3000:
            for k in sorted(series)[:-2500]:
                series.pop(k,None)

def on_reply(uid,msg):
    return

def on_conn(uid,code):
    if "STOCKS_READY" in safe_msg(code):
        ready.set()

def on_tick(market,symbol,ptr,date,time_hms,time_micro,bid,ask,close,qty,simulate):
    try:
        ds=str(date)
        ts=str(time_hms).zfill(6)
        dt=datetime.strptime(ds+ts,"%Y%m%d%H%M%S")
        epoch=int(dt.timestamp())
    except Exception:
        epoch=int(time.time())
    q={
        "symbol":symbol,
        "market":market,
        "date":date,
        "time":time_hms,
        "bid":px(bid),
        "ask":px(ask),
        "last":px(close),
        "qty":qty,
        "simulate":simulate,
        "received_at":time.time()
    }
    with lock:
        quotes[symbol]=q
        ticks[symbol].append(q)
        if q["last"] is not None:
            update_bars(symbol,epoch,q["last"],qty or 0)

def init_db():
    con=sqlite3.connect(DB_PATH)
    con.execute("""CREATE TABLE IF NOT EXISTS ticks(
        symbol TEXT, received_at REAL, market INTEGER, trade_date INTEGER,
        trade_time INTEGER, bid REAL, ask REAL, last REAL, qty INTEGER, simulate INTEGER
    )""")
    con.execute("CREATE INDEX IF NOT EXISTS idx_ticks_symbol_time ON ticks(symbol,received_at)")
    con.commit()
    con.close()

def persist_loop():
    last_seen={}
    while not stop_evt.wait(1):
        rows=[]
        with lock:
            for sym,q in quotes.items():
                marker=(q.get("date"),q.get("time"),q.get("last"),q.get("qty"))
                if last_seen.get(sym)==marker:
                    continue
                last_seen[sym]=marker
                rows.append((sym,q["received_at"],q["market"],q["date"],q["time"],q["bid"],q["ask"],q["last"],q["qty"],q["simulate"]))
        if rows:
            try:
                con=sqlite3.connect(DB_PATH)
                con.executemany("INSERT INTO ticks VALUES(?,?,?,?,?,?,?,?,?,?)",rows)
                con.commit()
                con.close()
            except Exception:
                pass

def snapshot():
    now=time.time()
    with lock:
        return {
            "ok":True,
            "uptime_sec":round(now-started_at,1),
            "ready":ready.is_set(),
            "symbols":SYMBOLS,
            "quotes":quotes.copy()
        }

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        return
    def sendj(self,obj,code=200):
        body=json.dumps(obj,ensure_ascii=False,separators=(",",":")).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type","application/json; charset=utf-8")
        self.send_header("Cache-Control","no-store")
        self.send_header("Content-Length",str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def do_GET(self):
        u=urlparse(self.path)
        parts=[p for p in u.path.split("/") if p]
        if u.path=="/health":
            self.sendj(snapshot()); return
        if len(parts)==2 and parts[0]=="quote":
            sym=parts[1].upper()
            with lock: q=quotes.get(sym)
            if not q:
                self.sendj({"ok":False,"error":"symbol_not_ready","symbol":sym},404); return
            out=dict(q); out["age_ms"]=int((time.time()-q["received_at"])*1000)
            self.sendj({"ok":True,"quote":out}); return
        if u.path=="/quotes":
            qs=parse_qs(u.query)
            syms=[x.strip().upper() for x in qs.get("symbols",[""])[0].split(",") if x.strip()]
            with lock:
                data={}
                for sym in syms:
                    if sym in quotes:
                        q=dict(quotes[sym]); q["age_ms"]=int((time.time()-q["received_at"])*1000); data[sym]=q
            self.sendj({"ok":True,"quotes":data}); return
        if len(parts)==2 and parts[0]=="bars":
            sym=parts[1].upper()
            qs=parse_qs(u.query)
            tf=qs.get("tf",["1m"])[0]
            limit=min(max(int(qs.get("limit",["100"])[0]),1),1000)
            if tf not in TF_SECONDS:
                self.sendj({"ok":False,"error":"bad_tf"},400); return
            with lock:
                rows=list(bars[sym][tf].values())[-limit:]
            self.sendj({"ok":True,"symbol":sym,"tf":tf,"bars":rows}); return
        self.sendj({"ok":False,"error":"not_found"},404)

def subscribe():
    SK.OnReplyMessage(on_reply)
    SK.OnConnection(on_conn)
    SK.OnNotifyTicksLONG(on_tick)
    login=SK.Login(USER,PASSWORD,AUTH)
    if login.Code!=0:
        raise RuntimeError("login_failed:"+safe_msg(login.Code))
    rc=SK.ManageServerConnection(USER,0,1)
    if rc!=0:
        raise RuntimeError("connect_failed:"+safe_msg(rc))
    if not ready.wait(20):
        raise RuntimeError("stocks_ready_timeout")
    SK.LoadCommodity(2)
    time.sleep(0.5)
    item=1
    for sym in SYMBOLS:
        rc=SK.SKQuoteLib_RequestTicks(item,sym)
        if rc==3027:
            item+=1
            rc=SK.SKQuoteLib_RequestTicks(item,sym)
        item+=1
        # No credentials/account identifiers are logged.
        print(json.dumps({"event":"subscribe","symbol":sym,"code":rc,"message":safe_msg(rc)},ensure_ascii=True),flush=True)

def main():
    init_db()
    subscribe()
    threading.Thread(target=persist_loop,daemon=True).start()
    server=ThreadingHTTPServer((HOST,PORT),Handler)
    print(json.dumps({"event":"ready","host":HOST,"port":PORT,"symbols":SYMBOLS},ensure_ascii=True),flush=True)
    try:
        server.serve_forever(poll_interval=0.2)
    finally:
        stop_evt.set()
        server.server_close()

if __name__=="__main__":
    main()
