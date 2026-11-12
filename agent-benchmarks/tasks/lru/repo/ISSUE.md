# Bug report

Our `LRUCache` evicts the wrong item. After `put(a)`, `put(b)`, `get(a)`, `put(c)` with capacity 2, key `a` was evicted, but `a` was the most recently used. Updating an existing key also seems to count against capacity. Fix it.
