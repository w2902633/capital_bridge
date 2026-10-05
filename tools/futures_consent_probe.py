import os,sys,time,threading,ctypes
BASE=r"C:\Capital\SKDLLPythonTester"
if BASE not in sys.path: sys.path.insert(0,BASE)
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
    print("[CONN]",c,msg(c),flush=True)
    if "STOCKS_READY" in msg(c): ready.set()

SK.OnReplyMessage(on_reply)
SK.OnConnection(on_conn)
login=SK.Login(USER,PASSWORD,AUTH)
print("[LOGIN]",login.Code,msg(login.Code),flush=True)
if login.Code!=0: raise SystemExit(login.Code)
rc=SK.ManageServerConnection(USER,0,1)
print("[MANAGE]",rc,msg(rc),flush=True)
ready.wait(15)
print("[READY]",ready.is_set(),flush=True)
for n in ["SKQuoteLib_GetStrikePrices","SKQuoteLib_IsConnected","SKQuoteLib_RequestFutureTradeInfo"]:
    print("[HAS]",n,hasattr(SK._dll,n),flush=True)

if hasattr(SK._dll,"SKQuoteLib_IsConnected"):
    fn=SK._dll.SKQuoteLib_IsConnected
    fn.argtypes=[]; fn.restype=ctypes.c_int
    v=fn()
    print("[IS_CONNECTED]",v,msg(v),flush=True)

if hasattr(SK._dll,"SKQuoteLib_GetStrikePrices"):
    fn=SK._dll.SKQuoteLib_GetStrikePrices
    fn.argtypes=[]; fn.restype=ctypes.c_int
    v=fn()
    print("[GET_STRIKE_PRICES]",v,msg(v),flush=True)
else:
    print("[GET_STRIKE_PRICES] export absent",flush=True)
