from cache import LRUCache
def test_recency():
    c=LRUCache(2); c.put('a',1); c.put('b',2); c.get('a'); c.put('c',3)
    assert c.get('a')==1 and c.get('b') is None and c.get('c')==3
def test_update():
    c=LRUCache(2); c.put('a',1); c.put('a',2); c.put('b',3)
    assert c.get('a')==2 and c.get('b')==3
def test_update_refresh():
    c=LRUCache(2); c.put('a',1); c.put('b',2); c.put('a',9); c.put('c',3)
    assert c.get('b') is None and c.get('a')==9
def test_cap1():
    c=LRUCache(1); c.put('x',1); c.put('y',2); assert c.get('x') is None and c.get('y')==2
