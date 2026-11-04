"""Serveur de développement SANS Docker (dépannage / machines sans Docker Desktop).

Sert le frontend sur http://127.0.0.1:8501 et relaie /api/* vers l'API Flask lancée
séparément sur http://127.0.0.1:5000 (python3 api/app.py). Reproduit le rôle de Nginx.
"""
import http.server
import os
import urllib.error
import urllib.request

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")
API = os.environ.get("API_URL", "http://127.0.0.1:5000")


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=ROOT, **k)

    def _proxy(self):
        url = API + self.path[len("/api"):]
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else None
        req = urllib.request.Request(url, data=body, method=self.command,
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                data, status, ctype = r.read(), r.status, r.headers.get("Content-Type", "application/json")
        except urllib.error.HTTPError as e:
            data, status, ctype = e.read(), e.code, "application/json"
        except Exception as e:  # API éteinte
            data, status, ctype = ('{"error": "API injoignable : %s"}' % e).encode(), 502, "application/json"
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path.startswith("/api/"):
            return self._proxy()
        return super().do_GET()

    def do_POST(self):
        if self.path.startswith("/api/"):
            return self._proxy()
        self.send_error(405)

    def log_message(self, fmt, *args):
        print("[dev-server]", fmt % args)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8501))
    print(f"Frontend : http://127.0.0.1:{port}  (proxy /api → {API})")
    http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
