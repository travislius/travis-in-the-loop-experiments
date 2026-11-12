import re
def _seg(p):
    out=""; i=0
    while i<len(p):
        c=p[i]
        if c=="\\" and i+1<len(p): out+=re.escape(p[i+1]); i+=2; continue
        if c=="*": out+="[^/]*"
        elif c=="?": out+="[^/]"
        elif c=="[" and p.find("]",i+1)>0:
            j=p.find("]",i+1); body=p[i+1:j]
            if body.startswith("!"): out+="[^/"+body[1:]+"]"
            else: out+="(?!/)["+body+"]"
            i=j
        else: out+=re.escape(c)
        i+=1
    return out
def match(pattern,path):
    segs=pattern.split("/"); rx=""
    for k,sg in enumerate(segs):
        last=k==len(segs)-1
        if sg=="**": rx+="(?:.+)" if last else "(?:[^/]+/)*"
        else: rx+=_seg(sg)+("" if last else "/")
    return re.fullmatch(rx,path) is not None
