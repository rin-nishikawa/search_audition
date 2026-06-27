from datetime import date

from dotenv import load_dotenv

load_dotenv()

from src import collectors, formatter, mailer
from src import state as state_mod


def main() -> None:
    today = date.today()

    print("オーディション情報を収集中...")
    shiki = collectors.fetch_shiki()
    toho = collectors.fetch_toho()
    horipro = collectors.fetch_horipro()

    print("ニュースを取得中...")
    news = collectors.fetch_news(today.isoformat())

    print("状態を更新中...")
    current_state = state_mod.load()
    state_mod.update(current_state, "shiki", shiki, today)
    state_mod.update(current_state, "toho", toho, today)
    state_mod.update_list(current_state, "horipro", horipro, today)

    visibility = {
        org: state_mod.should_display(current_state.get(org), today)
        for org in ("shiki", "toho")
    }
    horipro_items = state_mod.display_list(current_state.get("horipro"), today)

    subject, body = formatter.build_email(current_state, visibility, horipro_items, news, today)

    state_mod.save(current_state)

    print("メールを送信中...")
    mailer.send(subject, body)
    print(f"送信完了: {subject}")


if __name__ == "__main__":
    main()
