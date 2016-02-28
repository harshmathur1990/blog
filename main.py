from gevent import monkey
monkey.patch_all()
from gevent.wsgi import WSGIServer
from flask import Flask
app = Flask(__name__)


if __name__ == "__main__":
    app.debug = True
    http_server = WSGIServer(('', 8000), app)
    http_server.serve_forever()