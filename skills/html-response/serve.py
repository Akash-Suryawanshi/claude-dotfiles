#!/usr/bin/env python3
"""
html-response · local server.

Serves response HTML files from `state/responses/` on a fixed port (4747 by
default). Routing:

  GET /            -> latest response file (alias)
  GET /version     -> JSON {latest: "<filename>", mtime: <unix>}
  GET /index       -> auto-generated list of all responses
  GET /r-*.html    -> specific response file
  GET /<other>     -> 404

Idempotent re-entry: if another instance is already bound to the port, exits 0
(the caller can assume the server is up). Otherwise binds, writes PID to
`state/server.pid`, and serves until killed.

Stdlib only — no pip install.
"""
from __future__ import annotations

import json
import os
import socket
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HOST = "127.0.0.1"
PORT = 4747
SKILL_ROOT = Path(__file__).resolve().parent
STATE_DIR = SKILL_ROOT / "state"
RESPONSES_DIR = STATE_DIR / "responses"
PID_FILE = STATE_DIR / "server.pid"
LOG_FILE = STATE_DIR / "server.log"


def latest_response_path() -> Path | None:
    """Lexicographically last `r-*.html` file in responses/, or None if empty.

    Filenames use ISO-8601-ish timestamps (`r-2026-05-14T16-34-22.html`) so
    lexical order = chronological order. No mtime stat per file needed.
    """
    if not RESPONSES_DIR.exists():
        return None
    files = sorted(RESPONSES_DIR.glob("r-*.html"))
    return files[-1] if files else None


