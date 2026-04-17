import http from 'http';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PORT = 3456;
const MIME = { '.html':'text/html', '.json':'application/json', '.jpg':'image/jpeg', '.png':'image/png', '.js':'application/javascript', '.css':'text/css' };

http.createServer((req, res) => {
  /* Strip query string (cache busters etc.) before resolving the file */
  const cleanUrl = (req.url || '/').split('?')[0];
  const filePath = path.join(__dirname, cleanUrl === '/' ? 'index.html' : cleanUrl);
  fs.stat(filePath, (statErr, stat) => {
    if (statErr) { res.writeHead(404); return res.end('Not found'); }
    fs.readFile(filePath, (err, data) => {
      if (err) { res.writeHead(404); return res.end('Not found'); }
      /* ETag based on file mtime — browser will revalidate, get 304 if unchanged */
      const etag = '"' + stat.mtimeMs.toString(36) + '-' + stat.size.toString(36) + '"';
      if (req.headers['if-none-match'] === etag) {
        res.writeHead(304); return res.end();
      }
      res.writeHead(200, {
        'Content-Type': MIME[path.extname(filePath)] || 'text/plain',
        'Access-Control-Allow-Origin': '*',
        'Cache-Control': 'no-store, no-cache, must-revalidate, max-age=0',
        'Pragma': 'no-cache',
        'Expires': '0',
        'ETag': etag,
        'Last-Modified': stat.mtime.toUTCString(),
      });
      res.end(data);
    });
  });
}).listen(PORT, () => console.log('Serving at http://localhost:' + PORT));
