
import unittest
from calc.core import evaluate, CalcError
class T(unittest.TestCase):
    def test_add(self): self.assertEqual(evaluate("1 + 2 * 3"), 7)
    def test_paren(self): self.assertEqual(evaluate("(1 + 2) * 3"), 9)
    def test_var(self): self.assertEqual(evaluate("x * 2", {"x": 5}), 10)
    def test_err(self):
        with self.assertRaises(CalcError): evaluate("1 +")
if __name__ == "__main__": unittest.main()
