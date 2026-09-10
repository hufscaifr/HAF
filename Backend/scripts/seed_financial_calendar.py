from __future__ import annotations

import argparse
import sys
from datetime import timedelta
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from cam_pipeline.financial_calendar import (
    DEFAULT_FINANCIAL_CALENDAR_MODEL,
    default_end_date,
    get_today,
    refresh_financial_calendar,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Seed the SQLite financial calendar in smaller OpenAI collection windows.",
    )
    parser.add_argument(
        "--chunk-days",
        type=int,
        default=5,
        help="Number of calendar days to collect per OpenAI request.",
    )
    parser.add_argument(
        "--lookahead-days",
        type=int,
        default=5,
        help="Total number of days to collect from today, including today.",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_FINANCIAL_CALENDAR_MODEL,
        help="OpenAI model used for collection.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.chunk_days <= 0:
        raise SystemExit("--chunk-days must be greater than 0.")
    if args.lookahead_days <= 0:
        raise SystemExit("--lookahead-days must be greater than 0.")

    start = get_today()
    final_end = start + timedelta(days=args.lookahead_days - 1)
    current_start = start
    total = 0

    while current_start <= final_end:
        current_end = min(
            current_start + timedelta(days=args.chunk_days - 1),
            final_end,
        )
        print(f"Refreshing {current_start.isoformat()} -> {current_end.isoformat()} ...", flush=True)
        result = refresh_financial_calendar(
            start_date=current_start,
            end_date=current_end,
            model=args.model,
        )
        inserted_or_updated = int(result.get("inserted_or_updated", 0) or 0)
        total += inserted_or_updated
        print(f"  inserted_or_updated={inserted_or_updated}", flush=True)
        current_start = current_end + timedelta(days=1)

    print(f"Done. total_inserted_or_updated={total}")
    print(f"Default GET window ends at {default_end_date(start).isoformat()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
