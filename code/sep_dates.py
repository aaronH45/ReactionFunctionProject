"""
sep_dates.py
============
Single source of truth for the SEP meeting calendar.

Every SEP with a published dot plot, January 2012 (the first) through
March 2026. The date is the SECOND day of the meeting, which is the release
date -- the SEP is published at 2:00pm Eastern that afternoon.

Notes on the calendar itself:
  - 2012 has FIVE SEPs (January, April, June, September, December). The January
    2012 meeting introduced the dot plot. Every later year has four.
  - March 2020 is absent: that SEP was cancelled during the COVID disruption.
    The gap between 2019-12-11 and 2020-06-10 is real, not missing data.
"""

SEP_DATES = [
    "20120125", "20120425", "20120620", "20120913", "20121212",
    "20130320", "20130619", "20130918", "20131218",
    "20140319", "20140618", "20140917", "20141217",
    "20150318", "20150617", "20150917", "20151216",
    "20160316", "20160615", "20160921", "20161214",
    "20170315", "20170614", "20170920", "20171213",
    "20180321", "20180613", "20180926", "20181219",
    "20190320", "20190619", "20190918", "20191211",
    # 2020-03 cancelled
    "20200610", "20200916", "20201216",
    "20210317", "20210616", "20210922", "20211215",
    "20220316", "20220615", "20220921", "20221214",
    "20230322", "20230614", "20230920", "20231213",
    "20240320", "20240612", "20240918", "20241218",
    "20250319", "20250618", "20250917", "20251210",
    "20260318",
]

assert len(SEP_DATES) == 57, len(SEP_DATES)


def as_timestamp(d):
    import pandas as pd
    return pd.Timestamp(f"{d[:4]}-{d[4:6]}-{d[6:]}")
