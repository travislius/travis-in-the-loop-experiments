from money import parse_amount as p
import pytest
def test_us(): assert p("$1,234.50")==1234.5
def test_paren(): assert p("(1,234.50)")==-1234.5
def test_neg(): assert p("-12")==-12.0
def test_eu(): assert p("1.234,50 €")==1234.5
def test_eu2(): assert p("EUR 3,5")==3.5
def test_plain(): assert p("7")==7.0
def test_us_thousands_only(): assert p("1,234")==1234.0
