from datetime import date

DIVIDER = "━" * 20


def _is_active(entry: dict, today: date) -> bool:
    dl = entry.get("deadline")
    if not dl:
        return False
    try:
        return date.fromisoformat(dl) >= today
    except ValueError:
        return False


def _format_org(label: str, entry: dict | None, today: date) -> str:
    lines = [f"【{label}】"]
    if entry and _is_active(entry, today):
        lines.append(f"概要：{entry['title']}")
        lines.append(f"公演日：{entry['public_date']}")
        lines.append(f"応募条件：{entry['conditions']}")
        lines.append(f"応募締切：{entry['deadline']}")
        lines.append(f"URL：{entry['url']}")
    else:
        lines.append("新着情報なし")
    return "\n".join(lines)


def _format_org_list(label: str, entries: list[dict], today: date) -> str:
    lines = [f"【{label}】"]
    if not entries:
        lines.append("新着情報なし")
        return "\n".join(lines)
    visible = [e for e in entries if _is_active(e, today)]
    if not visible:
        lines.append("新着情報なし")
        return "\n".join(lines)
    for entry in visible:
        lines.append(f"概要：{entry['title']}")
        lines.append(f"公演日：{entry['public_date']}")
        lines.append(f"応募条件：{entry['conditions']}")
        lines.append(f"応募締切：{entry['deadline']}")
        lines.append(f"URL：{entry['url']}")
        lines.append("")
    return "\n".join(lines).rstrip()


def _format_zenn(articles: list) -> str:
    lines = [f"【Zenn 注目記事 Top5】"]
    if not articles:
        lines.append("記事を取得できませんでした")
        return "\n".join(lines)
    for i, a in enumerate(articles, 1):
        lines.append(f"{i}. {a.title}")
        lines.append(f"   ❤️  いいね：{a.liked_count}　最終更新：{a.body_updated_at}")
        lines.append(f"   URL：{a.url}")
        lines.append("")
    return "\n".join(lines).rstrip()


def build_email(
    state: dict | None,
    horipro_items: list[dict],
    news_items: list[str],
    today: date,
    zenn_articles: list | None = None,
    news_urls: list[str] | None = None,
) -> tuple[str, str]:
    date_str = today.strftime("%Y/%m/%d")
    subject = f"🎭 今日の報告 {date_str}"

    lines = [
        DIVIDER,
        "📰 今日のニュース",
        DIVIDER,
        "",
    ]

    urls = news_urls or []
    for i, sentence in enumerate(news_items, 1):
        lines.append(f"{i}. {sentence}")
        if i <= len(urls) and urls[i - 1]:
            lines.append(f"   URL：{urls[i - 1]}")
        lines.append("")

    lines += [
        DIVIDER,
        "📝 Zenn 最新記事（いいね数Top5）",
        DIVIDER,
        "",
        _format_zenn(zenn_articles or []),
        "",
    ]

    if state is not None:
        lines += [
            DIVIDER,
            "🎤 オーディション情報",
            DIVIDER,
            "",
            _format_org("劇団四季", state.get("shiki"), today),
            "",
            _format_org("東宝", state.get("toho"), today),
            "",
            _format_org_list("ホリプロ", horipro_items, today),
            "",
        ]

    return subject, "\n".join(lines)
