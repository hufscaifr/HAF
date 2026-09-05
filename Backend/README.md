# Corporate Analysis Model

This project is being built step by step.

Current status:
- Step 1 implemented: scrape a news article from a URL
- Step 2 implemented: use an LLM to select promising KOSPI/KOSDAQ companies
- Step 3 implemented: fetch OHLCV data from Yahoo Finance for the selected companies
- Step 4 implemented: calculate technical indicators from the OHLCV data
- Step 4B implemented: fetch DART-based financial indicators such as EPS, BPS, PER, and PBR
- Step 5 implemented: derive buy/sell opinions from the indicators
- Step 6 implemented: save recent stock-price plots for the selected companies

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Python 3.10+ is recommended. The current Gemini SDK still installs on Python 3.9, but its auth dependencies emit end-of-life warnings there.

## Usage

```bash
python3 main.py scrape "https://example.com/news-article"
python3 main.py scrape "https://example.com/news-article" --json

python3 main.py select "https://example.com/news-article" --provider openai
python3 main.py select "https://example.com/news-article" --provider gemini --json

python3 main.py ohlcv "https://example.com/news-article" --provider openai --period 6mo --interval 1d
python3 main.py ohlcv "https://example.com/news-article" --provider gemini --json

python3 main.py indicators "https://example.com/news-article" --provider openai --period 6mo --interval 1d
python3 main.py indicators "https://example.com/news-article" --provider gemini --recent-rows 5 --json

python3 main.py fundamentals "https://example.com/news-article" --provider openai --period 6mo --interval 1d
python3 main.py fundamentals "https://example.com/news-article" --provider gemini --json

python3 main.py opinion "https://example.com/news-article" --provider openai --period 6mo --interval 1d
python3 main.py opinion "https://example.com/news-article" --provider gemini --json

python3 main.py plot "https://example.com/news-article" --provider openai --recent-points 60 --clear-output-dir
python3 main.py plot "https://example.com/news-article" --provider gemini --output-dir plots --json

python3 main.py report "https://example.com/news-article" --provider openai --recent-points 60 --output-dir plots --clear-output-dir
python3 main.py report "https://example.com/news-article" --provider gemini --json

python3 main.py research "https://example.com/news-article" --provider openai --period 6mo --interval 1d
python3 main.py research "https://example.com/news-article" --provider gemini --json

python3 main.py word-report "https://example.com/news-article" --provider openai --output-dir word_reports --recent-points 60
python3 main.py word-report "https://example.com/news-article" --provider gemini --json
```

## Backend API for Framer

Run the HTTP API server:

```bash
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

The Framer `/new_research` page can submit a news URL to:

```http
POST http://localhost:8000/api/new-research
Content-Type: application/json

{
  "url": "https://example.com/news-article"
}
```

The API crawls the article, sends the article text to the configured AI provider, forces exactly three recommended companies for the frontend layout, and returns:
- `article`
- `selection.summary`
- `selection.companies`
- `summary`
- `companies`

If the frontend only needs the AI-recommended company cards, use:

```http
POST http://localhost:8000/api/recommended-companies
Content-Type: application/json

