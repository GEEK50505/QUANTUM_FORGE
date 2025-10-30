<#
cline_cache.ps1

Simple file-backed prompt/response cache for local use. This reduces repeated OpenRouter calls for identical prompts,
which improves throughput when you run similar tasks repeatedly.

Usage examples:
  # Get cached response (or empty if not present)
  .\scripts\cline_cache.ps1; Get-ClineCache -Prompt "Summarize the README"

  # Set a cache entry
  .\scripts\cline_cache.ps1; Set-ClineCache -Prompt "Summarize the README" -Response "Short summary" -TtlMinutes 60

  # Invoke provider with cache fallback (will call OpenRouter if not cached). Requires OPENROUTER_API_KEY to be set.
  .\scripts\cline_cache.ps1; Invoke-OpenRouterWithCache -Prompt "Summarize the README"

# Note: This script is intended as a developer helper. You can adapt/pipe it into an editor extension or wrapper.
#>

param()

Set-StrictMode -Version Latest

$CacheFile = Join-Path (Resolve-Path "$(Split-Path -Parent $PSCommandPath)\..") ".cline\cline_cache.json"
if (-not (Test-Path (Split-Path $CacheFile))) { New-Item -ItemType Directory -Path (Split-Path $CacheFile) | Out-Null }
if (-not (Test-Path $CacheFile)) { '{}' | Out-File -FilePath $CacheFile -Encoding UTF8 }

function Read-Cache() {
    try { Get-Content $CacheFile -Raw | ConvertFrom-Json -ErrorAction Stop } catch { @{} }
}

function Write-Cache($obj) {
    $obj | ConvertTo-Json -Depth 5 | Out-File -FilePath $CacheFile -Encoding UTF8 -Force
}

function Get-KeyForPrompt([string]$prompt) {
    # simple key: sha256 hex of the prompt
    $sha = [System.Security.Cryptography.SHA256]::Create()
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($prompt)
    $hash = $sha.ComputeHash($bytes)
    ($hash | ForEach-Object { $_.ToString('x2') }) -join ''
}

function Get-ClineCache {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)] [string]$Prompt
    )
    $cache = Read-Cache
    $key = Get-KeyForPrompt $Prompt
    if ($cache.ContainsKey($key)) {
        $entry = $cache[$key]
        $expiry = [DateTime]::Parse($entry.expires)
        if ($expiry -gt (Get-Date)) { return $entry.response }
        else { $cache.Remove($key); Write-Cache $cache; return $null }
    }
    return $null
}

function Set-ClineCache {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)] [string]$Prompt,
        [Parameter(Mandatory=$true)] [string]$Response,
        [int]$TtlMinutes = 60
    )
    $cache = Read-Cache
    $key = Get-KeyForPrompt $Prompt
    $obj = @{ response = $Response; expires = (Get-Date).AddMinutes($TtlMinutes).ToString('o') }
    $cache[$key] = $obj
    Write-Cache $cache
    return $true
}

function Invoke-OpenRouterWithCache {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)] [string]$Prompt,
        [int]$MaxTokens = 128,
        [int]$TtlMinutes = 60
    )
    $cached = Get-ClineCache -Prompt $Prompt
    if ($cached) {
        Write-Host "Returning cached response" -ForegroundColor Green
        return $cached
    }

    if (-not $env:OPENROUTER_API_KEY) { Write-Error "OPENROUTER_API_KEY not set. Cannot call provider."; return $null }

    $body = @{ model = 'qwen/qwen3-coder:free'; input = $Prompt; max_tokens = $MaxTokens } | ConvertTo-Json
    try {
        $resp = Invoke-RestMethod -Uri 'https://api.openrouter.ai/v1/chat/completions' -Method Post -Headers @{ Authorization = "Bearer $($env:OPENROUTER_API_KEY)" } -Body $body -ContentType 'application/json' -TimeoutSec 30
        # extract text; provider schemas vary — make a best-effort
        $text = $null
        if ($resp.choices -and $resp.choices.Count -gt 0) { $text = $resp.choices[0].message.content }
        if (-not $text) { $text = ($resp | ConvertTo-Json -Depth 3) }
        if ($text) { Set-ClineCache -Prompt $Prompt -Response $text -TtlMinutes $TtlMinutes }
        return $text
    } catch {
        Write-Warning "Provider call failed: $_"
        return $null
    }
}

Export-ModuleMember -Function Get-ClineCache,Set-ClineCache,Invoke-OpenRouterWithCache
