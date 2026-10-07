"""Generate a lightweight static dashboard from project reports."""

from __future__ import annotations

import argparse
import html
import json
import os
from datetime import date
from pathlib import Path
from typing import Any

from scigraph.utils.config import load_config, resolve_project_path


def load_optional_json(path: Path) -> dict[str, Any]:
    """Load JSON if present, otherwise return an empty mapping."""
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def format_number(value: Any) -> str:
    """Format dashboard numbers consistently."""
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.4f}" if abs(value) < 10 else f"{value:,.2f}"
    if isinstance(value, int):
        return f"{value:,}"
    return html.escape(str(value))


def _path(config: dict[str, Any], key: str) -> Path:
    return resolve_project_path(config, config["paths"][key])


def figure_src(dashboard_path: Path, figure: Path) -> str:
    """Return a relative figure path from the dashboard HTML location."""
    return Path(os.path.relpath(figure, dashboard_path.parent)).as_posix()


def metric(label: str, value: Any) -> str:
    """Render one metric cell."""
    return f"<div class='metric'><span>{html.escape(label)}</span><strong>{format_number(value)}</strong></div>"


def generate_dashboard(config: dict[str, Any]) -> Path:
    """Generate a static HTML dashboard from measured report artifacts."""
    root = resolve_project_path(config, ".")
    dashboard_path = _path(config, "dashboard_html")
    dashboard_path.parent.mkdir(parents=True, exist_ok=True)
    results = root / "reports" / "results"
    figures = root / "reports" / "figures"

    schema = load_optional_json(results / "schema_summary.json")
    pipeline = load_optional_json(results / "bronze_silver_gold_report.json")
    retrieval = load_optional_json(results / "advanced_retrieval_results.json")
    vector = load_optional_json(_path(config, "vector_index_report_json"))
    field = load_optional_json(_path(config, "citation_field_report_json"))
    feature = load_optional_json(_path(config, "feature_mart_report_json"))
    file_arrival = load_optional_json(_path(config, "file_arrival_report_json"))

    stats = schema.get("dataset_statistics", {})
    stages = pipeline.get("stage_counts", {})
    systems = retrieval.get("systems", [])
    best_system = max(systems, key=lambda row: row.get("ndcg_at_k", 0.0), default={})

    figure_names = [
        ("Publications by year", "dataset_publications_by_year.png"),
        ("Pipeline stage counts", "pipeline_stage_counts.png"),
        ("Top text terms", "text_top_terms.png"),
        ("Author collaboration", "author_collaboration_summary.png"),
        ("Retrieval ablation", "retrieval_ablation.png"),
        ("Citation prediction", "ml_citation_prediction.png"),
        ("Feature availability", "feature_mart_availability.png"),
    ]
    figure_blocks = []
    for title, name in figure_names:
        path = figures / name
        if path.exists():
            figure_blocks.append(
                f"<figure><img src='{html.escape(figure_src(dashboard_path, path))}' alt='{html.escape(title)}'><figcaption>{html.escape(title)}</figcaption></figure>"
            )

    css = """
    :root { --surface: #ffffff; --muted: #f7f7f8; --ink: #111111; --line: #d8dbe2; --accent: #002fa7; }
    * { box-sizing: border-box; }
    body { margin: 0; background: var(--surface); color: var(--ink); font-family: "Helvetica Neue", Arial, sans-serif; letter-spacing: 0; }
    main { max-width: 1240px; margin: 0 auto; padding: 32px 24px 48px; }
    header { display: grid; grid-template-columns: 1.4fr 0.6fr; gap: 24px; border-bottom: 1px solid var(--ink); padding-bottom: 28px; }
    h1 { margin: 0; font-size: clamp(42px, 9vw, 112px); line-height: .88; font-weight: 700; color: var(--accent); }
    .meta { border-left: 1px solid var(--line); padding-left: 18px; align-self: end; font-size: 14px; line-height: 1.45; }
    .rulegrid { display: grid; grid-template-columns: repeat(4, 1fr); border-left: 1px solid var(--line); border-top: 1px solid var(--line); margin-top: 24px; }
    .metric { min-height: 118px; padding: 14px; border-right: 1px solid var(--line); border-bottom: 1px solid var(--line); display: flex; flex-direction: column; justify-content: space-between; }
    .metric span { font-size: 13px; color: #555b66; }
    .metric strong { font-size: clamp(24px, 4vw, 44px); line-height: 1; font-weight: 700; overflow-wrap: anywhere; }
    section { margin-top: 36px; }
    h2 { margin: 0 0 12px; font-size: 22px; font-weight: 700; }
    .figures { display: grid; grid-template-columns: repeat(2, 1fr); border-left: 1px solid var(--line); border-top: 1px solid var(--line); }
    figure { margin: 0; padding: 14px; border-right: 1px solid var(--line); border-bottom: 1px solid var(--line); background: var(--surface); }
    img { width: 100%; height: auto; display: block; }
    figcaption { margin-top: 10px; font-size: 13px; color: #555b66; }
    table { width: 100%; border-collapse: collapse; border-top: 1px solid var(--line); font-size: 14px; }
    th, td { text-align: left; padding: 10px 8px; border-bottom: 1px solid var(--line); vertical-align: top; }
    th { color: #555b66; font-weight: 500; }
    .note { background: var(--muted); border-top: 1px solid var(--line); border-bottom: 1px solid var(--line); padding: 14px; font-size: 14px; line-height: 1.5; }
    @media (max-width: 820px) { header, .figures { grid-template-columns: 1fr; } .rulegrid { grid-template-columns: repeat(2, 1fr); } .meta { border-left: 0; padding-left: 0; } }
    @media (max-width: 520px) { main { padding: 22px 14px 36px; } .rulegrid { grid-template-columns: 1fr; } }
    """
    rows = "".join(
        f"<tr><td>{html.escape(row.get('system', 'n/a'))}</td><td>{format_number(row.get('precision_at_k'))}</td><td>{format_number(row.get('ndcg_at_k'))}</td></tr>"
        for row in systems
    )
    body = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>SciGraph Dashboard</title>
  <style>{css}</style>
