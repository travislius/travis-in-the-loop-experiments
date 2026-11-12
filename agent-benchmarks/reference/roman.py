import re
V={"I":1,"V":5,"X":10,"L":50,"C":100,"D":500,"M":1000}
P=re.compile(r"^M{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$")
def from_roman(s):
    s=s.upper()
    if not s or not P.match(s): raise ValueError(s)
    t=0
    for i,ch in enumerate(s):
        v=V[ch]; t+= -v if i+1<len(s) and V[s[i+1]]>v else v
    return t
