# Bug report

Our `TokenBucket` rate limiter lets bursts through and sometimes never refills. Capacity is the max tokens; `rate` is tokens added per second, continuously (fractional refill allowed); a new bucket starts full; `allow(now)` consumes one token if available and returns True, else False. Time `now` is a float in seconds and may stay the same between calls. Tokens must never exceed capacity. Fix it.
