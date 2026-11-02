
from decimal import Decimal, ROUND_HALF_UP

def to_cents(amount):
    """Convert a dollar amount (str/float/Decimal) to integer cents, rounding half up."""
    return int(Decimal(str(amount)) * 100)   # BUG: truncates instead of rounding half up

def apply_discount(cents, percent):
    """Apply a percentage discount (0-100). Result rounded half up to the cent."""
    if percent < 0 or percent > 100:
        raise ValueError("percent must be between 0 and 100")
    return cents - cents * percent // 100      # BUG: discount rounds down, should round half up
