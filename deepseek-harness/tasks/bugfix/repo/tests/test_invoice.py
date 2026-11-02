
import unittest
from datetime import date
from invoice.money import to_cents, apply_discount
from invoice.dates import parse_due
from invoice.total import invoice_total

class T(unittest.TestCase):
    def test_cents_basic(self): self.assertEqual(to_cents("12.34"), 1234)
    def test_cents_round(self): self.assertEqual(to_cents("0.125"), 13)
    def test_cents_float(self): self.assertEqual(to_cents(19.995), 2000)
    def test_discount_round(self): self.assertEqual(apply_discount(999, 15), 849)
    def test_discount_bounds(self):
        with self.assertRaises(ValueError): apply_discount(100, 101)
    def test_iso(self): self.assertEqual(parse_due("2026-11-01"), date(2026,11,1))
    def test_us(self): self.assertEqual(parse_due("11/02/2026"), date(2026,11,2))
    def test_total(self): self.assertEqual(invoice_total([("10.00",2),("5.50",1)], 10, 0.1), 2525)
if __name__ == "__main__": unittest.main()
