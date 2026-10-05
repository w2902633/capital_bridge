import os, sys, struct, ctypes, threading, time, json
BASE = r"C:\Capital\SKDLLPythonTester"
DLL = os.path.join(BASE, "libs", "SKCOM.dll")
if BASE not in sys.path: sys.path.insert(0, BASE)
from SKDLLPython import SK

USER=os.environ.get("CAPITAL_USER_ID","")
PASSWORD=os.environ.get("CAPITAL_PASSWORD","")
AUTHORITY=int(os.environ.get("CAPITAL_AUTHORITY","0"))

def exports(path):
    data=open(path,"rb").read()
    pe=struct.unpack_from("<I",data,0x3c)[0]
    coff=pe+4
    nsec=struct.unpack_from("<H",data,coff+2)[0]
    optsz=struct.unpack_from("<H",data,coff+16)[0]
    opt=coff+20
    magic=struct.unpack_from("<H",data,opt)[0]
    dd=opt+(112 if magic==0x20b else 96)
    erva,_=struct.unpack_from("<II",data,dd)
    secoff=opt+optsz
    secs=[]
    for i in range(nsec):
        o=secoff+i*40
        vsize,vaddr,rsize,rptr=struct.unpack_from("<IIII",data,o+8)
        secs.append((vaddr,max(vsize,rsize),rptr))
    def off(rva):
        for va,sz,rp in secs:
            if va<=rva<va+sz: return rp+(rva-va)
        raise ValueError(rva)
    eo=off(erva)
    vals=struct.unpack_from("<IIHHIIIIIII",data,eo)
    nn=vals[7]; nrva=vals[9]; no=off(nrva)
    out=[]
    for i in range(nn):
        r=struct.unpack_from("<I",data,no+i*4)[0]
        p=off(r); e=data.find(b"\0",p)
        out.append(data[p:e].decode("ascii","ignore"))
    return sorted(out)

ex=exports(DLL)
print("=== MONITOR/QUOTE EXPORTS ===")
for n in ex:
    if any(k in n.lower() for k in ["monitor","quote","stockby","requesttick","requeststock"]):
        print(n)

print("=== DIRECT PRESENCE ===")
for n in ["SKQuoteLib_EnterMonitorLONG","SKQuoteLib_EnterMonitor","EnterMonitorLONG",
          "SKQuoteLib_GetStockByNoLONG","SKQuoteLib_GetStockByStockNo",
          "SKQuoteLib_RequestStocks","SKQuoteLib_RequestTicks"]:
    print(n, hasattr(SK._dll,n))

# Run current login first, then only call legacy entry point if it really exists.
ready=threading.Event(); ticks=[]; quotes=[]
def msg(c):
    try:return SK.GetMessage(c)
    except:return str(c)
def on_reply(uid,m): print("[REPLY]",str(m).encode("ascii","backslashreplace").decode("ascii"),flush=True)
def on_conn(uid,c):
    print("[CONN]",c,msg(c),flush=True)
    if c==3003 or "STOCKS_READY" in msg(c): ready.set()
def on_quote(m,s):
    quotes.append((m,s)); print("[QUOTE]",m,s,flush=True)
def on_tick(m,s,ptr,date,t,tm,bid,ask,close,qty,sim):
    row={"market":m,"symbol":s,"date":date,"time":t,"close":close,"qty":qty}
    ticks.append(row); print("[TICK]",json.dumps(row),flush=True)
SK.OnReplyMessage(on_reply); SK.OnConnection(on_conn); SK.OnNotifyQuoteLONG(on_quote); SK.OnNotifyTicksLONG(on_tick)

login=SK.Login(USER,PASSWORD,AUTHORITY)
print("[LOGIN]",msg(login.Code),flush=True)
if login.Code!=0: raise SystemExit(login.Code)

legacy=None
for n in ["SKQuoteLib_EnterMonitorLONG","SKQuoteLib_EnterMonitor","EnterMonitorLONG"]:
    if hasattr(SK._dll,n):
        legacy=n; break
print("[LEGACY_ENTRY]",legacy,flush=True)

if legacy:
    fn=getattr(SK._dll,legacy)
    try:
        fn.argtypes=[]
        fn.restype=ctypes.c_int
        rc=fn()
        print("[LEGACY_CALL_NOARGS]",legacy,rc,msg(rc),flush=True)
    except Exception as e:
        print("[LEGACY_CALL_NOARGS_EXC]",repr(e),flush=True)
else:
    print("[LEGACY_ENTRY_ABSENT] Falling back to current ManageServerConnection only as control.",flush=True)
    rc=SK.ManageServerConnection(USER,0,1)
    print("[MANAGE]",msg(rc),flush=True)

ready.wait(12)
print("[READY]",ready.is_set(),flush=True)
for m in [2,7,13]:
    try: print("[LOAD]",m,msg(SK.LoadCommodity(m)),flush=True)
    except Exception as e: print("[LOAD_EXC]",m,repr(e),flush=True)

time.sleep(1)
for i,sym in enumerate(["TX00","MTX00","PBF00","QEF00","6488"]):
    def req(item=i,s=sym):
        try: print("[REQ_STOCKS]",s,msg(SK.SKQuoteLib_RequestStocks(s)),flush=True)
        except Exception as e: print("[REQ_STOCKS_EXC]",s,repr(e),flush=True)
        try: print("[REQ_TICKS]",item,s,msg(SK.SKQuoteLib_RequestTicks(item,s)),flush=True)
        except Exception as e: print("[REQ_TICKS_EXC]",item,s,repr(e),flush=True)
    t=threading.Thread(target=req); t.start(); t.join(); time.sleep(1)

time.sleep(8)
print("[SUMMARY_QUOTES]",quotes,flush=True)
print("[SUMMARY_TICKS]",ticks,flush=True)
