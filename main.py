import mimetypes
import pathlib
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import json
from datetime import datetime
from jinja2 import Environment, FileSystemLoader


env = Environment(loader=FileSystemLoader("templates"))


class HttpHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        data = self.rfile.read(int(self.headers["Content-Length"]))
        print(data)
        data_parse = urllib.parse.unquote_plus(data.decode())
        print(data_parse)

        new_entry = {
            str(datetime.now()): {
                key: value
                for key, value in [el.split("=") for el in data_parse.split("&")]
            }
        }
        print(new_entry)

        try:
            with open("./storage/data.json", "r", encoding="utf-8") as fd:
                stored_data = json.load(fd)
        except (FileNotFoundError, json.JSONDecodeError):
            stored_data = {}

        stored_data.update(new_entry)

        with open("./storage/data.json", "w", encoding="utf-8") as fd:
            json.dump(stored_data, fd, indent=4)

        self.send_response(302)
        self.send_header("Location", "/")
        self.end_headers()

    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == "/":
            self.send_html_file("index.html")
        elif pr_url.path == "/message":
            self.send_html_file("message.html")
        elif pr_url.path == "/read":
            self.render_read_page()
        else:
            if pathlib.Path().joinpath(pr_url.path[1:]).exists():
                self.send_static()
            else:
                self.send_html_file("error.html", 404)

    def render_read_page(self):
        # Читаємо дані з файлу data.json
        try:
            with open("./storage/data.json", "r", encoding="utf-8") as fd:
                messages = json.load(fd)
        except (FileNotFoundError, json.JSONDecodeError):
            messages = {}

        # Рендеримо шаблон read.html з передачею даних
        template = env.get_template("read.html")
        content = template.render(messages=messages)

        # Відправляємо згенерований HTML у відповідь
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(content.encode("utf-8"))

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        with open(filename, "rb") as fd:
            self.wfile.write(fd.read())

    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", "text/plain")
        self.end_headers()
        with open(f".{self.path}", "rb") as file:
            self.wfile.write(file.read())


def run(server_class=HTTPServer, handler_class=HttpHandler):
    server_address = ("", 3000)
    http = server_class(server_address, handler_class)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()


if __name__ == "__main__":
    run()
