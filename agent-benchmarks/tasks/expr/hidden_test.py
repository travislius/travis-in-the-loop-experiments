import pytest
from calc import evaluate as e
def test_basic(): assert e("1 + 2 * 3")==7
def test_paren(): assert e("(1+2)*3")==9
def test_left(): assert e("8/4/2")==1 and e("10-4-3")==3
def test_pow_right(): assert e("2^3^2")==512
def test_unary_pow(): assert e("-2^2")==-4
def test_unary_mul(): assert e("2*-3")==-6 and e("--3")==3
def test_dec(): assert abs(e(".5 + 0.25")-0.75)<1e-12
def test_div(): assert e("7/2")==3.5
def test_zero():
    with pytest.raises(ZeroDivisionError): e("1/(2-2)")
@pytest.mark.parametrize("bad",["2+","(1+2","1 2","","2**3","abc","()"])
def test_bad(bad):
    with pytest.raises(ValueError): e(bad)
def test_noeval():
    import calc, inspect; src=inspect.getsource(calc); assert "eval(" not in src.replace("evaluate(","") and "import ast" not in src
