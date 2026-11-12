def overlaps(a_start, a_end, b_start, b_end):
    """Return True if the inclusive date ranges overlap."""
    return a_start < b_end and b_start < a_end
