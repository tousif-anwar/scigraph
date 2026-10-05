"""Configuration loading utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def project_root() -> Path:
    """Return the repository root based on this source file location."""
    return Path(__file__).resolve().parents[3]


def load_config(config_path: str | Path) -> dict[str, Any]:
    """Load a YAML config file and resolve path entries relative to the repo root."""
    root = project_root()
    path = Path(config_path)
    if not path.is_absolute():
        path = root / path

    with path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}

    config["_config_path"] = str(path)
    config["_project_root"] = str(root)
    return config


def resolve_project_path(config: dict[str, Any], path_value: str | Path) -> Path:
    """Resolve a config path relative to the project root."""
    path = Path(path_value)
    if path.is_absolute():
        return path
    return Path(config["_project_root"]) / path
