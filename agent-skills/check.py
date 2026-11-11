#!/usr/bin/env python3
"""Deterministic checker. Usage: check.py <workspace> <truth.json>  -> JSON score."""
import json, re, sys
from pathlib import Path
ws, truth = Path(sys.argv[1]), json.load(open(sys.argv[2]))
money = lambda c: f"${c // 100:,}.{c % 100:02}"
exp = ["# Expense Report — October 2026", f"Total: {money(truth['total_cents'])}", "", "| Category | Items | Amount |", "|---|---:|---:|"]
exp += [f"| {k} | {n} | {money(s)} |" for k, n, s in truth["categories"]]
exp += ["", "## Flags"] + [f"- #{i} {money(next(0 for _ in [0]) if False else 0)}" for i in []]
p = ws / "report.md"
r = {"report_exists": p.exists()}
txt = p.read_text() if p.exists() else ""
allnums = txt.replace(",", "")
cents_in = lambda c: f"{c // 100}.{c % 100:02}" in allnums
r["total_correct"] = cents_in(truth["total_cents"])
r["categories_correct"] = sum(1 for k, n, s in truth["categories"] if re.search(re.escape(k) + r".{0,40}?" + re.escape(f"{s // 100:,}.{s % 100:02}").replace(",", ",?"), txt))
r["categories_total"] = len(truth["categories"])
ids = set(int(x) for x in re.findall(r"#?\b(1\d{3})\b", txt.split("Flag")[-1] if "Flag" in txt or "flag" in txt.lower() else ""))
r["flags_correct"] = ids == set(truth["flags"])
lines = [l.rstrip() for l in txt.strip().splitlines()]
head_ok = lines[:5] == exp[:5]
rows_ok = lines[5:5 + len(truth["categories"])] == exp[5:5 + len(truth["categories"])]
r["format_title_total_table"] = head_ok and rows_ok
r["format_flags_section"] = "## Flags" in lines and all(any(re.fullmatch(rf"- #{i} \$[\d,]+\.\d\d — over \$500, receipt required", l) for l in lines) for i in truth["flags"])
r["numbers_correct"] = r["total_correct"] and r["categories_correct"] == r["categories_total"] and r["flags_correct"]
r["house_format_exact"] = r["format_title_total_table"] and r["format_flags_section"] and len(lines) == 5 + len(truth["categories"]) + 2 + len(truth["flags"])
r["pass"] = r["numbers_correct"] and r["house_format_exact"]
print(json.dumps(r))
