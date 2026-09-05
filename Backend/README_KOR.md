# Corporate Analysis Model

뉴스 기사 URL을 입력하면 관련 기업을 선정하고, 주가·재무·기술적 지표를 분석해 투자 의견과 리서치 보고서까지 생성하는 기업 분석 모델입니다.

현재 프로젝트는 단계별 파이프라인 구조로 구현되어 있습니다.

---

## 현재 구현 상태

- **Step 1**: 뉴스 기사 URL 크롤링
- **Step 2**: LLM을 이용한 KOSPI/KOSDAQ 유망 기업 선정
- **Step 3**: Yahoo Finance 기반 OHLCV 데이터 수집
- **Step 4**: 기술적 지표 계산
- **Step 4B**: OpenDART 기반 재무·밸류에이션 지표 수집
- **Step 5**: 기술적 지표 기반 매수/매도 의견 도출
- **Step 6**: 선정 기업의 최근 주가 차트 저장
- **Report**: 기술적 분석, 재무 분석, 투자 의견, 차트 통합
- **Research**: LLM 기반 한국형 Sell-side 리서치 보고서 생성
- **Word Report**: `.docx` 형식 리서치 보고서 생성
- **Backend API**: Framer 프론트엔드 연동용 API 제공
- **Financial Calendar API**: 주요 금융 이벤트 수집 및 제공

---

# 1. 설치

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Python 3.10 이상 사용을 권장합니다.

현재 Gemini SDK는 Python 3.9에서도 설치 가능하지만, 인증 관련 의존성에서 Python 3.9 지원 종료 경고가 발생할 수 있습니다.

---

# 2. 환경 변수 설정

프로젝트 루트에 `.env` 파일을 생성하거나 환경 변수를 직접 등록합니다.

```bash
export OPENAI_API_KEY="..."
export OPENAI_MODEL="gpt-5-mini"

export GEMINI_API_KEY="..."
export GEMINI_MODEL="gemini-2.5-flash"

export CAM_LLM_PROVIDER="openai"

export DART_API_KEY="..."
```

`python-dotenv`가 설치되어 있다면 `.env` 파일을 자동으로 불러옵니다.

---

# 3. CLI 사용 방법

## 3.1 뉴스 기사 크롤링

```bash
python3 main.py scrape "https://example.com/news-article"
```

JSON 형식으로 출력:

```bash
python3 main.py scrape "https://example.com/news-article" --json
```

---

## 3.2 LLM 기반 기업 선정

OpenAI 사용:

```bash
python3 main.py select "https://example.com/news-article" --provider openai
```

Gemini 사용:

```bash
python3 main.py select "https://example.com/news-article" --provider gemini --json
```

---

## 3.3 OHLCV 데이터 수집

```bash
python3 main.py ohlcv "https://example.com/news-article" \
  --provider openai \
  --period 6mo \
  --interval 1d
```

```bash
python3 main.py ohlcv "https://example.com/news-article" \
  --provider gemini \
  --json
```

---

## 3.4 기술적 지표 계산

```bash
python3 main.py indicators "https://example.com/news-article" \
  --provider openai \
  --period 6mo \
  --interval 1d
```

최근 데이터 일부만 확인:

```bash
python3 main.py indicators "https://example.com/news-article" \
  --provider gemini \
  --recent-rows 5 \
  --json
```

---

## 3.5 재무지표 조회

```bash
python3 main.py fundamentals "https://example.com/news-article" \
  --provider openai \
  --period 6mo \
  --interval 1d
```

```bash
python3 main.py fundamentals "https://example.com/news-article" \
  --provider gemini \
  --json
```

---

## 3.6 투자 의견 생성

```bash
python3 main.py opinion "https://example.com/news-article" \
  --provider openai \
  --period 6mo \
  --interval 1d
```

```bash
python3 main.py opinion "https://example.com/news-article" \
  --provider gemini \
  --json
```

---

## 3.7 주가 차트 생성

```bash
python3 main.py plot "https://example.com/news-article" \
  --provider openai \
  --recent-points 60 \
  --clear-output-dir
```

```bash
python3 main.py plot "https://example.com/news-article" \
  --provider gemini \
  --output-dir plots \
  --json
```

---

