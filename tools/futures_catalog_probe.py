import os
import sys
import time
import ctypes
import struct

BASE = r"C:\Capital\SKDLLPythonTester"
DLL = os.path.join(BASE, "libs", "SKCOM.dll")
if BASE not in sys.path:
    sys.path.insert(0, BASE)

from SKDLLPython import SK

USER = os.environ.get("CAPITAL_USER_ID", "")
PASSWORD = os.environ.get("CAPITAL_PASSWORD", "")
AUTHORITY = int(os.environ.get("CAPITAL_AUTHORITY", "0"))

def safe(s):
    if s is None:
        return ""
    return str(s).encode("ascii", "backslashreplace").decode("ascii")

def msg(code):
    try:
        return SK.GetMessage(code)
    except Exception:
        return str(code)

def pe_exports(path):
    data = open(path, "rb").read()
    if data[:2] != b"MZ":
        return []
    pe_off = struct.unpack_from("<I", data, 0x3C)[0]
    if data[pe_off:pe_off+4] != b"PE\0\0":
        return []
    coff = pe_off + 4
    num_sections = struct.unpack_from("<H", data, coff + 2)[0]
    opt_size = struct.unpack_from("<H", data, coff + 16)[0]
    opt = coff + 20
    magic = struct.unpack_from("<H", data, opt)[0]
    dd = opt + (112 if magic == 0x20B else 96)
    export_rva, export_size = struct.unpack_from("<II", data, dd)
    sec_off = opt + opt_size
    sections = []
    for i in range(num_sections):
        o = sec_off + i * 40
        name = data[o:o+8].split(b"\0",1)[0].decode("ascii","ignore")
        vsize, vaddr, raw_size, raw_ptr = struct.unpack_from("<IIII", data, o+8)
        sections.append((name, vaddr, max(vsize, raw_size), raw_ptr))
    def rva_to_off(rva):
        for _, va, sz, rp in sections:
            if va <= rva < va + sz:
                return rp + (rva - va)
        raise ValueError(f"RVA not mapped: {rva:x}")
    if not export_rva:
        return []
    eo = rva_to_off(export_rva)
    vals = struct.unpack_from("<IIHHIIIIIII", data, eo)
    num_names = vals[7]
    addr_names_rva = vals[9]
    names_off = rva_to_off(addr_names_rva)
    out = []
    for i in range(num_names):
        nrva = struct.unpack_from("<I", data, names_off + 4*i)[0]
        no = rva_to_off(nrva)
        end = data.find(b"\0", no)
        out.append(data[no:end].decode("ascii","ignore"))
    return out

events = []
def on_reply(login_id, message):
    print("[OnReplyMessage]", safe(message))

def on_connection(login_id, code):
    text = msg(code)
    events.append(text)
    print("[OnConnection]", safe(text))

SK.OnReplyMessage(on_reply)
SK.OnConnection(on_connection)

if not USER or not PASSWORD:
    raise SystemExit("Missing credentials")

login = SK.Login(USER, PASSWORD, AUTHORITY)
print("[Login]", msg(login.Code))
if login.Code != 0:
    raise SystemExit(login.Code)

code = SK.ManageServerConnection(USER, 0, 1)
print("[Domestic quote connection]", msg(code))
if code != 0:
    raise SystemExit(code)

deadline = time.time() + 12
while time.time() < deadline and not any("STOCKS_READY" in x for x in events):
    time.sleep(0.25)

print("\n=== DLL EXPORT DISCOVERY ===")
exports = pe_exports(DLL)
keywords = ("stocklist","stock","quote","future","commodity","market")
hits = sorted([x for x in exports if any(k in x.lower() for k in keywords)])
print("export_count=", len(exports), "filtered_count=", len(hits))
for name in hits:
    print(name)

print("\n=== CALLBACK/API PRESENCE ===")
for name in [
    "RegisterEventOnNotifyStockList",
    "SKQuoteLib_RequestStockList",
    "SKQuoteLib_RequestStocks",
    "SKQuoteLib_RequestTicks",
    "SKQuoteLib_GetStockByStockNo",
    "LoadCommodity",
]:
    print(name, hasattr(SK._dll, name))

def raw_stocklist(market):
    try:
        ptr = SK._dll.SKQuoteLib_RequestStockList(market)
        if not ptr:
            return ""
        if isinstance(ptr, (bytes, bytearray)):
            raw = bytes(ptr)
        else:
            raw = ctypes.cast(ptr, ctypes.c_char_p).value or b""
        try:
            return raw.decode("ansi")
        except Exception:
            return raw.decode("cp950", errors="backslashreplace")
    except Exception as e:
        return "EXCEPTION:" + repr(e)

def inspect_stocklist(label, market):
    raw = raw_stocklist(market)
    print(f"[{label}] market={market} len={len(raw)} head={safe(raw[:500])}")
    for needle in ["QEF","PBF","TX","MTX","TMF","MXF","\u570b\u5de8","\u74b0\u7403\u6676"]:
        if needle in raw:
            idx = raw.find(needle)
            print(f"  HIT {safe(needle)} @ {idx}: {safe(raw[max(0,idx-120):idx+260])}")
    return raw

print("\n=== STOCK LIST PROBES ===")
# Baseline before additional loads.
for market in [2,7,9,13]:
    inspect_stocklist("baseline", market)

sequences = [
    ("load2", [2]),
    ("load7", [7]),
    ("load13_then2", [13,2]),
    ("load13_then7", [13,7]),
    ("load2_then13", [2,13]),
]
for label, seq in sequences:
    print(f"\n--- sequence {label}: {seq} ---")
    for m in seq:
        rc = SK.LoadCommodity(m)
        print(f"LoadCommodity({m}) => {msg(rc)}")
        time.sleep(2.0)
    for wait in [0,2,5,10]:
        if wait:
            time.sleep(wait)
        print(f"wait={wait}s")
        for market in [2,7,9,13]:
            inspect_stocklist(label, market)

print("\n=== DONE ===")
