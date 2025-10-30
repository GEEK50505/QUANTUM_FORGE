# Cline optimizations and cache

This file explains the changes added to improve throughput and reduce interruptions when using the Cline/`cline` integration.

What we changed

- `c:\Users\G_R_E\.continue\config.yaml` — tightened limits, made the extension non-interactive, added an `includePaths` whitelist, disabled noisy progress notifications, and reduced max tokens and concurrency.
- `scripts\diagnose_cline_context.ps1` — diagnostics that simulate what files would be sent based on the config.
- `scripts\generate_file_summaries.ps1` — creates short summaries for large files into `.cline/summaries.json`.
- `scripts\cline_cache.ps1` — a local file-backed prompt/response cache and `Invoke-OpenRouterWithCache` helper. Use this when you want to avoid repeated remote calls for identical prompts.

How to use the cache helper (recommended for repeated tasks)

1. Ensure `OPENROUTER_API_KEY` is set (or use `scripts/rotate_openrouter_key.ps1` to set it).
2. In PowerShell, import or dot-source the script:

```powershell
. .\scripts\cline_cache.ps1
$resp = Invoke-OpenRouterWithCache -Prompt "Summarize the README" -MaxTokens 128 -TtlMinutes 120
Write-Output $resp
```

3. The first call will call the provider (and cache the response); subsequent identical prompts will return the cached response quickly.

Notes and caveats

- The cache is simple JSON stored at `.cline/cline_cache.json`. For production or team usage consider a dedicated cache (Redis, etc.).
- The `Invoke-OpenRouterWithCache` helper expects the provider to respond in an OpenAI-like shape; adjust parsing to match the actual provider responses if needed.
- If the extension itself does not support using an external cache, use this wrapper for scripted or manual tasks where repetition is common.

Debugging interruptions

- Temporarily set `logging.level` in `c:\Users\G_R_E\.continue\config.yaml` to `debug` to get a trace of context selection and provider calls. Revert to `info` afterwards.
- Use `scripts\diagnose_cline_context.ps1` to verify which files are being included before asking the model; this helps find surprises that cause delays.
