from __future__ import annotations

import csv
import io
from datetime import UTC, datetime

from capybucks.core.http import get_text
from capybucks.core.models import AssetType, History, OHLCVBar, Provenance
from capybucks.core.provider import Provider
from capybucks.exceptions import ProviderError, SymbolNotFound

_CSV = "https://stooq.com/q/d/l/"

_INTERVALS = {"1d": "d", "1wk": "w", "1w": "w", "1mo": "m"}


class StooqProvider(Provider):
    """Stooq daily/weekly/monthly CSV. Pin with provider='stooq'.

    Stooq often serves a JS bot-check instead of CSV to datacenter IPs;
    that is a ProviderError, not a silent empty frame.
    """

    name = "stooq"
    requires_key = False
    supports_stream = False

    def supports(self, asset_type: AssetType) -> bool:
        return asset_type is AssetType.EQUITY

    async def fetch_history(
        self,
        symbol: str,
        *,
        start: datetime | None = None,
        end: datetime | None = None,
        interval: str = "1d",
        auto_adjust: bool = True,
    ) -> History:
        mapped = _INTERVALS.get(interval)
        if mapped is None:
            raise ProviderError(f"stooq does not support interval {interval!r}")
        params = {"s": to_stooq_symbol(symbol), "i": mapped}
        if start is not None:
            params["d1"] = start.strftime("%Y%m%d")
        if end is not None:
            params["d2"] = end.strftime("%Y%m%d")
        text = await get_text(_CSV, provider=self.name, params=params)
        return parse_stooq_csv(text, symbol=symbol, auto_adjust=auto_adjust)


def to_stooq_symbol(symbol: str) -> str:
    lowered = symbol.lower()
    if "." in lowered:
        return lowered
    return f"{lowered}.us"


def parse_stooq_csv(text: str, *, symbol: str, auto_adjust: bool) -> History:
    stripped = text.lstrip()
    if stripped.startswith("<") or not stripped.upper().startswith("DATE"):
        raise ProviderError(
            "stooq returned a bot-check page instead of CSV; "
            "pin another provider or retry later"
        )
    reader = csv.DictReader(io.StringIO(stripped))
    bars: list[OHLCVBar] = []
    for row in reader:
        date_s = (row.get("Date") or row.get("date") or "").strip()
        if not date_s or date_s.lower() == "no data":
            continue
        close = _f(row.get("Close") or row.get("close"))
        if close is None:
            continue
        day = datetime.strptime(date_s, "%Y-%m-%d").replace(tzinfo=UTC)
        bars.append(
            OHLCVBar(
                timestamp=day,
                open=_f(row.get("Open") or row.get("open")) or close,
                high=_f(row.get("High") or row.get("high")) or close,
                low=_f(row.get("Low") or row.get("low")) or close,
                close=close,
                adj_close=close,
                volume=_f(row.get("Volume") or row.get("volume")),
            )
        )
    if not bars:
        raise SymbolNotFound(symbol, provider="stooq")
    bars.sort(key=lambda bar: bar.timestamp)
    return History(
        bars=bars,
        provenance=Provenance(
            provider="stooq",
            delayed=True,
            adjustment="split_and_dividend" if auto_adjust else "none",
            asof=datetime.now(UTC),
            timezone="UTC",
            currency=None,
        ),
    )


def _f(value: str | None) -> float | None:
    if value is None or value.strip() in {"", "-"}:
        return None
    try:
        return float(value)
    except ValueError:
        return None
