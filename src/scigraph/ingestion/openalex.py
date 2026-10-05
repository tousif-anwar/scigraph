"""OpenAlex-specific helpers."""

from __future__ import annotations

from typing import Any


def reconstruct_abstract(inverted_index: dict[str, list[int]] | None) -> str | None:
    """Reconstruct plaintext from OpenAlex's abstract inverted index."""
    if not inverted_index:
        return None

    positions: list[tuple[int, str]] = []
    for token, token_positions in inverted_index.items():
        if not isinstance(token_positions, list):
            continue
        for position in token_positions:
            if isinstance(position, int):
                positions.append((position, token))

    if not positions:
        return None

    return " ".join(token for _, token in sorted(positions))


def nested_get(record: dict[str, Any], dotted_path: str) -> Any:
    """Get a nested value using dot notation for documentation summaries."""
    current: Any = record
    for part in dotted_path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current
