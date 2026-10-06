import os,sys,time,threading,json
BASE=r"C:\Capital\SKDLLPythonTester"
if BASE not in sys.path: sys.path.insert(0,BASE)
from SKDLLPython import SK

USER=os.environ.get("CAPITAL_USER_ID","")
PASSWORD=os.environ.get("CAPITAL_PASSWORD","")
AUTH=int(os.environ.get("CAPITAL_AUTHORITY","0"))
ready=threading.Event()
ticks=[]; quotes=[]

def msg(c):
    try:return SK.GetMessage(c)
    except:return str(c)

def on_reply(uid,m):
    print("[REPLY]",str(m).encode("ascii","backslashreplace").decode("ascii"),flush=True)

def on_conn(uid,c):
    print("[CONN]",c,msg(c),flush=True)
    if "STOCKS_READY" in msg(c): ready.set()

def on_quote(m,s):
    quotes.append((m,s))
    print("[QUOTE]",m,s,flush=True)

def on_tick(m,s,ptr,date,t,tm,bid,ask,close,qty,sim):
    row={"market":m,"symbol":s,"date":date,"time":t,"bid":bid,"ask":ask,"close":close,"qty":qty}
    ticks.append(row)
    print("[TICK]",json.dumps(row,ensure_ascii=True),flush=True)

SK.OnReplyMessage(on_reply)
SK.OnConnection(on_conn)
SK.OnNotifyQuoteLONG(on_quote)
SK.OnNotifyTicksLONG(on_tick)

login=SK.Login(USER,PASSWORD,AUTH)
print("[LOGIN]",login.Code,msg(login.Code),flush=True)
if login.Code!=0: raise SystemExit(login.Code)

rc=SK.ManageServerConnection(USER,0,1)
print("[CONNECT]",rc,msg(rc),flush=True)
ready.wait(20)
print("[READY]",ready.is_set(),flush=True)

for m in [2,7,13]:
    try:
        rc=SK.LoadCommodity(m)
        print("[LOAD]",m,rc,msg(rc),flush=True)
    except Exception as e:
        print("[LOAD_EXC]",m,repr(e),flush=True)
    time.sleep(0.5)

# probe direct stock list return
for m in [2,3,7,13]:
    try:
        p=SK.RequestStockList(m)
        raw=p.RawData()
        print("[STOCKLIST]",m,"len",len(raw),"head",repr(raw[:300]),flush=True)
        hits=[]
        for needle in ["TX00","MTX00","TMF","PBF","QEF","OWF","LXF","QFF","國巨","環球晶"]:
            if needle in raw: hits.append(needle)
        print("[STOCKLIST_HITS]",m,hits,flush=True)
        for key in ["TMF","微型","微台","微臺"]:
            if key in raw:
                p0=raw.find(key)
                print("[MICRO_CONTEXT]",key,repr(raw[max(0,p0-160):p0+650]),flush=True)
    except Exception as e:
        print("[STOCKLIST_EXC]",m,type(e).__name__,repr(e),flush=True)

time.sleep(1)

# Find YaoHua futures quote codes from market 2 catalog.
yaohua_codes=[]
try:
    p=SK.RequestStockList(2)
    raw=p.RawData()
    for rec in raw.replace("\\n",";").split(";"):
        if "燿華" in rec:
            print("[YAOHUA_REC]",repr(rec),flush=True)
            parts=rec.split(",")
            if parts and parts[0]:
                code=parts[0].split("%")[-1]
                if code and code not in yaohua_codes:
                    yaohua_codes.append(code)
except Exception as e:
    print("[YAOHUA_SEARCH_EXC]",repr(e),flush=True)

# Prefer the outright nearby contract, not calendar spreads.
symbols=[]
print("[YAOHUA_CODES]",symbols,flush=True)
# Find Innolux nearby futures code.
innolux_codes=[]
try:
    p=SK.RequestStockList(2)
    raw=p.RawData()
    for rec in raw.replace("\n",";").split(";"):
        if "群創" in rec:
            print("[INNOLUX_REC]",repr(rec),flush=True)
            parts=rec.split(",")
            if parts and parts[0]:
                code=parts[0].split("%")[-1]
                if code and code not in innolux_codes:
                    innolux_codes.append(code)
except Exception as e:
    print("[INNOLUX_SEARCH_EXC]",repr(e),flush=True)

symbols=[]
if "VBF00" in yaohua_codes: symbols.append("VBF00")
for code in innolux_codes:
    if "/" not in code and (code.endswith("00") or code.endswith("0000")):
        symbols.append(code)
        break
symbols.append("QEF00")
print("[FOCUS_SYMBOLS]",symbols,flush=True)
results=[]
def req(item,sym):
    try:
        a=SK.SKQuoteLib_RequestStocks(sym)
        print("[REQ_STOCKS]",sym,a,msg(a),flush=True)
    except Exception as e:
        a=None; print("[REQ_STOCKS_EXC]",sym,repr(e),flush=True)
    try:
        b=SK.SKQuoteLib_RequestTicks(item,sym)
        print("[REQ_TICKS]",item,sym,b,msg(b),flush=True)
    except Exception as e:
        b=None; print("[REQ_TICKS_EXC]",item,sym,repr(e),flush=True)
    results.append((item,sym,a,b))

for i,sym in enumerate(symbols, start=1):
    t=threading.Thread(target=req,args=(i,sym))
    t.start(); t.join()
    time.sleep(1.0)

time.sleep(10)
print("[SUMMARY_QUOTES]",sorted(set(s for _,s in quotes)),flush=True)
print("[SUMMARY_TICKS]",sorted(set(x["symbol"] for x in ticks)),flush=True)
print("[RESULTS]",results,flush=True)
