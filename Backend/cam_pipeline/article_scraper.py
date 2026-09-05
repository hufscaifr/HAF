from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from typing import Any, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

try:
    import trafilatura
except ImportError:  # pragma: no cover
    trafilatura = None


DEFAULT_TIMEOUT = 20
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
}
DATE_META_KEYS = (
    "article:published_time",
    "article:modified_time",
    "og:published_time",
    "pubdate",
    "publishdate",
    "timestamp",
    "dc.date",
    "date",
)
CONTENT_SELECTORS = (
    "article",
    "[itemprop='articleBody']",
    "[data-module='ArticleBody']",
    ".article-body",
    ".article__body",
    ".story-body",
    ".news-content",
    ".news-body",
    ".post-content",
    ".entry-content",
    "#articleBody",
    "#newsct_article",
)
BOILERPLATE_PATTERNS = (
    "Sign up for free newsletters",
    "Get this delivered to your inbox",
    "All Rights Reserved",
    "A Versant Media Company",
    "Data is a real-time snapshot",
    "Market Data and Analysis",
    "Got a confidential news tip?",
)


@dataclass
class ArticleContent:
    url: str
    source: Optional[str]
    title: Optional[str]
    published_at: Optional[str]
    text: str
    extractor: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def scrape_article(url: str, timeout: int = DEFAULT_TIMEOUT) -> dict[str, Any]:
    html = fetch_html(url, timeout=timeout)

    article = extract_with_trafilatura(url, html)
    if article and article.text.strip():
        return article.to_dict()

    return extract_with_bs4(url, html).to_dict()


def fetch_html(url: str, timeout: int = DEFAULT_TIMEOUT) -> str:
    response = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
    response.raise_for_status()
    return response.text


def extract_with_trafilatura(url: str, html: str) -> Optional[ArticleContent]:
    if trafilatura is None:
        return None

    extracted = trafilatura.extract(
        html,
        url=url,
        output_format="json",
        with_metadata=True,
        include_comments=False,
        include_tables=False,
    )
    if not extracted:
        return None

    payload = json.loads(extracted)
    text = normalize_text(payload.get("text"))
    if not text:
        return None

    return ArticleContent(
        url=url,
        source=payload.get("sitename") or domain_from_url(url),
        title=payload.get("title"),
        published_at=payload.get("date"),
        text=text,
        extractor="trafilatura",
    )


def extract_with_bs4(url: str, html: str) -> ArticleContent:
    soup = BeautifulSoup(html, "html.parser")

    for element in soup(["script", "style", "noscript", "iframe", "svg"]):
        element.decompose()

    title = extract_title(soup)
    published_at = extract_published_at(soup)
    text = extract_body_text(soup)

    return ArticleContent(
        url=url,
        source=extract_source(soup, url),
        title=title,
        published_at=published_at,
        text=text,
        extractor="beautifulsoup4",
    )


def extract_title(soup: BeautifulSoup) -> Optional[str]:
    candidates = (
        soup.find("meta", attrs={"property": "og:title"}),
        soup.find("meta", attrs={"name": "twitter:title"}),
        soup.find("h1"),
        soup.find("title"),
    )
    for candidate in candidates:
        if not candidate:
            continue
        content = candidate.get("content") if candidate.name == "meta" else candidate.get_text()
        if content:
            return normalize_text(content)
    return None


def extract_published_at(soup: BeautifulSoup) -> Optional[str]:
    json_ld_date = extract_json_ld_date(soup)
    if json_ld_date:
        return json_ld_date

    for key in DATE_META_KEYS:
        tag = soup.find("meta", attrs={"property": key}) or soup.find(
            "meta", attrs={"name": key}
        )
        if tag and tag.get("content"):
            return normalize_text(tag["content"])

    time_tag = soup.find("time")
    if time_tag:
        return normalize_text(time_tag.get("datetime") or time_tag.get_text())

    return None


def extract_json_ld_date(soup: BeautifulSoup) -> Optional[str]:
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw_text = script.string or script.get_text()
        if not raw_text or not raw_text.strip():
            continue

        try:
            payload = json.loads(raw_text)
        except json.JSONDecodeError:
            continue

        date_value = find_date_in_json_ld(payload)
        if date_value:
            return normalize_text(date_value)

    return None


def find_date_in_json_ld(payload: Any) -> Optional[str]:
    if isinstance(payload, dict):
        for key in ("datePublished", "dateModified", "uploadDate"):
            if payload.get(key):
                return str(payload[key])
        for value in payload.values():
            found = find_date_in_json_ld(value)
            if found:
                return found

    if isinstance(payload, list):
        for item in payload:
            found = find_date_in_json_ld(item)
            if found:
                return found

    return None


def extract_body_text(soup: BeautifulSoup) -> str:
    for selector in CONTENT_SELECTORS:
        node = soup.select_one(selector)
        text = text_from_node(node)
        if text:
            return text

    paragraphs = clean_paragraphs(
        [
        normalize_text(p.get_text(" ", strip=True))
        for p in soup.find_all("p")
        ]
    )
    if paragraphs:
        return "\n\n".join(paragraphs)

    body_text = normalize_text(soup.get_text(" ", strip=True))
    return body_text


def text_from_node(node: Any) -> str:
    if node is None:
        return ""

    paragraphs = clean_paragraphs(
        [
        normalize_text(p.get_text(" ", strip=True))
        for p in node.find_all("p")
        ]
    )
    if paragraphs:
        return "\n\n".join(paragraphs)

    return normalize_text(node.get_text(" ", strip=True))


def clean_paragraphs(paragraphs: list[str]) -> list[str]:
    cleaned: list[str] = []
    seen: set[str] = set()

    for paragraph in paragraphs:
        if len(paragraph) < 30:
            continue
        if any(pattern in paragraph for pattern in BOILERPLATE_PATTERNS):
            continue
        if paragraph in seen:
            continue
        seen.add(paragraph)
        cleaned.append(paragraph)

    return cleaned


def extract_source(soup: BeautifulSoup, url: str) -> Optional[str]:
    tag = soup.find("meta", attrs={"property": "og:site_name"}) or soup.find(
        "meta", attrs={"name": "application-name"}
    )
    if tag and tag.get("content"):
        return normalize_text(tag["content"])
    return domain_from_url(url)


def normalize_text(value: Optional[str]) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def domain_from_url(url: str) -> Optional[str]:
    netloc = urlparse(url).netloc
    return netloc.replace("www.", "") if netloc else None
