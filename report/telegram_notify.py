from pathlib import Path

import requests

import config

_API_BASE = "https://api.telegram.org"


def _post(method: str, data: dict, files: dict | None = None) -> bool:
    url = f"{_API_BASE}/bot{config.TELEGRAM_BOT_TOKEN}/{method}"
    resp = requests.post(url, data=data, files=files, timeout=60)
    resp.raise_for_status()
    return True


def send_report(pdf_path: Path | None, message_text: str, card_path: Path | None = None) -> bool:
    """생성된 리포트를 텔레그램으로 전송한다.
    card_path가 있으면 요약 카드 이미지를 message_text와 함께 먼저 보낸다. pdf_path가 있으면
    PDF도 이어서 보낸다 (docx는 절대 보내지 않음 - PDF가 없으면 그 시점엔 문서 없이 카드만
    보내고, 나중에 retry_pdf.py가 PDF를 확보하면 그때 별도로 전송한다).
    토큰/챗ID가 설정 안 돼있거나 전송이 실패해도 파이프라인은 중단하지 않고 False를 반환한다."""
    if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
        return False

    try:
        if card_path and card_path.exists():
            with open(card_path, "rb") as f:
                _post(
                    "sendPhoto",
                    {"chat_id": config.TELEGRAM_CHAT_ID, "caption": message_text[:1024]},
                    {"photo": (card_path.name, f)},
                )
        if pdf_path and pdf_path.exists():
            doc_data = {"chat_id": config.TELEGRAM_CHAT_ID}
            if not card_path:
                doc_data["caption"] = message_text[:1024]
            with open(pdf_path, "rb") as f:
                _post("sendDocument", doc_data, {"document": (pdf_path.name, f)})
        elif not card_path:
            # 카드도 PDF도 없으면 최소한 텍스트라도 보낸다
            _post("sendMessage", {"chat_id": config.TELEGRAM_CHAT_ID, "text": message_text})
        return True
    except Exception as e:
        print(f"텔레그램 전송 실패 (건너뜀): {e}")
        return False
