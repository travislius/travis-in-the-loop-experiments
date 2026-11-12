def overlaps(a_start,a_end,b_start,b_end):
    a_start,a_end=sorted((a_start,a_end)); b_start,b_end=sorted((b_start,b_end))
    return a_start<=b_end and b_start<=a_end
