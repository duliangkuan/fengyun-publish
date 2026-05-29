/**
 * mp-proxy-worker
 *
 * 微信公众号文章反向代理 Worker,配合 wechat-article-exporter 的 privateProxyList 使用。
 *
 * 协议 (来自 BaseDownloader.ts:159):
 *   GET /?url=<urlencoded 微信文章URL>&headers=<urlencoded JSON>&authorization=<可选>
 *
 * 行为:
 *   1. 取出 ?url= 参数(微信公众号文章 URL)
 *   2. (可选) 解析 ?headers= JSON,作为额外请求头
 *   3. (可选) 检查 ?authorization= 是否匹配 SHARED_SECRET (如配置)
 *   4. fetch 微信 URL,返回响应
 */

const ALLOWED_HOSTS = new Set([
  'mp.weixin.qq.com',
  'res.wx.qq.com',
  'mmbiz.qpic.cn',
]);

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    // 健康检查
    if (url.pathname === '/health') {
      return new Response('ok', { headers: corsHeaders() });
    }

    // CORS 预检
    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders() });
    }

    const targetUrl = url.searchParams.get('url');
    if (!targetUrl) {
      return new Response('missing ?url=', { status: 400, headers: corsHeaders() });
    }

    // 可选鉴权 - 防止 Worker 被陌生人滥用
    if (env.SHARED_SECRET) {
      const auth = url.searchParams.get('authorization') || '';
      if (auth !== env.SHARED_SECRET) {
        return new Response('forbidden', { status: 403, headers: corsHeaders() });
      }
    }

    // 校验目标域名白名单
    let parsedTarget;
    try {
      parsedTarget = new URL(targetUrl);
    } catch (_) {
      return new Response('invalid ?url=', { status: 400, headers: corsHeaders() });
    }
    if (!ALLOWED_HOSTS.has(parsedTarget.hostname)) {
      return new Response(`host not allowed: ${parsedTarget.hostname}`, { status: 403, headers: corsHeaders() });
    }

    // 解析额外请求头(用于带 cookie 抓阅读量等元数据)
    const extraHeadersRaw = url.searchParams.get('headers');
    let extraHeaders = {};
    if (extraHeadersRaw) {
      try {
        extraHeaders = JSON.parse(extraHeadersRaw);
      } catch (_) {
        // 忽略,用空 headers
      }
    }

    const upstreamHeaders = {
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
      Accept: 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
      'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
      Referer: 'https://mp.weixin.qq.com/',
      ...extraHeaders,
    };

    try {
      const upstream = await fetch(targetUrl, {
        method: 'GET',
        headers: upstreamHeaders,
        redirect: 'follow',
      });

      const respHeaders = new Headers(upstream.headers);
      Object.entries(corsHeaders()).forEach(([k, v]) => respHeaders.set(k, v));

      return new Response(upstream.body, {
        status: upstream.status,
        statusText: upstream.statusText,
        headers: respHeaders,
      });
    } catch (err) {
      return new Response(`upstream fetch failed: ${err.message}`, { status: 502, headers: corsHeaders() });
    }
  },
};

function corsHeaders() {
  return {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, OPTIONS',
    'Access-Control-Allow-Headers': '*',
  };
}
