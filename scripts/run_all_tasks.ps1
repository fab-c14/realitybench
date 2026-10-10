# Run pushed RealityBench tasks on Kaggle, one model and task at a time.
# Kaggle reserves each call's worst-case cost up front, so parallel runs exhaust the quota.
# Usage: scripts/run_all_tasks.ps1 [-Models gpt-5.6-sol] [-Tasks chat,search]
param([string[]]$Tasks = @(), [string[]]$Models = @(
    "claude-opus-5-5-default",
    "gpt-5.6-sol",
    "gemini-3.8-flash",
    "gemma-4-31b-it",
    "qwen3-coder-480b-a35b-instruct"
))
$env:PYTHONIOENCODING = "utf-8"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $root

$Models = $Models -split ","
$Tasks = $Tasks -split "," | Where-Object { $_ }
$slugs = if ($Tasks) { $Tasks | ForEach-Object { "realitybench-$_" } } else {
    Get-ChildItem kaggle_tasks/*.py | Sort-Object Name | ForEach-Object { $_.BaseName }
}
foreach ($model in $Models) {
    foreach ($slug in $slugs) {
        Write-Host "=== $model / $slug ===" -ForegroundColor Cyan
        uv run kaggle b t run $slug -m $model --wait 1200 2>&1 | Select-Object -Last 1
    }
}
Write-Host "Done. Collect with: uv run python scripts/collect_kaggle_results.py" -ForegroundColor Green
