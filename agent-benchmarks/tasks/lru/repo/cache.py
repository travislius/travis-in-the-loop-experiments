class LRUCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.data = {}
        self.order = []
    def get(self, key, default=None):
        return self.data.get(key, default)
    def put(self, key, value):
        self.data[key] = value
        self.order.append(key)
        if len(self.order) > self.capacity:
            old = self.order.pop(0)
            self.data.pop(old, None)
