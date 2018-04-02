import shutil
from http.server import BaseHTTPRequestHandler
from mimetypes import guess_type

from conan_inquiry.web.file_retrieval import WebFiles


class DevelopmentHTTPRequestHandler(BaseHTTPRequestHandler):
    files = WebFiles()

    def _current_name(self):
        path = self.path.split('?')[0]
        if path == '/':
            return 'index.html'
        return path.strip('/')

    def _write(self, string: str):
        self.wfile.write(string.encode('utf-8'))

    def _head(self):
        if self.files.exists(self._current_name()):
            self.send_response(200)
            self.send_header('Content-Type', guess_type(self.path)[0])
        else:
            self.send_response(404)
            self.send_header('Content-Type', 'text/html')

    def do_HEAD(self):
        self._head()
        self.end_headers()

    def do_GET(self):
        self._head()
        if self.files.exists(self._current_name()):
            if self.files.is_constant(self._current_name()):
                self.send_header('Content-Length', self.files.size(self._current_name()))
                self.end_headers()
                with open(self.files.full_name(self._current_name()), 'rb') as f:
                    shutil.copyfileobj(f, self.wfile)
                self.log_request(200, self.files.size(self._current_name()))
            else:
                data = self.files.get_file(self._current_name(), debug=True)
                raw = data.encode('utf-8')
                self.send_header('Content-Length', len(raw))
                self.end_headers()
                self.wfile.write(raw)
        else:
            self._write('<html><body><h1>404 Not Found</h1></body></html>')
            self.log_request(404)
