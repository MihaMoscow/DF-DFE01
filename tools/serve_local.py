#!/usr/bin/env python3
"""Local HTTP server for testing VEB.js scenes without pushing to GitHub Pages.

Serves the `02_model/` folder on http://localhost:8080 with:
  - CORS headers (`Access-Control-Allow-Origin: *`)
  - Chrome Private Network Access header (`Access-Control-Allow-Private-Network: true`)
  - Zero caching (`Cache-Control: no-store, no-cache, must-revalidate, max-age=0`)

Usage:
    cd "$HOME/Documents/21. PoliMI Studies/2. Courses/2026/7_Digital factory/3_Project/02_model"
    python3 tools/serve_local.py
"""

from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import mimetypes
from pathlib import Path
import sys

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
ROOT = Path(__file__).resolve().parent.parent

mimetypes.add_type("model/gltf-binary", ".glb")
mimetypes.add_type("application/json", ".json")


class VEBLocalHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        # If a scene has a full URL in RepoPath alongside repoMod3d=.../assets/,
        # normalize '/assets/https://.../assets/Foo.glb' -> '/assets/Foo.glb'
        if "/assets/http" in path and path.count("/assets/") >= 2:
            path = "/assets/" + path.rsplit("/assets/", 1)[-1]
        return super().translate_path(path)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, HEAD, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Private-Network", "true")
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()


def main():
    handler = partial(VEBLocalHandler, directory=str(ROOT))
    server = ThreadingHTTPServer(("127.0.0.1", PORT), handler)
    base = f"http://localhost:{PORT}"
    veb = "https://digital-factory.io/vebjs/"
    print(f"Serving {ROOT} on {base} (no-cache + CORS + Private-Network enabled)\n")
    print("Open in Chrome:")
    print(f"  Your Excel/main scene: {veb}?inputscene={base}/DFE_01&repoMod3d={base}/assets/")
    print(f"  The v1 cell:           {veb}?inputscene={base}/DFE_01_v1&repoMod3d={base}/assets/")
    print("\nPress Ctrl + C to stop.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        server.server_close()


if __name__ == "__main__":
    main()
