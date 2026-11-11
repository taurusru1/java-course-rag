"""Small local server for the built Vue SPA with History API fallback."""

from argparse import ArgumentParser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from http.client import HTTPConnection
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
BACKEND_HOST = "127.0.0.1"
BACKEND_PORT = 8080
HOP_BY_HOP_HEADERS = {
    "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
    "te", "trailers", "transfer-encoding", "upgrade",
}


class SpaRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIST), **kwargs)

    def log_message(self, message_format, *args):
        """Do not let a detached console/log pipe break HTTP responses."""
        try:
            super().log_message(message_format, *args)
        except (BrokenPipeError, OSError, ValueError):
            pass

    def end_headers(self):
        """Keep the SPA entry fresh while allowing hashed assets to cache."""
        requested_path = urlparse(self.path).path
        if requested_path in {"/", "/index.html"} or not Path(self.translate_path(requested_path)).exists():
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        elif requested_path.startswith("/assets/"):
            self.send_header("Cache-Control", "public, max-age=31536000, immutable")
        super().end_headers()

    def send_head(self):
        requested_path = urlparse(self.path).path
        local_path = Path(self.translate_path(requested_path))
        accepts_html = "text/html" in self.headers.get("Accept", "")

        if requested_path != "/" and not local_path.exists() and accepts_html:
            original_path = self.path
            self.path = "/index.html"
            try:
                return super().send_head()
            finally:
                self.path = original_path

        return super().send_head()

    def _proxy_api(self):
        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length) if content_length else None
        headers = {
            name: value for name, value in self.headers.items()
            if name.lower() not in HOP_BY_HOP_HEADERS | {"host", "content-length"}
        }
        connection = HTTPConnection(BACKEND_HOST, BACKEND_PORT, timeout=35)
        try:
            connection.request(self.command, self.path, body=body, headers=headers)
            response = connection.getresponse()
            content_type = response.getheader("Content-Type", "")
            is_stream = content_type.startswith("text/event-stream")
            payload = None if is_stream else response.read()

            self.send_response(response.status, response.reason)
            for name, value in response.getheaders():
                if name.lower() not in HOP_BY_HOP_HEADERS | {"content-length"}:
                    self.send_header(name, value)
            if payload is not None:
                self.send_header("Content-Length", str(len(payload)))
            self.end_headers()

            if is_stream:
                while chunk := response.read(4096):
                    self.wfile.write(chunk)
                    self.wfile.flush()
            elif payload:
                self.wfile.write(payload)
        except (ConnectionError, OSError) as error:
            payload = b'{"code":502,"message":"Backend service is unavailable"}'
            self.send_response(502)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            self.log_error("API proxy failed: %s", error)
        finally:
            connection.close()

    def _dispatch(self):
        if urlparse(self.path).path.startswith("/api/"):
            self._proxy_api()
            return
        if self.command in {"GET", "HEAD"}:
            super_method = super().do_GET if self.command == "GET" else super().do_HEAD
            super_method()
            return
        self.send_error(405, "Method not allowed")

    def do_GET(self):
        self._dispatch()

    def do_HEAD(self):
        self._dispatch()

    def do_POST(self):
        self._dispatch()

    def do_PUT(self):
        self._dispatch()

    def do_DELETE(self):
        self._dispatch()

    def do_PATCH(self):
        self._dispatch()

    def do_OPTIONS(self):
        self._dispatch()


def main():
    parser = ArgumentParser(description="Serve the built frontend with SPA fallback")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=5173, type=int)
    args = parser.parse_args()

    if not (DIST / "index.html").exists():
        raise SystemExit("dist/index.html does not exist; run npm run build first")

    server = ThreadingHTTPServer((args.host, args.port), SpaRequestHandler)
    print(f"SPA preview: http://{args.host}:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
