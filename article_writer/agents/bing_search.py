from langchain_community.utilities.bing_search import BingSearchAPIWrapper


class EviryBingSearchAPIWrapper(BingSearchAPIWrapper):

    def run(self, query: str) -> str:
        snippets = []
        results = self._bing_search_results(query, count=self.k)
        if len(results) == 0:
            return "No good Bing Search Result was found"
        for result in results:
            snippets.append(
                f"## 抜粋\n{result['snippet']}\n## 参考URL\n{result['url']}"
            )

        return "\n".join(snippets)
