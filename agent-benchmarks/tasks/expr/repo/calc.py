def evaluate(s):
    s = s.replace(" ", "")
    total = 0.0
    for part in s.split("+"):
        total += float(part)
    return total
