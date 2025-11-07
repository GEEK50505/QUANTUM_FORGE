# Roo Code Automatic Key Testing & Proxy Setup

This repository includes automated key testing and proxy configuration that starts when you open VS Code. The system will:

1. Test all your OpenRouter API keys in parallel to find the fastest working one
2. Configure Roo Code to use the best key automatically
3. Start a local proxy that handles key rotation if you hit rate limits

## Files & Components

- `scripts/roo_proxy/key_tester.py` — Fast parallel key tester (tests all keys simultaneously)
- `scripts/roo_proxy/keys.json` — Your pool of API keys (copy from keys.json.sample)
- `scripts/roo_proxy/start_proxy.sh` — Automatic startup script
- `.vscode/tasks.json` — VS Code task that runs on workspace open
- `.vscode/settings.json` — Roo Code & proxy configuration

## Quick Start

1. Copy the sample keys file and add your keys:

```bash
# Copy the sample
cp scripts/roo_proxy/keys.json.sample scripts/roo_proxy/keys.json

# Edit keys.json and add your OpenRouter API keys
code scripts/roo_proxy/keys.json
```

2. Install Python packages (one-time setup):

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install aiohttp for fast parallel testing
pip install aiohttp
```

3. That's it! Now when you open VS Code:
- The workspace task will run automatically
- It tests all your keys in parallel to find the fastest one
- Roo Code is pre-configured to use the best key
- The proxy handles auto-rotation if you hit rate limits

Manual Testing (optional):
```bash
# Test your keys manually and see diagnostics
python3 scripts/roo_proxy/key_tester.py --keys-file scripts/roo_proxy/keys.json

# Or just get the best key
python3 scripts/roo_proxy/key_tester.py --keys-file scripts/roo_proxy/keys.json --best-only
```

## How It Works

The automated system has three parts:

1. **Fast Key Testing**:
   - Uses asyncio + aiohttp to test all keys simultaneously
   - Probes OpenRouter's lightweight /models endpoint
   - Measures response times to find the fastest working key
   - Results cached in `.vscode/current_key.txt`

2. **VS Code Integration**:
   - Task in `tasks.json` runs on workspace open
   - Updates Roo Code settings automatically
   - Proxy starts in background if needed

3. **Key Rotation**:
   - Proxy watches for rate limits (429 responses)
   - Auto-switches to next best key when needed
   - Keys disabled temporarily after rate limits
   - Re-tests keys periodically to find fastest

## Security Notes

- `keys.json` stores keys locally in plaintext
- Keep it out of version control (in .gitignore)
- Consider file permissions to protect keys
- Proxy is for local dev only - do not expose publicly

## Advanced Usage

- Edit `key_tester.py` options:
  ```bash
  # Change concurrency (default 20):
  python3 key_tester.py --concurrency 10

  # Adjust timeout (default 5s):
  python3 key_tester.py --timeout 3.0
  
  # Use different test endpoint:
  python3 key_tester.py --test-url "https://..."
  ```

- VS Code settings in `.vscode/settings.json` configure:
  - Proxy URL and auto-start
  - Key rotation behavior
  - Python environment paths
