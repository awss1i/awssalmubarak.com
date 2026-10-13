#!/usr/bin/env python3
"""Serve the repo root for the builds benchmark, and count every byte it sends.

  python3 bench/serve.py [PORT]     # default 8000

Three things differ from `python3 -m http.server`, each of which would skew the numbers:

  - Every response carries Cache-Control: no-store, so a reload downloads everything again
    instead of reusing files the browser cached on the last run.
  - Range requests get 206 Partial Content, the way GitHub Pages answers them. Browsers fetch
    video in ranges, and some won't play video from a server that ignores them.
  - The server counts the bytes of every file body it sends. GET /__bench/bytes returns
    {"bytes", "requests"} as JSON, and the count starts again whenever a benchmark page itself
    (bench/dist/builds-*.html) is requested, so it covers exactly one page load. The browser's
    own Resource Timing can't do this, because it leaves out what a live preview downloads
    inside its frame and video that was cut short.
"""
import http.server
import json
import os
import re
import sys
import threading

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_lock = threading.Lock()
_count = {"bytes": 0, "requests": 0}


def _add(n):
    with _lock:
        _count["bytes"] += n
        _count["requests"] += 1


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def log_message(self, *args):
        pass

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/__bench/bytes":
            with _lock:
                body = json.dumps(_count).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if re.fullmatch(r"/bench/dist/builds-[a-z]+\.html", path):
            with _lock:
                _count["bytes"] = _count["requests"] = 0
        rng = self.headers.get("Range")
        if rng:
            return self._range(rng)
        super().do_GET()

    def copyfile(self, source, outputfile):
        sent = 0
        while True:
            chunk = source.read(64 * 1024)
            if not chunk:
                break
            try:
                outputfile.write(chunk)
            except (BrokenPipeError, ConnectionResetError):
                break
            sent += len(chunk)
        _add(sent)

    def _range(self, header):
        path = self.translate_path(self.path)
        m = re.fullmatch(r"bytes=(\d*)-(\d*)", header.strip())
        if not m or not os.path.isfile(path):
            return super().do_GET()
        size = os.path.getsize(path)
        start = int(m.group(1)) if m.group(1) else max(0, size - int(m.group(2) or 0))
        end = int(m.group(2)) if m.group(1) and m.group(2) else size - 1
        end = min(end, size - 1)
        if start > end:
            self.send_response(416)
            self.send_header("Content-Range", "bytes */%d" % size)
            self.end_headers()
            return
        self.send_response(206)
        self.send_header("Content-Type", self.guess_type(path))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Range", "bytes %d-%d/%d" % (start, end, size))
        self.send_header("Content-Length", str(end - start + 1))
        self.end_headers()
        sent, left = 0, end - start + 1
        with open(path, "rb") as f:
            f.seek(start)
            while left > 0:
                chunk = f.read(min(64 * 1024, left))
                if not chunk:
                    break
                try:
                    self.wfile.write(chunk)
                except (BrokenPipeError, ConnectionResetError):
                    break
                sent += len(chunk)
                left -= len(chunk)
        _add(sent)


def main(argv):
    port = int(argv[1]) if len(argv) > 1 else 8000
    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print("serving %s on http://127.0.0.1:%d, bytes counted at /__bench/bytes" % (ROOT, port))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main(sys.argv)
