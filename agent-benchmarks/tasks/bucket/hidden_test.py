from ratelimit import TokenBucket
def test_starts_full():
    b=TokenBucket(3,1.0); assert [b.allow(100.0) for _ in range(4)]==[True,True,True,False]
def test_fractional():
    b=TokenBucket(1,2.0); assert b.allow(10.0); assert not b.allow(10.2); assert b.allow(10.5)
def test_cap():
    b=TokenBucket(2,1.0); b.allow(0.0); b.allow(0.0)
    assert [b.allow(1000.0) for _ in range(3)]==[True,True,False]
def test_small_steps():
    b=TokenBucket(1,1.0); b.allow(0.0)
    r=[b.allow(0.0+0.25*i) for i in range(1,5)]; assert r==[False,False,False,True]
