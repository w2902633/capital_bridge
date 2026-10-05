import os, re, zipfile, html

temp=os.environ.get("TEMP","")
terms=["PBF","QEF","LXF","OWF","TXF","MXF","TX00","MTX00","QuoteCode","商品代碼","報價代碼","下單代碼"]
cands=[]
for dp,dns,fns in os.walk(temp):
    for fn in fns:
        if fn.lower().endswith(".docx") and "2.13.58" in fn:
            cands.append(os.path.join(dp,fn))
print("[DOCX_COUNT]",len(cands),flush=True)
for p in cands[:5]:
    print("[DOCX]",os.path.basename(p),flush=True)
    try:
        with zipfile.ZipFile(p) as z:
            xml=z.read("word/document.xml").decode("utf-8","ignore")
        text=re.sub(r"<w:tab[^>]*/>","\t",xml)
        text=re.sub(r"</w:p>","\n",text)
        text=re.sub(r"<[^>]+>","",text)
        text=html.unescape(text)
        text=re.sub(r"[ \t]+"," ",text)
        for term in terms:
            starts=[m.start() for m in re.finditer(re.escape(term),text,re.I)]
            if starts:
                print(f"[TERM] {term} count={len(starts)}",flush=True)
                for pos in starts[:8]:
                    lo=max(0,pos-240); hi=min(len(text),pos+520)
                    snippet=text[lo:hi].replace("\r"," ").replace("\n"," | ")
                    print("[CTX]",snippet,flush=True)
    except Exception as e:
        print("[ERR]",type(e).__name__,flush=True)
