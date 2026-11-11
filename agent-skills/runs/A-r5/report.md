# October 2026 Expense Report

**Period:** October 1–31, 2026  
**Source:** `expenses.csv`  
**Currency:** USD

## Summary

- **Total expenses:** $7,860.11
- **Included transactions:** 43
- **Average transaction:** $182.79
- **Largest expense:** $889.77 — Software (ID 1052, October 19)

## Spending by Category

| Category | Transactions | Amount (USD) | Share |
|:---------|-------------:|-------------:|------:|
| Software | 7 | $2,008.24 | 25.5% |
| Course | 4 | $1,077.36 | 13.7% |
| Hotel | 2 | $855.09 | 10.9% |
| License | 3 | $677.81 | 8.6% |
| SaaS | 3 | $628.46 | 8.0% |
| Taxi | 3 | $584.79 | 7.4% |
| Dinner | 3 | $514.04 | 6.5% |
| Airbnb | 3 | $470.41 | 6.0% |
| Flight | 3 | $376.61 | 4.8% |
| Lunch | 3 | $269.21 | 3.4% |
| Uber | 3 | $149.13 | 1.9% |
| Coffee | 4 | $144.82 | 1.8% |
| Books | 2 | $104.14 | 1.3% |
| **Total** | **43** | **$7,860.11** | **100.0%** |

*Percentages are rounded and may not sum exactly to 100%.*

## Transactions

| Date | ID | Category | Amount (USD) |
|:-----|---:|:---------|-------------:|
| 2026-10-01 | 1016 | Lunch | $37.67 |
| 2026-10-01 | 1030 | Software | $45.01 |
| 2026-10-02 | 1041 | Hotel | $319.68 |
| 2026-10-03 | 1043 | Taxi | $16.26 |
| 2026-10-03 | 1051 | Software | $30.74 |
| 2026-10-04 | 1046 | SaaS | $266.92 |
| 2026-10-05 | 1026 | Software | $828.09 |
| 2026-10-06 | 1003 | Coffee | $84.73 |
| 2026-10-06 | 1009 | Uber | $103.86 |
| 2026-10-07 | 1060 | Uber | $16.41 |
| 2026-10-08 | 1049 | License | $131.40 |
| 2026-10-10 | 1010 | Software | $147.27 |
| 2026-10-10 | 1032 | Flight | $48.87 |
| 2026-10-10 | 1047 | Flight | $60.38 |
| 2026-10-11 | 1028 | SaaS | $38.66 |
| 2026-10-11 | 1036 | Dinner | $4.83 |
| 2026-10-12 | 1029 | Coffee | $13.55 |
| 2026-10-12 | 1057 | Lunch | $43.16 |
| 2026-10-13 | 1012 | Software | $44.10 |
| 2026-10-13 | 1020 | Course | $268.29 |
| 2026-10-13 | 1053 | SaaS | $322.88 |
| 2026-10-13 | 1058 | Books | $67.06 |
| 2026-10-14 | 1035 | Coffee | $24.66 |
| 2026-10-15 | 1045 | Hotel | $535.41 |
| 2026-10-17 | 1039 | Airbnb | $45.07 |
| 2026-10-17 | 1048 | Airbnb | $47.60 |
| 2026-10-17 | 1055 | Taxi | $346.75 |
| 2026-10-18 | 1014 | Airbnb | $377.74 |
| 2026-10-18 | 1054 | Uber | $28.86 |
| 2026-10-19 | 1052 | Software | $889.77 |
| 2026-10-21 | 1001 | Coffee | $21.88 |
| 2026-10-21 | 1023 | Dinner | $251.32 |
| 2026-10-21 | 1037 | Lunch | $188.38 |
| 2026-10-22 | 1025 | License | $363.02 |
| 2026-10-24 | 1006 | Taxi | $221.78 |
| 2026-10-24 | 1007 | Flight | $267.36 |
| 2026-10-24 | 1031 | Software | $23.26 |
| 2026-10-25 | 1015 | Course | $316.13 |
| 2026-10-26 | 1017 | Dinner | $257.89 |
| 2026-10-26 | 1050 | License | $183.39 |
| 2026-10-27 | 1056 | Books | $37.08 |
| 2026-10-28 | 1022 | Course | $107.02 |
| 2026-10-28 | 1027 | Course | $385.92 |
| **Total** | | | **$7,860.11** |

## Notes and Reconciliation

The source file contains 64 expense rows. October 2026 rows with a non-void status were included after removing duplicate entries.

| Treatment | Rows |
|:----------|-----:|
| Included | 43 |
| Excluded — dated outside October 2026 | 12 |
| Excluded — void within October 2026 | 7 |
| Excluded — duplicate October entry | 2 |
| **Total source rows** | **64** |

- **Date range:** Only transactions dated October 1–31, 2026 were included. The 12 excluded out-of-period rows comprise nine September entries and three November entries.
- **Void entries:** Seven October rows are marked `void` and were excluded; they total $652.43. One out-of-period row (ID 1021) is also void and is counted under the out-of-period exclusion.
- **Duplicates:** IDs 1029, 1034, 1051, and 1005 each appear twice with identical values. Each unique transaction was counted once. Only 1029 and 1051 are included October entries, so only those affect the total.
- **Formatting:** Amounts were normalized from plain numbers and `$`/`USD` prefix or suffix formats. All amounts are in USD; no currency conversion was required. Category names were normalized for capitalization and whitespace.
