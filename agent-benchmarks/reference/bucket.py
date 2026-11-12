class TokenBucket:
    def __init__(self,capacity,rate): self.capacity=capacity; self.rate=rate; self.tokens=float(capacity); self.last=None
    def allow(self,now):
        if self.last is not None: self.tokens=min(self.capacity,self.tokens+(now-self.last)*self.rate)
        self.last=now
        if self.tokens>=1-1e-9: self.tokens-=1; return True
        return False
