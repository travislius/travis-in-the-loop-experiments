def parse_amount(s):
    s = s.replace("$", "").replace(",", "")
    return float(s)
