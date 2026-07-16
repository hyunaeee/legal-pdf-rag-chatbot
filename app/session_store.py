from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from threading import RLock


@dataclass(frozen=True)
class ConversationTurn:
    sequence: int
    role: str
    content: str


class SQLiteSessionStore:
    """Stores bounded conversation history by tenant and session."""

    def __init__(self, path: str = ":memory:") -> None:
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._lock = RLock()
        self._initialize()

    def _initialize(self) -> None:
        with self._lock, self._connection:
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS conversation_turns (
                    tenant_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    sequence INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (tenant_id, session_id, sequence)
                )
                """
            )

    def append(
        self,
        *,
        tenant_id: str,
        session_id: str,
        role: str,
        content: str,
    ) -> ConversationTurn:
        if role not in {"user", "assistant", "system"}:
            raise ValueError(f"Unsupported conversation role: {role}")
        with self._lock, self._connection:
            row = self._connection.execute(
                """
                SELECT COALESCE(MAX(sequence), 0) AS last_sequence
                FROM conversation_turns
                WHERE tenant_id = ? AND session_id = ?
                """,
                (tenant_id, session_id),
            ).fetchone()
            sequence = int(row["last_sequence"]) + 1
            self._connection.execute(
                """
                INSERT INTO conversation_turns (
                    tenant_id,
                    session_id,
                    sequence,
                    role,
                    content
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (tenant_id, session_id, sequence, role, content),
            )
        return ConversationTurn(sequence=sequence, role=role, content=content)

    def recent(
        self,
        *,
        tenant_id: str,
        session_id: str,
        limit: int,
    ) -> list[ConversationTurn]:
        if limit < 1:
            return []
        with self._lock:
            rows = self._connection.execute(
                """
                SELECT sequence, role, content
                FROM conversation_turns
                WHERE tenant_id = ? AND session_id = ?
                ORDER BY sequence DESC
                LIMIT ?
                """,
                (tenant_id, session_id, limit),
            ).fetchall()
        return [
            ConversationTurn(
                sequence=int(row["sequence"]),
                role=str(row["role"]),
                content=str(row["content"]),
            )
            for row in reversed(rows)
        ]

    def delete(self, *, tenant_id: str, session_id: str) -> int:
        with self._lock, self._connection:
            cursor = self._connection.execute(
                """
                DELETE FROM conversation_turns
                WHERE tenant_id = ? AND session_id = ?
                """,
                (tenant_id, session_id),
            )
        return int(cursor.rowcount)
