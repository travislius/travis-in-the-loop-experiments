import datetime as dt
def next_run(expr, after):
    minute, hour, dom, month, dow = expr.split()
    t = after.replace(second=0, microsecond=0) + dt.timedelta(minutes=1)
    return t.replace(minute=int(minute) if minute != "*" else t.minute)