def render_index() -> bytes:
    """Auto-generated HTML index of all responses, newest first."""
    files = sorted(RESPONSES_DIR.glob("r-*.html"), reverse=True) if RESPONSES_DIR.exists() else []
    rows = []
    for f in files:
        # Extract timestamp portion from filename: r-2026-05-14T16-34-22.html
        ts = f.stem[2:].replace("T", " · ").replace("-", ":", 2)  # crude prettify
        # Try to peek at the <title> tag for a label
        title = ""
        try:
            head = f.read_text(encoding="utf-8", errors="ignore")[:4096]
            start = head.find("<title>")
            end = head.find("</title>")
            if start != -1 and end > start:
                title = head[start + 7 : end].strip()
        except Exception:
            pass
        rows.append(
            f'<tr><td><a href="/{f.name}"><span class="ts">{ts}</span></a></td>'
            f'<td>{title or "—"}</td></tr>'
        )
    body = "\n".join(rows) if rows else (
        '<tr><td colspan="2" style="color:var(--ink-3);padding:20px;text-align:center;">'
        "no responses yet — Claude will write the first one here</td></tr>"
    )
    return (
        f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>html-response · all responses</title>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@1,500&family=Inter:wght@400;500&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root {{
  --bg:#0A0907; --surface:rgba(255,255,255,.025); --border:rgba(212,171,104,.08);
  --ink:#F0EBE0; --ink-2:rgba(240,235,224,.62); --ink-3:rgba(240,235,224,.38);
  --gold:#D4AB68;
}}
body{{background:var(--bg);color:var(--ink);font-family:Inter,system-ui,sans-serif;margin:0;padding:64px 32px;}}
.r-page{{max-width:920px;margin:0 auto;}}
.r-eyebrow{{font-family:'JetBrains Mono',monospace;font-size:10.5px;letter-spacing:.22em;text-transform:uppercase;color:var(--ink-3);margin-bottom:18px;}}
h1{{font-family:'Cormorant Garamond',Georgia,serif;font-style:italic;font-weight:500;font-size:42px;margin:0 0 24px;background:linear-gradient(180deg,#F8F1E3,var(--gold));-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;}}
table{{width:100%;border-collapse:collapse;margin-top:24px;}}
th,td{{text-align:left;padding:12px 14px;border-bottom:1px solid var(--border);}}
th{{font-family:'JetBrains Mono',monospace;font-size:10px;letter-spacing:.22em;text-transform:uppercase;color:var(--ink-3);font-weight:500;}}
td{{color:var(--ink-2);}}
a{{color:var(--gold);text-decoration:none;}} a:hover{{text-decoration:underline;}}
.ts{{font-family:'JetBrains Mono',monospace;font-size:12.5px;}}
.r-footer{{margin-top:64px;font-family:'JetBrains Mono',monospace;font-size:10.5px;letter-spacing:.18em;text-transform:uppercase;color:var(--ink-3);}}
.r-footer a{{color:var(--ink-3);}} .r-footer a:hover{{color:var(--gold);}}
</style></head><body>
<div class="r-page">
  <div class="r-eyebrow">html-response · history</div>
  <h1>all responses</h1>
  <table><thead><tr><th>when</th><th>title</th></tr></thead><tbody>
  {body}
  </tbody></table>
  <div class="r-footer"><a href="/">← latest</a></div>
</div>
</body></html>"""
    ).encode("utf-8")


class ResponseHandler(BaseHTTPRequestHandler):
    # Quieter than default — we'll log via log_message override
    def log_message(self, fmt: str, *args) -> None:
        ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
        line = f"{ts} {self.address_string()} {fmt % args}\n"
        try:
            with LOG_FILE.open("a", encoding="utf-8") as fh:
                fh.write(line)
        except Exception:
            pass

    def _send(self, status: int, body: bytes, content_type: str = "text/html; charset=utf-8") -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 — http.server API
        path = self.path.split("?", 1)[0]

        if path == "/" or path == "":
            latest = latest_response_path()
            if latest is None:
                self._send(200, render_empty_landing())
                return
            try:
                self._send(200, latest.read_bytes())
            except Exception as exc:
                self._send(500, f"<pre>error reading {latest.name}: {exc}</pre>".encode())
            return

        if path == "/version":
            latest = latest_response_path()
            if latest is None:
                payload = {"latest": None, "mtime": 0}
            else:
                payload = {"latest": latest.name, "mtime": latest.stat().st_mtime}
            self._send(200, json.dumps(payload).encode(), "application/json")
            return

        if path == "/index":
            self._send(200, render_index())
            return

        # Serve any file (html, png, jpg, svg, gif, webp, ico) from state/responses/.
        # Path traversal guarded; arbitrary other extensions get a 404.
        if "/" not in path.lstrip("/"):  # single-level only, no subdirs
            fname = path.lstrip("/")
            ext = fname.rsplit(".", 1)[-1].lower() if "." in fname else ""
            if ext in {"html", "png", "jpg", "jpeg", "svg", "gif", "webp", "ico"}:
                candidate = (RESPONSES_DIR / fname).resolve()
                try:
                    candidate.relative_to(RESPONSES_DIR.resolve())
                except ValueError:
                    self._send(403, b"<pre>forbidden</pre>")
                    return
                if not candidate.is_file():
                    self._send(404, f"<pre>not found: {path}</pre>".encode())
                    return
                mime = {
                    "html": "text/html; charset=utf-8",
                    "png": "image/png",
                    "jpg": "image/jpeg", "jpeg": "image/jpeg",
                    "svg": "image/svg+xml",
                    "gif": "image/gif",
                    "webp": "image/webp",
                    "ico": "image/x-icon",
                }[ext]
                self._send(200, candidate.read_bytes(), mime)
                return

        self._send(404, f"<pre>not found: {path}</pre>".encode())


def render_empty_landing() -> bytes:
    return (
        """<!doctype html><html><head><meta charset="utf-8">
<title>html-response · ready</title>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@1,500&family=Inter:wght@400&family=JetBrains+Mono:wght@400&display=swap" rel="stylesheet">
<style>
body{background:#0A0907;color:#F0EBE0;font-family:Inter,system-ui,sans-serif;margin:0;
     min-height:100vh;display:flex;align-items:center;justify-content:center;text-align:center;padding:32px;}
.eyebrow{font-family:'JetBrains Mono',monospace;font-size:10.5px;letter-spacing:.22em;text-transform:uppercase;color:rgba(240,235,224,.38);margin-bottom:18px;}
h1{font-family:'Cormorant Garamond',Georgia,serif;font-style:italic;font-weight:500;font-size:42px;margin:0 0 12px;background:linear-gradient(180deg,#F8F1E3,#D4AB68);-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;}
p{color:rgba(240,235,224,.62);max-width:48ch;margin:0 auto;}
.hint{margin-top:32px;font-family:'JetBrains Mono',monospace;font-size:11px;letter-spacing:.18em;text-transform:uppercase;color:rgba(240,235,224,.38);}
</style></head><body><div>
<div class="eyebrow">html-response · ready</div>
<h1>waiting for the first response</h1>
<p>The server is up on port 4747. Claude will write the first response into <code>state/responses/</code> and this page will refresh.</p>
<div class="hint">port 4747 · stdlib http.server</div>
<script>setInterval(()=>fetch('/version').then(r=>r.json()).then(d=>{if(d.latest)location.reload();}),3000);</script>
</div></body></html>"""
    ).encode("utf-8")


def port_in_use(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        try:
            s.connect((host, port))
            return True
        except (ConnectionRefusedError, socket.timeout, OSError):
            return False


def main() -> int:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    RESPONSES_DIR.mkdir(parents=True, exist_ok=True)

    if port_in_use(HOST, PORT):
        # Another instance is up — that's fine, that's the contract
        print(f"html-response server already running on http://{HOST}:{PORT}/", file=sys.stderr)
        return 0

    PID_FILE.write_text(str(os.getpid()))
    server = ThreadingHTTPServer((HOST, PORT), ResponseHandler)
    print(f"html-response serving on http://{HOST}:{PORT}/", file=sys.stderr)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        try:
            PID_FILE.unlink()
        except FileNotFoundError:
            pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
