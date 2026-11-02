
from datetime import date

def parse_due(text):
    """Parse 'YYYY-MM-DD' or 'MM/DD/YYYY' into a date."""
    text = text.strip()
    if "-" in text:
        y, m, d = text.split("-")
        return date(int(y), int(m), int(d))
    m, d, y = text.split("/")
    return date(int(y), int(m), int(d))
