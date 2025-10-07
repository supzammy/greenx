"""Lightweight mock API for smoke testing.

This uses the standard library's http.server so it can run without uvicorn.
It's intentionally small and returns deterministic JSON suitable for the demo.
"""
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import math
from datetime import datetime, timedelta


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, obj, code=200):
        data = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/parking":
            qs = parse_qs(parsed.query)
            hours = int(qs.get("hours", [6])[0])
            now = datetime.now()
            hours_list = []
            for i in range(hours):
                t = now + timedelta(hours=i)
                # simple sinusoidal occupancy (0-1)
                occ = 0.4 + 0.4 * math.sin(2 * math.pi * (t.hour / 24.0))
                hours_list.append({"hour": t.strftime("%Y-%m-%dT%H:00:00"), "predicted_occupancy": round(float(occ), 3), "uncertainty_std": 0.05})
            self._send_json({"hours": hours_list})
            return
        if parsed.path == "/route":
            qs = parse_qs(parsed.query)
            start = qs.get("start", [None])[0]
            end = qs.get("end", [None])[0]
            if start == "Main Gate" and end == "Library":
                self._send_json({"route": "fast", "distance_km": 0.5, "time_min": 6})
                return
            # not found
            self._send_json({"detail": "Route not found"}, code=404)
            return
        # default
        self._send_json({"detail": "Not found"}, code=404)


def run(port: int = 8000):
    server = HTTPServer(("127.0.0.1", port), Handler)
    print(f"Mock API serving on http://127.0.0.1:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()


if __name__ == "__main__":
    run()