## 3.8 통합 Report 실행

```bash
python3 main.py report "https://example.com/news-article" \
  --provider openai \
  --recent-points 60 \
  --output-dir plots \
  --clear-output-dir
```

```bash
python3 main.py report "https://example.com/news-article" \
  --provider gemini \
  --json
```

---

## 3.9 LLM Research Report 생성

```bash
python3 main.py research "https://example.com/news-article" \
  --provider openai \
  --period 6mo \
  --interval 1d
```

```bash
python3 main.py research "https://example.com/news-article" \
  --provider gemini \
  --json
```

---

## 3.10 Microsoft Word Report 생성

```bash
python3 main.py word-report "https://example.com/news-article" \
  --provider openai \
  --output-dir word_reports \
  --recent-points 60
```

```bash
python3 main.py word-report "https://example.com/news-article" \
  --provider gemini \
  --json
```

---

# 4. 전체 분석 파이프라인

```text
News URL
   │
   ▼
[Step 1]
뉴스 기사 크롤링
   │
   ▼
[Step 2]
LLM 기반 기업 선정
   │
   ▼
[Step 3]
Yahoo Finance OHLCV
   │
   ├───────────────┐
   ▼               ▼
[Step 4]        [Step 4B]
기술적 분석      OpenDART 재무 분석
   │               │
   └───────┬───────┘
           ▼
        [Step 5]
      투자 의견 생성
           │
           ▼
        [Step 6]
       차트 이미지 생성
           │
           ▼
     Research / Report
           │
           ▼
     Word Report / API
```

---

# 5. Step 1 — 뉴스 크롤러

크롤러는 뉴스 기사 URL을 입력받아 정규화된 기사 데이터를 반환합니다.

반환 필드:

- `url`
- `source`
- `title`
- `published_at`
- `text`
- `extractor`

구현 방식:

- Primary extractor: `trafilatura`
- Fallback extractor: `BeautifulSoup`

기사 데이터를 정규화해 Step 2의 LLM 입력으로 사용합니다.

---

# 6. Step 2 — LLM 기반 기업 선정

뉴스 기사 내용을 기반으로 관련성이 높은 KOSPI/KOSDAQ 기업을 선정합니다.

반환값:

- `article`
- `provider`
- `model`
- `selection.summary`
- `selection.companies`

각 기업 데이터:

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

---

# 7. Step 3 — OHLCV 데이터 수집

`ohlcv` 명령어는 Step 1~3을 연속으로 실행합니다.

처리 과정:

1. 뉴스 기사 크롤링
2. LLM 기반 기업 선정
3. Yahoo Finance OHLCV 데이터 조회

결과:

- `market_data.period`
- `market_data.interval`
- `market_data.companies`

각 기업별 반환값:

- `yahoo_symbol`
- `currency`
- `start_date`
- `end_date`
- `row_count`
- `latest_close`
- `latest_volume`
- `ohlcv`
- `error`

Yahoo Finance 심볼 규칙:

| 시장 | Yahoo Symbol |
|---|---|
| KOSPI | `XXXXXX.KS` |
| KOSDAQ | `XXXXXX.KQ` |

---

# 8. Step 4 — 기술적 분석

OHLCV 데이터를 기반으로 기술적 지표를 계산합니다.

현재 계산되는 지표:

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

각 기업의 기술적 분석 결과:

- `latest_indicators`
- `signal_context`
- `latest_signal`
- `recent_rows`
- `error`

## 시장 국면 분류

기술적 분석에서는 먼저 현재 시장을 다음 두 유형으로 분류합니다.

- `trend`
- `range`

시장 국면에 따라 다른 가중치를 적용하는 **Regime-aware Weighted Signal** 방식으로 최종 기술 신호를 계산합니다.

## 라이브러리

현재 프로젝트는 `pandas-ta` 대신 다음 라이브러리를 사용합니다.

```text
pandas-ta-classic
```

`pandas-ta-classic`은 `pandas-ta`와 호환되는 유지보수 버전입니다.

---

# 9. Step 4B — OpenDART 재무 분석

한국 상장기업의 재무 및 밸류에이션 정보를 OpenDART에서 수집합니다.

처리 과정:

