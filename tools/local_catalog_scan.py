import os, sys, time, threading

BASE = r"C:\Capital\SKDLLPythonTester"
if BASE not in sys.path:
    sys.path.insert(0, BASE)
from SKDLLPython import SK

USER=os.environ.get("CAPITAL_USER_ID","")
PASSWORD=os.environ.get("CAPITAL_PASSWORD","")
AUTH=int(os.environ.get("CAPITAL_AUTHORITY","0"))
ready=threading.Event()

def msg(c):
    try:return SK.GetMessage(c)
    except:return str(c)

def on_reply(uid,m): pass
def on_conn(uid,c):
    if "STOCKS_READY" in msg(c): ready.set()

SK.OnReplyMessage(on_reply)
SK.OnConnection(on_conn)
login=SK.Login(USER,PASSWORD,AUTH)
print("[LOGIN]",msg(login.Code),flush=True)
if login.Code!=0: raise SystemExit(login.Code)
rc=SK.ManageServerConnection(USER,0,1)
print("[CONNECT]",msg(rc),flush=True)
ready.wait(15)
print("[READY]",ready.is_set(),flush=True)
for m in [2,7,13,0,1]:
    try: print("[LOAD]",m,msg(SK.LoadCommodity(m)),flush=True)
    except Exception as e: print("[LOAD_EXC]",m,type(e).__name__,flush=True)
    time.sleep(0.5)

time.sleep(2)

roots=[BASE, os.environ.get("TEMP","")]
needles=[b"TXF",b"MTX",b"PBF",b"QEF",b"OWF",b"LXF"]
utf16=[x.decode().encode("utf-16le") for x in needles]
seen=set()
for root in roots:
    if not root or not os.path.isdir(root): continue
    for dp, dns, fns in os.walk(root):
        if "actions-runner" in dp: continue
        for fn in fns:
            p=os.path.join(dp,fn)
            try:
                size=os.path.getsize(p)
                if size<=0 or size>50*1024*1024: continue
                with open(p,"rb") as f:
                    data=f.read()
                hits=[n.decode() for n in needles if n in data]
                hits += [n.decode()+"(u16)" for n,u in zip(needles,utf16) if u in data]
                if hits:
                    rel=os.path.relpath(p,root)
                    key=(root,rel)
                    if key in seen: continue
                    seen.add(key)
                    print("[MATCH_FILE]", "BASE" if root==BASE else "TEMP", rel, "size=",size, "hits=",",".join(hits), flush=True)
                    # Print short ASCII contexts around hits only, sanitized to printable ASCII.
                    for n in needles:
                        pos=data.find(n)
                        if pos>=0:
                            lo=max(0,pos-80); hi=min(len(data),pos+220)
                            chunk=data[lo:hi]
                            safe="".join(chr(b) if 32<=b<127 else "." for b in chunk)
                            print("[CTX]",n.decode(),safe,flush=True)
            except Exception:
                pass
