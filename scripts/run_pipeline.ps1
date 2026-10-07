param(
    [string]$Config = "configs/dev.yaml",
    [string]$LogDir = "logs"
)

$ErrorActionPreference = "Stop"

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$timestamp = Get-Date -Format "yyyyMMddTHHmmss"
$logPath = Join-Path $LogDir "pipeline_$timestamp.log"

$steps = @(
    @{ Name = "Acquire OpenAlex"; Command = "python -m scigraph.ingestion.acquire_openalex --config $Config" },
    @{ Name = "Inspect Schema"; Command = "python -m scigraph.ingestion.inspect_schema --config $Config" },
    @{ Name = "Data Quality"; Command = "python -m scigraph.preprocessing.quality --config $Config" },
    @{ Name = "Bronze Silver Gold Pipeline"; Command = "python -m scigraph.preprocessing.pipeline --config $Config" },
    @{ Name = "Scalability Benchmark"; Command = "python -m scigraph.experiments.scalability_benchmark --config $Config" },
    @{ Name = "Text TF-IDF"; Command = "python -m scigraph.text.tfidf --config $Config" },
    @{ Name = "Text Clustering"; Command = "python -m scigraph.text.clustering --config $Config" },
    @{ Name = "Citation Graph"; Command = "python -m scigraph.graph.citation_graph --config $Config" },
    @{ Name = "Author Collaboration"; Command = "python -m scigraph.graph.author_collaboration --config $Config" },
    @{ Name = "Temporal Trends"; Command = "python -m scigraph.temporal.trends --config $Config" },
    @{ Name = "Streaming Microbatch"; Command = "python -m scigraph.streaming.microbatch --config $Config" },
    @{ Name = "Sparse Retrieval"; Command = "python -m scigraph.retrieval.sparse --config $Config" },
    @{ Name = "Advanced Retrieval"; Command = "python -m scigraph.retrieval.advanced --config $Config" },
    @{ Name = "Citation Prediction"; Command = "python -m scigraph.evaluation.citation_prediction --config $Config" },
    @{ Name = "Composite Ranking"; Command = "python -m scigraph.ranking.composite --config $Config" },
    @{ Name = "Publication Feature Mart"; Command = "python -m scigraph.features.publication_mart --config $Config" },
    @{ Name = "Visualizations"; Command = "python -m scigraph.visualization.figures --config $Config" },
    @{ Name = "Tests"; Command = "python -m pytest" }
)

Start-Transcript -Path $logPath | Out-Null
try {
    Write-Host "SciGraph pipeline run"
    Write-Host "Config: $Config"
    Write-Host "Log: $logPath"
    Write-Host "Spark UI: check http://localhost:4040 while Spark stages are running."

    $pipelineStart = Get-Date
    foreach ($step in $steps) {
        $stepStart = Get-Date
        Write-Host ""
        Write-Host "[$($stepStart.ToString('s'))] START $($step.Name)"
        Write-Host ">>> $($step.Command)"

        Invoke-Expression $step.Command
        if ($LASTEXITCODE -ne 0) {
            throw "Step failed with exit code ${LASTEXITCODE}: $($step.Name)"
        }

        $elapsed = (Get-Date) - $stepStart
        Write-Host "[$((Get-Date).ToString('s'))] END $($step.Name) in $($elapsed.ToString())"
    }

    $total = (Get-Date) - $pipelineStart
    Write-Host ""
    Write-Host "Pipeline complete in $($total.ToString())."
}
finally {
    Stop-Transcript | Out-Null
    Write-Host "Transcript saved to $logPath"
}
