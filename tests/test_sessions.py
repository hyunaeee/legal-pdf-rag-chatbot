from app.agent import PolicyAgent
from app.retrieval import InMemoryRetriever
from app.session_store import SQLiteSessionStore


def test_session_history_is_tenant_isolated() -> None:
    store = SQLiteSessionStore()
    store.append(
        tenant_id="alpha",
        session_id="shared-session",
        role="user",
        content="alpha secret",
    )
    store.append(
        tenant_id="beta",
        session_id="shared-session",
        role="user",
        content="beta secret",
    )

    alpha = store.recent(
        tenant_id="alpha",
        session_id="shared-session",
        limit=10,
    )
    beta = store.recent(
        tenant_id="beta",
        session_id="shared-session",
        limit=10,
    )

    assert [turn.content for turn in alpha] == ["alpha secret"]
    assert [turn.content for turn in beta] == ["beta secret"]


def test_session_store_returns_bounded_history_in_order() -> None:
    store = SQLiteSessionStore()
    for index in range(5):
        store.append(
            tenant_id="alpha",
            session_id="session-1",
            role="user",
            content=f"turn-{index}",
        )

    recent = store.recent(
        tenant_id="alpha",
        session_id="session-1",
        limit=3,
    )
    assert [turn.content for turn in recent] == ["turn-2", "turn-3", "turn-4"]


def test_session_can_be_deleted_for_one_tenant() -> None:
    store = SQLiteSessionStore()
    store.append(
        tenant_id="alpha",
        session_id="shared-session",
        role="user",
        content="delete me",
    )
    store.append(
        tenant_id="beta",
        session_id="shared-session",
        role="user",
        content="keep me",
    )

    deleted = store.delete(tenant_id="alpha", session_id="shared-session")

    assert deleted == 1
    assert store.recent(
        tenant_id="alpha",
        session_id="shared-session",
        limit=10,
    ) == []
    assert len(
        store.recent(
            tenant_id="beta",
            session_id="shared-session",
            limit=10,
        )
    ) == 1


def test_agent_persists_and_reuses_bounded_history() -> None:
    retriever = InMemoryRetriever()
    retriever.ingest(
        tenant_id="alpha",
        title="leave-policy.pdf",
        text="연차 휴가는 연 15일입니다.",
    )
    store = SQLiteSessionStore()
    agent = PolicyAgent(
        retriever,
        session_store=store,
        session_history_limit=4,
    )

    first = agent.answer(
        tenant_id="alpha",
        query="연차 휴가는 며칠입니까?",
        session_id="session-1",
    )
    second = agent.answer(
        tenant_id="alpha",
        query="그 규정의 일수는?",
        session_id="session-1",
    )

    assert first.metrics["history_turn_count"] == 0
    assert second.metrics["history_turn_count"] == 2
    turns = store.recent(
        tenant_id="alpha",
        session_id="session-1",
        limit=10,
    )
    assert len(turns) == 4
