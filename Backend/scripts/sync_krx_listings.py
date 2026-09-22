from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from cam_pipeline.krx_listings import refresh_krx_listings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Synchronize KOSPI/KOSDAQ listing titles and tickers from the KRX Open API.",
    )
    parser.add_argument(
        "--bas-dd",
        default=None,
        help="KRX base date in YYYYMMDD format. Omit to let the KRX API use its default/latest date.",
    )
    parser.add_argument(
        "--markets",
        nargs="+",
        default=["KOSPI", "KOSDAQ"],
        choices=["KOSPI", "KOSDAQ"],
        help="Markets to synchronize.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = refresh_krx_listings(
        bas_dd=args.bas_dd,
        markets=tuple(args.markets),
    )
    print(
        "KRX listings synchronized: "
        f"total={result['total']} counts={result['counts']} bas_dd={result['bas_dd'] or 'latest'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