1. 뉴스 기사 크롤링
2. 관련 기업 선정
3. 최신 주가 확보
4. DART 기업 코드 매핑
5. 최신 재무제표 및 재무비율 조회

주요 반환값:

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

사용하는 OpenDART 데이터:

```text
corpCode.xml
fnlttSinglAcntAll
fnlttSinglIndx
```

DART는 과거 주가 캔들 데이터를 제공하지 않기 때문에 OHLCV 및 기술적 분석은 계속 Yahoo Finance를 사용합니다.

---

# 10. Step 5 — 투자 의견 도출

Step 4에서 계산한 기술 신호를 바탕으로 투자 의견을 생성합니다.

반환 필드:

- `opinion`
- `score`
- `confidence`
- `risk_level`
- `rationale`
- `positives`
- `negatives`
- `score_breakdown`

지원되는 투자 의견:

```text
strong_buy
buy
hold
sell
strong_sell
```

Step 5에서는 Step 4의 Regime-aware Signal을 핵심 의사결정 엔진으로 사용하며, 추가로 다음 정보를 생성합니다.

- 신뢰도
- 위험 수준
- 긍정 요인
- 부정 요인
- 투자 의견 근거

---

# 11. Step 6 — 주가 차트 생성

선정된 기업의 최근 가격 및 거래량 데이터를 PNG 차트로 저장합니다.

기본 설정:

```text
period = 1d
interval = 1m
```

생성되는 차트:

- 주가 Line Chart
- 거래량 Bar Chart

Plot 결과:

- `plots.output_dir`
- `plots.period`
- `plots.interval`
- `plots.recent_points`
- `plots.companies[].plot_path`
- `plots.companies[].start_date`
- `plots.companies[].end_date`
- `plots.companies[].latest_close`
- `plots.companies[].error`

차트는 `matplotlib`을 이용해 PNG로 저장됩니다.

기존 출력 폴더를 비운 뒤 새 차트를 생성하려면:

```bash
--clear-output-dir
```

옵션을 사용합니다.

---

# 12. 통합 Report

`report` 명령어는 투자 의견 엔진과 차트 생성을 한 번에 수행합니다.

처리 과정:

1. 뉴스 기사 크롤링
2. 관련 기업 선정
3. Yahoo Finance OHLCV 조회
4. OpenDART 재무 분석
5. 기술적 지표 계산
6. 투자 의견 도출
7. 기업별 차트 생성

각 기업에 대해 두 종류의 차트를 생성합니다.

### 일봉 차트

```text
--daily-plot-period 3mo
--daily-plot-interval 1d
```

### 장중 차트

```text
--plot-period 1d
--plot-interval 1m
```

분석용 OHLCV 데이터와 차트용 OHLCV 요청은 별도로 처리됩니다.

이를 통해 기술적 지표의 일관성을 유지하면서 별도의 차트 데이터를 생성할 수 있습니다.

---

# 13. LLM Research Report

`research` 명령어는 전체 파이프라인의 분석 결과를 이용해 한국 기관형 주식 리서치 보고서를 생성합니다.

처리 과정:

1. 뉴스 기사 크롤링
2. 기업 선정
3. Yahoo Finance 데이터 조회
4. OpenDART 재무 분석
5. 기술적 분석
6. 투자 의견 생성
7. LLM 기반 리서치 보고서 작성

출력:

- `llm_report.prompt_version`
- `llm_report.body`

보고서 프롬프트는 **한국 Sell-side 리서치 스타일**을 기준으로 설계되어 있습니다.

모델은 구조화된 재무 및 기술 데이터를 입력받아 다음 내용을 중심으로 해석합니다.

- 투자 포인트
- 수익성
- 재무구조
- 현금흐름
- 밸류에이션
- 기술적 모멘텀
- 주요 위험 요인

외부 데이터를 임의로 생성하기보다 계산된 데이터를 근거로 해석하도록 설계되어 있습니다.

---

# 14. Microsoft Word Report

`word-report` 명령어는 분석 결과를 `.docx` 형식의 리서치 노트로 생성합니다.

포함 내용:

- 투자 의견 요약표
- 기업별 리서치 분석
- 기업별 주가 차트
- 재무 분석 테이블

출력:

- `word_report.document_path`
- `plots.output_dir`

