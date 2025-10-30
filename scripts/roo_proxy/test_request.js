async function run() {
  const url = 'http://localhost:3002/v1/chat/completions';
  const body = { model: 'qwen/qwen3-coder:free', input: 'Test ping from local proxy', max_tokens: 32 };
  try {
    const r = await fetch(url, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(body) });
    console.log('STATUS', r.status);
    const text = await r.text();
    console.log('BODY', text.substring(0,1000));
  } catch (e) {
    console.error('ERROR', e && e.message ? e.message : e);
  }
}

run();
