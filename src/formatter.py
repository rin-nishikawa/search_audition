from datetime import date

from src.collectors import NewsItem

DIVIDER = "━" * 20


def _format_org(label: str, entry: dict | None, visible: bool) -> str:
    lines = [f"【{label}】"]
    if entry and visible:
        lines.append(f"概要：{entry['title']}")
        lines.append(f"公演日：{entry['public_date']}")
        lines.append(f"応募条件：{entry['conditions']}")
        lines.append(f"応募締切：{entry.get('deadline') or '不明'}")
        lines.append(f"URL：{entry['url']}")
    else:
        lines.append("新着情報なし")
    return "\n".join(lines)


def _format_org_list(label: str, entries: list[dict]) -> str:
    lines = [f"【{label}】"]
    if not entries:
        lines.append("新着情報なし")
        return "\n".join(lines)
    visible = [e for e in entries if e.get("deadline")]
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


def build_email(
    state: dict,
    visibility: dict,
    horipro_items: list[dict],
    news_items: list[NewsItem],
    today: date,
) -> tuple[str, str]:
    date_str = today.strftime("%Y/%m/%d")
    subject = f"🎭 今日の報告 {date_str}"

    lines = [
        DIVIDER,
        "🎤 オーディション情報",
        DIVIDER,
        "",
        _format_org("劇団四季", state.get("shiki"), visibility.get("shiki", False)),
        "",
        _format_org("東宝", state.get("toho"), visibility.get("toho", False)),
        "",
        _format_org_list("ホリプロ", horipro_items),
        "",
        DIVIDER,
        "📰 今日のニュース",
        DIVIDER,
        "",
    ]

    for i, item in enumerate(news_items, 1):
        lines.append(f"{i}. {item.title}")
        lines.append("")

    return subject, "\n".join(lines)
