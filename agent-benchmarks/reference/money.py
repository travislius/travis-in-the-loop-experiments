import re
def parse_amount(s):
    s=s.strip(); neg=False
    if s.startswith("(") and s.endswith(")"): neg=True; s=s[1:-1]
    s=re.sub(r"[^0-9,.\-]","",s)
    if s.startswith("-"): neg=not neg if False else True; s=s[1:]
    if "," in s and "." in s:
        if s.rfind(",")>s.rfind("."): s=s.replace(".","").replace(",",".")
        else: s=s.replace(",","")
    elif "," in s:
        a,b=s.rsplit(",",1)
        s = s.replace(",","") if len(b)==3 else a.replace(",","")+"."+b
    v=float(s); return -v if neg else v
