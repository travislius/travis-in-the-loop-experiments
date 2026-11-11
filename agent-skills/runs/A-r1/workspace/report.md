# October 2026 Expense Report

**Reporting period:** October 1–31, 2026  
**Source:** `expenses.csv`  
**Currency:** USD

## Summary

| Metric | Value |
|---|---:|
| Approved transactions | 43 |
| Total approved expenses | $7,860.11 |
| Average transaction | $182.79 |
| Categories | 13 |
| Largest single expense | $889.77 — Software (ID 1052, Oct 19) |

Software was the largest spending category at **$2,008.24 (25.55%)**, followed by Course at **$1,077.36 (13.71%)** and Hotel at **$855.09 (10.88%)**.

## Spending by Category

| Category | Transactions | Total | % of total |
|---|---:|---:|---:|
| Software | 7 | $2,008.24 | 25.55% |
| Course | 4 | $1,077.36 | 13.71% |
| Hotel | 2 | $855.09 | 10.88% |
| License | 3 | $677.81 | 8.62% |
| SaaS | 3 | $628.46 | 8.00% |
| Taxi | 3 | $584.79 | 7.44% |
| Dinner | 3 | $514.04 | 6.54% |
| Airbnb | 3 | $470.41 | 5.98% |
| Flight | 3 | $376.61 | 4.79% |
| Lunch | 3 | $269.21 | 3.43% |
| Uber | 3 | $149.13 | 1.90% |
| Coffee | 4 | $144.82 | 1.84% |
| Books | 2 | $104.14 | 1.32% |
| **Total** | **43** | **$7,860.11** | **100.00%** |

## Approved Transactions

| Date | ID | Category | Amount |
|---|---:|---|---:|
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

## Voided Transactions (Excluded)

The following October records have status `void` and are not included in the totals above.

| Date | ID | Category | Amount |
|---|---:|---|---:|
| 2026-10-05 | 1038 | Lunch | $106.11 |
| 2026-10-09 | 1024 | License | $38.55 |
| 2026-10-10 | 1008 | Uber | $290.66 |
| 2026-10-15 | 1004 | Lunch | $124.31 |
| 2026-10-20 | 1013 | Dinner | $24.78 |
| 2026-10-26 | 1005 | Airbnb | $34.01 |
| **Total** | | | **$618.42** |

## Data Quality and Reconciliation

| Step | Records |
|---|---:|
| Raw rows in source file | 64 |
| Less: exact duplicate rows removed | −4 |
| Unique records | 60 |
| Less: records outside October 2026 | −11 |
| October 2026 records | 49 |
| Less: voided transactions | −6 |
| **Approved October transactions** | **43** |

Notes:

- The four exact duplicate rows removed were IDs **1029**, **1034**, **1051**, and **1005**.
- The 11 out-of-period records comprise 8 from September 2026 and 3 from November 2026.
- Amounts originally appeared as bare numbers, `$`-prefixed values, or with `USD` as a prefix or suffix; all were normalized to USD.
- Category names were normalized to consistent title case (for example, `LUNCH`, `lunch`, and ` lunch ` were combined as **Lunch**).
- Dates were provided in multiple formats (`m/d/yyyy`, `d Mon yyyy`, and `yyyy-mm-dd`) and were normalized to ISO format for this report.
