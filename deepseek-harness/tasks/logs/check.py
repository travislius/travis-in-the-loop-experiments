
import sys,json
ws,truth=sys.argv[1],json.load(open(sys.argv[2]))
try: out=json.load(open(ws+"/incident.json"))
except Exception as e: print(json.dumps({"ok":False,"fields":0,"error":str(e)})); sys.exit()
f={k: out.get(k)==truth[k] for k in truth}
print(json.dumps({"ok":all(f.values()),"fields":sum(f.values()),"fields_total":len(f),**{"match_"+k:v for k,v in f.items()}}))
