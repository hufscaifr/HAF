"""launchd가 매일 아침 실행하는 진입점.
한국거래소(KRX) 개장일이 아니면(주말·공휴일) 아무것도 하지 않고 종료한다."""
import sys
import traceback
from datetime import datetime

import exchange_calendars as xcals

from main import run_auto


def is_krx_trading_day(date) -> bool:
    calendar = xcals.get_calendar("XKRX")
    return calendar.is_session(date.strftime("%Y-%m-%d"))


def main():
    today = datetime.now()
    print(f"=== {today.isoformat()} 실행 시작 ===")

    if not is_krx_trading_day(today):
        print("오늘은 한국거래소 휴장일입니다. 건너뜁니다.")
        return

    try:
        out_path, pdf_path = run_auto()
        print(f"완료: {out_path}")
        if pdf_path:
            print(f"PDF: {pdf_path}")
    except Exception:
        print("자동 실행 중 오류 발생:")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
