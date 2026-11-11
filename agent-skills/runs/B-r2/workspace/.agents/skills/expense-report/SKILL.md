---
name: expense-report
description: Build the monthly expense report (report.md) from an expenses.csv export, in the finance team's house format. Use whenever someone asks for an expense report, expense summary or monthly spend report.
---

# Expense report (house format)

Finance reads these reports with a script, so the format must match exactly.

Rules (all of them matter):
1. Only rows dated in the report month count. Dates come as `2026-10-07`, `10/7/2026` or `7 Oct 2026`.
2. Skip rows whose status is `void`.
3. The export sometimes repeats a row: count each `id` once.
4. Amounts look like `$1,234.50`, `1234.50`, `USD 1,234.50` or `1,234.50 USD`. Work in integer cents.
5. Map the raw category (case/space-insensitive) to the house category:
   taxi, uber, flight -> Travel · hotel, airbnb -> Lodging · lunch, dinner, coffee -> Meals ·
   saas, software, license -> Software · books, course -> Learning
6. Flag every single expense over $500.00 (strictly greater).

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

Check your numbers before you finish: re-add the category amounts and make sure they equal the total.
