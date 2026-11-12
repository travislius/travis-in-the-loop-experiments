import pytest
from roman import from_roman as r
def test_ok():
    assert r("XIV")==14 and r("MCMXCIV")==1994 and r("MMMCMXCIX")==3999 and r("xiv")==14 and r("XL")==40
@pytest.mark.parametrize("bad",["IIII","VX","IC","XM","VV","MMMM","","IL","LL","IXI","ABC","XCX"])
def test_bad(bad):
    with pytest.raises(ValueError): r(bad)
