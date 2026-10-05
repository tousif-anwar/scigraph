"""Spark RAW -> BRONZE -> SILVER -> GOLD pipeline for OpenAlex works."""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from scigraph.utils.config import load_config, resolve_project_path


def _spark_imports():
    """Import PySpark lazily so unit tests can run without Spark installed."""
    try:
        from pyspark.sql import SparkSession
        from pyspark.sql import functions as F
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "PySpark is not installed. Install project requirements with "
            "`python -m pip install -r requirements.txt` before running the Spark pipeline."
        ) from exc
    return SparkSession, F


def find_java_executable() -> str | None:
    """Find a Java executable from PATH or JAVA_HOME."""
    java = shutil.which("java")
    if java:
        return java

    import os

    java_home = os.environ.get("JAVA_HOME")
    if java_home:
        java_path = Path(java_home) / "bin" / "java.exe"
        if java_path.exists():
            return str(java_path)
        java_path = Path(java_home) / "bin" / "java"
        if java_path.exists():
            return str(java_path)
    return None


def preflight_environment() -> dict[str, Any]:
    """Check whether Spark dependencies required for execution are available."""
    result: dict[str, Any] = {"ok": True, "checks": []}
    try:
        import pyspark

        result["checks"].append(
            {"name": "pyspark_import", "status": "pass", "details": pyspark.__version__}
        )
    except ModuleNotFoundError:
        result["ok"] = False
        result["checks"].append(
            {"name": "pyspark_import", "status": "fail", "details": "PySpark is not installed."}
        )

    java = find_java_executable()
    if java:
        result["checks"].append({"name": "java_executable", "status": "pass", "details": java})
    else:
        result["ok"] = False
        result["checks"].append(
            {
                "name": "java_executable",
                "status": "fail",
                "details": "No Java executable found on PATH or under JAVA_HOME/bin.",
            }
        )
    return result


def create_spark_session(config: dict[str, Any]):
    """Create a local SparkSession from config."""
    SparkSession, _ = _spark_imports()
    return (
        SparkSession.builder.appName(config["spark"]["app_name"])
        .master(config["spark"]["master"])
        .config("spark.sql.session.timeZone", "UTC")
        .getOrCreate()
    )


def _path(config: dict[str, Any], key: str) -> str:
    return str(resolve_project_path(config, config["paths"][key]))


def _write_parquet(df, path: str) -> None:
    df.write.mode("overwrite").parquet(path)


def build_bronze(spark, config: dict[str, Any]):
    """Read raw JSONL and write minimally processed Bronze records."""
    _, F = _spark_imports()
    raw_path = _path(config, "raw_sample_jsonl")
    bronze_path = _path(config, "bronze_works")
    raw_df = spark.read.json(raw_path)
    bronze_df = (
        raw_df.withColumn("_bronze_ingested_at_utc", F.current_timestamp())
        .withColumn("_source_dataset", F.lit(config["dataset"]["name"]))
        .withColumn("_source_license", F.lit(config["dataset"]["license"]))
    )
    _write_parquet(bronze_df, bronze_path)
    return bronze_df


def build_silver(bronze_df, config: dict[str, Any]):
    """Validate and normalize publications into a Silver table."""
    _, F = _spark_imports()
    silver_path = _path(config, "silver_publications")

    source = F.col("primary_location.source")
    referenced_works = F.coalesce(F.col("referenced_works"), F.array())
    authorships = F.coalesce(F.col("authorships"), F.array())
    concepts = F.coalesce(F.col("concepts"), F.array())
    topics = F.coalesce(F.col("topics"), F.array())

    title = F.trim(F.coalesce(F.col("title"), F.col("display_name")))
    title_normalized = F.trim(F.regexp_replace(F.lower(title), r"[^\w\s]", " "))
    title_normalized = F.regexp_replace(title_normalized, r"\s+", " ")

    quality_flags = F.array_compact(
        F.array(
            F.when(F.col("id").isNull() | (F.trim(F.col("id")) == ""), F.lit("missing_id")),
            F.when(title.isNull() | (title == ""), F.lit("missing_title")),
            F.when(F.col("abstract_inverted_index").isNull(), F.lit("missing_abstract")),
            F.when(F.size(authorships) == 0, F.lit("missing_authorships")),
            F.when(F.to_date("publication_date").isNull(), F.lit("malformed_publication_date")),
            F.when(
                F.year(F.to_date("publication_date")) != F.col("publication_year"),
                F.lit("publication_year_mismatch"),
            ),
        )
    )

    silver_df = bronze_df.select(
        F.col("id").alias("paper_id"),
        F.regexp_replace(F.col("id"), r"^https://openalex\.org/", "").alias("paper_openalex_id"),
        F.when(F.col("doi").startswith("https://doi.org/"), F.lower(F.col("doi")))
        .when(F.col("doi").startswith("10."), F.concat(F.lit("https://doi.org/"), F.lower(F.col("doi"))))
        .otherwise(F.lower(F.col("doi")))
        .alias("doi"),
        title.alias("title"),
        title_normalized.alias("title_normalized"),
        F.col("abstract_inverted_index").isNotNull().alias("abstract_available"),
        F.col("publication_date"),
        F.col("publication_year"),
        F.col("type").alias("document_type"),
        F.col("language"),
        F.col("cited_by_count"),
        source.id.alias("source_id"),
        source.display_name.alias("source_name"),
        F.size(referenced_works).alias("reference_count"),
        F.size(authorships).alias("author_count"),
        F.size(concepts).alias("concept_count"),
        F.size(topics).alias("topic_count"),
        referenced_works.alias("referenced_works"),
        authorships.alias("authorships"),
        concepts.alias("concepts"),
        topics.alias("topics"),
        quality_flags.alias("quality_flags"),
    )
    _write_parquet(silver_df, silver_path)
    return silver_df


