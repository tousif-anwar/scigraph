param(
    [int]$ExpectedRecords = 1000000,
    [int]$RefreshSeconds = 30,
    [double]$ApproxBytesPerRecord = 13812.0,
    [switch]$Once
)

$ErrorActionPreference = "SilentlyContinue"

$rawPath = "data/raw/openalex_works_sample.jsonl"
$metadataPath = "data/raw/openalex_sample_metadata.json"
$reports = @(
    "reports/results/schema_summary.json",
    "reports/results/data_quality_report.json",
    "reports/results/bronze_silver_gold_report.json",
    "reports/results/text_analysis_report.json",
    "reports/results/clustering_report.json",
    "reports/results/citation_graph_report.json",
    "reports/results/author_collaboration_report.json",
    "reports/results/temporal_analysis_report.json",
    "reports/results/streaming_simulation_report.json",
    "reports/results/retrieval_report.json",
    "reports/results/advanced_retrieval_results.json",
    "reports/results/ml_citation_prediction_report.json",
    "reports/results/ranking_report.json",
    "reports/results/feature_mart_report.json"
)

function Show-Monitor {
    Clear-Host
    Write-Host "SciGraph pipeline monitor - $(Get-Date -Format s)"
    Write-Host ""
    Write-Host "Spark UI while Spark jobs run:"
    Write-Host "  http://localhost:4040"
    Write-Host "  http://localhost:4041 if 4040 is already in use"
    Write-Host ""

    if (Test-Path $rawPath) {
        $raw = Get-Item $rawPath
        $gb = [math]::Round($raw.Length / 1GB, 3)
        $mb = [math]::Round($raw.Length / 1MB, 1)
        $approxRecords = [math]::Floor($raw.Length / $ApproxBytesPerRecord)
        $percent = if ($ExpectedRecords -gt 0) {
            [math]::Round([math]::Min(100, ($approxRecords / $ExpectedRecords) * 100), 2)
        } else {
            0
        }
        Write-Host "Raw acquisition file:"
        Write-Host "  Path: $rawPath"
        Write-Host "  Size: $mb MB ($gb GB)"
        Write-Host "  Last write: $($raw.LastWriteTime)"
        Write-Host "  Approx records by file size: $approxRecords / $ExpectedRecords ($percent%)"
    } else {
        Write-Host "Raw acquisition file does not exist yet: $rawPath"
    }

    if (Test-Path $metadataPath) {
        try {
            $metadata = Get-Content $metadataPath -Raw | ConvertFrom-Json
            Write-Host ""
            Write-Host "Latest acquisition metadata:"
            Write-Host "  Mode: $($metadata.acquisition_mode)"
            Write-Host "  Actual records: $($metadata.actual_record_count)"
            Write-Host "  Retrieved UTC: $($metadata.retrieval_datetime_utc)"
        } catch {
            Write-Host ""
            Write-Host "Metadata exists but is not complete JSON yet."
        }
    }

    Write-Host ""
    Write-Host "Report files:"
    foreach ($report in $reports) {
        if (Test-Path $report) {
            $item = Get-Item $report
            $status = ""
            try {
                $json = Get-Content $report -Raw | ConvertFrom-Json
                if ($json.status) {
                    $status = " status=$($json.status)"
                }
            } catch {
                $status = ""
            }
            Write-Host ("  {0,-58} {1,10} bytes  {2}{3}" -f $report, $item.Length, $item.LastWriteTime.ToString("s"), $status)
        } else {
            Write-Host ("  {0,-58} missing" -f $report)
        }
    }
}

do {
    Show-Monitor
    if ($Once) {
        break
    }
    Start-Sleep -Seconds $RefreshSeconds
} while ($true)
