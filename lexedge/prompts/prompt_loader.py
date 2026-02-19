from __future__ import annotations

from functools import lru_cache
from pathlib import Path

PROMPT_LIBRARY_DIR = Path(__file__).resolve().parent.parent / "prompt_library"


@lru_cache(maxsize=None)
def load_prompt(relative_path: str) -> str:
    """Load a prompt template from the prompt library."""
    prompt_path = PROMPT_LIBRARY_DIR / relative_path
    return prompt_path.read_text(encoding="utf-8")


def render_prompt(template: str, **kwargs) -> str:
    """Render a prompt template using {{placeholders}}."""
    rendered = template
    for key, value in kwargs.items():
        placeholder = "{{" + key + "}}"
        rendered = rendered.replace(placeholder, str(value) if value else "[Not provided]")
    return rendered
