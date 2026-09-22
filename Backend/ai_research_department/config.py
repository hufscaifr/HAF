from __future__ import annotations

from pathlib import Path
import sys

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None


def load_backend_env() -> None:
    """Load Backend/.env so scripts can use configured API keys."""
    if load_dotenv is None:
        return
    env_path = Path(__file__).resolve().parents[1] / ".env"
    load_dotenv(dotenv_path=env_path)


def disable_incompatible_pandas_accelerators() -> None:
    """Avoid importing optional pandas accelerators that are ABI-broken locally."""
    sys.modules.setdefault("numexpr", None)
    sys.modules.setdefault("bottleneck", None)