</head>
<body>
<main>
  <header>
    <div><h1>SciGraph</h1></div>
    <div class="meta">
      <strong>Project dashboard</strong><br>
      Generated {date.today().isoformat()}<br>
      Source: OpenAlex Works sample<br>
      Config: {html.escape(str(config.get("_config_path", "")))}
    </div>
  </header>
  <div class="rulegrid">
    {metric("Sample records", stats.get("record_count") or stages.get("raw_records"))}
    {metric("Gold publications", stages.get("gold_publications"))}
    {metric("Vector documents", vector.get("document_count"))}
    {metric("Field/year citation groups", field.get("field_year_group_count"))}
    {metric("Feature mart rows", feature.get("publication_rows"))}
    {metric("Best retrieval NDCG", best_system.get("ndcg_at_k"))}
    {metric("File-arrival records", file_arrival.get("record_count"))}
    {metric("Missing author rate", file_arrival.get("missing_author_rate"))}
  </div>
  <section>
    <h2>Figures</h2>
    <div class="figures">{''.join(figure_blocks)}</div>
  </section>
  <section>
    <h2>Retrieval Systems</h2>
    <table><thead><tr><th>System</th><th>Precision@K</th><th>NDCG@K</th></tr></thead><tbody>{rows}</tbody></table>
  </section>
  <section>
    <h2>Operational Notes</h2>
    <div class="note">The dashboard is generated from report JSON and figure files already produced by the pipeline. Empty values mean that a dependent milestone has not been rerun yet, not that the metric was fabricated.</div>
  </section>
</main>
</body>
</html>
"""
    dashboard_path.write_text(body, encoding="utf-8")
    return dashboard_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/dev.yaml")
    args = parser.parse_args()
    dashboard = generate_dashboard(load_config(Path(args.config)))
    print(json.dumps({"dashboard": str(dashboard)}, indent=2))


if __name__ == "__main__":
    main()
