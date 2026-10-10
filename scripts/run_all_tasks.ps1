# Run every pushed RealityBench task on Kaggle against a set of models.
# Usage: scripts/run_all_tasks.ps1 [-Models claude-opus-5-5-default,gpt-5.6-sol]
param([string[]]$Models = @(
    "claude-opus-5-5-default",
    "gpt-5.6-sol",
    "gemini-3.8-flash",
    "gemma-4-31b-it",
    "qwen3-coder-480b-a35b-instruct"
))
$env:PYTHONIOENCODING = "utf-8"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $root

$modelArgs = $Models | ForEach-Object { "-m"; $_ }
Get-ChildItem kaggle_tasks/*.py | Sort-Object Name | ForEach-Object {
    $slug = $_.BaseName
    Write-Host "=== Running $slug ===" -ForegroundColor Cyan
    uv run kaggle b t run $slug @modelArgs 2>&1 | Select-Object -Last 3
}
Write-Host "All runs started. Collect with: uv run python scripts/collect_kaggle_results.py" -ForegroundColor Green
