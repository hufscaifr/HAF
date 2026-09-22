import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
OPENDART_API_KEY = os.environ["OPENDART_API_KEY"]

# 텔레그램 전송은 선택 기능이라 없어도 파이프라인은 돌아간다 (report/telegram_notify.py 참고).
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# 외부 서버(api.caifr.com) DB 업로드도 선택 기능. 서버 개발자가 실제 경로/토큰을 확정하면
# .env의 REPORT_API_URL / REPORT_API_TOKEN만 바꾸면 된다 (report/api_upload.py 참고).
# 토큰은 서버 쪽에서 `openssl rand -hex 32`로 발급 예정 - 발급되면 .env에 넣어주면 됨.
REPORT_API_URL = os.environ.get("REPORT_API_URL", "https://api.caifr.com/api/reports")
REPORT_API_TOKEN = os.environ.get("REPORT_API_TOKEN")
REPORT_AUTHOR = "제갈민찬"

# 역할별 OpenAI 모델. 품질/비용 균형이 안 맞으면 여기만 바꾸면 됨.
MODEL_LIGHT = "gpt-5.6-luna"     # 요약, 핵심 문장 추출, 제목 등 단순 작업
MODEL_STANDARD = "gpt-5.6-terra"  # 기업 선정, 투자분석/기술적분석 본문 등 품질 중요 작업

KRX_MASTER_CACHE = BASE_DIR / "data" / "krx_master_cache.csv"
KRX_MASTER_MAX_AGE_DAYS = 7

TEMPLATE_PATH = BASE_DIR / "report" / "template.docx"

# ~/Documents로 옮기면 팝업이 없어질까 시도해봤으나, 오히려 Word의 AppleScript 자동화가
# Documents 폴더에 PDF를 저장할 때 -1708(메시지 인식 못함) 오류로 조용히 실패하는 걸 확인함
# (원래 이 프로젝트 폴더로 저장할 때는 문제없이 성공). 그래서 원래 위치로 되돌림.
OUTPUT_DIR = BASE_DIR / "output"
CHART_TMP_DIR = OUTPUT_DIR / ".charts_tmp"

# 기술적 지표 파라미터 (원본 n8n 시트 수식의 정확한 값은 확인 불가 → 업계 표준값 채택)
STOCK_HISTORY_RANGE = "3y"
RSI_LENGTH = 14
STOCH_RSI_LENGTH = 14
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
BB_LENGTH = 20
BB_STD = 2
MA_PERIODS = (5, 20, 60, 120)
VOLUME_AVG_PERIOD = 20
TECH_CHART_LOOKBACK_DAYS = 60  # 원본 프롬프트가 "최근 60거래일" 지표를 근거로 분석