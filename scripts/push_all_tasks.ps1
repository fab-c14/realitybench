# Build self-contained bundles and push all 12 RealityBench tasks to Kaggle Benchmarks.
# Prerequisites: `uv run kaggle auth login` (account must be phone-verified).
$ErrorActionPreference = "Stop"
$env:PYTHONIOENCODING = "utf-8"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $root

uv run python scripts/build_kaggle_tasks.py

Get-ChildItem kaggle_tasks/*.py | Sort-Object Name | ForEach-Object {
    $slug = $_.BaseName
    Write-Host "=== Pushing $slug ===" -ForegroundColor Cyan
    uv run kaggle b t push $slug -f $_.FullName --wait 600
}
Write-Host "All tasks pushed." -ForegroundColor Green
