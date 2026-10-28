import sys
import json
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from pathlib import Path
import threading
import webbrowser
from typing import Dict, Any

from src.orchestrator.pipeline import ArchitecturePipeline

class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

class ArchitectureGUIHandler(BaseHTTPRequestHandler):
    pipeline = ArchitecturePipeline()
    template_path = Path(__file__).resolve().parent / "templates" / "index.html"
    inputs_dir = Path(__file__).resolve().parent.parent.parent / "inputs"
    outputs_dir = Path(__file__).resolve().parent.parent.parent / "outputs"

    def _send_json(self, status: int, data: Dict[str, Any]):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def _send_text(self, status: int, text: str, content_type: str = "text/plain; charset=utf-8"):
        body = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path == "/" or path == "/index.html":
            if self.template_path.exists():
                content = self.template_path.read_text(encoding="utf-8")
                self._send_text(200, content, "text/html; charset=utf-8")
            else:
                self._send_text(404, "UI template not found.")
            return

        elif path == "/api/samples":
            samples = []
            if self.inputs_dir.exists():
                for f in sorted(self.inputs_dir.glob("*.md")):
                    title = f.stem.replace("_", " ").title()
                    # Peek at first line for title
                    try:
                        first_line = f.read_text(encoding="utf-8").splitlines()[0]
                        if first_line.startswith("# "):
                            title = first_line.replace("# ", "").strip()
                    except Exception:
                        pass

                    samples.append({
                        "id": f.name,
                        "title": title,
                        "filename": f.name
                    })
            self._send_json(200, {"samples": samples})
            return

        elif path == "/api/sample":
            sample_id = query.get("id", [""])[0]
            if not sample_id:
                self._send_json(400, {"error": "Missing 'id' parameter"})
                return

            file_path = self.inputs_dir / sample_id
            if file_path.exists() and file_path.is_file():
                content = file_path.read_text(encoding="utf-8")
                self._send_json(200, {"id": sample_id, "content": content})
            else:
                self._send_json(404, {"error": f"Sample '{sample_id}' not found."})
            return

        elif path.startswith("/api/artifact/"):
            # Download or inspect raw generated artifacts
            artifact_rel = path.replace("/api/artifact/", "")
            target_file = (self.outputs_dir / artifact_rel).resolve()
            # Ensure within outputs directory
            if str(target_file).startswith(str(self.outputs_dir.resolve())) and target_file.exists():
                content = target_file.read_text(encoding="utf-8")
                self._send_text(200, content, "text/plain; charset=utf-8")
            else:
                self._send_json(404, {"error": "Artifact file not found."})
            return

        self._send_json(404, {"error": "Endpoint not found"})

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/generate":
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                raw_body = self.rfile.read(content_length).decode("utf-8")
                payload = json.loads(raw_body) if raw_body else {}
                prd_text = payload.get("prd", "")

                if not prd_text.strip():
                    self._send_json(400, {"error": "Empty PRD content provided."})
                    return

                # Run multi-agent pipeline
                results = self.pipeline.run_with_state(prd_text)

                response_data = {
                    "success": True,
                    "prd": results["prd"].model_dump(),
                    "arch": results["arch"].model_dump(),
                    "capacity": results.get("capacity", {}),
                    "agent_logs": results.get("agent_logs", []),
                    "mermaid": results["mermaid"],
                    "er_diagram": results["er_diagram"],
                    "sql": results["sql"],
                    "docker_compose": results["docker_compose"],
                    "spec": results["spec"]
                }

                self._send_json(200, response_data)
            except Exception as e:
                self._send_json(500, {"error": f"Pipeline generation error: {str(e)}"})
            return

        self._send_json(404, {"error": "Endpoint not found"})

    def log_message(self, format, *args):
        # Clean logging format
        sys.stderr.write(f"[GUI Server] {args[0]} {args[1]} -> {args[2]}\n")

def start_gui_server(host: str = "127.0.0.1", port: int = 8080, open_browser: bool = True):
    server = ThreadingHTTPServer((host, port), ArchitectureGUIHandler)
    url = f"http://{host}:{port}"
    print(f"\n" + "=" * 70)
    print(f"🚀 MULTI-AGENT PRD-TO-ARCHITECTURE STUDIO (GUI)")
    print(f"=" * 70)
    print(f"Server running at : {url}")
    print(f"Local host binding: {host}:{port}")
    print(f"Press CTRL+C in this terminal to stop the server.")
    print(f"=" * 70 + "\n")

    if open_browser:
        def _open():
            import time
            time.sleep(0.6)
            webbrowser.open(url)
        threading.Thread(target=_open, daemon=True).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[!] Shutting down GUI server gracefully...")
        server.server_close()

if __name__ == "__main__":
    start_gui_server()
