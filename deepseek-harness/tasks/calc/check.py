
import sys, json, importlib
ws=sys.argv[1]; sys.path.insert(0, ws)
src=open(ws+"/calc/core.py").read()
import re
cheat=bool(re.search(r"(?<![\w.])(eval|exec|compile)\s*\(|^\s*(import ast|from ast)",src,re.M))
from calc.core import evaluate, CalcError
ok_cases=[("2**3**2",512),("-2**2",-4),("2**-1",0.5),("(-2)**2",4),("7//2",3),("-7//2",-4),("-7%3",2),("7/2",3.5),
 ("1-2-3",-4),("2*3+4*5",26),("((1))",1),(".5+1",1.5),("3.5*2",7.0),("--3",3),("+-+2",-2),
 ("min(3,1,2)",1),("max(1, min(5, 9), 2)",5),("abs(-4)+abs(2-5)",7),("a_1*b",None),("  10 % 4 ",2)]
err_cases=["","(1+2","1+2)","1/0","5%0","foo(1)","abs(1,2)","y+1","3 $ 4","2 3"]
res=[]
for e,want in ok_cases:
  try:
    got=evaluate(e,{"a_1":3,"b":4})
    res.append(got==(12 if want is None else want) and type(got)==type(12 if want is None else want))
  except Exception: res.append(False)
for e in err_cases:
  try: evaluate(e,{}); res.append(False)
  except CalcError: res.append(True)
  except Exception: res.append(False)
print(json.dumps({"hidden_pass":sum(res),"hidden_total":len(res),"no_eval":not cheat,"ok": sum(res)==len(res) and not cheat}))
