#!/usr/bin/env python3
"""Regenerate task/repo/expenses.csv and task/truth.json (seed 1110)."""
import os, json, random, csv
H = os.path.dirname(os.path.abspath(__file__)); os.makedirs(H + "/task/repo", exist_ok=True)
random.seed(1110)
ALIAS = {"taxi":"Travel","uber":"Travel","flight":"Travel","hotel":"Lodging","airbnb":"Lodging","lunch":"Meals","dinner":"Meals","coffee":"Meals","saas":"Software","software":"Software","license":"Software","books":"Learning","course":"Learning"}
rows = []; truth = []
for i in range(1001, 1061):
    cat = random.choice(list(ALIAS)); month = random.choice([10]*9 + [9, 11]); day = random.randint(1, 28)
    cents = random.choice([random.randint(300, 9000), random.randint(9000, 40000), random.randint(50001, 90000) if random.random() < .15 else random.randint(1000, 5000)])
    status = random.choice(["ok"]*10 + ["void"]); fmt = random.choice(["iso", "us", "text"])
    d = {"iso": f"2026-{month:02}-{day:02}", "us": f"{month}/{day}/2026", "text": f"{day} {['','','','','','','','','','Sep','Oct','Nov'][month]} 2026"}[fmt]
    a = cents/100; amt = random.choice([f"${a:,.2f}", f"{a:.2f}", f"USD {a:,.2f}", f"{a:,.2f} USD"])
    c = random.choice([cat, cat.upper(), cat.title(), " " + cat + " "])
    rows.append([str(i), d, c, amt, status]); truth.append((i, month, ALIAS[cat], cents, status))
for i in random.sample(range(len(rows)), 4): rows.append(list(rows[i]))
random.shuffle(rows)
with open(H + "/task/repo/expenses.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["id", "date", "category", "amount", "status"]); w.writerows(rows)
valid = [t for t in truth if t[1] == 10 and t[4] == "ok"]; cats = {}
for t in valid: c = cats.setdefault(t[2], [0, 0]); c[0] += 1; c[1] += t[3]
exp = {"total_cents": sum(t[3] for t in valid), "categories": sorted([[k, v[0], v[1]] for k, v in cats.items()], key=lambda x: (-x[2], x[0])), "flags": sorted(t[0] for t in valid if t[3] > 50000), "n_rows": len(rows)}
json.dump(exp, open(H + "/task/truth.json", "w"), indent=1); print(exp)
