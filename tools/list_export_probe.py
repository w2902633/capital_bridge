import os, struct, sys
BASE=r"C:\Capital\SKDLLPythonTester"
DLL=os.path.join(BASE,"libs","SKCOM.dll")

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
            if va<=rva<va+sz:return rp+(rva-va)
        raise ValueError
    eo=off(erva)
    vals=struct.unpack_from("<IIHHIIIIIII",data,eo)
    nn=vals[7]; no=off(vals[9])
    out=[]
    for i in range(nn):
        nrva=struct.unpack_from("<I",data,no+i*4)[0]
        p=off(nrva); e=data.find(b"\0",p)
        out.append(data[p:e].decode("ascii","ignore"))
    return sorted(out)

ex=exports(DLL)
for n in ex:
    l=n.lower()
    if ("stocklist" in l or "commoditylist" in l or ("notify" in l and ("commodity" in l or "stock" in l))):
        print(n)
