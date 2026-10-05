import os,re,zipfile,html
temp=os.environ.get("TEMP","")
p=None
for dp,dns,fns in os.walk(temp):
    for fn in fns:
        if fn.lower().endswith(".docx") and "2.13.58" in fn:
            p=os.path.join(dp,fn); break
    if p: break
if not p: raise SystemExit("no doc")
with zipfile.ZipFile(p) as z:
    xml=z.read("word/document.xml").decode("utf-8","ignore")
text=re.sub(r"<w:tab[^>]*/>","\t",xml)
text=re.sub(r"</w:p>","\n",text)
text=re.sub(r"<[^>]+>","",text)
text=html.unescape(text)
text=re.sub(r"[ \t]+"," ",text)
for term in ["SKQuoteLib_RequestStockList","sMarketNo","市場別代號"]:
    print("\n==",term,"==")
    ms=list(re.finditer(re.escape(term),text,re.I))
    for m in ms[:8]:
        pos=m.start()
        print(text[max(0,pos-700):min(len(text),pos+1800)].replace("\n"," | "))
