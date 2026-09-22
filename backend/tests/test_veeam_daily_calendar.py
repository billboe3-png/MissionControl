"""Tests for the Veeam jobs-grid calendar window."""

import itertools
from datetime import date, timedelta

from app.plugins.installed.official_veeam.veeam_provider import (
    _job_stats_daily_calendar,
)


def test_calendar_covers_exactly_n_days_ending_today():
    days = 8
    result = _job_stats_daily_calendar(days)
    assert len(result) == days
    assert result[-1] == date.today().isoformat()
    assert result[0] == (date.today() - timedelta(days=days - 1)).isoformat()


def test_calendar_is_ascending_and_contiguous():
    result = _job_stats_daily_calendar(14)
    assert result == sorted(result)
    for prev, nxt in itertools.pairwise(result):
        assert (date.fromisoformat(nxt) - date.fromisoformat(prev)).days == 1


def test_calendar_handles_nonpositive_days():
    assert len(_job_stats_daily_calendar(0)) == 7
    assert len(_job_stats_daily_calendar(None)) == 7
    assert len(_job_stats_daily_calendar(-3)) == 1