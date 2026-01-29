import http from 'node:http';
import { createReadStream } from 'node:fs';
import { access, stat } from 'node:fs/promises';
import { extname, join, normalize } from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = normalize(join(__filename, '..'));

const ROOT = process.cwd();
const PORT = Number(process.env.PORT || 3000);

const CONTENT_TYPES = new Map([
  ['.html', 'text/html; charset=utf-8'],
  ['.js', 'text/javascript; charset=utf-8'],
  ['.mjs', 'text/javascript; charset=utf-8'],
  ['.css', 'text/css; charset=utf-8'],
  ['.json', 'application/json; charset=utf-8'],
  ['.wasm', 'application/wasm'],
  ['.map', 'application/json; charset=utf-8'],
  ['.svg', 'image/svg+xml'],
  ['.png', 'image/png'],
  ['.jpg', 'image/jpeg'],
  ['.jpeg', 'image/jpeg'],
  ['.gif', 'image/gif'],
]);

function safeJoin(root, target) {
  const normalized = normalize(target).replace(/^(\.\.(\/|\\|$))+/, '');
  return join(root, normalized);
}

function resolvePath(urlPath) {
  if (urlPath === '/' || urlPath === '') {
    return join(ROOT, 'tests', 'browser', 'test.html');
  }
  return safeJoin(ROOT, urlPath);
}

const server = http.createServer(async (req, res) => {
  try {
    const url = new URL(req.url, `http://${req.headers.host}`);
    const filePath = resolvePath(url.pathname);

    await access(filePath);

    const stats = await stat(filePath);
    if (stats.isDirectory()) {
      res.writeHead(302, { Location: `${url.pathname}/test.html` });
      res.end();
      return;
    }

    const ext = extname(filePath);
    const contentType = CONTENT_TYPES.get(ext) || 'application/octet-stream';
    res.writeHead(200, {
      'Content-Type': contentType,
      'Cache-Control': 'no-cache',
    });

    const stream = createReadStream(filePath);
    stream.pipe(res);
  } catch (err) {
    res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
    res.end('Not Found');
  }
});

server.listen(PORT, () => {
  // eslint-disable-next-line no-console
  console.log(`Test server running at http://localhost:${PORT}`);
});
