# Bug report

`parse_amount()` fails on real bank exports. It must handle: `'$1,234.50'` -> 1234.5, accounting negatives `'(1,234.50)'` -> -1234.5, `'-12'` -> -12.0, European format `'1.234,50 €'` -> 1234.5, and `'EUR 3,5'` -> 3.5. Return a float. Fix it.
