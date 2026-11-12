import datetime as dt
def _field(f,lo,hi):
    out=set()
    for part in f.split(","):
        rng,_,step=part.partition("/"); step=int(step) if step else 1
        if rng=="*": a,b=lo,hi
        elif "-" in rng: a,b=map(int,rng.split("-"))
        else: a=int(rng); b=a if not _ else hi
        out.update(range(a,b+1,step))
    return out
def next_run(expr,after):
    mi,ho,dm,mo,dw=expr.split()
    M,Hh,DM,MO,DW=_field(mi,0,59),_field(ho,0,23),_field(dm,1,31),_field(mo,1,12),{d%7 for d in _field(dw,0,7)}
    t=after.replace(second=0,microsecond=0)+dt.timedelta(minutes=1); end=after+dt.timedelta(days=366*5)
    while t<=end:
        if t.month not in MO: t=(t.replace(day=1,hour=0,minute=0)+dt.timedelta(days=32)).replace(day=1); continue
        dom_ok=t.day in DM; dow_ok=((t.weekday()+1)%7) in DW
        day_ok=(dom_ok or dow_ok) if (dm!="*" and dw!="*") else (dom_ok if dm!="*" else dow_ok if dw!="*" else True)
        if not day_ok: t=t.replace(hour=0,minute=0)+dt.timedelta(days=1); continue
        if t.hour not in Hh: t=t.replace(minute=0)+dt.timedelta(hours=1); continue
        if t.minute in M: return t
        t+=dt.timedelta(minutes=1)
    raise ValueError(expr)
