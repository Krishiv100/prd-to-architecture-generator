import io
import json
from unittest.mock import MagicMock
import pytest
from src.gui.server import ArchitectureGUIHandler

class DummyHandler(ArchitectureGUIHandler):
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

def test_gui_index_page():
    handler = DummyHandler("GET", "/")
    handler.do_GET()
    output = handler.wfile.getvalue().decode("utf-8")
    assert "HTTP/1.0 200 OK" in output or "200" in output
    assert "Multi-Agent PRD-to-Architecture Studio" in output

def test_gui_samples_api():
    handler = DummyHandler("GET", "/api/samples")
    handler.do_GET()
    output = handler.wfile.getvalue().decode("utf-8")
    assert "application/json" in output
    # Extract body after headers
    body_part = output.split("\r\n\r\n", 1)[1] if "\r\n\r\n" in output else output
    data = json.loads(body_part)
    assert "samples" in data
    assert len(data["samples"]) >= 4

def test_gui_sample_fetch():
    handler = DummyHandler("GET", "/api/sample?id=sample_fintech_prd.md")
    handler.do_GET()
    output = handler.wfile.getvalue().decode("utf-8")
    assert "application/json" in output
    body_part = output.split("\r\n\r\n", 1)[1] if "\r\n\r\n" in output else output
    data = json.loads(body_part)
    assert "content" in data
    assert "FinTech Checkout" in data["content"]

def test_gui_generate_api():
    body = json.dumps({
        "prd": """# Test Service
## Functional Entities
- Entity: Order
- Entity: Customer -> Order

## Non-Functional Requirements
- Throughput: 10000 req/s
- Latency: 25 ms
- Availability: 99.99%
- Compliance: PCI-DSS
"""
    }).encode("utf-8")

    handler = DummyHandler("POST", "/api/generate", body=body, headers={"Content-Length": str(len(body))})
    handler.do_POST()
    output = handler.wfile.getvalue().decode("utf-8")
    assert "application/json" in output
    body_part = output.split("\r\n\r\n", 1)[1] if "\r\n\r\n" in output else output
    result = json.loads(body_part)

    assert result["success"] is True
    assert result["prd"]["project_name"] == "Test Service"
    assert result["arch"]["topology"] == "Event-Driven Microservices"
    assert "mermaid" in result
    assert "sql" in result
    assert "docker_compose" in result
