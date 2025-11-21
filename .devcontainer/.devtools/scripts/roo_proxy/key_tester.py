#!/usr/bin/env python3
"""Fast parallel OpenRouter API key tester for Roo Code

This script is intended to be called by the Roo Code extension or locally by
developers to quickly probe a pool of OpenRouter API keys and select the best
one (lowest latency + valid) for immediate use by a local proxy or extension.

Output: JSON printed to stdout with per-key diagnostics and a chosen best_key
field (or null if none available).

Notes:
- Uses GET /v1/models which is a lightweight, read-only endpoint. If your
  provider differs, pass --test-url to change it.
- Requires Python 3.8+. Uses aiohttp; install with `pip install aiohttp` in
  your dev environment (recommended inside a venv).
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from typing import List, Dict, Any

try:
    import aiohttp
except Exception as e:
    print(json.dumps({"error": "missing-dependency", "message": "aiohttp is required. Install with: pip install aiohttp"}))
    raise


DEFAULT_TEST_URL = os.environ.get("ROO_KEY_TEST_URL", "https://openrouter.ai/api/v1/models")

# Persistence paths
BASE_DIR = os.path.dirname(__file__)
BEST_KEY_JSON = os.environ.get("ROO_BEST_KEY_JSON", os.path.join(BASE_DIR, "best_key.json"))
BEST_KEY_ENV = os.environ.get("ROO_BEST_KEY_ENV", os.path.join(BASE_DIR, ".env"))
STALLED_KEYS_JSON = os.environ.get("ROO_STALLED_KEYS_JSON", os.path.join(BASE_DIR, "stalled_keys.json"))
WORKING_KEYS_JSON = os.environ.get("ROO_WORKING_KEYS_JSON", os.path.join(BASE_DIR, "working_keys.json"))


def load_stalled_keys() -> Dict[str, float]:
    """Return dict mapping key -> stalled_until_timestamp (epoch seconds)."""
    if not os.path.exists(STALLED_KEYS_JSON):
        return {}
    try:
        with open(STALLED_KEYS_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
            # expect {key: timestamp}
            if isinstance(data, dict):
                return {k: float(v) for k, v in data.items()}
    except Exception:
        pass
    return {}


def save_stalled_keys(d: Dict[str, float]) -> None:
    try:
        with open(STALLED_KEYS_JSON, "w", encoding="utf-8") as f:
            json.dump(d, f)
    except Exception:
        # non-fatal
        pass


# Retry/backoff config
MAX_RETRIES = int(os.environ.get("ROO_TESTER_MAX_RETRIES", "3"))
BACKOFF_BASE = float(os.environ.get("ROO_TESTER_BACKOFF_BASE", "1.5"))
BACKOFF_MAX = float(os.environ.get("ROO_TESTER_BACKOFF_MAX", "30"))

# Daily quota detection tokens
DAILY_QUOTA_TOKENS = ["free-models-per-day", "Add 10 credits", "daily quota", "free models per day"]

# Configure logger to stderr
logger = logging.getLogger("roo_key_tester")
if not logger.handlers:
    h = logging.StreamHandler(stream=sys.stderr)
    fmt = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")
    h.setFormatter(fmt)
    logger.addHandler(h)
logger.setLevel(logging.INFO)



async def probe_key(session: aiohttp.ClientSession, key: str, url: str, timeout: float) -> Dict[str, Any]:
    headers = {"Authorization": f"Bearer {key}"}
    attempt = 0
    last_err = None
    while attempt < MAX_RETRIES:
        attempt += 1
        start = time.perf_counter()
        try:
            async with session.get(url, headers=headers, timeout=timeout) as resp:
                latency = time.perf_counter() - start
                status = resp.status
                # Try to parse JSON body (may contain rate-limit message)
                body_text = None
                try:
                    body = await resp.text()
                    body_text = body or ""
                    # attempt JSON parse too
                    try:
                        _ = json.loads(body)
                    except Exception:
                        # ignore json parse errors - we still inspect text
                        pass
                except Exception:
                    body_text = ""

                # Detect daily quota message explicitly
                body_lower = (body_text or "").lower()
                daily_hit = any(tok.lower() in body_lower for tok in DAILY_QUOTA_TOKENS)

                if status == 200:
                    return {"key": key, "status": status, "latency": latency, "ok": True}

                # If this is a daily quota hit, return immediately with flag
                if status == 429 and daily_hit:
                    return {"key": key, "status": status, "latency": latency, "ok": False, "error": body_text, "quota_daily": True}

                # For other 429s or 5xx, we may retry
                if status in (429, 502, 503, 504):
                    last_err = {"key": key, "status": status, "latency": latency, "ok": False, "error": body_text}
                    # if not last attempt, sleep then retry
                    if attempt < MAX_RETRIES:
                        backoff = min(BACKOFF_MAX, BACKOFF_BASE ** attempt)
                        await asyncio.sleep(backoff)
                        continue
                    else:
                        return last_err

                # For other non-200 responses, return result (don't retry)
                return {"key": key, "status": status, "latency": latency, "ok": False, "error": body_text}

        except asyncio.TimeoutError:
            last_err = {"key": key, "status": "timeout", "latency": None, "ok": False, "error": "timeout"}
            if attempt < MAX_RETRIES:
                backoff = min(BACKOFF_MAX, BACKOFF_BASE ** attempt)
                await asyncio.sleep(backoff)
                continue
            return last_err
        except aiohttp.ClientResponseError as e:
            last_err = {"key": key, "status": e.status if hasattr(e, "status") else "error", "latency": None, "ok": False, "error": str(e)}
            if attempt < MAX_RETRIES:
                backoff = min(BACKOFF_MAX, BACKOFF_BASE ** attempt)
                await asyncio.sleep(backoff)
                continue
            return last_err
        except Exception as e:
            last_err = {"key": key, "status": "error", "latency": None, "ok": False, "error": str(e)}
            if attempt < MAX_RETRIES:
                backoff = min(BACKOFF_MAX, BACKOFF_BASE ** attempt)
                await asyncio.sleep(backoff)
                continue
            return last_err

    # Fallback
    return last_err or {"key": key, "status": "error", "latency": None, "ok": False, "error": "unknown"}


async def run_probe(keys: List[str], url: str, concurrency: int, timeout: float) -> List[Dict[str, Any]]:
    timeout_obj = aiohttp.ClientTimeout(total=None)
    connector = aiohttp.TCPConnector(limit=concurrency)
    async with aiohttp.ClientSession(timeout=timeout_obj, connector=connector) as session:
        sem = asyncio.Semaphore(concurrency)

        async def _bounded_probe(k: str):
            async with sem:
                return await probe_key(session, k, url, timeout)

        tasks = [asyncio.create_task(_bounded_probe(k)) for k in keys]
        results = await asyncio.gather(*tasks, return_exceptions=False)
        return results


def load_keys_from_file(path: str) -> List[str]:
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    with open(path, "r", encoding="utf-8") as fh:
        try:
            data = json.load(fh)
        except Exception:
            # allow simple newline-delimited file
            fh.seek(0)
            lines = [ln.strip() for ln in fh if ln.strip()]
            return lines

    # Accept either list of strings or list of objects with `key`
    if isinstance(data, list):
        keys: List[str] = []
        for item in data:
            if isinstance(item, str):
                keys.append(item)
            elif isinstance(item, dict) and "key" in item:
                keys.append(item["key"])
        return keys
    raise ValueError("Unsupported keys file format: expected JSON list of keys or objects")


def pick_best(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    # Filter ok results with numeric latency
    ok = [r for r in results if r.get("ok") and isinstance(r.get("latency"), (int, float))]
    ok_sorted = sorted(ok, key=lambda r: r["latency"]) if ok else []
    best = ok_sorted[0] if ok_sorted else None
    return {"best_key": best["key"] if best else None, "best_latency": best["latency"] if best else None}


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Parallel OpenRouter API key tester for Roo Code")
    p.add_argument("--keys-file", "-k", default="./scripts/roo_proxy/keys.json", help="Path to keys JSON or newline-delimited file")
    p.add_argument("--concurrency", "-c", type=int, default=20, help="Max concurrent probes")
    p.add_argument("--timeout", "-t", type=float, default=5.0, help="Per-request timeout in seconds")
    p.add_argument("--test-url", default=DEFAULT_TEST_URL, help="URL to probe (default: OpenRouter models endpoint)")
    p.add_argument("--best-only", action="store_true", help="Print only the best key string instead of full JSON")
    p.add_argument("--max-retries", type=int, default=MAX_RETRIES, help="Max retries per key (overrides ROO_TESTER_MAX_RETRIES)")
    p.add_argument("--backoff-base", type=float, default=BACKOFF_BASE, help="Backoff base (overrides ROO_TESTER_BACKOFF_BASE)")
    p.add_argument("--backoff-max", type=float, default=BACKOFF_MAX, help="Backoff max seconds (overrides ROO_TESTER_BACKOFF_MAX)")
    p.add_argument("--interval", type=int, default=0, help="If >0, run in watch mode and repeat probes every INTERVAL seconds")
    p.add_argument("--working-file", default=WORKING_KEYS_JSON, help="Path to write list of working keys (JSON)")
    p.add_argument("--verbose", action="store_true", help="Enable debug logging to stderr")
    return p


def main(argv: List[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    # Apply CLI-configured retry/backoff settings
    global MAX_RETRIES, BACKOFF_BASE, BACKOFF_MAX
    MAX_RETRIES = int(args.max_retries)
    BACKOFF_BASE = float(args.backoff_base)
    BACKOFF_MAX = float(args.backoff_max)

    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")

    try:
        keys = load_keys_from_file(args.keys_file)
    except Exception as e:
        print(json.dumps({"error": "failed-to-load-keys", "message": str(e)}))
        return 2

    if not keys:
        print(json.dumps({"error": "no-keys", "message": "No keys found in keys file"}))
        return 3

    # Normalize keys (strip)
    keys = [k.strip() for k in keys if k and isinstance(k, str)]
    # Load stalled keys and filter expired
    stalled = load_stalled_keys()
    now = time.time()
    # purge expired
    stalled = {k: v for k, v in stalled.items() if v > now}
    # keys available for testing
    available_keys = [k for k in keys if k not in stalled]

    if not available_keys:
        # nothing to test (all are stalled) -> return existing stalled info
        print(json.dumps({"error": "all-keys-stalled", "stalled_until": stalled}))
        return 6

    # helper to run a probe cycle (so watch mode can loop)
    def run_cycle() -> Dict[str, Any]:
        try:
            results = asyncio.run(run_probe(available_keys, args.test_url, args.concurrency, args.timeout))
        except Exception as e:
            logger.error("Probe failed: %s", str(e))
            return {"error": "probe-failed", "message": str(e)}

        # Detect quota/daily-hit and mark them stalled for 24 hours
        stall_seconds = 24 * 3600
        to_stall = {}
        now = time.time()
        for r in results:
            if r.get("quota_daily"):
                to_stall[r.get("key")] = now + stall_seconds
            else:
                err = str(r.get("error", "")).lower() if r.get("error") else ""
                if any(tok.lower() in err for tok in DAILY_QUOTA_TOKENS):
                    to_stall[r.get("key")] = now + stall_seconds

        merged = load_stalled_keys()
        for k, ts in to_stall.items():
            merged[k] = max(merged.get(k, 0), ts)
        merged = {k: v for k, v in merged.items() if v > now}
        save_stalled_keys(merged)

        summary = pick_best(results)
        output = {"summary": summary, "results": results, "stalled": merged}

        # Persist best key and working keys list
        best_key = summary.get("best_key")
        working = [
            {"key": r.get("key"), "latency": r.get("latency")} for r in results if r.get("ok")
        ]
        try:
            with open(args.working_file, "w", encoding="utf-8") as wf:
                json.dump({"working": working, "ts": int(now)}, wf)
        except Exception:
            logger.warning("Failed to write working keys to %s", args.working_file)

        if best_key:
            try:
                with open(BEST_KEY_JSON, "w", encoding="utf-8") as bf:
                    json.dump({"best_key": best_key, "best_latency": summary.get("best_latency")}, bf)
                env_lines = []
                if os.path.exists(BEST_KEY_ENV):
                    with open(BEST_KEY_ENV, "r", encoding="utf-8") as ef:
                        env_lines = [ln.rstrip("\n") for ln in ef.readlines() if ln.strip()]
                env_lines = [ln for ln in env_lines if not ln.startswith("OPENROUTER_API_KEY=") and not ln.startswith("ROO_CODE_API_KEY=")]
                env_lines.append(f"OPENROUTER_API_KEY={best_key}")
                env_lines.append(f"ROO_CODE_API_KEY={best_key}")
                with open(BEST_KEY_ENV, "w", encoding="utf-8") as ef:
                    ef.write("\n".join(env_lines) + "\n")
            # Also write into workspace .vscode/settings.json so VS Code extensions
            # that read a workspace setting for the API key will pick it up
            try:
                # workspace root is two levels up from this script (scripts/roo_proxy)
                ws_root = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
                ws_vscode_dir = os.path.join(ws_root, ".vscode")
                ws_settings_path = os.path.join(ws_vscode_dir, "settings.json")
                os.makedirs(ws_vscode_dir, exist_ok=True)

                workspace_settings = {}
                if os.path.exists(ws_settings_path):
                    try:
                        with open(ws_settings_path, "r", encoding="utf-8") as sf:
                            raw = sf.read()
                            # allow simple JSONC by stripping full-line // comments
                            cleaned = "\n".join([ln for ln in raw.splitlines() if not ln.strip().startswith("//")])
                            if cleaned.strip():
                                workspace_settings = json.loads(cleaned)
                    except Exception:
                        # if parsing fails, preserve nothing and overwrite minimally
                        workspace_settings = {}

                # Write direct API-key settings used by common extensions as a convenience.
                # This stores the key in workspace settings.json (workspace-local). Add
                # the key under both Continue/OpenRouter and rooCode setting names to
                # maximize compatibility with different extension naming conventions.
                workspace_settings["continue.openrouter.apiKey"] = best_key
                workspace_settings["rooCode.apiKey"] = best_key

                with open(ws_settings_path, "w", encoding="utf-8") as sf:
                    json.dump(workspace_settings, sf, indent=2)
            except Exception:
                # Any failure persisting files/settings is non-fatal but reported
                output.setdefault("meta", {})["persist_error"] = True

        return output

    # If interval is set, run watch loop
    if args.interval and args.interval > 0:
        logger.info("Starting watch mode: probing every %s seconds", args.interval)
        try:
            while True:
                out = run_cycle()
                logger.info("Cycle complete: best_key=%s working=%d stalled=%d", out.get("summary", {}).get("best_key"), len(out.get("results", [])) if out.get("results") else 0, len(out.get("stalled", {})))
                time.sleep(args.interval)
        except KeyboardInterrupt:
            logger.info("Watch mode stopped by user")
            return 0
    else:
        out = run_cycle()
        if "error" in out:
            print(json.dumps(out))
            return 4
        if args.best_only:
            if out.get("summary", {}).get("best_key"):
                print(out.get("summary")["best_key"])
                return 0
            else:
                print("")
                return 5
        print(json.dumps(out, indent=2))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
