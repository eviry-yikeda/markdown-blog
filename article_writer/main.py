import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from agents import FINISH_MESSAGE, collector_agent, reviewer_agent, writer_agent


def collect_info(msg: str, clear_thread: bool = False) -> str:
    if clear_thread:
        collector_agent.clear_thread_id()
    return collector_agent.invoke(msg)


def create_article(msg: str, clear_thread: bool = False) -> str:
    if clear_thread:
        writer_agent.clear_thread_id()
    return writer_agent.invoke(msg)


def review_article(article: str, clear_thread: bool = False) -> str:
    if clear_thread:
        reviewer_agent.clear_thread_id()
    return reviewer_agent.invoke(article)


def export_article(topic: str, article: str) -> None:
    now = datetime.now(tz=ZoneInfo("Asia/Tokyo"))
    data = (
        f"---\ntitle: {topic}\npubDate: {now.date()}\ndescription: {topic}\n"
        f'author: "GPT-4"\nlayout: "@/layouts/BlogLayout.astro"\ntags: []\n---\n{article}\n'
    )
    Path("articles").mkdir(exist_ok=True, parents=True)
    fname = f"articles/{now.strftime('%Y%m%d%H%M%S')}.md"
    with open(fname, "w") as f:
        f.write(data)


def main(topic: str):
    info = collect_info(topic, clear_thread=True)
    is_first_review = True
    print("--INFO--")
    print(info)
    print("collector_tid", collector_agent.settings.thread_id)
    while True:
        article = create_article(
            f"{topic}に関する記事を執筆しています。参考情報は以下の通りです。\n{info}",
            clear_thread=True,
        )
        print("--ARTICLE--")
        print(article)
        print("writer_tid", writer_agent.settings.thread_id)
        if FINISH_MESSAGE not in article:
            info = collect_info(
                f"{topic}に関する記事を執筆するための情報を収集しています。以下の通り追加の情報を収集してください。\n{info}"
            )
            print("--INFO--")
            print(info)
            print("collector_tid", collector_agent.settings.thread_id)
        else:
            info = review_article(
                f"{topic}に関する記事を執筆しました。以下の記事をレビューしてください。\n{article}",
                clear_thread=is_first_review,
            )
            is_first_review = False
            print("--REVIEW--")
            print(info)
            print("reviewer_tid", writer_agent.settings.thread_id)
            if FINISH_MESSAGE in info:
                # info = input("追加指示があれば入力してください：")
                # if not info:
                    break

    export_article(article=article.replace(FINISH_MESSAGE, ""), topic=topic)


if __name__ == "__main__":
    args = sys.argv

    topic = args[1] if len(args) > 1 else "Youtubeにおける美容トレンドはなんですか？"
    main(topic)
