"""Citation outcome prediction baseline using Spark ML."""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from scigraph.preprocessing.pipeline import _spark_imports, create_spark_session, preflight_environment
from scigraph.utils.config import load_config, resolve_project_path


FEATURE_COLUMNS = [
    "publication_year_index",
    "reference_count",
    "author_count",
    "concept_count",
    "topic_count",
    "abstract_available_numeric",
]


def high_citation_label(cited_by_count: int, threshold: float) -> int:
    """Return binary high-citation label for deterministic unit tests."""
    return int(cited_by_count >= threshold)


def majority_baseline_accuracy(positive_count: int, negative_count: int) -> float:
    """Return accuracy of always predicting the majority class."""
    total = positive_count + negative_count
    if total <= 0:
        return 0.0
    return max(positive_count, negative_count) / total


def _path(config: dict[str, Any], key: str) -> str:
    return str(resolve_project_path(config, config["paths"][key]))


def build_feature_table(publications, citation_threshold: float):
    """Build publication-level ML feature rows."""
    _, F, _ = _spark_imports()
    from pyspark.sql import Window

    all_rows = Window.rowsBetween(Window.unboundedPreceding, Window.unboundedFollowing)
    return (
        publications.select(
            "paper_id",
            "title",
            F.coalesce(F.col("publication_year"), F.lit(0)).cast("double").alias("publication_year"),
            F.coalesce(F.col("cited_by_count"), F.lit(0)).cast("double").alias("cited_by_count"),
            F.coalesce(F.col("reference_count"), F.lit(0)).cast("double").alias("reference_count"),
            F.coalesce(F.col("author_count"), F.lit(0)).cast("double").alias("author_count"),
            F.coalesce(F.col("concept_count"), F.lit(0)).cast("double").alias("concept_count"),
            F.coalesce(F.col("topic_count"), F.lit(0)).cast("double").alias("topic_count"),
            F.when(F.col("abstract_available"), F.lit(1.0)).otherwise(F.lit(0.0)).alias(
                "abstract_available_numeric"
            ),
        )
        .withColumn(
            "publication_year_index",
            F.col("publication_year") - F.min("publication_year").over(all_rows),
        )
        .withColumn("label", (F.col("cited_by_count") >= F.lit(citation_threshold)).cast("double"))
    )


def evaluate_confusion_counts(predictions) -> dict[str, int]:
    """Collect confusion matrix counts from prediction rows."""
    _, F, _ = _spark_imports()
    row = predictions.agg(
        F.sum(F.when((F.col("label") == 1.0) & (F.col("prediction") == 1.0), F.lit(1)).otherwise(F.lit(0))).alias("tp"),
        F.sum(F.when((F.col("label") == 0.0) & (F.col("prediction") == 1.0), F.lit(1)).otherwise(F.lit(0))).alias("fp"),
        F.sum(F.when((F.col("label") == 0.0) & (F.col("prediction") == 0.0), F.lit(1)).otherwise(F.lit(0))).alias("tn"),
        F.sum(F.when((F.col("label") == 1.0) & (F.col("prediction") == 0.0), F.lit(1)).otherwise(F.lit(0))).alias("fn"),
    ).collect()[0]
    return {key: int(row[key] or 0) for key in ["tp", "fp", "tn", "fn"]}


