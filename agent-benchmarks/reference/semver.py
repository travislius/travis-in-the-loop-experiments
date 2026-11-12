def _key(v):
    v=v.split("+")[0]; core,_,pre=v.partition("-")
    c=tuple(int(x) for x in core.split("."))
    if not pre: return (c,1,())
    ids=tuple((0,int(x),"") if x.isdigit() else (1,0,x) for x in pre.split("."))
    return (c,0,ids)
def compare(a,b):
    ka,kb=_key(a),_key(b); return (ka>kb)-(ka<kb)