{
  "url": "https://example.com/news-article"
}
```

Response shape:

```json
{
  "status": "success",
  "summary": "AI analysis summary",
  "companies": [
    {
      "name": "삼성전자",
      "ticker": "005930.KS",
      "score": 0.91,
      "score_percent": 91.0,
      "company_name": "Samsung Electronics",
      "company_name_ko": "삼성전자",
      "korean_ticker": "005930",
      "market": "KOSPI"
    },
    {
      "name": "SK하이닉스",
      "ticker": "000660.KS",
      "score": 0.87,
      "score_percent": 87.0,
      "company_name": "SK Hynix",
      "company_name_ko": "SK하이닉스",
      "korean_ticker": "000660",
      "market": "KOSPI"
    },
    {
      "name": "하나마이크론",
      "ticker": "067310.KQ",
      "score": 0.74,
      "score_percent": 74.0,
      "company_name": "Hana Micron",
      "company_name_ko": "하나마이크론",
      "korean_ticker": "067310",
      "market": "KOSDAQ"
    }
  ]
}
```

The `companies` array is forced to exactly three items for the current Framer layout.

### Financial calendar API

The backend can collect major financial calendar events with the OpenAI Responses API web search tool, store them in SQLite, and serve them to the frontend.

By default, the calendar uses a short rolling window from today through 45 days later. The GET endpoint refreshes this near-term window once per day before returning events.
The collector is intentionally selective: it focuses on medium/high-impact events for Korean investors rather than trying to fill every date. If no reliable events exist in a window, the API can return an empty `events` array.

```http
GET http://localhost:8000/api/financial-calendar
```

Optional query parameters:
- `start_date`: `YYYY-MM-DD`
- `end_date`: `YYYY-MM-DD`
- `category`: `rate`, `economic_indicator`, `earning`, `policy`, `market_holiday`, `auction`, or `other`
- `importance`: `high`, `medium`, or `low`
- `refresh_if_stale`: `true` or `false`
- `model`: OpenAI model override for stale refreshes

Response shape:

```json
{
  "status": "success",
  "start_date": "2026-07-19",
  "end_date": "2026-09-02",
  "count": 1,
  "events": [
    {
      "id": 1,
      "date": "2026-08-20",
      "title": "엔비디아 실적 발표",
      "category": "earning",
      "importance": "high",
      "detail": "AI 반도체 수요 지속 여부가 주목돼요.",
      "country": "US",
      "source_name": "NVIDIA Investor Relations",
      "source_url": "https://investor.nvidia.com/"
    }
  ],
  "refresh": {
    "refreshed": true,
    "last_refresh_date": "2026-07-19"
  },
  "refresh_error": null
}
```

To force a refresh manually:

```http
POST http://localhost:8000/api/financial-calendar/refresh
Content-Type: application/json

{
  "start_date": "2026-07-19",
  "end_date": "2026-09-02"
}
```

To seed the DB from the backend without running the API server:

```bash
python3 scripts/seed_financial_calendar.py
```

The seed script defaults to a 45-day lookahead split into 15-day OpenAI requests. You can override it when needed:

```bash
python3 scripts/seed_financial_calendar.py --lookahead-days 90 --chunk-days 15
```

Configuration:
- `OPENAI_API_KEY`: required for calendar refresh.
- `OPENAI_FINANCIAL_CALENDAR_MODEL`: optional, defaults to the existing OpenAI model setting.
- `CAM_FINANCIAL_CALENDAR_DB`: optional SQLite path, defaults to `financial_calendar.db` in the project root.
- `CAM_FINANCIAL_CALENDAR_LOOKAHEAD_DAYS`: optional default API window, defaults to `45`.
- `OPENAI_FINANCIAL_CALENDAR_TIMEOUT_SECONDS`: optional OpenAI request timeout, defaults to `90`.
- `OPENAI_FINANCIAL_CALENDAR_SEARCH_CONTEXT_SIZE`: optional web search context size, defaults to `low`.
- `OPENAI_FINANCIAL_CALENDAR_ALLOWED_DOMAINS`: optional comma-separated web search domain allowlist. Defaults to core sources such as Fed, BOK, BLS, BEA, KOSTAT, KRX, DART, Yahoo Finance, Nasdaq, and major company IR domains.
- `CAM_TIMEZONE`: optional, defaults to `Asia/Seoul`.

If the frontend also needs stock-price chart images, use:

```http
POST http://localhost:8000/api/company-dashboard
Content-Type: application/json

{
  "url": "https://example.com/news-article"
}
```

The chart response keeps the same `summary` and `companies` shape, and each company also includes:
- `daily_chart_url`
- `intraday_chart_url`
- `chart_url`
- `latest_close`
- `ai_opinion`
- `technical_opinion`
- `opinion_rationale`
- `recommendation_reason`
- `risks`
- `risk_analysis`
- `financial_analysis`
- `financial_metrics`

Those chart URLs point to PNG files served by the backend under `/static/plots/...`, so the frontend can render them directly with `<img src={company.daily_chart_url} />`.

This endpoint bundles company metadata, latest close, AI recommendation text, technical opinion, and DART-based financial analysis in one JSON response. The chart images themselves are not embedded as base64; only image URLs are returned, so live price refresh can later be added as a separate lightweight API.

The `financial_analysis` field is generated by the configured LLM from OpenDART financial statements and valuation metrics. The prompt asks for Korean sell-side research style: profitability, balance-sheet risk, cash-flow quality, valuation burden/upside, and the earnings or ROE assumptions needed to justify the valuation.

Example browser-side request:

```javascript
const response = await fetch("http://localhost:8000/api/recommended-companies", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ url: newsUrl }),
})