def write_report(config: dict[str, Any], payload: dict[str, Any]) -> None:
    """Write ML citation prediction JSON and Markdown reports."""
    json_path = resolve_project_path(config, config["paths"]["ml_citation_report_json"])
    markdown_path = resolve_project_path(config, config["paths"]["ml_citation_report_md"])
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    lines = [
        "# ML Citation Prediction",
        "",
        f"Generated on {date.today().isoformat()}.",
        "",
        "## Summary",
        "",
        f"- Status: {payload.get('status')}",
        f"- Records: {payload.get('record_count')}",
        f"- Citation threshold: {payload.get('citation_threshold')}",
        f"- Train rows: {payload.get('train_count')}",
        f"- Test rows: {payload.get('test_count')}",
        f"- Positive labels: {payload.get('positive_count')}",
        f"- Negative labels: {payload.get('negative_count')}",
        f"- Area under ROC: {payload.get('area_under_roc'):.4f}",
        f"- Accuracy: {payload.get('accuracy'):.4f}",
        f"- Majority baseline accuracy: {payload.get('majority_baseline_accuracy'):.4f}",
        "",
        "## Confusion Matrix",
        "",
        "| true positive | false positive | true negative | false negative |",
        "| ---: | ---: | ---: | ---: |",
    ]
    matrix = payload.get("confusion_matrix", {})
    lines.append(
        f"| {matrix.get('tp', 0)} | {matrix.get('fp', 0)} | {matrix.get('tn', 0)} | {matrix.get('fn', 0)} |"
    )
    lines.extend(
        [
            "",
            "## Feature Coefficients",
            "",
            "| feature | coefficient |",
            "| --- | ---: |",
        ]
    )
    for row in payload.get("feature_coefficients", []):
        lines.append(f"| {row['feature']} | {row['coefficient']:.6f} |")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "This is a small supervised baseline for identifying papers in the top citation quartile within the current sample. It is not a causal model and should not be interpreted as predicting scientific quality. Recent papers have had less time to accumulate citations, so publication year can dominate this task.",
        ]
    )
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_citation_prediction(config: dict[str, Any]) -> dict[str, Any]:
    """Run citation prediction baseline and write outputs."""
    preflight = preflight_environment(config)
    if not preflight["ok"]:
        payload = {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": "blocked",
            "preflight": preflight,
        }
        write_report(config, payload)
        return payload

    spark = create_spark_session(config)
    try:
        _, F, _ = _spark_imports()
        from pyspark.ml.classification import LogisticRegression
        from pyspark.ml.evaluation import BinaryClassificationEvaluator, MulticlassClassificationEvaluator
        from pyspark.ml.feature import VectorAssembler

        ml_config = config["spark"].get("ml", {})
        seed = int(ml_config.get("seed", 660))
        test_fraction = float(ml_config.get("test_fraction", 0.3))
        high_citation_quantile = float(ml_config.get("high_citation_quantile", 0.75))

        publications = spark.read.parquet(_path(config, "gold_publications"))
        citation_threshold = publications.approxQuantile(
            "cited_by_count", [high_citation_quantile], 0.0
        )[0]
        features = build_feature_table(publications, citation_threshold).cache()
        features.write.mode("overwrite").parquet(_path(config, "ml_citation_features"))

        assembler = VectorAssembler(inputCols=FEATURE_COLUMNS, outputCol="features")
        assembled = assembler.transform(features)
        train, test = assembled.randomSplit([1.0 - test_fraction, test_fraction], seed=seed)
        train = train.cache()
        test = test.cache()

        model = LogisticRegression(featuresCol="features", labelCol="label", maxIter=50, regParam=0.1).fit(train)
        predictions = model.transform(test).cache()
        predictions.select(
            "paper_id",
            "title",
            "cited_by_count",
            "label",
            "prediction",
            "probability",
            *FEATURE_COLUMNS,
        ).write.mode("overwrite").parquet(_path(config, "ml_citation_predictions"))

        binary_evaluator = BinaryClassificationEvaluator(labelCol="label", rawPredictionCol="rawPrediction")
        multiclass_evaluator = MulticlassClassificationEvaluator(
            labelCol="label", predictionCol="prediction", metricName="accuracy"
        )
        area_under_roc = float(binary_evaluator.evaluate(predictions, {binary_evaluator.metricName: "areaUnderROC"}))
        accuracy = float(multiclass_evaluator.evaluate(predictions))

        positive_count = features.where("label = 1.0").count()
        negative_count = features.where("label = 0.0").count()
        feature_coefficients = [
            {"feature": feature, "coefficient": float(coefficient)}
            for feature, coefficient in zip(FEATURE_COLUMNS, model.coefficients)
        ]
        top_predictions = [
            row.asDict()
            for row in predictions.orderBy(F.desc("probability"), F.desc("cited_by_count"))
            .select("paper_id", "title", "cited_by_count", "label", "prediction")
            .limit(10)
            .collect()
        ]
        payload = {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": "success",
            "preflight": preflight,
            "record_count": features.count(),
            "citation_threshold": citation_threshold,
            "high_citation_quantile": high_citation_quantile,
            "train_count": train.count(),
            "test_count": test.count(),
            "positive_count": positive_count,
            "negative_count": negative_count,
            "area_under_roc": area_under_roc,
            "accuracy": accuracy,
            "majority_baseline_accuracy": majority_baseline_accuracy(positive_count, negative_count),
            "confusion_matrix": evaluate_confusion_counts(predictions),
            "feature_columns": FEATURE_COLUMNS,
            "feature_coefficients": feature_coefficients,
            "top_predictions": top_predictions,
            "outputs": {
                key: str(resolve_project_path(config, value))
                for key, value in config["paths"].items()
                if key.startswith("ml_citation_")
            },
        }
        write_report(config, payload)
        return payload
    finally:
        spark.stop()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/dev.yaml")
    args = parser.parse_args()
    config = load_config(Path(args.config))
    payload = run_citation_prediction(config)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "record_count": payload.get("record_count"),
                "citation_threshold": payload.get("citation_threshold"),
                "area_under_roc": payload.get("area_under_roc"),
                "accuracy": payload.get("accuracy"),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
