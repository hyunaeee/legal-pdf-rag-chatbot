from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from threading import RLock


@dataclass(frozen=True)
class ContractRecord:
    contract_id: str
    tenant_id: str
    owner: str
    status: str
    renewal_date: str
    risk_level: str

    def as_evidence(self) -> str:
        return (
            f"Contract {self.contract_id}: owner={self.owner}, status={self.status}, "
            f"renewal_date={self.renewal_date}, risk_level={self.risk_level}."
        )


class SQLiteContractRepository:
    """Tenant-scoped structured data adapter for contract workflow records."""

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
                CREATE TABLE IF NOT EXISTS contracts (
                    tenant_id TEXT NOT NULL,
                    contract_id TEXT NOT NULL,
                    owner TEXT NOT NULL,
                    status TEXT NOT NULL,
                    renewal_date TEXT NOT NULL,
                    risk_level TEXT NOT NULL,
                    PRIMARY KEY (tenant_id, contract_id)
                )
                """
            )

    def upsert(self, record: ContractRecord) -> None:
        with self._lock, self._connection:
            self._connection.execute(
                """
                INSERT INTO contracts (
                    tenant_id,
                    contract_id,
                    owner,
                    status,
                    renewal_date,
                    risk_level
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT (tenant_id, contract_id) DO UPDATE SET
                    owner = excluded.owner,
                    status = excluded.status,
                    renewal_date = excluded.renewal_date,
                    risk_level = excluded.risk_level
                """,
                (
                    record.tenant_id,
                    record.contract_id,
                    record.owner,
                    record.status,
                    record.renewal_date,
                    record.risk_level,
                ),
            )

    def get(self, *, tenant_id: str, contract_id: str) -> ContractRecord | None:
        with self._lock:
            row = self._connection.execute(
                """
                SELECT contract_id, tenant_id, owner, status, renewal_date, risk_level
                FROM contracts
                WHERE tenant_id = ? AND contract_id = ?
                """,
                (tenant_id, contract_id),
            ).fetchone()
        return self._to_record(row) if row else None

    def search(self, *, tenant_id: str, query: str, limit: int = 3) -> list[ContractRecord]:
        normalized = query.lower()
        with self._lock:
            rows = self._connection.execute(
                """
                SELECT contract_id, tenant_id, owner, status, renewal_date, risk_level
                FROM contracts
                WHERE tenant_id = ?
                ORDER BY contract_id
                """,
                (tenant_id,),
            ).fetchall()

        records = [self._to_record(row) for row in rows]
        matched = [
            record
            for record in records
            if any(
                value.lower() in normalized or normalized in value.lower()
                for value in (
                    record.contract_id,
                    record.owner,
                    record.status,
                    record.renewal_date,
                    record.risk_level,
                )
            )
        ]
        if matched:
            return matched[:limit]

        contract_ids = [
            record
            for record in records
            if record.contract_id.lower() in normalized
        ]
        return contract_ids[:limit]

    @staticmethod
    def _to_record(row: sqlite3.Row) -> ContractRecord:
        return ContractRecord(
            contract_id=str(row["contract_id"]),
            tenant_id=str(row["tenant_id"]),
            owner=str(row["owner"]),
            status=str(row["status"]),
            renewal_date=str(row["renewal_date"]),
            risk_level=str(row["risk_level"]),
        )
