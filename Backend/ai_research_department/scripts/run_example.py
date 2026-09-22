from __future__ import annotations

import asyncio
from pathlib import Path
import sys

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PACKAGE_ROOT.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from ai_research_department.models import ResearchRequest
from ai_research_department.orchestration.research_director import ResearchDirector


async def main() -> None:
    """Run the deterministic end-to-end demo."""
    database_path = PACKAGE_ROOT / "data" / "example_workspace.db"
    if database_path.exists():
        database_path.unlink()
    director = ResearchDirector(database_path=database_path)
    result = await director.run_research(
        ResearchRequest(
            company="Example Electronics",
            ticker="000000",
            research_type="earnings_preview",
            as_of_date="2026-09-19",
            objective="신규 반도체 공장 가동과 DRAM 가격 상승의 실적 영향을 분석",
        )
    )
    for line in result["logs"]:
        print(line)
    print()
    print(result["report"]["title"])
    for section in result["report"]["sections"]:
        print(f"\n## {section['title']}")
        print(section["body"])


if __name__ == "__main__":
    asyncio.run(main())
