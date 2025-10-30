<#
generate_file_summaries.ps1

Create simple file summaries for large files and save them to `.cline/summaries.json`.
These summaries are lightweight placeholders to avoid sending full files to the model repeatedly.

Usage:
  powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\generate_file_summaries.ps1

#>
param(
    [string]$RepoRoot = (Get-Location).Path,
    [int]$PerFileCharLimit = 800,
    [int]$MinFileSizeToSummarize = 2000
)

$outDir = Join-Path $RepoRoot ".cline"
if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir | Out-Null }
$summaryFile = Join-Path $outDir "summaries.json"

$summaries = @{}

Get-ChildItem -Path $RepoRoot -Recurse -File -ErrorAction SilentlyContinue | Where-Object {
    # Skip node_modules and frontend as per project defaults
    ($_.FullName -notmatch "\\node_modules\\") -and ($_.FullName -notmatch "\\frontend\\")
} | ForEach-Object {
    try {
        $text = Get-Content $_.FullName -Raw -ErrorAction Stop
    } catch { return }
    if ($text.Length -ge $MinFileSizeToSummarize) {
        $snippet = $text.Substring(0, [Math]::Min($PerFileCharLimit, $text.Length))
        $summaries[$_.FullName] = @{ summary = $snippet; generated = (Get-Date).ToString('o'); len = $text.Length }
    }
}

$summaries | ConvertTo-Json -Depth 3 | Out-File -FilePath $summaryFile -Encoding UTF8 -Force
Write-Host "Wrote summaries for $($summaries.Count) files to $summaryFile"
