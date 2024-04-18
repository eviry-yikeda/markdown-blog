import pickle
from dataclasses import dataclass, field
from typing import Self

import openai
from langchain.agents import AgentExecutor
from langchain.agents.openai_assistant import OpenAIAssistantRunnable
from langchain_core.tools import BaseTool
from langchain_core.utils.function_calling import convert_to_openai_tool


@dataclass
class AgentSettings:
    name: str
    instructions: str
    tools: list[BaseTool] = field(default_factory=list)
    model: str = "gpt-4-0125-preview"
    assistant_id: str | None = None
    thread_id: str | None = None
    verbose: bool = True

    @property
    def openai_tools(self):
        return [convert_to_openai_tool(tool) for tool in self.tools]


class AgentBase:

    def __init__(
        self,
        settings: AgentSettings,
    ):
        self._agent = (
            self._create_agent(settings)
            if settings.assistant_id is None
            else self._load_agent(settings=settings)
        )
        self._settings = settings
        self._settings.assistant_id = self._agent.assistant_id
        self._executor = AgentExecutor(
            agent=self._agent,
            tools=self._settings.tools,
            verbose=self._settings.verbose,
        )
        self.response: dict | None = None

    @property
    def settings(self) -> AgentSettings:
        return self._settings

    def clear_thread_id(self):
        self._settings.thread_id = None

    def invoke(self, msg: str) -> dict:
        self.response = self._executor.invoke(
            {"content": msg}
            if self._settings.thread_id is None
            else {"content": msg, "thread_id": self._settings.thread_id}
        )
        self._settings.thread_id = self.response["thread_id"]
        return self.response["output"]

    @staticmethod
    def _create_agent(settings: AgentSettings) -> OpenAIAssistantRunnable:
        return OpenAIAssistantRunnable.create_assistant(
            name=settings.name,
            instructions=settings.instructions,
            model=settings.model,
            tools=settings.openai_tools,
            as_agent=True,
        )

    @staticmethod
    def _load_agent(
        settings: AgentSettings,
    ) -> OpenAIAssistantRunnable:
        client = openai.OpenAI()
        assistant = client.beta.assistants.update(
            name=settings.name,
            assistant_id=settings.assistant_id,
            instructions=settings.instructions,
            tools=settings.openai_tools,
            model=settings.model,
        )
        return OpenAIAssistantRunnable(
            assistant_id=assistant.id, client=client, as_agent=True
        )

    def save(self, filename: str):
        with open(filename, "wb") as f:
            pickle.dump(self._settings, f)

    @classmethod
    def load(cls, filename: str) -> Self:
        with open(filename, "rb") as f:
            settings = pickle.load(f)
        return cls(settings)
