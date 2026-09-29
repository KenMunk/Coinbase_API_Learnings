"""Download a year of 15-minute LTC-USD candles and save them to a CSV file.

GET https://api.coinbase.com/api/v3/brokerage/products/{product_id}/candles
Docs: https://docs.cdp.coinbase.com/api-reference/advanced-trade-api/rest-api/products/get-product-candles
"""

import csv
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from config import get_client

PRODUCT_ID = "LTC-USD"
GRANULARITY = "FIFTEEN_MINUTE"
GRANULARITY_SECONDS = 15 * 60
LOOKBACK = timedelta(days=365)
MAX_CANDLES_PER_REQUEST = 350  # API limit
OUTPUT_PATH = Path(__file__).parent / "data" / f"{PRODUCT_ID}_15m.csv"


def fetch_candles(client, start: int, end: int) -> list[dict]:
    """Fetch every candle in [start, end), paging in windows the API accepts."""
    # One candle short of the limit, leaving room for the 1s start offset below.
    window = (MAX_CANDLES_PER_REQUEST - 1) * GRANULARITY_SECONDS
    candles: dict[int, dict] = {}

    for window_start in range(start, end, window):
        window_end = min(window_start + window, end)
        # The API excludes a candle starting exactly at `start`, so ask from 1s earlier.
        response = client.get_candles(
            product_id=PRODUCT_ID,
            start=str(window_start - 1),
            end=str(window_end),
            granularity=GRANULARITY,
            limit=MAX_CANDLES_PER_REQUEST,
        )
        # Keyed by start time so candles on a window boundary aren't duplicated.
        # The API includes a candle starting at `end`; drop it so the still-open
        # current candle never makes it into the file.
        for candle in response.candles or []:
            if start <= int(candle.start) < end:
                candles[int(candle.start)] = candle.to_dict()

        done = window_end - start
        print(f"\r{done / (end - start):6.1%}  {len(candles):,} candles", end="", flush=True)
        time.sleep(0.1)  # stay well under the rate limit

    print()
    return [candles[t] for t in sorted(candles)]


def write_csv(candles: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "datetime_utc", "open", "high", "low", "close", "volume"])
        for c in candles:
            ts = int(c["start"])
            writer.writerow([
                ts,
                datetime.fromtimestamp(ts, timezone.utc).isoformat(),
                c["open"], c["high"], c["low"], c["close"], c["volume"],
            ])


def main() -> None:
    now = datetime.now(timezone.utc)
    # Align to the granularity so every window starts on a candle boundary.
    end = int(now.timestamp()) // GRANULARITY_SECONDS * GRANULARITY_SECONDS
    start = int((now - LOOKBACK).timestamp()) // GRANULARITY_SECONDS * GRANULARITY_SECONDS

    print(f"Fetching {PRODUCT_ID} {GRANULARITY} candles from "
          f"{datetime.fromtimestamp(start, timezone.utc):%Y-%m-%d %H:%M} to "
          f"{datetime.fromtimestamp(end, timezone.utc):%Y-%m-%d %H:%M} UTC")

    candles = fetch_candles(get_client(), start, end)
    write_csv(candles, OUTPUT_PATH)

    expected = (end - start) // GRANULARITY_SECONDS
    print(f"Wrote {len(candles):,} candles to {OUTPUT_PATH} "
          f"({expected - len(candles):,} intervals had no trades or were missing)")


if __name__ == "__main__":
    main()
