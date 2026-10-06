from pathlib import Path

from scigraph.visualization.figures import FIGURE_NAMES, load_json


def test_figure_names_are_pngs() -> None:
    assert FIGURE_NAMES
    assert all(name.endswith(".png") for name in FIGURE_NAMES)


def test_load_json(tmp_path: Path) -> None:
    path = tmp_path / "sample.json"
    path.write_text('{"ok": true}', encoding="utf-8")
    assert load_json(path) == {"ok": True}
