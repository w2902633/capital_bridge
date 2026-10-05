import os
temp=os.environ.get("TEMP","")
roots=[]
for dp,dns,fns in os.walk(temp):
    base=os.path.basename(dp)
    if base=="CapitalAPI_2.13.58":
        roots.append(dp)
print("[ROOTS]",len(roots))
for root in roots[:5]:
    print("[ROOT]",root)
    for dp,dns,fns in os.walk(root):
        for fn in fns:
            low=fn.lower()
            if low.endswith((".py",".cs",".vb",".cpp",".h",".txt",".md",".xml",".json")):
                p=os.path.join(dp,fn)
                try:
                    data=open(p,"rb").read()
                except: continue
                for needle in [b"OnNotifyStockList",b"OnNotifyCommodityList",b"RequestStockList",b"GetStockByIndexLONG",b"EnterMonitorLONG"]:
                    if needle.lower() in data.lower():
                        print("[MATCH]",os.path.relpath(p,root),"needle=",needle.decode())
                        try:
                            txt=data.decode("utf-8","ignore")
                        except: txt=""
                        idx=txt.lower().find(needle.decode().lower())
                        if idx>=0:
                            s=txt[max(0,idx-500):idx+1400].replace("\r"," ").replace("\n"," | ")
                            print("[CTX]",s)
                        break
