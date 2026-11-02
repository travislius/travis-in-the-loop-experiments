
from decimal import Decimal, ROUND_HALF_UP

from .money import to_cents, apply_discount

def invoice_total(lines, discount_percent=0, tax_rate=0.0):
    """lines: list of (unit_price, qty). Discount applies before tax. Returns cents."""
    subtotal = sum(to_cents(p) * q for p, q in lines)
    discounted = apply_discount(subtotal, discount_percent)
    tax = (Decimal(discounted) * Decimal(str(tax_rate))).quantize(
        Decimal("1"), rounding=ROUND_HALF_UP
    )
    return discounted + int(tax)