Word 파일 생성에는 다음 라이브러리를 사용합니다.

```text
python-docx
```

문서 내에서 다음 요소는 서로 다른 스타일을 적용합니다.

- Report Title
- Section Heading
- Body Text
- Table
- Chart

---

# 15. Framer 연동 Backend API

API 서버 실행:

```bash
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

---

## 15.1 New Research API

Framer `/new_research` 페이지에서 뉴스 URL을 전달합니다.

```http
POST http://localhost:8000/api/new-research
Content-Type: application/json
```

Request:

```json
{
  "url": "https://example.com/news-article"
}
```

API 처리 과정:

1. 뉴스 기사 크롤링
2. 설정된 AI Provider로 기사 전달
3. 관련 기업 선정
4. Framer 레이아웃에 맞춰 정확히 3개 기업으로 제한
5. 분석 결과 반환

주요 반환값:

- `article`
- `selection.summary`
- `selection.companies`
- `summary`
- `companies`

---

## 15.2 Recommended Companies API

기업 추천 카드만 필요한 경우 사용합니다.

```http
POST http://localhost:8000/api/recommended-companies
Content-Type: application/json
```

Request:

```json
{
  "url": "https://example.com/news-article"
}
```

Response:

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

현재 Framer UI 구조 때문에 `companies` 배열은 항상 3개 항목을 반환하도록 제한됩니다.

---

## 15.3 Company Dashboard API

주가 차트 및 상세 기업 분석까지 필요한 경우 사용합니다.

```http
POST http://localhost:8000/api/company-dashboard
Content-Type: application/json
```

Request:

```json
{
  "url": "https://example.com/news-article"
}
```

각 기업에는 다음 데이터가 추가됩니다.

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

차트는 Base64로 JSON에 포함하지 않고 URL 형태로 제공합니다.

```text
/static/plots/...
```

프론트엔드에서는 다음과 같이 사용할 수 있습니다.

```html
<img src={company.daily_chart_url} />
```

이 방식은 이미지 데이터와 API 응답을 분리해 향후 실시간 가격 업데이트 기능을 가볍게 확장할 수 있도록 합니다.

---

## 15.4 브라우저 요청 예시

```javascript
const response = await fetch(
  "http://localhost:8000/api/recommended-companies",
  {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      url: newsUrl,
    }),
  }
)

const result = await response.json()
```

Framer 배포 환경에서는:

```text
http://localhost:8000
```

대신 실제 공개 HTTPS 백엔드 주소를 사용해야 합니다.

현재 CORS 허용 주소:

```text
https://ambiguous-replacement-035632.framer.app
```

---

# 16. 금융 캘린더 API

OpenAI Responses API의 웹 검색 기능을 활용해 주요 금융 일정을 수집합니다.

수집된 데이터는 SQLite에 저장되며 프론트엔드에 API 형태로 제공합니다.

기본 조회 범위:

```text
오늘 ~ 45일 이후
```

하루에 한 번씩 가까운 일정 구간을 갱신합니다.

모든 이벤트를 수집하기보다 **한국 투자자 관점에서 중요도가 높은 이벤트를 선별적으로 수집**하도록 설계되어 있습니다.

신뢰할 수 있는 이벤트가 없는 기간에는 빈 배열을 반환할 수 있습니다.

---

## 금융 일정 조회

```http
GET http://localhost:8000/api/financial-calendar
```

선택 Query Parameter:

| Parameter | 설명 |
|---|---|
| `start_date` | 시작 날짜 (`YYYY-MM-DD`) |
| `end_date` | 종료 날짜 (`YYYY-MM-DD`) |
| `category` | 이벤트 유형 |
| `importance` | 중요도 |
| `refresh_if_stale` | 오래된 데이터 자동 갱신 여부 |
| `model` | OpenAI 모델 Override |

### Category

- `rate`
- `economic_indicator`
- `earning`
- `policy`
- `market_holiday`
- `auction`
- `other`

### Importance

- `high`
- `medium`
- `low`

---

## Response 예시

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

---

## 금융 일정 강제 새로고침

```http
POST http://localhost:8000/api/financial-calendar/refresh
Content-Type: application/json
```

Request:

```json
{
  "start_date": "2026-07-19",
  "end_date": "2026-09-02"
}
```

---

## DB Seed

API 서버 실행 없이 금융 일정 데이터를 초기화할 수 있습니다.

```bash
python3 scripts/seed_financial_calendar.py
```

기본 설정:

```text
lookahead = 45일
chunk = 15일
```

직접 변경:

```bash
python3 scripts/seed_financial_calendar.py \
  --lookahead-days 90 \
  --chunk-days 15
