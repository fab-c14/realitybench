# Build self-contained bundles and push RealityBench tasks to Kaggle Benchmarks.
# Prerequisites: `uv run kaggle auth login` (account must be phone-verified).
# Usage: scripts/push_all_tasks.ps1 [-Skip realitybench-checkout,...]
param([string[]]$Skip = @())
$env:PYTHONIOENCODING = "utf-8"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $root

uv run python scripts/build_kaggle_tasks.py

Get-ChildItem kaggle_tasks/*.py | Sort-Object Name | Where-Object { $Skip -notcontains $_.BaseName } | ForEach-Object {
    $slug = $_.BaseName
    Write-Host "=== Pushing $slug ===" -ForegroundColor Cyan
    uv run kaggle b t push $slug -f $_.FullName --wait 900 2>&1 | Select-Object -Last 3
    uv run kaggle b t status $slug 2>&1 | Select-String "Status:"
}
Write-Host "All tasks pushed." -ForegroundColor Green
