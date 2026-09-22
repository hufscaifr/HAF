from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Iterable, Optional, Type, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def dump_model(model: BaseModel) -> dict[str, Any]:
    """Serialize a Pydantic v1 or v2 model."""
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def validate_model(model_class: Type[T], payload: dict[str, Any]) -> T:
    """Validate a payload with Pydantic v1 or v2."""
    if hasattr(model_class, "model_validate"):
        return model_class.model_validate(payload)
    return model_class.parse_obj(payload)


class SQLiteWorkspaceRepository:
    """SQLite-backed repository that stores structured entities as JSON payloads."""

    def __init__(self, database_path: str | Path = "research_workspace.db") -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.database_path)

    def _initialize(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS entities (
                    entity_type TEXT NOT NULL,
                    entity_id TEXT NOT NULL,
                    project_id TEXT,
                    payload TEXT NOT NULL,
                    created_at TEXT,
                    PRIMARY KEY (entity_type, entity_id)
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_entities_project
                ON entities(project_id, entity_type)
                """
            )

    def save(self, entity_type: str, entity_id: str, model: BaseModel, project_id: Optional[str] = None) -> None:
        """Persist a Pydantic model in the workspace."""
        payload = json.dumps(dump_model(model), ensure_ascii=False, default=str)
        created_at = str(getattr(model, "created_at", ""))
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO entities(entity_type, entity_id, project_id, payload, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (entity_type, entity_id, project_id, payload, created_at),
            )

    def get(self, entity_type: str, entity_id: str, model_class: Type[T]) -> Optional[T]:
        """Load one entity by type and id."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT payload FROM entities WHERE entity_type = ? AND entity_id = ?",
                (entity_type, entity_id),
            ).fetchone()
        if not row:
            return None
        return validate_model(model_class, json.loads(row[0]))

    def list(self, entity_type: str, model_class: Type[T], project_id: Optional[str] = None) -> list[T]:
        """List entities by type, optionally scoped to a project."""
        sql = "SELECT payload FROM entities WHERE entity_type = ?"
        params: list[Any] = [entity_type]
        if project_id is not None:
            sql += " AND project_id = ?"
            params.append(project_id)
        sql += " ORDER BY created_at ASC"
        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [validate_model(model_class, json.loads(row[0])) for row in rows]

    def search_payload(self, entity_type: str, needle: str, model_class: Type[T]) -> list[T]:
        """Simple payload text search for MVP workflows."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT payload FROM entities WHERE entity_type = ? AND payload LIKE ?",
                (entity_type, f"%{needle}%"),
            ).fetchall()
        return [validate_model(model_class, json.loads(row[0])) for row in rows]

    def save_many(self, entity_type: str, entities: Iterable[tuple[str, BaseModel]], project_id: Optional[str] = None) -> None:
        """Persist multiple entities."""
        for entity_id, entity in entities:
            self.save(entity_type, entity_id, entity, project_id=project_id)
