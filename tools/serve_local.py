#!/usr/bin/env python3
"""
serve_local.py - serve this repository on http://localhost so VEB.js can load
the scene straight from your Mac (no push, no GitHub Pages cache).

Usage (from the repo folder 02_model):
    python3 tools/serve_local.py            # port 8080
    python3 tools/serve_local.py 8090       # another port

Then open the URL printed below in Chrome. After every Export from Excel,
just reload the VEB.js page (Cmd+R): files are served with caching disabled.
Stop the server with Ctrl+C.

Headers sent:
- Access-Control-Allow-Origin: *        -> VEB.js (another site) may read the files
- Access-Control-Allow-Private-Network  -> Chrome's rule for public sites calling localhost
- Cache-Control: no-store               -> always the latest export
"""
import http.server, os, sys

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # repo root


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Private-Network", "true")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Cache-Control", "no-store, max-age=0")
        super().end_headers()

    def do_OPTIONS(self):            # CORS / private-network preflight
        self.send_response(204)
        self.end_headers()

    def log_message(self, fmt, *args):   # one short line per file request
        sys.stderr.write("  " + (fmt % args) + "\n")


if __name__ == "__main__":
    base = f"http://localhost:{PORT}"
    veb = "https://digital-factory.io/vebjs/?inputscene={0}/{1}&repoMod3d={0}/assets/"
    print(f"Serving {ROOT} on {base}  (Ctrl+C to stop)\n")
    print("Open in Chrome:")
    print("  Original scene : " + veb.format(base, "DFE_01"))
    print("  Cell v1 scene  : " + veb.format(base, "DFE_01_v1"))
    print("\nAfter each Excel export: reload the page (Cmd+R).\n")
    http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