def build_gold(silver_df, config: dict[str, Any]) -> dict[str, Any]:
    """Create analysis-ready Gold tables."""
    _, F = _spark_imports()
    paths = config["paths"]

    publications = silver_df.select(
        "paper_id",
        "paper_openalex_id",
        "doi",
        "title",
        "title_normalized",
        "abstract_available",
        "publication_date",
        "publication_year",
        "document_type",
        "language",
        "cited_by_count",
        "source_id",
        "source_name",
        "reference_count",
        "author_count",
        "concept_count",
        "topic_count",
        "quality_flags",
    )

    author_rows = (
        silver_df.select("paper_id", F.posexplode_outer("authorships").alias("author_position", "authorship"))
        .select(
            "paper_id",
            "author_position",
            F.col("authorship.author.id").alias("author_id"),
            F.col("authorship.author.display_name").alias("author_name"),
        )
        .where(F.col("author_id").isNotNull())
    )

    authors = author_rows.select("author_id", "author_name").dropDuplicates(["author_id"])
    citation_edges = (
        silver_df.select("paper_id", F.explode_outer("referenced_works").alias("referenced_paper_id"))
        .where(F.col("referenced_paper_id").isNotNull())
        .where(F.col("paper_id") != F.col("referenced_paper_id"))
    )

    topic_rows = silver_df.select("paper_id", F.explode_outer("topics").alias("topic")).select(
        "paper_id",
        F.col("topic.id").alias("topic_id"),
        F.col("topic.display_name").alias("topic_name"),
        F.col("topic.domain.display_name").alias("topic_domain"),
        F.col("topic.field.display_name").alias("topic_field"),
        F.col("topic.subfield.display_name").alias("topic_subfield"),
    )

    outputs = {
        "gold_publications": publications,
        "gold_authors": authors,
        "gold_author_publications": author_rows,
        "gold_citation_edges": citation_edges,
        "gold_topics": topic_rows.where(F.col("topic_id").isNotNull()),
    }
    for key, df in outputs.items():
        _write_parquet(df, str(resolve_project_path(config, paths[key])))
    return outputs


def _count_quality_flags(silver_df) -> dict[str, int]:
    _, F = _spark_imports()
    rows = (
        silver_df.select(F.explode_outer("quality_flags").alias("flag"))
        .where(F.col("flag").isNotNull())
        .groupBy("flag")
        .count()
        .collect()
    )
    return {row["flag"]: row["count"] for row in rows}


