class TokenBucket:
    def __init__(self, capacity, rate):
        self.capacity = capacity
        self.rate = rate
        self.tokens = 0
        self.last = 0
    def allow(self, now):
        self.tokens += int((now - self.last) * self.rate)
        self.last = now
        if self.tokens > 0:
            self.tokens -= 1
            return True
        return False
