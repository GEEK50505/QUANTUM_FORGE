param(
    [Parameter(Mandatory=$true)][string]$KeyPrefix
)

# Determine keys.json location relative to this script
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$keysFile = Join-Path $scriptDir 'roo_proxy\keys.json'
if (-not (Test-Path $keysFile)) { Write-Error "$keysFile not found"; exit 1 }

try { $arr = Get-Content $keysFile -Raw | ConvertFrom-Json -ErrorAction Stop } catch { $arr = @() }

$new = @()
foreach ($e in $arr) {
    if ($e.key -like "$KeyPrefix*") { continue }
    $new += $e
}

$new | ConvertTo-Json -Depth 5 | Out-File -FilePath $keysFile -Encoding UTF8 -Force
Write-Host "Removed keys with prefix $KeyPrefix (if any)"
