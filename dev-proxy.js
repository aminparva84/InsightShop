/**
 * Development proxy: listen on port 5000, forward /api to Flask (5001), everything else to React dev server (3000).
 * Use so you can open http://localhost:5000 and get instant frontend updates (HMR) without rebuilding.
 */
const http = require('http');
const httpProxy = require('http-proxy');

const PROXY_PORT = parseInt(process.env.PROXY_PORT || '5000', 10);
const API_TARGET = `http://127.0.0.1:${process.env.FLASK_PORT || '5001'}`;
const WEB_TARGET = `http://127.0.0.1:${process.env.REACT_PORT || '3000'}`;

const apiProxy = httpProxy.createProxyServer({ target: API_TARGET });
const webProxy = httpProxy.createProxyServer({ target: WEB_TARGET, ws: true });

apiProxy.on('error', (err, req, res) => {
  console.error('[proxy] API error:', err.message);
  if (res && !res.headersSent) res.writeHead(502, { 'Content-Type': 'text/plain' }).end('API proxy error');
});
webProxy.on('error', (err, req, res) => {
  console.error('[proxy] Web error:', err.message);
  if (res && !res.headersSent) res.writeHead(502, { 'Content-Type': 'text/plain' }).end('Web proxy error');
});

const server = http.createServer((req, res) => {
  if (req.url && req.url.startsWith('/api/')) {
    apiProxy.web(req, res, { target: API_TARGET });
  } else {
    webProxy.web(req, res, { target: WEB_TARGET });
  }
});

server.on('upgrade', (req, socket, head) => {
  webProxy.ws(req, socket, head, { target: WEB_TARGET });
});

server.listen(PROXY_PORT, '0.0.0.0', () => {
  console.log(`[dev-proxy] http://localhost:${PROXY_PORT} -> API ${API_TARGET} | Web + HMR ${WEB_TARGET}`);
});