const result = await response.json()
```

For deployed Framer usage, deploy this backend to a public HTTPS URL and replace `localhost:8000` with that backend URL. CORS is already enabled for `https://ambiguous-replacement-035632.framer.app`.

The scraper returns:
- `url`
- `source`
- `title`
- `published_at`
- `text`
- `extractor`

Implementation notes:
- Primary extractor: `trafilatura`
- Fallback extractor: `BeautifulSoup`
- This makes step 2 easier because the LLM can receive a normalized article payload.

## Step 2 Environment Variables

Create a local `.env` file or export these variables in your shell:

```bash
export OPENAI_API_KEY="..."
export OPENAI_MODEL="gpt-5-mini"

export GEMINI_API_KEY="..."
export GEMINI_MODEL="gemini-2.5-flash"

export CAM_LLM_PROVIDER="openai"
export DART_API_KEY="..."
```

The app now auto-loads `.env` if `python-dotenv` is installed.

Step 2 returns:
- `article`
- `provider`
- `model`
- `selection.summary`
- `selection.companies`

Each company includes:
- `company_name`
- `company_name_ko`
- `ticker`
- `market`
- `rationale`
- `article_relevance`
- `key_catalysts`
- `risks`
- `risk_analysis`
- `confidence`

## Step 3 Output

The `ohlcv` command runs steps 1 to 3 together:
- Scrape the article
- Select KOSPI/KOSDAQ companies with an LLM
- Fetch Yahoo Finance OHLCV data for those companies

The result adds:
- `market_data.period`
- `market_data.interval`
- `market_data.companies`

Each market-data company includes:
- `yahoo_symbol`
- `currency`
- `start_date`
- `end_date`
- `row_count`
- `latest_close`
- `latest_volume`
- `ohlcv`
- `error`

Yahoo symbol mapping used in this project:
- KOSPI: `XXXXXX.KS`
- KOSDAQ: `XXXXXX.KQ`

## Step 4 Output

The `indicators` command runs steps 1 to 4 together:
- Scrape the article
- Select KOSPI/KOSDAQ companies with an LLM
- Fetch Yahoo Finance OHLCV data
- Calculate technical indicators

Configured indicators:
- `sma_20`
- `sma_50`
- `ema_20`
- `rsi_14`
- `macd_12_26_9`
- `bbands_20_2`
- `atr_14`
- `adx_14`
- `stoch_14_3_3`
- `obv`
- `volume_sma_20`

Each technical-analysis company includes:
- `latest_indicators`
- `signal_context`
- `latest_signal`
- `recent_rows`
- `error`

Implementation note:
- This project uses `pandas-ta-classic`, the maintained compatible fork of `pandas-ta`, because the current `pandas-ta` package requires newer Python versions than this environment.
- The technical-analysis step now computes a regime-aware weighted signal that first classifies the market as `trend` or `range`, then applies different scoring rules for each regime.
- The CLI prints the exact latest value for every computed indicator so you can directly verify metrics such as RSI, MACD, Bollinger levels, ADX/DI, OBV, and recent returns.

## Step 5 Output

The `opinion` command runs steps 1 to 5 together:
- Scrape the article
- Select KOSPI/KOSDAQ companies with an LLM
- Fetch Yahoo Finance OHLCV data
- Calculate technical indicators
- Derive rule-based buy/sell opinions

Opinion outputs include:
- `opinion`
- `score`
- `confidence`
- `risk_level`
- `rationale`
- `positives`
- `negatives`
- `score_breakdown`

Current opinion labels:
- `strong_buy`
- `buy`
- `hold`
- `sell`
- `strong_sell`

Implementation note:
- Step 5 now uses the regime-aware technical signal from Step 4 as the canonical decision engine and adds confidence, risk, and rationale around that output.

## Step 4B Output

The `fundamentals` command runs steps 1 to 3 together, then fetches financial indicators:
- Scrape the article
- Select KOSPI/KOSDAQ companies with an LLM
- Fetch price data to source the latest close
- Fetch DART financial statements and ratios

