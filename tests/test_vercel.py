import io
import json
import pytest
from api.index import handler

class MockVercelHandler(handler):
    def __init__(self, method, path, body=b"", headers=None):
        self.rfile = io.BytesIO(body)
        self.wfile = io.BytesIO()
        self.command = method
        self.path = path
        self.headers = headers or {}
        self.request_version = "HTTP/1.1"
        self.close_connection = False
        self.requestline = f"{method} {path} HTTP/1.1"

    def setup(self):
        pass

    def finish(self):
        pass

    def handle(self):
        pass

def test_vercel_index_route():
    h = MockVercelHandler("GET", "/")
    h.do_GET()
    out = h.wfile.getvalue().decode("utf-8")
    assert "200" in out
    assert "Multi-Agent PRD-to-Architecture Studio" in out

def test_vercel_generate_route():
    payload = json.dumps({
        "prd": "Build an Uber clone with riders, drivers, trips, payments at 25k rps and 99.99% uptime"
    }).encode("utf-8")

    h = MockVercelHandler("POST", "/api/generate", body=payload, headers={"Content-Length": str(len(payload))})
    h.do_POST()
    out = h.wfile.getvalue().decode("utf-8")
    assert "application/json" in out

    body = out.split("\r\n\r\n", 1)[1] if "\r\n\r\n" in out else out
    data = json.loads(body)

    assert data["success"] is True
    assert "capacity" in data
    assert "agent_logs" in data
    assert "mermaid" in data
    assert "sql" in data
