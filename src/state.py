import json
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.collectors import AuditionInfo

STATE_FILE = Path(__file__).parent.parent / "state.json"
ORGS = ("shiki", "toho", "horipro")


def load() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {org: None for org in ORGS}


def save(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def update_list(state: dict, org: str, fetched: list[AuditionInfo], today: date) -> None:
    current: list[dict] = []

    for f in fetched:
        if f.deadline and date.fromisoformat(f.deadline) < today:
            continue
        current.append({
            "title": f.title,
            "public_date": f.public_date,
            "conditions": f.conditions,
            "deadline": f.deadline,
            "url": f.url,
        })

    state[org] = current


def get_list(state: dict, org: str) -> list[dict]:
    entries = state.get(org)
    return entries if isinstance(entries, list) else []


def update(state: dict, org: str, fetched: AuditionInfo | None, today: date) -> None:
    current = state.get(org)

    # 期限切れリセット
    if current and current.get("deadline"):
        if date.fromisoformat(current["deadline"]) < today:
            state[org] = None

    if fetched is None:
        return

    if fetched.deadline and date.fromisoformat(fetched.deadline) < today:
        return

    state[org] = {
        "title": fetched.title,
        "public_date": fetched.public_date,
        "conditions": fetched.conditions,
        "deadline": fetched.deadline,
        "url": fetched.url,
    }
