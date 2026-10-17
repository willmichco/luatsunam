import assert from 'node:assert/strict';
const { default: worker, domainAllowed } = await import(new URL('./worker.js', import.meta.url));
const env = { GITHUB_CLIENT_ID: 'cid', GITHUB_CLIENT_SECRET: 'sec', ALLOWED_DOMAINS: 'willmichco.github.io, *.luatsunam.pages.dev, luatsunam.pages.dev' };
assert.equal(domainAllowed('willmichco.github.io', env.ALLOWED_DOMAINS), true);
assert.equal(domainAllowed('abc123.luatsunam.pages.dev', env.ALLOWED_DOMAINS), true);
assert.equal(domainAllowed('evil.com', env.ALLOWED_DOMAINS), false);
assert.equal(domainAllowed('a.b.luatsunam.pages.dev', env.ALLOWED_DOMAINS), false);
assert.equal(domainAllowed('xluatsunam.pages.dev', env.ALLOWED_DOMAINS), false);
// 1. tên miền lạ
let r = await worker.fetch(new Request('https://w.dev/auth?provider=github&site_id=evil.com&scope=repo'), env);
assert.match(await r.text(), /UNSUPPORTED_DOMAIN/);
// 2. chuyển hướng tới GitHub + cookie
r = await worker.fetch(new Request('https://w.dev/auth?provider=github&site_id=willmichco.github.io&scope=repo'), env);
assert.equal(r.status, 302);
const loc = new URL(r.headers.get('Location'));
assert.equal(loc.origin + loc.pathname, 'https://github.com/login/oauth/authorize');
const state = loc.searchParams.get('state');
assert.match(r.headers.get('Set-Cookie'), new RegExp(`csrf-token=github_${state}; HttpOnly`));
// 3. sai state
r = await worker.fetch(new Request(`https://w.dev/callback?code=abc&state=${'0'.repeat(32)}`, { headers: { Cookie: `csrf-token=github_${state}` } }), env);
assert.match(await r.text(), /CSRF_DETECTED/);
// 4. thành công (giả lập GitHub trả token)
globalThis.fetch = async (url, init) => { assert.equal(JSON.parse(init.body).client_secret, 'sec'); return new Response(JSON.stringify({ access_token: 'gho_TEST' })); };
r = await worker.fetch(new Request(`https://w.dev/callback?code=abc&state=${state}`, { headers: { Cookie: `csrf-token=github_${state}` } }), env);
const html = await r.text();
assert.ok(!html.includes('sec"'), 'không lộ secret');
// chạy đoạn script trong trang kết quả với cửa sổ giả
const script = html.match(/<script>([\s\S]*?)<\/script>/)[1];
for (const [origin, expectSent] of [['https://willmichco.github.io', true], ['https://evil.com', false]]) {
  const sent = []; let handler;
  const window = { addEventListener: (_, h) => { handler = h; }, opener: { postMessage: (m, o) => sent.push([m, o]) } };
  new Function('window', script)(window);
  assert.deepEqual(sent[0], ['authorizing:github', '*']);
  handler({ data: 'authorizing:github', origin });
  const tokenMsg = sent.find(([m]) => m.startsWith('authorization:github:success:'));
  assert.equal(Boolean(tokenMsg), expectSent, origin);
  if (tokenMsg) { assert.equal(tokenMsg[1], origin); assert.equal(JSON.parse(tokenMsg[0].split('success:')[1]).token, 'gho_TEST'); }
}
console.log('✓ Worker: 4 kịch bản + chặn gửi token sang tên miền lạ – đạt');
