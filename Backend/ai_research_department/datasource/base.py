from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class DataSourceConnector(ABC):
    """Common interface for future DART, IR, KRX, KOSIS, FRED, and news connectors."""

    @abstractmethod
    async def search(self, query: str) -> list[dict[str, Any]]:
        """Search for candidate source records."""

    @abstractmethod
    async def fetch(self, source_id: str) -> dict[str, Any]:
        """Fetch a raw source record."""

    @abstractmethod
    async def extract(self, raw_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract evidence-like facts from raw source data."""
