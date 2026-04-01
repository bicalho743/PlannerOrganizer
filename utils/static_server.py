import threading
import http.server
import os

_started = False

class StaticHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.join(os.path.dirname(__file__), '..', 'static'), **kwargs)

    def log_message(self, format, *args):
        pass

def start_static_server(port=5051):
    global _started
    if _started:
        return
    _started = True
    server = http.server.HTTPServer(("0.0.0.0", port), StaticHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
