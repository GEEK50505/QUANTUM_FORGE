import express from 'express';
import fs from 'fs';
import path from 'path';
import morgan from 'morgan';
import { fileURLToPath } from 'url';

const app = express();
app.use(express.json({ limit: '1mb' }));
app.use(morgan('tiny'));

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const KEYS_FILE = path.join(__dirname, 'keys.json');

function loadKeys() {
  try {
    const raw = fs.readFileSync(KEYS_FILE, 'utf8');
    const arr = JSON.parse(raw);
    return arr;
  } catch (e) {
    return [];
  }
}

function saveKeys(arr) {
  fs.writeFileSync(KEYS_FILE, JSON.stringify(arr, null, 2), 'utf8');
}

let keys = loadKeys();
// keys: [{ key: 'sk-...', disabledUntil: null }]
let currentIndex = 0;

function pickAvailableKey() {
  const now = Date.now();
  const start = currentIndex;
  for (let i = 0; i < keys.length; i++) {
    const idx = (start + i) % keys.length;
    const entry = keys[idx];
    if (!entry.disabledUntil || now > entry.disabledUntil) {
      currentIndex = (idx + 1) % Math.max(keys.length, 1);
      return { entry, idx };
    }
  }
  return null;
}

async function forward(req, res) {
  const providerBase = 'https://api.openrouter.ai';
  // forward path and query
  const targetUrl = providerBase + req.originalUrl;

  // reload keys on each request to pick up manual updates
  keys = loadKeys();
  const pick = pickAvailableKey();
  if (!pick) {
    // No available keys: tell clients to retry later with Retry-After header
    res.setHeader('Retry-After', '60');
    res.status(503).json({ error: 'No available API keys (all are throttled or none configured)', retry_after_seconds: 60 });
    return;
  }

  const apiKey = pick.entry.key;
  try {
    const fetchResp = await fetch(targetUrl, {
      method: req.method,
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json'
      },
      body: req.method === 'GET' || req.method === 'HEAD' ? undefined : JSON.stringify(req.body),
      // note: keep default redirect and similar
    });

    const text = await fetchResp.text();
    // if rate-limited, mark key as disabled for a short backoff window
    if (fetchResp.status === 429) {
      // mark disabled for 60 seconds by default
      const backoffMs = 60 * 1000;
      keys[pick.idx].disabledUntil = Date.now() + backoffMs;
      saveKeys(keys);
      // try another key recursively (but avoid infinite loops)
      const otherPick = pickAvailableKey();
      if (otherPick) {
        // call forward again with a different key
        return forward(req, res);
      }
      // No keys available after marking this one — respond with 503 and Retry-After
      res.setHeader('Retry-After', '60');
      res.status(503).json({ error: 'Rate limited and no other keys available', retry_after_seconds: 60 });
      return;
    }

    // pipe status and headers back
    res.status(fetchResp.status);
    // try to parse json
    const ct = fetchResp.headers.get('content-type') || '';
    if (ct.includes('application/json')) {
      try { res.json(JSON.parse(text)); } catch (e) { res.send(text); }
    } else {
      res.send(text);
    }
  } catch (err) {
    // Distinguish DNS/network errors vs key-level errors.
    console.warn('Request forwarding error:', err && err.message ? err.message : err);
    const msg = (err && err.message) ? err.message : String(err);
    // If the error looks like a DNS / network resolution problem, do NOT mark the key as throttled;
    // instead return a clear 502 explaining upstream network/DNS issues so operator can troubleshoot.
    if (msg.includes('ENOTFOUND') || msg.includes('getaddrinfo') || msg.includes('fetch failed') || msg.includes('network')) {
      console.warn('Upstream network/DNS error detected; not disabling key.');
      res.status(502).json({ error: 'Upstream network/DNS error', details: msg });
      return;
    }

    // mark key as possibly bad and try next
    keys[pick.idx].disabledUntil = Date.now() + 30 * 1000;
    saveKeys(keys);
    const otherPick = pickAvailableKey();
    if (otherPick) { return forward(req, res); }
    res.setHeader('Retry-After', '30');
    res.status(503).json({ error: 'Provider proxy error and no keys available', details: msg, retry_after_seconds: 30 });
  }
}

// Admin endpoint to inspect key status (masked). Local only.
app.get('/admin/keys', (req, res) => {
  // reload from disk for freshest view
  keys = loadKeys();
  if (!Array.isArray(keys) || keys.length === 0) {
    return res.status(200).json({ error: 'No available API keys (all are throttled or none configured)' });
  }
  const masked = keys.map(k => ({ key: (k.key && k.key.length>8) ? (k.key.substring(0,4)+'...'+k.key.substring(k.key.length-4)) : '****', disabledUntil: k.disabledUntil }));
  res.json({ keys: masked });
});

// Proxy any path to the provider
app.all('/*', async (req, res) => {
  // don't proxy admin endpoints
  if (req.path && req.path.startsWith('/admin')) { return res.status(404).end(); }
  await forward(req, res);
});

const PORT = process.env.ROO_PROXY_PORT ? Number(process.env.ROO_PROXY_PORT) : 3002;
app.listen(PORT, () => {
  console.log(`Roo proxy listening on http://localhost:${PORT} — forwarding to OpenRouter`);
});
