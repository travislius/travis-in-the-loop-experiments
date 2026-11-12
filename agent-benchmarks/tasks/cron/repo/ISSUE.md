# Bug report

`next_run(expr, after)` must return the first datetime strictly AFTER `after` (naive datetime, minute precision, seconds dropped) that matches a standard 5-field cron expression `minute hour day-of-month month day-of-week`. Currently it is a stub that ignores most syntax. Requirements:
- Fields support `*`, single numbers, lists `1,15,30`, ranges `1-5`, steps `*/15` and `10-40/10`.
- Day-of-week: 0-6 with 0 = Sunday; 7 also means Sunday.
- Standard Vixie-cron rule: if BOTH day-of-month and day-of-week are restricted (neither is `*`), a day matches if EITHER matches. If only one is restricted, only that one applies.
- Must handle month/year rollovers and February 29 (search up to 5 years ahead; raise ValueError if nothing matches).
Use only the Python standard library.
