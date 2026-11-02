
import sys,json
ws,truth=sys.argv[1],json.load(open(sys.argv[2]))
try: out=json.load(open(ws+"/summary.json"))
except Exception as e: print(json.dumps({"ok":False,"error":str(e)})); sys.exit()
tot=out.get("totals",{}); mal=sorted(out.get("malformed",[]))
print(json.dumps({"ok":tot==truth["totals"] and mal==truth["malformed"],"totals_match":tot==truth["totals"],"malformed_match":mal==truth["malformed"],"refund_excluded":"refund" not in tot}))
