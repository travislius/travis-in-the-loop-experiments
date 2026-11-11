---
name: expense-report
description: Build the monthly expense report (report.md) from an expenses.csv export, in the finance team's house format. Use whenever someone asks for an expense report, expense summary or monthly spend report.
---

# Expense report (house format)

Finance reads these reports with a script, so the format must match exactly.

## Do this
Run the bundled script instead of computing by hand:

```
python3 <this skill's directory>/scripts/build_report.py expenses.csv --month 2026-10 > report.md
```

Then open report.md and confirm it has a title, a Total line, a category table and a Flags section.
Only if the script fails, follow the rules in the script's docstring and the format below by hand.

Output format — `report.md`, exactly this shape (no other lines, no extra commentary):

```
# Expense Report — October 2026
Total: $7,654.32

| Category | Items | Amount |
|---|---:|---:|
| Software | 12 | $3,210.00 |
| Travel | 9 | $1,100.50 |

## Flags
- #1042 $612.00 — over $500, receipt required
```

- Title uses an em dash (—) and the full month name.
- Category rows sorted by amount, largest first. Money always `$` + thousands commas + 2 decimals.
- Flags sorted by id ascending. If there are none, write `- none`.
