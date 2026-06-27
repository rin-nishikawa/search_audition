import json
from datetime import date
from pathlib import Path

from src.collectors import AuditionInfo

STATE_FILE = Path(__file__).parent.parent / "state.json"
ORGS = ("shiki", "toho", "horipro")


def load() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {org: None for org in ORGS}


def save(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def should_display(entry: dict | None, today: date) -> bool:
    if entry is None:
        return False
    first_seen = date.fromisoformat(entry["first_seen"])
    if (today - first_seen).days > 7:
        return False
    deadline = entry.get("deadline")
    if deadline and date.fromisoformat(deadline) < today:
        return False
    return True


def update_list(state: dict, org: str, fetched: list[AuditionInfo], today: date) -> None:
    raw = state.get(org)
    current: list[dict] = raw if isinstance(raw, list) else []

    # 期限切れ削除
    current = [
        e for e in current
        if not (e.get("deadline") and date.fromisoformat(e["deadline"]) < today)
    ]

    current_titles = {e["title"] for e in current}
    for f in fetched:
        if f.title not in current_titles:
            current.append({
                "title": f.title,
                "public_date": f.public_date,
                "conditions": f.conditions,
                "deadline": f.deadline,
                "url": f.url,
                "first_seen": today.isoformat(),
            })

    state[org] = current


def display_list(entries: list | None, today: date) -> list[dict]:
    if not entries:
        return []
    return [e for e in entries if should_display(e, today)]


def update(state: dict, org: str, fetched: AuditionInfo | None, today: date) -> None:
    current = state.get(org)

    # 期限切れリセット
    if current and current.get("deadline"):
        if date.fromisoformat(current["deadline"]) < today:
            state[org] = None
            current = None

    if fetched is None:
        return

    # 新着検知（タイトル変化 or 初回）
    is_new = current is None or current.get("title") != fetched.title

    if is_new:
        state[org] = {
            "title": fetched.title,
            "public_date": fetched.public_date,
            "conditions": fetched.conditions,
            "deadline": fetched.deadline,
            "url": fetched.url,
            "first_seen": today.isoformat(),
        }
