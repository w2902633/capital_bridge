import os
temp=os.environ.get("TEMP","")
for dp,dns,fns in os.walk(temp):
    if os.path.basename(dp)=="CapitalAPI_2.13.58":
        root=dp
        break
else:
    raise SystemExit("not found")
for dp,dns,fns in os.walk(root):
    rel=os.path.relpath(dp,root)
    depth=0 if rel=="." else rel.count(os.sep)+1
    if depth<=3:
        for fn in fns:
            p=os.path.join(dp,fn)
            try:size=os.path.getsize(p)
            except:size=-1
            print(os.path.relpath(p,root), size)