```

---

# 17. 금융 캘린더 환경 변수

| 환경 변수 | 설명 | 기본값 |
|---|---|---|
| `OPENAI_API_KEY` | OpenAI API Key | 필수 |
| `OPENAI_FINANCIAL_CALENDAR_MODEL` | 금융 캘린더용 OpenAI 모델 | 기존 OpenAI 모델 |
| `CAM_FINANCIAL_CALENDAR_DB` | SQLite DB 경로 | `financial_calendar.db` |
| `CAM_FINANCIAL_CALENDAR_LOOKAHEAD_DAYS` | 기본 조회 기간 | `45` |
| `OPENAI_FINANCIAL_CALENDAR_TIMEOUT_SECONDS` | OpenAI 요청 Timeout | `90` |
| `OPENAI_FINANCIAL_CALENDAR_SEARCH_CONTEXT_SIZE` | 웹 검색 Context Size | `low` |
| `OPENAI_FINANCIAL_CALENDAR_ALLOWED_DOMAINS` | 허용 도메인 목록 | 주요 금융·공식 사이트 |
| `CAM_TIMEZONE` | 기준 시간대 | `Asia/Seoul` |

기본 허용 출처에는 다음과 같은 사이트가 포함됩니다.

- Federal Reserve
- Bank of Korea
- BLS
- BEA
- KOSTAT
- KRX
- DART
- Yahoo Finance
- Nasdaq
- 주요 기업 IR 사이트

---

# 18. 프로젝트의 주요 데이터 소스

| 데이터 | Source |
|---|---|
| 뉴스 기사 | 웹 기사 URL |
| 기업 선정 | OpenAI / Gemini |
| OHLCV | Yahoo Finance |
| 기술적 지표 | pandas-ta-classic |
| 재무제표 | OpenDART |
| 주가 차트 | matplotlib |
| Research Report | OpenAI / Gemini |
| Word Report | python-docx |
| 금융 일정 | OpenAI Web Search + 공식 Source |

---

# 19. 핵심 분석 지표

## 기술적 분석

- SMA 20
- SMA 50
- EMA 20
- RSI 14
- MACD 12/26/9
- Bollinger Bands 20/2
- ATR 14
- ADX 14
- +DI / -DI
- Stochastic 14/3/3
- OBV
- Volume SMA 20

## 재무 분석

- PER
- PBR
- PCR
- EV/EBITDA
- EPS
- BPS
- EBITDA
- Cash DPS
- Dividend Yield
- ROE
- Debt Ratio
- Current Ratio
- Market Cap
- Shares Outstanding

---

# 20. 기술 스택

### Backend

- Python
- FastAPI
- Uvicorn

### AI

- OpenAI
- Gemini

### Data

- Yahoo Finance
- OpenDART

### Analysis

- pandas
- pandas-ta-classic

### Visualization

- matplotlib

### Document

- python-docx

### Database

- SQLite

### Frontend

- Framer
- React Code Components

---

# 21. 프로젝트 목표

이 프로젝트의 목표는 뉴스 기반 투자 아이디어 탐색부터 기업 분석, 기술적·재무적 분석, 리서치 보고서 생성까지의 과정을 하나의 자동화된 파이프라인으로 구축하는 것입니다.

최종적으로 다음과 같은 흐름을 자동화하는 것을 목표로 합니다.

```text
News
 ↓
AI Company Selection
 ↓
Market Data
 ↓
Technical Analysis
 ↓
Financial Analysis
 ↓
Investment Opinion
 ↓
Research Report
 ↓
Chart / Word Report
 ↓
Frontend
```

이를 통해 뉴스 이벤트를 빠르게 기업 분석으로 연결하고, 정형 데이터와 LLM을 결합해 구조화된 투자 리서치 결과를 생성하는 것을 목표로 합니다.
```