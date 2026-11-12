import datetime as dt, pytest
from cron import next_run
D=dt.datetime
def test_every15(): assert next_run("*/15 * * * *", D(2026,1,1,10,7))==D(2026,1,1,10,15)
def test_strict_after(): assert next_run("30 9 * * *", D(2026,1,1,9,30))==D(2026,1,2,9,30)
def test_range_step(): assert next_run("10-40/10 * * * *", D(2026,1,1,10,41))==D(2026,1,1,11,10)
def test_list_hours(): assert next_run("0 8,20 * * *", D(2026,3,31,21,0))==D(2026,4,1,8,0)
def test_dow_only(): assert next_run("0 9 * * 1", D(2026,11,11,12,0))==D(2026,11,16,9,0)
def test_sunday7(): assert next_run("0 0 * * 7", D(2026,11,11,0,0))==D(2026,11,15,0,0)
def test_dom_or_dow(): assert next_run("0 0 13 * 5", D(2026,11,1,0,0))==D(2026,11,6,0,0)
def test_leap(): assert next_run("0 0 29 2 *", D(2026,3,1))==D(2028,2,29,0,0)
def test_year_roll(): assert next_run("5 4 1 1 *", D(2026,12,31,23,59))==D(2027,1,1,4,5)
def test_seconds_dropped(): assert next_run("* * * * *", D(2026,1,1,10,7,59))==D(2026,1,1,10,8)
def test_impossible():
    with pytest.raises(ValueError): next_run("0 0 31 2 *", D(2026,1,1))
