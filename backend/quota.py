"""Signed browser-cookie quota for sponsored Claude readings."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import hmac
import json


class VisitorQuotaExceeded(Exception):
    """Raised when a visitor has used their monthly reading allowance."""


@dataclass(frozen=True)
class QuotaState:
    period: str
    count: int


class ReadingQuota:
    """Track a best-effort per-browser quota without server-side storage."""

    def __init__(self, secret: str, visitor_monthly_limit: int = 5):
        if not secret:
            raise ValueError("A quota signing secret is required")
        self.secret = sha256(f"moira-reading-quota|{secret}".encode("utf-8")).digest()
        self.visitor_monthly_limit = visitor_monthly_limit

    @staticmethod
    def _period(now: datetime | None = None) -> str:
        current = now or datetime.now(timezone.utc)
        return current.strftime("%Y-%m")

    def _signature(self, payload: bytes) -> str:
        return hmac.new(self.secret, payload, sha256).hexdigest()

    def _encode(self, state: QuotaState) -> str:
        payload = json.dumps(
            {"period": state.period, "count": state.count},
            separators=(",", ":"),
        ).encode("utf-8")
        encoded = base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")
        return f"{encoded}.{self._signature(payload)}"

    def _decode(self, cookie_value: str | None, now: datetime | None = None) -> QuotaState:
        period = self._period(now)
        if not cookie_value or "." not in cookie_value:
            return QuotaState(period, 0)

        encoded, supplied_signature = cookie_value.rsplit(".", 1)
        try:
            padding = "=" * (-len(encoded) % 4)
            payload = base64.urlsafe_b64decode(encoded + padding)
            if not hmac.compare_digest(self._signature(payload), supplied_signature):
                return QuotaState(period, 0)
            data = json.loads(payload.decode("utf-8"))
            if data.get("period") != period:
                return QuotaState(period, 0)
            count = int(data.get("count", 0))
            return QuotaState(period, max(0, count))
        except (ValueError, TypeError, json.JSONDecodeError):
            return QuotaState(period, 0)

    def reserve(self, cookie_value: str | None, now: datetime | None = None) -> str:
        """Return the signed cookie for one additional successful reading."""
        state = self._decode(cookie_value, now)
        if state.count >= self.visitor_monthly_limit:
            raise VisitorQuotaExceeded
        return self._encode(QuotaState(state.period, state.count + 1))

    def remaining(self, cookie_value: str | None, now: datetime | None = None) -> int:
        state = self._decode(cookie_value, now)
        return max(0, self.visitor_monthly_limit - state.count)
