# OpenRouter API key rotation

This workspace is configured to let the Continue extension use OpenRouter (Qwen 3 Coder free mode). The signing key is read from the environment variable `OPENROUTER_API_KEY`.

This document explains the recommended, simple rotation workflow.

Steps

1. Run the provided PowerShell script to rotate the key:

   - From the repository root (Windows PowerShell):

```powershell
.\scripts\rotate_openrouter_key.ps1
# or with a parameter
.\scripts\rotate_openrouter_key.ps1 -NewKey "sk-..."
```

2. The script will:
   - Back up any existing `.env.local` to `.env.local.bak.TIMESTAMP`.
   - Write `OPENROUTER_API_KEY=...` into `.env.local`.
   - Persist the value into your user environment (via `setx`) so new processes pick it up.
   - Record a masked history entry in `openrouter_keys_history.json`.

3. Restart VS Code (or open a new VS Code window) so the editor picks up the updated user environment variable.

Security notes

- The script does NOT store full keys in the history file; only masked values are kept.
- `.env.local` and `openrouter_keys_history.json` are added to `.gitignore` to avoid accidental commits.
- If you prefer to store keys in a secure secrets manager (recommended for teams), adapt the script to call that provider instead of `setx`.

Troubleshooting

- If the Continue extension does not pick up the key after rotation, restart the entire OS session or sign out/in so `setx` changes are available in new processes.
- You can check the current value available to new shells with:

```powershell
Get-ChildItem Env:OPENROUTER_API_KEY
```
