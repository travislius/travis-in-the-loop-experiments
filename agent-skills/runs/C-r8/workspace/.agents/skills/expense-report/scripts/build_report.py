#!/usr/bin/env python3
"""Build the house-format monthly expense report.

Usage: build_report.py expenses.csv --month YYYY-MM > report.md
Rules: report month only; skip status=void; dedupe by id; integer cents;
category aliases -> house categories; flag single expenses > $500.00.
"""
import csv, re, sys, datetime, argparse
ALIAS = {"taxi": "Travel", "uber": "Travel", "flight": "Travel", "hotel": "Lodging", "airbnb": "Lodging",
         "lunch": "Meals", "dinner": "Meals", "coffee": "Meals", "saas": "Software", "software": "Software",
         "license": "Software", "books": "Learning", "course": "Learning"}
MON = {m: i for i, m in enumerate(["jan","feb","mar","apr","may","jun","jul","aug","sep","oct","nov","dec"], 1)}
def parse_date(s):
    s = s.strip()
    if m := re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", s): y, mo, d = m.groups()
    elif m := re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", s): mo, d, y = m.groups()
    elif m := re.fullmatch(r"(\d{1,2}) ([A-Za-z]{3})\w* (\d{4})", s): d, mo, y = m.groups(); mo = MON[mo.lower()[:3]]
    else: raise ValueError("bad date: " + s)
    return datetime.date(int(y), int(mo), int(d))
def cents(s):
    s = re.sub(r"USD|\$|,|\s", "", s)
    whole, _, frac = s.partition(".")
    return int(whole) * 100 + int((frac + "00")[:2])
money = lambda c: f"${c // 100:,}.{c % 100:02}"
ap = argparse.ArgumentParser(); ap.add_argument("csv"); ap.add_argument("--month", required=True); a = ap.parse_args()
y, m = map(int, a.month.split("-"))
seen, cats, flags, total = set(), {}, [], 0
for r in csv.DictReader(open(a.csv, newline="")):
    if r["id"] in seen: continue
    seen.add(r["id"])
    d = parse_date(r["date"])
    if (d.year, d.month) != (y, m) or r["status"].strip().lower() == "void": continue
    c = cents(r["amount"]); cat = ALIAS[r["category"].strip().lower()]
    n, s = cats.get(cat, (0, 0)); cats[cat] = (n + 1, s + c); total += c
    if c > 50000: flags.append((int(r["id"]), c))
print(f"# Expense Report — {datetime.date(y, m, 1):%B %Y}")
print(f"Total: {money(total)}\n")
print("| Category | Items | Amount |\n|---|---:|---:|")
for k, (n, s) in sorted(cats.items(), key=lambda kv: (-kv[1][1], kv[0])): print(f"| {k} | {n} | {money(s)} |")
print("\n## Flags")
for i, c in sorted(flags): print(f"- #{i} {money(c)} — over $500, receipt required")
if not flags: print("- none")
