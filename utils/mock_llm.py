from langchain_core.messages import AIMessage, HumanMessage, SystemMessage


class MockLLM:
    """Small mock fallback when OpenAI credentials are unavailable."""

    def bind_tools(self, _tools: list[object]) -> "MockLLM":
        return self

    def invoke(self, messages: list[object]) -> AIMessage:
        last_user_message = ""
        for message in reversed(messages):
            if isinstance(message, HumanMessage):
                last_user_message = message.content
                break

        if not last_user_message:
            for message in messages:
                if isinstance(message, SystemMessage):
                    last_user_message = message.content[:120]
                    break

        return AIMessage(
            content=(
                "Mock response: he thong dang chay o che do gia lap. "
                f"Tin nhan gan nhat cua ban: {last_user_message}"
            )
        )

