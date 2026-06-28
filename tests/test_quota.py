from datetime import datetime, timezone

import pytest

from quota import ReadingQuota, VisitorQuotaExceeded


def test_visitor_gets_five_readings_per_calendar_month():
    quota = ReadingQuota("test-secret", visitor_monthly_limit=5)
    june = datetime(2026, 6, 27, tzinfo=timezone.utc)
    cookie = None

    for expected_remaining in (4, 3, 2, 1, 0):
        cookie = quota.reserve(cookie, now=june)
        assert quota.remaining(cookie, now=june) == expected_remaining

    with pytest.raises(VisitorQuotaExceeded):
        quota.reserve(cookie, now=june)


def test_quota_is_per_visitor_and_resets_next_month():
    quota = ReadingQuota("test-secret", visitor_monthly_limit=1)
    june = datetime(2026, 6, 30, tzinfo=timezone.utc)
    july = datetime(2026, 7, 1, tzinfo=timezone.utc)

    visitor_a = quota.reserve(None, now=june)
    visitor_b = quota.reserve(None, now=june)
    visitor_a_next_month = quota.reserve(visitor_a, now=july)

    assert quota.remaining(visitor_a, now=june) == 0
    assert quota.remaining(visitor_b, now=june) == 0
    assert quota.remaining(visitor_a_next_month, now=july) == 0


def test_tampered_cookie_cannot_increase_the_allowance():
    quota = ReadingQuota("test-secret", visitor_monthly_limit=5)
    june = datetime(2026, 6, 27, tzinfo=timezone.utc)
    valid_cookie = quota.reserve(None, now=june)
    payload, signature = valid_cookie.rsplit(".", 1)
    replacement = "0" if signature[-1] != "0" else "1"
    tampered_cookie = f"{payload}.{signature[:-1]}{replacement}"

    # Invalid signatures are treated as a fresh browser, never trusted data.
    assert quota.remaining(tampered_cookie, now=june) == 5
