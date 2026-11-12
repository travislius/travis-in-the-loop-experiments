from collections import OrderedDict
class LRUCache:
    def __init__(self,capacity): self.capacity=capacity; self.d=OrderedDict()
    def get(self,key,default=None):
        if key not in self.d: return default
        self.d.move_to_end(key); return self.d[key]
    def put(self,key,value):
        self.d[key]=value; self.d.move_to_end(key)
        while len(self.d)>self.capacity: self.d.popitem(last=False)
