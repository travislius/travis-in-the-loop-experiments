# October 2026 Expense Report

**Period:** October 1–31, 2026  
**Source:** `expenses.csv`  
**Prepared:** November 10, 2026

## Summary

| Metric | Value |
|---|---:|
| Valid transactions | 43 |
| Total spend | **$7,860.11** |
| Average transaction | $182.79 |
| Largest transaction | $889.77 (Software, Oct 19) |
| Smallest transaction | $4.83 (Dinner, Oct 11) |
| Days with spending | 24 |

## Spending by Category

| Category | Amount | Share |
|---|---:|---:|
| Software | $2,008.24 | 25.5% |
| Course | $1,077.36 | 13.7% |
| Hotel | $855.09 | 10.9% |
| License | $677.81 | 8.6% |
| SaaS | $628.46 | 8.0% |
| Taxi | $584.79 | 7.4% |
| Dinner | $514.04 | 6.5% |
| Airbnb | $470.41 | 6.0% |
| Flight | $376.61 | 4.8% |
| Lunch | $269.21 | 3.4% |
| Uber | $149.13 | 1.9% |
| Coffee | $144.82 | 1.8% |
| Books | $104.14 | 1.3% |
| **Total** | **$7,860.11** | **100.0%** |

Software is the largest category at roughly a quarter of monthly spend, followed by courses and hotels. Together, the top three categories account for about half of the total.

## Daily Totals

| Date | Amount | Date | Amount |
|---|---:|---|---:|
| Oct 1 | $82.68 | Oct 15 | $535.41 |
| Oct 2 | $319.68 | Oct 17 | $439.42 |
| Oct 3 | $47.00 | Oct 18 | $406.60 |
| Oct 4 | $266.92 | Oct 19 | $889.77 |
| Oct 5 | $828.09 | Oct 21 | $461.58 |
| Oct 6 | $188.59 | Oct 22 | $363.02 |
| Oct 7 | $16.41 | Oct 24 | $512.40 |
| Oct 8 | $131.40 | Oct 25 | $316.13 |
| Oct 10 | $256.52 | Oct 26 | $441.28 |
| Oct 11 | $43.49 | Oct 27 | $37.08 |
| Oct 12 | $56.71 | Oct 28 | $492.94 |
| Oct 13 | $702.33 | | |
| Oct 14 | $24.66 | | |

## Transaction Detail

| Date | ID | Category | Amount |
|---|---|---|---:|
| Oct 1 | 1016 | Lunch | $37.67 |
| Oct 1 | 1030 | Software | $45.01 |
| Oct 2 | 1041 | Hotel | $319.68 |
| Oct 3 | 1043 | Taxi | $16.26 |
| Oct 3 | 1051 | Software | $30.74 |
| Oct 4 | 1046 | SaaS | $266.92 |
| Oct 5 | 1026 | Software | $828.09 |
| Oct 6 | 1003 | Coffee | $84.73 |
| Oct 6 | 1009 | Uber | $103.86 |
| Oct 7 | 1060 | Uber | $16.41 |
| Oct 8 | 1049 | License | $131.40 |
| Oct 10 | 1010 | Software | $147.27 |
| Oct 10 | 1032 | Flight | $48.87 |
| Oct 10 | 1047 | Flight | $60.38 |
| Oct 11 | 1028 | SaaS | $38.66 |
| Oct 11 | 1036 | Dinner | $4.83 |
| Oct 12 | 1029 | Coffee | $13.55 |
| Oct 12 | 1057 | Lunch | $43.16 |
| Oct 13 | 1012 | Software | $44.10 |
| Oct 13 | 1020 | Course | $268.29 |
| Oct 13 | 1053 | SaaS | $322.88 |
| Oct 13 | 1058 | Books | $67.06 |
| Oct 14 | 1035 | Coffee | $24.66 |
| Oct 15 | 1045 | Hotel | $535.41 |
| Oct 17 | 1039 | Airbnb | $45.07 |
| Oct 17 | 1048 | Airbnb | $47.60 |
| Oct 17 | 1055 | Taxi | $346.75 |
| Oct 18 | 1014 | Airbnb | $377.74 |
| Oct 18 | 1054 | Uber | $28.86 |
| Oct 19 | 1052 | Software | $889.77 |
| Oct 21 | 1001 | Coffee | $21.88 |
| Oct 21 | 1023 | Dinner | $251.32 |
| Oct 21 | 1037 | Lunch | $188.38 |
| Oct 22 | 1025 | License | $363.02 |
| Oct 24 | 1006 | Taxi | $221.78 |
| Oct 24 | 1007 | Flight | $267.36 |
| Oct 24 | 1031 | Software | $23.26 |
| Oct 25 | 1015 | Course | $316.13 |
| Oct 26 | 1017 | Dinner | $257.89 |
| Oct 26 | 1050 | License | $183.39 |
| Oct 27 | 1056 | Books | $37.08 |
| Oct 28 | 1022 | Course | $107.02 |
| Oct 28 | 1027 | Course | $385.92 |
| **Total** | | | **$7,860.11** |

## Data Cleaning Notes

The source file contained 64 rows. The report includes 43 valid October charges after applying these rules:

- **Duplicates:** 4 exact duplicate rows were removed (IDs 1034, 1029, 1051, and 1005).
- **Voided transactions:** 8 rows marked `void` were excluded, including 6 dated in October (IDs 1038, 1013, 1005, 1024, 1004, 1008).
- **Out of period:** 9 valid charges dated in September or November 2026 were excluded, along with 1 voided September charge.
- **Normalization:** Category names were trimmed and standardized to title case (e.g. ` software ` → Software); amounts in `$`, `USD`, and plain-number formats were converted to a single numeric value; dates in `M/D/YYYY`, `D Mon YYYY`, and `YYYY-MM-DD` formats were parsed to a common date.
