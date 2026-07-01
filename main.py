from datetime import datetime, timezone, timedelta

from dotenv import load_dotenv

load_dotenv()

from src import collectors, formatter, mailer
from src import state as state_mod


def main() -> None:
    JST = timezone(timedelta(hours=9))
    today = datetime.now(JST).date()
    is_audition_day = today.day % 5 == 0

    print("ニュースを取得中...")
    news = collectors.fetch_news(today.isoformat())
    news_sentences = collectors.format_news(news)

    audition_state = None
    horipro_items: list = []

    if is_audition_day:
        print("オーディション情報を収集中...")
        shiki = collectors.fetch_shiki()
        toho = collectors.fetch_toho()
        horipro = collectors.fetch_horipro()

        print("状態を更新中...")
        current_state = state_mod.load()
        state_mod.update(current_state, "shiki", shiki)
        state_mod.update(current_state, "toho", toho)
        state_mod.update_list(current_state, "horipro", horipro)

        horipro_items = state_mod.get_list(current_state, "horipro")
        audition_state = current_state

        state_mod.save(current_state)
    else:
        print("本日はオーディション収集日ではありません（5の倍数の日のみ）")

    subject, body = formatter.build_email(
        audition_state, horipro_items, news_sentences, today,
    )

    print("メールを送信中...")
    mailer.send(subject, body)
    print(f"送信完了: {subject}")


if __name__ == "__main__":
    main()