Fundamentals outputs include:
- `valuation_metrics.per`
- `valuation_metrics.pbr`
- `valuation_metrics.pcr`
- `valuation_metrics.ev_to_ebitda`
- `business_year`
- `report_name`
- `statement_date`
- `valuation_metrics.eps`
- `valuation_metrics.bps`
- `valuation_metrics.ebitda`
- `valuation_metrics.cash_dps`
- `valuation_metrics.cash_dividend_yield`
- `valuation_metrics.roe`
- `valuation_metrics.debt_ratio`
- `valuation_metrics.current_ratio`
- `valuation_metrics.market_cap`
- `valuation_metrics.shares_outstanding`

Implementation note:
- Step 4B now uses OpenDART for Korean-company fundamentals.
- The code maps stock codes to `corp_code` via DART's `corpCode.xml`, then pulls the latest available report with `fnlttSinglAcntAll` and ratio data from `fnlttSinglIndx`.
- OHLCV and technical-analysis steps still use Yahoo Finance because DART does not provide historical price candles.

## Step 6 Output

The `plot` command runs steps 1 to 3 together, then saves recent intraday price/volume charts:
- Scrape the article
- Select KOSPI/KOSDAQ companies with an LLM
- Fetch Yahoo Finance 1-minute OHLCV data by default
- Save price-line and colored volume-bar charts as PNG files

Plot outputs include:
- `plots.output_dir`
- `plots.period`
- `plots.interval`
- `plots.recent_points`
- `plots.companies[].plot_path`
- `plots.companies[].start_date`
- `plots.companies[].end_date`
- `plots.companies[].latest_close`
- `plots.companies[].error`

Implementation note:
- Step 6 uses `matplotlib` to save PNG charts of recent price and volume movement for each selected company.
- The chart default is `--period 1d --interval 1m`; use those options if you want a different Yahoo Finance range.
- Use `--clear-output-dir` if you want old PNG files in the target plot folder removed before each new run.

## Combined Run

The `report` command runs the opinion engine and report chart generation together in one command:
- Scrape the article
- Select KOSPI/KOSDAQ companies with an LLM
- Fetch Yahoo Finance OHLCV data for analysis
- Fetch DART financial indicators
- Calculate technical indicators
- Derive buy/sell opinions
- Save two report charts per company: a 3-month daily price chart and a 1-minute intraday price/volume chart

Implementation note:
- `report` keeps the analysis fetch separate from chart fetching, so daily indicators can remain stable while chart images use `--daily-plot-period 3mo --daily-plot-interval 1d` and `--plot-period 1d --plot-interval 1m` by default.
- `report --clear-output-dir` clears existing PNG charts in the target output folder before saving the new report charts.

## LLM Research Report

The `research` command writes a Korean institutional-style thematic equity research report using the calculated pipeline outputs:
- Scrape the article
- Select KOSPI/KOSDAQ companies with an LLM
- Fetch Yahoo Finance OHLCV data
- Calculate DART-based financial indicators
- Calculate technical indicators
- Derive rule-based opinions
- Ask the LLM to write a full Korean sell-side style report using only those inputs

Research report outputs include:
- `llm_report.prompt_version`
- `llm_report.body`

Implementation note:
- The report prompt is designed to keep the output conservative and evidence-based.
- Financial and technical data are passed into the model as structured inputs so the report interprets the calculated metrics instead of inventing external assumptions.

## Microsoft Word Report

The `word-report` command generates a `.docx` research note with charts and tables:
- Scrape the article
- Select KOSPI/KOSDAQ companies with an LLM
- Fetch Yahoo Finance OHLCV data
- Calculate DART-based financial indicators
- Calculate technical indicators
- Derive rule-based opinions
- Generate the Korean LLM research report
- Save a Microsoft Word report with:
  - a top investment-opinion summary table
  - stock-price plots beneath the company analysis section
  - a financial analysis table for each company

Word report outputs include:
- `word_report.document_path`
- `plots.output_dir`

Implementation note:
- The report is exported as a Microsoft Word `.docx` file using `python-docx`.
- The generated document applies different font sizes for the title, section headings, and body text.
