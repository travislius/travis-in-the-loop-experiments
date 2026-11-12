def compare(a, b):
    pa = a.split(".")
    pb = b.split(".")
    if pa < pb: return -1
    if pa > pb: return 1
    return 0
