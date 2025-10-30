<#
rotate_openrouter_key.ps1

Simple script to rotate the OpenRouter API key used by the Continue extension.
This script will:
 - prompt for (or accept) a new API key
 - backup the existing .env.local (if present)
 - write the new OPENROUTER_API_KEY to .env.local
 - persist the key to the current user environment with `setx` so new processes pick it up
 - record a masked history entry in `openrouter_keys_history.json` (does NOT store full keys)

Usage:
  .\rotate_openrouter_key.ps1 -NewKey "sk-..."
  or run without parameter to be prompted interactively.

#>
param(
    [Parameter(Mandatory=$false)]
    [string]$NewKey
)

function Convert-SecureStringToPlainText([System.Security.SecureString]$s) {
    $ptr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($s)
    try { [System.Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr) }
    finally { [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr) }
}

if (-not $NewKey) {
    Write-Host "Enter new OpenRouter API key (input will be hidden):"
    $secure = Read-Host -AsSecureString
    $NewKey = Convert-SecureStringToPlainText $secure
}

if (-not $NewKey) {
    Write-Error "No API key provided. Exiting."
    exit 1
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Resolve-Path "$scriptDir\.."
$envFile = Join-Path $repoRoot ".env.local"
$historyFile = Join-Path $repoRoot "openrouter_keys_history.json"

function Mask-Key($k) {
    if (-not $k) { return "" }
    if ($k.Length -le 8) { return ('*' * ($k.Length -4)) + $k.Substring($k.Length-4) }
    return $k.Substring(0,4) + '...' + $k.Substring($k.Length-4)
}

# Backup existing env file
if (Test-Path $envFile) {
    $ts = (Get-Date).ToString('yyyyMMdd_HHmmss')
    $bak = "$envFile.bak.$ts"
    Copy-Item $envFile $bak -Force
    Write-Host "Backed up existing .env.local -> $bak"
}

# Write new .env.local (overwrite)
"OPENROUTER_API_KEY=$NewKey" | Out-File -FilePath $envFile -Encoding UTF8 -Force
Write-Host "Wrote new key to $envFile"

# Persist to user environment (setx writes new variable for future processes)
try {
    setx OPENROUTER_API_KEY $NewKey | Out-Null
    Write-Host "Persisted OPENROUTER_API_KEY to user environment (setx). New processes will inherit it."
} catch {
    Write-Warning "Failed to persist env var via setx: $_"
}

# Update history (store masked key only)
$entry = @{ timestamp = (Get-Date).ToString('o'); key = (Mask-Key $NewKey) }
if (Test-Path $historyFile) {
    try {
        $arr = Get-Content $historyFile -Raw | ConvertFrom-Json
    } catch {
        $arr = @()
    }
} else { $arr = @() }

$newArr = ,$entry + $arr | Select-Object -First 20
$newArr | ConvertTo-Json -Depth 3 | Out-File -FilePath $historyFile -Encoding UTF8 -Force
Write-Host "Appended masked key entry to $historyFile"

Write-Host "Rotation complete. NOTE: Restart VS Code (or open a new window) to pick up the updated user environment variable." -ForegroundColor Green
