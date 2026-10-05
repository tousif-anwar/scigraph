from pathlib import Path

from scigraph.utils.config import load_config, project_root, resolve_project_path


def test_load_dev_config() -> None:
    config = load_config("configs/dev.yaml")

    assert config["project"]["name"] == "scigraph"
    assert config["dataset"]["name"] == "openalex_works"
    assert config["dataset"]["sample_size"] > 0
    assert Path(config["_project_root"]) == project_root()


def test_resolve_project_path() -> None:
    config = load_config("configs/dev.yaml")

    resolved = resolve_project_path(config, "data/raw/example.jsonl")

    assert resolved == project_root() / "data" / "raw" / "example.jsonl"
