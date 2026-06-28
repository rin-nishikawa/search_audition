import os
import re
import xml.etree.ElementTree as ET

import requests
from openai import OpenAI
from pydantic import BaseModel
from tavily import TavilyClient

# from google import genai
# from google.genai import types


class AuditionInfo(BaseModel):
    title: str
    public_date: str      # "NA" または公演日文字列
    conditions: str
    deadline: str | None  # "YYYY-MM-DD" または None
    url: str


class NewsItem(BaseModel):
    title: str
    source: str


class _NewsSentences(BaseModel):
    items: list[str]


def format_news(news_items: list[NewsItem]) -> list[str]:
    if not news_items:
        return []
    titles = "\n".join(f"{i + 1}. {item.title}" for i, item in enumerate(news_items))
    try:
        client = _openai_client()
        response = client.responses.parse(
            model="gpt-5-chat",
            input=[
                {
                    "role": "system",
                    "content": (
                        "ニュースのタイトルを、「は」「を」「が」「だ」「である」などを補い、"
                        "自然な読みやすい日本語の1文に書き換えてください。"
                        "元のリストと同じ順序・同じ件数で返してください。"
                    ),
                },
                {"role": "user", "content": titles},
            ],
            text_format=_NewsSentences,
        )
        result = response.output_parsed
        return result.items if result else [item.title for item in news_items]
    except Exception as e:
        print(f"[openai] ニュース整形失敗: {e}")
        return [item.title for item in news_items]


def _openai_client() -> OpenAI:
    return OpenAI(
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        base_url=os.environ["AZURE_OPENAI_ENDPOINT"],
    )


# def _gemini_client() -> genai.Client:
#     return genai.Client(api_key=os.environ["GEMINI_API_KEY"])


def _tavily_client() -> TavilyClient:
    return TavilyClient(api_key=os.environ["TAVILY_API_KEY"])


def _strip_html(html: str) -> str:
    html = re.sub(r"<(script|style)[^>]*>.*?</(script|style)>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<[^>]+>", "", html)
    html = re.sub(r"\s+", " ", html).strip()
    return html[:12000]


def _fetch_audition_from_html(url: str) -> AuditionInfo | None:
    try:
        resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        text = _strip_html(resp.text)
    except Exception as e:
        print(f"[fetch] {url} 取得失敗: {e}")
        return None

    try:
        client = _openai_client()
        response = client.responses.parse(
            model="gpt-5",
            input=[
                {
                    "role": "system",
                    "content": (
                        "最新のオーディション情報を1件だけ抽出してください。"
                        "締切日は YYYY-MM-DD 形式で返してください。不明な場合は null にしてください。"
                        "公演日が不明な場合は public_date を \"NA\" にしてください。"
                    ),
                },
                {"role": "user", "content": f"以下は {url} のページです。\n\n{text}"},
            ],
            text_format=AuditionInfo,
        )
        result = response.output_parsed
        result.url = url
        return result
    except Exception as e:
        print(f"[openai] {url} 抽出失敗: {e}")
        return None


def fetch_shiki() -> AuditionInfo | None:
    return _fetch_audition_from_html("https://www.shiki.jp/group/audition/")


class _AuditionInfoList(BaseModel):
    items: list[AuditionInfo]


def fetch_horipro() -> list[AuditionInfo]:
    url = "https://www.horipro.co.jp/audition/"
    try:
        resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        text = _strip_html(resp.text)
    except Exception as e:
        print(f"[fetch] {url} 取得失敗: {e}")
        return []

    try:
        client = _openai_client()
        response = client.responses.parse(
            model="gpt-4o-mini",
            input=[
                {
                    "role": "system",
                    "content": (
                        "オーディション情報を最大3件抽出してください。"
                        "締切日は YYYY-MM-DD 形式で返してください。不明な場合は null にしてください。"
                        'public_date が不明な場合は "NA" にしてください。'
                    ),
                },
                {"role": "user", "content": f"以下は {url} のページです。\n\n{text}"},
            ],
            text_format=_AuditionInfoList,
        )
        parsed = response.output_parsed
        if parsed is None:
            return []
        items = parsed.items[:3]
        for item in items:
            item.url = url
        return items
    except Exception as e:
        print(f"[openai] {url} 抽出失敗: {e}")
        return []


def fetch_toho() -> AuditionInfo | None:
    try:
        tavily = _tavily_client()
        results = tavily.search(query="東宝ステージ オーディション 2026", max_results=3)
        items = results.get("results", [])
        if not items:
            return None
        combined = "\n\n".join(f"URL: {r['url']}\n{r.get('content', '')}" for r in items)
        top_url = items[0]["url"]
    except Exception as e:
        print(f"[tavily] 東宝検索失敗: {e}")
        return None

    try:
        client = _openai_client()
        response = client.responses.parse(
            model="gpt-4o-mini",
            input=[
                {
                    "role": "system",
                    "content": (
                        "以下は東宝のオーディションに関する検索結果です。"
                        "最新のオーディション情報を1件だけ抽出してください。"
                        "締切日は YYYY-MM-DD 形式で返してください。不明な場合は null にしてください。"
                        "公演日が不明な場合は public_date を \"NA\" にしてください。"
                    ),
                },
                {"role": "user", "content": combined},
            ],
            text_format=AuditionInfo,
        )
        result = response.output_parsed
        if not result.url or result.url == "NA":
            result.url = top_url
        return result
    except Exception as e:
        print(f"[openai] 東宝抽出失敗: {e}")
        return None


def fetch_news(_today: str = "") -> list[NewsItem]:
    try:
        resp = requests.get(
            "https://news.yahoo.co.jp/rss/topics/top-picks.xml",
            timeout=15,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        items = root.findall("./channel/item")[:5]
        return [
            NewsItem(title=item.findtext("title") or "", source="")
            for item in items
            if item.findtext("title")
        ]
    except Exception as e:
        print(f"[rss] ニュース取得失敗: {e}")
        return []
