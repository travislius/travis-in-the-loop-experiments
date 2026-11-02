
from decimal import Decimal, ROUND_HALF_UP

def to_cents(amount):
    """Convert a dollar amount (str/float/Decimal) to integer cents, rounding half up."""
    cents = Decimal(str(amount)) * 100
    return int(cents.quantize(Decimal("1"), rounding=ROUND_HALF_UP))

def apply_discount(cents, percent):
    """Apply a percentage discount (0-100). Result rounded half up to the cent."""
    if percent < 0 or percent > 100:
        raise ValueError("percent must be between 0 and 100")
    discount = (Decimal(cents) * Decimal(str(percent)) / 100).quantize(
        Decimal("1"), rounding=ROUND_HALF_UP
    )
    return cents - int(discount)
