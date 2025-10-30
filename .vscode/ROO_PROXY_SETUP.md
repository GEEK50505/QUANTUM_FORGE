# Roo proxy and key rotation

This repository contains a small local proxy that you can run to avoid hitting provider rate limits directly from the Roo extension or other tools. The proxy rotates API keys when it detects rate limits or provider errors.

Files of interest

- `scripts/roo_proxy/proxy.js` — Node/Express proxy that forwards requests to OpenRouter (`https://api.openrouter.ai`) and rotates keys from `keys.json` when 429 responses or errors occur.
- `scripts/roo_proxy/keys.json` — pool of API keys (managed by the helper scripts).
- `scripts/add_roo_key.ps1` — add a new key to the pool (masking output).
- `scripts/remove_roo_key.ps1` — remove keys by prefix.

Quick start

1. Install dependencies for the proxy (requires Node.js installed):

```powershell
cd .\scripts\roo_proxy
npm install
```

2. Add your keys (repeat for each key you rotate into):

```powershell
. .\..\add_roo_key.ps1 -Key "sk-or-<your-key-here>"
```

3. Start the proxy (runs on port 3002 by default):

```powershell
cd .\scripts\roo_proxy
npm start
# or
node proxy.js
```

4. Configure the Roo extension (or other extension) to use the proxy as the API base URL.

   - If the extension lets you change the provider base URL, set it to:

     `http://localhost:3002`

   - If the extension requires an API key, leave it blank (the proxy manages keys). If the extension insists on a key, use a placeholder; real keys are supplied by the proxy.

How rotation works

- The proxy picks the next available key in round-robin fashion.
- When it receives a 429 from OpenRouter, it marks the key as disabled for a short backoff (default 60s) and retries with the next available key.
- If all keys are exhausted, the proxy returns a 502/429 to the client.

Security notes

- `keys.json` stores keys in plaintext locally. Keep it out of version control (it is not added to the repo by default); you may want to protect it using filesystem permissions.
- This proxy is for local development only. Do not expose it publicly.

Advanced

- You can edit `proxy.js` to change backoff timings or persist disabledUntil timestamps differently.
- Consider replacing the simple JSON store with an encrypted store or a small Redis instance if you need multi-user rotation.
