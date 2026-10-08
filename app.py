from flask import Flask

app = Flask(__name__)


@app.route("/")
def index():
    return "<h1>八幡平 産直掲示板</h1><p>こんにちは、Flask！</p>"


@app.route("/hello/<name>")
def hello(name):
    return f"<p>こんにちは、{name}さん</p>"
