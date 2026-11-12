import re
TOK=re.compile(r"\s*(?:(\d+\.\d*|\.\d+|\d+)|(.))")
def evaluate(s):
    toks=[]; pos=0; s2=s
    for mt in TOK.finditer(s):
        if mt.group(1): toks.append(("n",float(mt.group(1))))
        elif mt.group(2):
            if mt.group(2) not in "+-*/^()": raise ValueError(s)
            toks.append(("o",mt.group(2)))
    toks.append(("e",None)); i=[0]
    def peek(): return toks[i[0]]
    def take(): t=toks[i[0]]; i[0]+=1; return t
    def expr():
        v=term()
        while peek()==("o","+") or peek()==("o","-"):
            op=take()[1]; r=term(); v=v+r if op=="+" else v-r
        return v
    def term():
        v=unary()
        while peek()==("o","*") or peek()==("o","/"):
            op=take()[1]; r=unary(); v=v*r if op=="*" else v/r
        return v
    def unary():
        if peek()==("o","-"): take(); return -unary()
        return power()
    def power():
        b=atom()
        if peek()==("o","^"): take(); return b**unary()
        return b
    def atom():
        t=take()
        if t[0]=="n": return t[1]
        if t==("o","("):
            v=expr()
            if take()!=("o",")"): raise ValueError(s)
            return v
        raise ValueError(s)
    v=expr()
    if peek()[0]!="e": raise ValueError(s)
    return v
