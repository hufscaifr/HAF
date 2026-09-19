from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
import sys

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PACKAGE_ROOT.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from ai_research_department.models import ResearchRequest
from ai_research_department.orchestration.research_director import ResearchDirector


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run real-data company research.")
    parser.add_argument("company", help="Company name, e.g. 삼성전자")
    parser.add_argument("--ticker", default="", help="Optional KRX ticker, e.g. 005930")
    parser.add_argument("--market", default=None, help="Optional market, KOSPI or KOSDAQ")
    parser.add_argument("--research-type", default="earnings_preview")
    parser.add_argument("--objective", default="기업명 기반 실데이터 수집 리서치")
    parser.add_argument("--price-period", default="6mo")
    parser.add_argument("--price-interval", default="1d")
    parser.add_argument(
        "--refresh-krx-listings",
        action="store_true",
        help="Refresh KRX listings before resolving the company and running agents.",
    )
    parser.add_argument("--database-path", default=str(PACKAGE_ROOT / "data" / "real_workspace.db"))
    parser.add_argument("--json", action="store_true", help="Print the full workflow result as JSON.")
    return parser


async def main() -> None:
    args = build_parser().parse_args()
    director = ResearchDirector(database_path=args.database_path)
    result = await director.run_research(
        ResearchRequest(
            company=args.company,
            ticker=args.ticker,
            market=args.market,
            research_type=args.research_type,
            objective=args.objective,
            data_mode="real",
            price_period=args.price_period,
            price_interval=args.price_interval,
            refresh_krx_listings=args.refresh_krx_listings,
        )
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
        return
    for line in result["logs"]:
        print(line)
    print()
    print(result["report"]["title"])
    for section in result["report"]["sections"]:
        print(f"\n## {section['title']}")
        print(section["body"])


if __name__ == "__main__":
    asyncio.run(main())
