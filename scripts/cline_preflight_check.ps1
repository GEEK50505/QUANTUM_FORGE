<#
cline_preflight_check.ps1

Quick preflight: simulate what Cline will include for a prompt and fail fast if the assembled
context would be too large. Use this before running a request to avoid sending oversized prompts
that cause provider errors or timeouts.

Usage:
  powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\cline_preflight_check.ps1

Options:
  -Path <file>   # path to the file you're editing/asking about (optional)

#>
param(
    [string]$Path
)

function Read-Config($path) {
    $yaml = Get-Content $path -Raw
    $cfg = @{ perFileCharLimit = 400; totalContextCharLimit = 2000; excludePaths = @('node_modules','frontend'); includePaths = @('src') }
    foreach ($line in $yaml -split "`n") {
        $l = $line.Trim()
        if ($l -match "perFileCharLimit:\s*(\d+)") { $cfg.perFileCharLimit = [int]$Matches[1] }
        if ($l -match "totalContextCharLimit:\s*(\d+)") { $cfg.totalContextCharLimit = [int]$Matches[1] }
        if ($l -like "- 'src'*" -or $l -like ' - "src"*') { $cfg.includePaths = @('src') }
    }
    return $cfg
}

$configPath = "$env:USERPROFILE\\.continue\\config.yaml"
if (-not (Test-Path $configPath)) { $configPath = "c:\Users\G_R_E\.continue\config.yaml" }
if (-not (Test-Path $configPath)) { Write-Error "Cannot find cline config at $configPath"; exit 1 }

$cfg = Read-Config $configPath
Write-Host "Using perFileCharLimit=$($cfg.perFileCharLimit), totalContextCharLimit=$($cfg.totalContextCharLimit)" -ForegroundColor Cyan

# Find candidate files under includePaths but respect excludePaths
$repoRoot = (Resolve-Path .).Path
$candidates = @()
foreach ($inc in $cfg.includePaths) {
    $root = Join-Path $repoRoot $inc
    if (-not (Test-Path $root)) { continue }
    $files = Get-ChildItem -Path $root -Recurse -File -ErrorAction SilentlyContinue
    foreach ($f in $files) {
        $skip = $false
        foreach ($ex in $cfg.excludePaths) { if ($f.FullName -like "*$ex*") { $skip = $true; break } }
        if (-not $skip) { $candidates += $f }
    }
}

$report = @()
$total = 0
foreach ($f in $candidates) {
    try { $text = Get-Content $f.FullName -Raw -ErrorAction Stop } catch { continue }
    $len = $text.Length
    $inc = [Math]::Min($len, $cfg.perFileCharLimit)
    $report += [PSCustomObject]@{ File = $f.FullName; Length = $len; Included = $inc }
}

$report = $report | Sort-Object -Property Included -Descending

Write-Host "Top candidate files (will be truncated to include limit):" -ForegroundColor Green
$report | Select-Object -First 20 | Format-Table @{Label='Included';Expression={$_.Included}}, @{Label='Length';Expression={$_.Length}}, File -AutoSize

$selectedTotal = 0
$selected = @()
foreach ($r in $report) {
    if ($selectedTotal -ge $cfg.totalContextCharLimit) { break }
    $toAdd = [Math]::Min($r.Included, $cfg.totalContextCharLimit - $selectedTotal)
    if ($toAdd -le 0) { break }
    $selected += [PSCustomObject]@{ File = $r.File; Included = $toAdd }
    $selectedTotal += $toAdd
}

Write-Host "\nFiles that would actually be sent (truncated):" -ForegroundColor Cyan
$selected | Format-Table @{Label='Included';Expression={$_.Included}}, File -AutoSize

Write-Host "Total selected chars: $selectedTotal (limit: $($cfg.totalContextCharLimit))" -ForegroundColor Yellow
if ($selectedTotal -gt $cfg.totalContextCharLimit) { Write-Error "Context too large: reduce perFileCharLimit or exclude files"; exit 2 }
Write-Host "Preflight OK — selected context is within limits." -ForegroundColor Green
exit 0
