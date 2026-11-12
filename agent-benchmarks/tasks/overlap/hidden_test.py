import datetime as d
from booking import overlaps
D=lambda n: d.date(2026,11,n)
def test_touch(): assert overlaps(D(1),D(5),D(5),D(9))
def test_touch_rev(): assert overlaps(D(5),D(9),D(1),D(5))
def test_apart(): assert not overlaps(D(1),D(4),D(5),D(9))
def test_inside(): assert overlaps(D(1),D(9),D(3),D(4))
def test_same_day(): assert overlaps(D(3),D(3),D(3),D(3))
