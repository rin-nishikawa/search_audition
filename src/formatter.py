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


def build_email(
    state: dict,
    horipro_items: list[dict],
    news_items: list[str],
    today: date,
) -> tuple[str, str]:
    date_str = today.strftime("%Y/%m/%d")
    subject = f"🎭 今日の報告 {date_str}"

    lines = [
        DIVIDER,
        "📰 今日のニュース",
        DIVIDER,
        "",
    ]

    for i, sentence in enumerate(news_items, 1):
        lines.append(f"{i}. {sentence}")
        lines.append("")

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