def write_pipeline_report(report: dict[str, Any], markdown_path: Path) -> None:
    """Write a compact human-readable pipeline report."""
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    if report.get("status") != "success":
        lines = [
            "# Bronze/Silver/Gold Pipeline Report",
            "",
            f"Generated on {date.today().isoformat()}.",
            "",
            f"Status: {report.get('status', 'unknown')}",
            "",
            "## Runtime Blocker",
            "",
            report.get("message", "Pipeline did not complete."),
            "",
            "## Preflight Checks",
            "",
            "| check | status | details |",
            "| --- | --- | --- |",
        ]
        for check in report.get("preflight", {}).get("checks", []):
            lines.append(f"| {check['name']} | {check['status']} | {check['details']} |")
        lines.extend(
            [
                "",
                "## Planned Outputs",
                "",
                "When Spark can run, this pipeline writes Bronze, Silver, and Gold Parquet datasets using the paths configured in `configs/dev.yaml`.",
            ]
        )
        markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return

    lines = [
        "# Bronze/Silver/Gold Pipeline Report",
        "",
        f"Generated on {date.today().isoformat()}.",
        "",
        "## Stage Counts",
        "",
        f"- Raw records read: {report['stage_counts']['raw_records']}",
        f"- Bronze records written: {report['stage_counts']['bronze_records']}",
        f"- Silver publications written: {report['stage_counts']['silver_publications']}",
        f"- Gold publications written: {report['stage_counts']['gold_publications']}",
        f"- Gold authors written: {report['stage_counts']['gold_authors']}",
        f"- Gold author-publication rows written: {report['stage_counts']['gold_author_publications']}",
        f"- Gold citation edges written: {report['stage_counts']['gold_citation_edges']}",
        f"- Gold topic rows written: {report['stage_counts']['gold_topics']}",
        "",
        "## Transform Accounting",
        "",
        f"- Records removed in Silver: {report['transform_counts']['records_removed_in_silver']}",
        f"- Records with quality flags: {report['transform_counts']['records_with_quality_flags']}",
        f"- Self-citations removed from Gold citation edges: {report['transform_counts']['self_citations_removed']}",
        "",
        "Quality flag counts:",
        "",
        "```json",
        json.dumps(report["quality_flag_counts"], indent=2, sort_keys=True),
        "```",
        "",
        "## Notes",
        "",
        "Bronze preserves raw nested OpenAlex fields plus ingestion metadata. Silver normalizes publication-level columns and records validation flags. Gold creates publication, author, author-publication, citation-edge, and topic tables for later analysis.",
    ]
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_pipeline(config: dict[str, Any]) -> dict[str, Any]:
    """Run the Spark Bronze/Silver/Gold pipeline and write reports."""
    preflight = preflight_environment()
    if not preflight["ok"]:
        report = {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": "blocked",
            "message": "Spark pipeline was not executed because the local Spark runtime preflight failed.",
            "preflight": preflight,
            "outputs": {
                key: str(resolve_project_path(config, value))
                for key, value in config["paths"].items()
                if key.startswith(("bronze_", "silver_", "gold_"))
            },
        }
        json_path = resolve_project_path(config, config["paths"]["pipeline_report_json"])
        markdown_path = resolve_project_path(config, config["paths"]["pipeline_report_md"])
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
        write_pipeline_report(report, markdown_path)
        return report

    spark = create_spark_session(config)
    try:
        raw_records = spark.read.json(_path(config, "raw_sample_jsonl")).count()
        bronze_df = build_bronze(spark, config)
        bronze_count = bronze_df.count()
        silver_df = build_silver(bronze_df, config)
        silver_count = silver_df.count()
        gold_outputs = build_gold(silver_df, config)

        gold_counts = {name: df.count() for name, df in gold_outputs.items()}
        quality_flag_counts = _count_quality_flags(silver_df)
        records_with_flags = silver_df.where("size(quality_flags) > 0").count()
        raw_self_citations = (
            silver_df.selectExpr("paper_id", "explode_outer(referenced_works) as referenced_paper_id")
            .where("paper_id = referenced_paper_id")
            .count()
        )

        report = {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": "success",
            "preflight": preflight,
            "stage_counts": {
                "raw_records": raw_records,
                "bronze_records": bronze_count,
                "silver_publications": silver_count,
                **gold_counts,
            },
            "transform_counts": {
                "records_removed_in_silver": bronze_count - silver_count,
                "records_with_quality_flags": records_with_flags,
                "self_citations_removed": raw_self_citations,
            },
            "quality_flag_counts": quality_flag_counts,
            "outputs": {
                key: str(resolve_project_path(config, value))
                for key, value in config["paths"].items()
                if key.startswith(("bronze_", "silver_", "gold_"))
            },
        }

        json_path = resolve_project_path(config, config["paths"]["pipeline_report_json"])
        markdown_path = resolve_project_path(config, config["paths"]["pipeline_report_md"])
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
        write_pipeline_report(report, markdown_path)
        return report
    finally:
        spark.stop()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/dev.yaml")
    args = parser.parse_args()

    config = load_config(Path(args.config))
    report = run_pipeline(config)
    if report.get("status") == "success":
        print(json.dumps(report["stage_counts"], indent=2, sort_keys=True))
    else:
        print(json.dumps({"status": report["status"], "preflight": report["preflight"]}, indent=2))


if __name__ == "__main__":
    main()
