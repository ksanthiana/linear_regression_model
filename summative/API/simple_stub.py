import json
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading


class Handler(BaseHTTPRequestHandler):
    def _set_json(self, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()

    def do_GET(self):
        if self.path == '/':
            self._set_json(200)
            self.wfile.write(json.dumps({'message': 'Stub API running', 'docs': '/docs', 'model': 'simple-stub-v1'}).encode())
        else:
            self._set_json(404)
            self.wfile.write(json.dumps({'detail': 'Not Found'}).encode())

    def do_POST(self):
        if self.path == '/predict':
            length = int(self.headers.get('Content-Length', 0))
            raw = self.rfile.read(length)
            try:
                body = json.loads(raw.decode())
                months = (body.get('harvest_year', 0) - body.get('planting_year', 0)) * 12 + (body.get('harvest_month', 0) - body.get('planting_month', 0))
                area = float(body.get('area', 0.0))
                area_factor = max(0.0, min(10.0, area / 1500.0))
                pred = round(0.5 + 0.5 * months + 0.2 * area_factor, 3)
                if pred < 0:
                    pred = 0.0
                resp = {'predicted_yield_t_per_ha': pred, 'model_used': 'simple-stub-v1'}
                self._set_json(200)
                self.wfile.write(json.dumps(resp).encode())
            except Exception as exc:
                self._set_json(400)
                self.wfile.write(json.dumps({'detail': f'Bad request: {exc}'}).encode())
        else:
            self._set_json(404)
            self.wfile.write(json.dumps({'detail': 'Not Found'}).encode())


def run(server_class=HTTPServer, handler_class=Handler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting simple stub server on port {port}...')
    httpd.serve_forever()


if __name__ == '__main__':
    run()
