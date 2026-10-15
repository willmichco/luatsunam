/**
 * Worker đăng nhập GitHub cho trang quản trị /admin (Sveltia CMS).
 *
 * Luồng: /admin mở cửa sổ <worker>/auth → GitHub hỏi đồng ý → GitHub gọi <worker>/callback
 * → Worker đổi mã lấy access token → gửi token về đúng cửa sổ /admin (postMessage) → đóng.
 * Client Secret chỉ nằm trong biến bí mật của Worker, trình duyệt không bao giờ thấy.
 *
 * Biến môi trường (Cloudflare → Workers → Settings → Variables):
 *   GITHUB_CLIENT_ID      (Plaintext) Client ID của GitHub OAuth App
 *   GITHUB_CLIENT_SECRET  (Secret)    Client Secret của GitHub OAuth App
 *   ALLOWED_DOMAINS       (Plaintext) Tên miền được dùng /admin, cách nhau dấu phẩy; hỗ trợ *.
 *                         Ví dụ: willmichco.github.io, luatsunam.pages.dev, *.luatsunam.pages.dev
 */

const GITHUB = 'https://github.com';

const escapeHtml = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);

/** Tên miền có nằm trong danh sách cho phép không. "*.abc.dev" khớp đúng một cấp: x.abc.dev. */
const MATCH = (host, p) => p === host || (p.startsWith('*.') && host.endsWith(p.slice(1)) && host.split('.').length === p.split('.').length);
export const domainAllowed = (host, allowed) => {
  if (!host) return false;
  const list = String(allowed || '').split(',').map((s) => s.trim().toLowerCase()).filter(Boolean);
  return list.some((p) => MATCH(host.toLowerCase(), p));
};

/** Trang nhỏ gửi kết quả về cửa sổ /admin rồi tự đóng (giao thức của Decap/Sveltia CMS). */
const outputHTML = ({ provider = 'github', token, error, errorCode, allowed }) => {
  const state = error ? 'error' : 'success';
  const content = error ? { provider, error, errorCode } : { provider, token };
  const msg = `authorization:${provider}:${state}:${JSON.stringify(content)}`;
  return new Response(
    `<!doctype html><html lang="vi"><head><meta charset="utf-8"><title>Đăng nhập</title></head><body>
<p>${error ? escapeHtml(error) : 'Đăng nhập thành công, đang quay lại trang quản trị…'}</p>
<script>
(() => {
  const allowed = ${JSON.stringify(String(allowed || ''))}.split(',').map((s) => s.trim().toLowerCase()).filter(Boolean);
  const match = ${MATCH.toString()};
  const ok = (host) => allowed.some((p) => match(host.toLowerCase(), p));
  window.addEventListener('message', ({ data, origin }) => {
    if (data === 'authorizing:${provider}' && ok(new URL(origin).hostname)) {
      window.opener?.postMessage(${JSON.stringify(msg)}, origin);
    }
  });
  window.opener?.postMessage('authorizing:${provider}', '*');
})();
</script></body></html>`,
    {
      headers: {
        'Content-Type': 'text/html;charset=UTF-8',
        // Xóa cookie chống giả mạo sau khi dùng xong
        'Set-Cookie': 'csrf-token=deleted; HttpOnly; Max-Age=0; Path=/; SameSite=Lax; Secure',
        'Cache-Control': 'no-store',
      },
    },
  );
};

const handleAuth = async (request, env) => {
  const { searchParams } = new URL(request.url);
  const provider = searchParams.get('provider');
  const siteId = searchParams.get('site_id');
  const scope = searchParams.get('scope') || 'repo';
  if (provider !== 'github') {
    return outputHTML({ provider: provider || 'github', error: 'Chỉ hỗ trợ đăng nhập GitHub.', errorCode: 'UNSUPPORTED_BACKEND', allowed: env.ALLOWED_DOMAINS });
  }
  if (!domainAllowed(siteId, env.ALLOWED_DOMAINS)) {
    return outputHTML({ error: `Tên miền “${siteId}” chưa được phép dùng trang quản trị.`, errorCode: 'UNSUPPORTED_DOMAIN', allowed: env.ALLOWED_DOMAINS });
  }
  if (!env.GITHUB_CLIENT_ID || !env.GITHUB_CLIENT_SECRET) {
    return outputHTML({ error: 'Worker chưa được cấu hình Client ID/Secret.', errorCode: 'MISCONFIGURED_CLIENT', allowed: env.ALLOWED_DOMAINS });
  }
  const state = crypto.randomUUID().replaceAll('-', '');
  const params = new URLSearchParams({ client_id: env.GITHUB_CLIENT_ID, scope, state });
  return new Response('', {
    status: 302,
    headers: {
      Location: `${GITHUB}/login/oauth/authorize?${params}`,
      'Set-Cookie': `csrf-token=github_${state}; HttpOnly; Path=/; Max-Age=600; SameSite=Lax; Secure`,
      'Cache-Control': 'no-store',
    },
  });
};

const handleCallback = async (request, env) => {
  const { searchParams } = new URL(request.url);
  const code = searchParams.get('code');
  const state = searchParams.get('state');
  const cookie = request.headers.get('Cookie') || '';
  const saved = cookie.match(/\bcsrf-token=github_([0-9a-f]{32})\b/)?.[1];
  if (!code || !state) {
    return outputHTML({ error: 'Thiếu mã ủy quyền từ GitHub.', errorCode: 'AUTH_CODE_REQUEST_FAILED', allowed: env.ALLOWED_DOMAINS });
  }
  if (!saved || saved !== state) {
    return outputHTML({ error: 'Phát hiện yêu cầu không hợp lệ (CSRF). Vui lòng đăng nhập lại.', errorCode: 'CSRF_DETECTED', allowed: env.ALLOWED_DOMAINS });
  }
  let token;
  let error;
  try {
    const res = await fetch(`${GITHUB}/login/oauth/access_token`, {
      method: 'POST',
      headers: { Accept: 'application/json', 'Content-Type': 'application/json' },
      body: JSON.stringify({ client_id: env.GITHUB_CLIENT_ID, client_secret: env.GITHUB_CLIENT_SECRET, code }),
    });
    ({ access_token: token, error } = await res.json());
  } catch {
    return outputHTML({ error: 'Không nhận được phản hồi từ GitHub. Thử lại sau.', errorCode: 'TOKEN_REQUEST_FAILED', allowed: env.ALLOWED_DOMAINS });
  }
  if (!token) {
    return outputHTML({ error: `GitHub từ chối cấp quyền: ${error || 'không rõ lý do'}.`, errorCode: 'TOKEN_REQUEST_FAILED', allowed: env.ALLOWED_DOMAINS });
  }
  return outputHTML({ token, allowed: env.ALLOWED_DOMAINS });
};

export default {
  async fetch(request, env) {
    const { pathname } = new URL(request.url);
    if (request.method === 'GET' && ['/auth', '/oauth/authorize'].includes(pathname)) return handleAuth(request, env);
    if (request.method === 'GET' && ['/callback', '/oauth/redirect'].includes(pathname)) return handleCallback(request, env);
    return new Response('Worker đăng nhập CMS – Luật Sư Nam', { status: 200, headers: { 'Content-Type': 'text/plain;charset=UTF-8' } });
  },
};
