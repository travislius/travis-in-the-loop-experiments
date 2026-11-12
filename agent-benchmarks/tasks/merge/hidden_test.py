from intervals import merge_intervals as m
def test_unsorted(): assert m([[5,7],[1,3],[2,4]])==[[1,4],[5,7]]
def test_touch(): assert m([[1,3],[3,5]])==[[1,5]]
def test_nested(): assert m([[1,10],[2,3]])==[[1,10]]
def test_empty(): assert m([])==[]
def test_nomutate():
    x=[[3,4],[1,2]]; m(x); assert x==[[3,4],[1,2]]
