param(
    [Parameter(Mandatory=$true)][string]$Key
)

# Determine the script directory reliably regardless of current working directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$keysDir = Join-Path $scriptDir 'roo_proxy'
$keysFile = Join-Path $keysDir 'keys.json'

if (-not (Test-Path $keysDir)) {
    New-Item -ItemType Directory -Path $keysDir | Out-Null
}

if (-not (Test-Path $keysFile)) {
    '[]' | Out-File -FilePath $keysFile -Encoding UTF8
}

try {
    $arr = Get-Content $keysFile -Raw | ConvertFrom-Json -ErrorAction Stop
} catch {
    $arr = @()
}

# If the file contained a single object, ConvertFrom-Json returns a PSCustomObject.
# Normalize to an array so we can append safely.
if ($arr -is [System.Management.Automation.PSCustomObject]) { $arr = @($arr) }
if ($null -eq $arr) { $arr = @() }

$obj = @{ key = $Key; disabledUntil = $null }
$arr = @($arr) + $obj

$arr | ConvertTo-Json -Depth 5 | Out-File -FilePath $keysFile -Encoding UTF8 -Force

function MaskKey($k) { if ($k.Length -gt 8) { return $k.Substring(0,4) + '...' + $k.Substring($k.Length-4) } else { return ('*' * ($k.Length - 4)) + $k.Substring($k.Length-4) } }

Write-Host "Added key to $keysFile (masked): $(MaskKey $Key)"
