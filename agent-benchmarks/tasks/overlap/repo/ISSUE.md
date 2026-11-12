# Bug report

Booking system bug: `overlaps(a_start, a_end, b_start, b_end)` (dates, end date INCLUSIVE — a booking ending on the 5th still occupies the 5th) says `[1,5]` and `[5,9]` do NOT overlap, so we double-booked a room. Also it crashes or misbehaves when the ranges are given in any order. Fix it.
