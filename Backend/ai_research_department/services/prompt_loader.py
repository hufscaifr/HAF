from __future__ import annotations

from pathlib import Path


class PromptLoader:
    """Load agent prompts from the prompts directory."""

    def __init__(self, prompt_root: str | Path | None = None) -> None:
        self.prompt_root = Path(prompt_root or Path(__file__).resolve().parents[1] / "prompts")

    def load(self, relative_path: str) -> str:
        """Load a prompt by relative path, such as `issue/junior.md`."""
        path = (self.prompt_root / relative_path).resolve()
        root = self.prompt_root.resolve()
        if root not in path.parents and path != root:
            raise ValueError("Prompt path must stay inside prompt root.")
        return path.read_text(encoding="utf-8")
