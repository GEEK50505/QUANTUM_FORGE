<#
diagnose_cline_context.ps1

Simulate the `cline` context selection using rules from c:\Users\G_R_E\.continue\config.yaml.
It will:
 - load the config
 - walk the repo (from repo root)
 - apply exclude paths and char limits
 - report the top files that would be included and the total estimated characters

Usage:
  powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\diagnose_cline_context.ps1

#>
param(
    [string]$RepoRoot = (Resolve-Path "$(Split-Path -Parent $PSCommandPath)\.." ),
    [string]$ConfigPath = "c:\Users\G_R_E\.continue\config.yaml"
)

function Read-Config($path) {
    if (-not (Test-Path $path)) { Write-Error "Config not found: $path"; exit 1 }
    $yaml = Get-Content $path -Raw
    # Very small YAML parse for the limited config keys we need (no external deps)
    $cfg = @{ excludePaths = @(); perFileCharLimit = 2000; totalContextCharLimit = 8000 }
    foreach ($line in $yaml -split "`n") {
        $l = $line.Trim()
        if ($l -like "- *node_modules*") { $cfg.excludePaths += "node_modules" }
        if ($l -like "*frontend*" -and $l.StartsWith('-')) { $cfg.excludePaths += "frontend" }
        if ($l -match "perFileCharLimit:\s*(\d+)") { $cfg.perFileCharLimit = [int]$Matches[1] }
        if ($l -match "totalContextCharLimit:\s*(\d+)") { $cfg.totalContextCharLimit = [int]$Matches[1] }
        if ($l -like "*\.svg*" -and $l.StartsWith('-')) { $cfg.excludeExtensions += ".svg" }
        if ($l -like "*\.map*" -and $l.StartsWith('-')) { $cfg.excludeExtensions += ".map" }
        if ($l -like "*\.css*" -and $l.StartsWith('-')) { $cfg.excludeExtensions += ".css" }
        if ($l -like "*\.png*" -and $l.StartsWith('-')) { $cfg.excludeExtensions += ".png" }
    }
    return $cfg
}

$cfg = Read-Config $ConfigPath
Write-Host "Using config: perFileCharLimit=$($cfg.perFileCharLimit), totalContextCharLimit=$($cfg.totalContextCharLimit)" -ForegroundColor Cyan
Write-Host "Excluding paths: $($cfg.excludePaths -join ', ')" -ForegroundColor Cyan

$files = Get-ChildItem -Path $RepoRoot -Recurse -File -ErrorAction SilentlyContinue | Where-Object {
    $include = $true
    foreach ($ex in $cfg.excludePaths) {
        if ($_.FullName -like "*$ex*") { $include = $false; break }
    }
    # skip binary heavy files by extension and configured excludeExtensions
    $ext = $_.Extension.ToLower()
    $binarySkip = @('.exe','.dll','.png','.jpg','.jpeg','.gif','.zip','.tar','.gz','.so','.bin')
    if ($ext -in $binarySkip) { $include = $false }
    if ($cfg.ContainsKey('excludeExtensions') -and $cfg.excludeExtensions -contains $ext) { $include = $false }
    $include
}

$report = @()
$totalChars = 0
foreach ($f in $files) {
    try {
        $text = Get-Content $f.FullName -Raw -ErrorAction Stop
    } catch { continue }
    $chars = $text.Length
    $charsIncluded = [Math]::Min($chars, $cfg.perFileCharLimit)
    $report += [PSCustomObject]@{ FullName = $f.FullName; Chars = $chars; Included = $charsIncluded }
    $totalChars += $charsIncluded
}

# Now simulate selecting files until the totalContextCharLimit is reached
$report = $report | Sort-Object -Property Included -Descending

Write-Host "Files considered (Ordered by IncludedChars):" -ForegroundColor Green
$report | Select-Object -First 30 | Format-Table @{Label='IncludedChars';Expression={$_.Included}}, @{Label='TotalChars';Expression={$_.Chars}}, FullName -AutoSize

$selected = @()
$selectedTotal = 0
foreach ($r in $report) {
    if ($selectedTotal -ge $cfg.totalContextCharLimit) { break }
    $toAdd = [Math]::Min($r.Included, $cfg.totalContextCharLimit - $selectedTotal)
    if ($toAdd -le 0) { break }
    $selected += [PSCustomObject]@{ FullName = $r.FullName; Included = $toAdd; TotalChars = $r.Chars }
    $selectedTotal += $toAdd
}

Write-Host "\nFiles that would be sent (in order, truncated by limits):" -ForegroundColor Cyan
$selected | Format-Table @{Label='IncludedChars';Expression={$_.Included}}, @{Label='TotalChars';Expression={$_.TotalChars}}, FullName -AutoSize

Write-Host "\nTotal chars selected for context: $selectedTotal (limit: $($cfg.totalContextCharLimit))" -ForegroundColor Yellow
if ($selectedTotal -ge $cfg.totalContextCharLimit) {
    Write-Host "Context would reach the configured limit; large files are truncated or skipped. Consider raising limits or refining excludes if needed." -ForegroundColor Yellow
} else {
    Write-Host "Context is within the configured limit." -ForegroundColor Green
}
