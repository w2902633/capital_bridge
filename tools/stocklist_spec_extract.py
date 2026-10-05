import os,re,zipfile,html
temp=os.environ.get("TEMP","")
docs=[]
for dp,dns,fns in os.walk(temp):
    for fn in fns:
        if fn.lower().endswith(".docx") and "2.13.58" in fn:
            docs.append(os.path.join(dp,fn))
if not docs: raise SystemExit("no doc")
p=docs[0]
with zipfile.ZipFile(p) as z:
    xml=z.read("word/document.xml").decode("utf-8","ignore")
text=re.sub(r"<w:tab[^>]*/>","\t",xml)
text=re.sub(r"</w:p>","\n",text)
text=re.sub(r"<[^>]+>","",text)
text=html.unescape(text)
text=re.sub(r"[ \t]+"," ",text)
terms=["SKQuoteLib_RequestStockList","OnNotifyCommodityListWithTypeNo","OnNotifyStockList","商品資料(商品代碼及商品中文名稱)"]
for term in terms:
    print("\n===",term,"===",flush=True)
    for m in list(re.finditer(re.escape(term),text,re.I))[:12]:
        pos=m.start(); lo=max(0,pos-900); hi=min(len(text),pos+2200)
        print(text[lo:hi].replace("\n"," | "),flush=True)
