from flask import Flask, render_template

app = Flask(__name__)

# まだデータベースが無いので、Python のリストで仮のデータを用意する
PRODUCTS = [
    {"name": "りんご（ふじ）", "price": 300, "producer_name": "高橋農園"},
    {"name": "八幡平マッシュルーム", "price": 450, "producer_name": "松尾きのこ園"},
    {"name": "ほうれん草", "price": 150, "producer_name": "西根ファーム"},
    {"name": "安代りんどうの鉢植え", "price": 1500, "producer_name": "安代花き"},
]


@app.route("/")
def index():
    return render_template("products/index.html", products=PRODUCTS)
