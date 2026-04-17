from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from pydantic import BaseModel, Field
from typing_extensions import TypedDict
import uvicorn

from app.auth import verify_api_key
from app.config import get_settings
from app.cost_guard import guard_chat_cost
from app.rate_limiter import InMemoryRateLimiter
from tools import (
    book_appointment,
    check_red_flag,
    find_clinics,
    get_doctors,
    get_slots,
    map_symptoms,
)
from utils.mock_llm import MockLLM


settings = get_settings()

app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

rate_limiter = InMemoryRateLimiter(max_requests=settings.rate_limit_per_minute)


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = Field(default_factory=list)


class ChatResponse(BaseModel):
    response: str


def _load_system_prompt() -> str:
    prompt_path = Path(__file__).resolve().parents[1] / "system_prompt.txt"
    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8")
    return "You are a helpful healthcare booking assistant."


SYSTEM_PROMPT = _load_system_prompt()


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


TOOLS = [
    check_red_flag,
    map_symptoms,
    find_clinics,
    get_doctors,
    get_slots,
    book_appointment,
]


def _build_llm():
    if settings.use_mock_llm or not settings.openai_api_key:
        return MockLLM()
    return ChatOpenAI(
        model=settings.openai_model,
        temperature=0,
        api_key=settings.openai_api_key,
    )


llm_with_tools = _build_llm().bind_tools(TOOLS)


def _to_text(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        fragments: list[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                fragments.append(str(item.get("text", "")))
            else:
                fragments.append(str(item))
        return "\n".join(fragment for fragment in fragments if fragment).strip()
    return str(content)


def agent_node(state: AgentState) -> AgentState:
    messages = state["messages"]
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages

    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


builder = StateGraph(AgentState)
builder.add_node("agent", agent_node)
builder.add_node("tools", ToolNode(TOOLS))
builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", tools_condition)
builder.add_edge("tools", "agent")
graph = builder.compile()


def _client_key(request: Request) -> str:
    explicit = request.headers.get("x-client-id")
    if explicit:
        return explicit

    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    if request.client:
        return request.client.host
    return "anonymous"


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": f"{settings.app_name} is running"}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    request: Request,
    _: None = Depends(verify_api_key),
) -> ChatResponse:
    if not rate_limiter.allow(_client_key(request)):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please retry in a minute.",
        )

    try:
        history_messages: list[AIMessage | HumanMessage] = []
        for message in payload.history:
            if message.role in {"user", "human"}:
                history_messages.append(HumanMessage(content=message.content))
            else:
                history_messages.append(AIMessage(content=message.content))

        guard_chat_cost(message=payload.message, history=history_messages)

        history_messages.append(HumanMessage(content=payload.message))
        result = graph.invoke({"messages": history_messages})
        response_text = _to_text(result["messages"][-1].content)
        return ChatResponse(response=response_text)

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


if __name__ == "__main__":
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=False)
