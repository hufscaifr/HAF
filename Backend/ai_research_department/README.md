# AI Research Department

Python-only multi-agent research system that models a sell-side equity research organization.

The MVP uses deterministic mock data and a SQLite workspace so the full workflow can run without API keys:

```bash
cd Backend
python ai_research_department/scripts/run_example.py
```

Real-data company-name mode:

```bash
cd Backend
python ai_research_department/scripts/run_company_research.py 삼성전자
```

Print the full frontend-ready JSON payload:

```bash
python ai_research_department/scripts/run_company_research.py 삼성전자 --json
```

Refresh KRX listings before agent execution:

```bash
python ai_research_department/scripts/run_company_research.py 삼성전자 --refresh-krx-listings
```

Frontend can trigger the same refresh independently with:

```http
POST /api/krx-listings/refresh
POST /api/ai-research/krx-listings/refresh
```

API keys are not required for the mock MVP path. Real-data mode reads keys from `Backend/.env` or environment variables:

- `KRX_AUTH_KEY` to refresh KRX listings when the local listings DB is missing
- `DART_API_KEY` for OpenDART filings
- `OPENAI_API_KEY` and `OPENAI_MODEL` for future real structured LLM generation
- `DATABASE_URL` when replacing SQLite with PostgreSQL

Core flow:

```text
ResearchDirector
ResearchManager
Issue -> Cause -> Data -> Fundamental -> Estimate -> Report -> Verification
```

Every major output is a structured Pydantic object persisted through the shared SQLite research workspace. Report claims keep explicit lineage to evidence, hypotheses, or estimates.
