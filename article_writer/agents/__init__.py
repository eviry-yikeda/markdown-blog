from datetime import datetime, timedelta
from typing import Callable
from zoneinfo import ZoneInfo

from langchain_community.tools.bing_search import BingSearchRun

from .bing_search import EviryBingSearchAPIWrapper
from .core import AgentBase, AgentSettings

FINISH_MESSAGE = "FB8C5B7A-5F43-4754-A54E-AE6A9718290A"
TREND_THRESH = 15
_now: Callable[..., datetime] = lambda: datetime.now(ZoneInfo("Asia/Tokyo"))
_oldest_datetime: Callable[..., datetime] = lambda: _now() - timedelta(
    days=TREND_THRESH
)
_bing_search = BingSearchRun(api_wrapper=EviryBingSearchAPIWrapper())
_bing_search.api_wrapper.k = 10
_bing_search.api_wrapper.search_kwargs = {
    "mkt": "ja-JP",
    "freshness": f"{_oldest_datetime().strftime('%Y-%m-%d')}..{_now().strftime('%Y-%m-%d')}",
}
_tools = [_bing_search]

collector_instructions = f"""
# 目的
トレンドマスターは、YouTubeとTikTokの動画コンテンツに関連するリアルタイムのトレンドを収集し記事を生成するために情報を収集するGPTです。このGPTは、YouTubeとTikTok上での人気動画、バイラルトレンド、クリエイターの活動、視聴者の反応など、動画コンテンツに関連するトピックを中心に情報を収集します。
情報はbing-searchを使用して最新の情報を収集します。

# トレンド定義
1. トレンドマスターが取り扱うトレンドはYouTubeとTikTokの動画コンテンツの構成、話題、サムネイル、動画内で使用される楽曲、動画内で扱われるトピックを指します。
2. トレンドマスターが取り扱うトレンドは日本国内のトレンドに限定します。
3. トレンドマスターが取り扱うトレンドは{_oldest_datetime().strftime("%Y年%m月%d日")}以降のトレンドです。それ以前はトレンドとして扱いません。

# 方法
1. ユーザの問い合わせトピックに関連するYouTubeとTikTokのトレンドに関する情報をBing検索します。
2. 検索した情報を記事の執筆者が参考にできるようにまとめて出力します。このとき情報収集で参考にしたURLを参考文献として挿入します。
"""

collector_agent = AgentBase(
    AgentSettings(
        name="トレンドマスター(collector)",
        instructions=collector_instructions,
        tools=_tools,
        model="gpt-4-0125-preview",
        assistant_id="asst_UdMKX8QM4DOLePodJTlg69Ax",
        thread_id="thread_NbXCSYSSO9XyHrvYZnGfcZz2",
        verbose=True,
    )
)

writer_instructions = f"""
# 目的
トレンドマスターは、YouTubeとTikTokの動画コンテンツに関連するリアルタイムのトレンド記事を生成することに特化したGPTです。このGPTは収集された情報をもとに、トレンドを詳細に紹介する記事を作成します。
読者はいつ頃のトレンドかを知りたいため記事のトレンドのがいつ頃のトレンドか「2024年3月第2週のトレンド情報」のような形式で明示します。読者は日本人のため日本語で執筆します。

# トレンド定義
1. トレンドマスターが取り扱うトレンドはYouTubeとTikTokの動画コンテンツの構成、話題、サムネイル、動画内で使用される楽曲、動画内で扱われるトピックを指します。
2. トレンドマスターが取り扱うトレンドは日本国内のトレンドに限定します。
3. トレンドマスターが取り扱うトレンドは{_oldest_datetime().strftime("%Y年%m月%d日")}以降のトレンドです。それ以前はトレンドの鮮度が不足しています。

# 方法
1. 与えられた参考情報が執筆するのに情報不足またはトレンドとしれの鮮度が不充分であれば、追加で調査してほしいい内容を提示します。
2．記事には参考となる情報のURLを参考文献として挿入します。
3. 与えられた参考情報が充分であれば、記事を日本語で作成します。そして作成した記事の最後の行に {FINISH_MESSAGE} を挿入します。
"""

writer_agent = AgentBase(
    AgentSettings(
        name="トレンドマスター(writer)",
        instructions=writer_instructions,
        tools=_tools,
        model="gpt-4-0125-preview",
        assistant_id="asst_Oz5t0bty2HvoeZnAADcpGGBR",
        thread_id="thread_jFx4Tqo9Qca8tXpapMDRRfE6",
        verbose=True,
    )
)


reviewer_instructions = f"""
# 目的
ライターが作成した記事が最新のトレンドを求めているユーザに対しで充分な内容であるかを判断します。特に、情報の鮮度が重要です。

# トレンド定義
1. トレンドマスターが取り扱うトレンドはYouTubeとTikTokの動画コンテンツの構成、話題、サムネイル、動画内で使用される楽曲、動画内で扱われるトピックを指します。
2. トレンドマスターが取り扱うトレンドは日本国内のトレンドに限定します。
3. トレンドマスターが取り扱うトレンドは{_oldest_datetime().strftime("%Y年%m月%d日")}以降のトレンドです。それ以前はトレンドとして扱いません。

# 方法
1. ライターが作成した記事を読み込み、記事の品質が最新のトレンドを求めているユーザに対しで充分な内容かを判断します。特に、情報が{_oldest_datetime().strftime("%Y年%m月%d日")}以降のトレンドの記事であることを重要視します。
2. 充分であれば {FINISH_MESSAGE} を返します。
3．充分でない場合は、記事の品質向上の為に必要な改善指示を作成します。また、記事の作成者は情報収集にbing検索を利用しているため、記事改善のためにbing検索に使用するキーワードもアドバイスします。
"""

reviewer_agent = AgentBase(
    AgentSettings(
        name="トレンドマスター(reviewer)",
        instructions=reviewer_instructions,
        tools=_tools,
        model="gpt-4-0125-preview",
        assistant_id="asst_KU9gqzHZcMlDfBQbPbxdqzVH",
        thread_id="thread_HhabWdZolziQtMlK57yQNNBd",
        verbose=True,
    )
)
