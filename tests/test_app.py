import pytest

from app import Producer, Product, create_app, db


@pytest.fixture
def app():
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


def add_producer(app, name="高橋農園", area="西根"):
    with app.app_context():
        producer = Producer(name=name, area=area)
        db.session.add(producer)
        db.session.commit()
        return producer.id


def add_product(app, producer_id, name="りんご", price=300):
    with app.app_context():
        product = Product(name=name, price=price, producer_id=producer_id)
        db.session.add(product)
        db.session.commit()
        return product.id


def test_一覧ページが表示される(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "商品一覧" in response.text


def test_商品を登録できる(app, client):
    producer_id = add_producer(app)
    response = client.post(
        "/products/new",
        data={
            "name": "りんご",
            "price": "300",
            "producer_id": str(producer_id),
            "description": "",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "りんご" in response.text
    assert "高橋農園" in response.text
    with app.app_context():
        assert db.session.scalar(db.select(db.func.count(Product.id))) == 1


def test_商品名が空だと登録できない(app, client):
    producer_id = add_producer(app)
    response = client.post(
        "/products/new",
        data={"name": "", "price": "300", "producer_id": str(producer_id)},
    )
    assert response.status_code == 422
    assert "商品名を入力してください" in response.text
    with app.app_context():
        assert db.session.scalar(db.select(db.func.count(Product.id))) == 0


def test_存在しない生産者は選べない(app, client):
    response = client.post(
        "/products/new",
        data={"name": "りんご", "price": "300", "producer_id": "999"},
    )
    assert response.status_code == 422
    assert "選んだ生産者が見つかりません" in response.text
    with app.app_context():
        assert db.session.scalar(db.select(db.func.count(Product.id))) == 0


def test_商品を削除できる(app, client):
    product_id = add_product(app, add_producer(app))
    client.post(f"/products/{product_id}/delete")
    with app.app_context():
        assert db.session.get(Product, product_id) is None


def test_存在しない商品は404(client):
    response = client.get("/products/999")
    assert response.status_code == 404


def test_生産者を登録できる(app, client):
    response = client.post(
        "/producers/new",
        data={"name": "松尾きのこ園", "area": "松尾"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "松尾きのこ園" in response.text
    with app.app_context():
        assert db.session.scalar(db.select(db.func.count(Producer.id))) == 1


def test_生産者名が空だと登録できない(app, client):
    response = client.post("/producers/new", data={"name": "", "area": ""})
    assert response.status_code == 422
    assert "生産者名を入力してください" in response.text


def test_同じ名前の生産者は登録できない(app, client):
    add_producer(app, name="高橋農園")
    response = client.post("/producers/new", data={"name": "高橋農園", "area": ""})
    assert response.status_code == 422
    assert "すでに登録されています" in response.text


def test_生産者ページにはその生産者の商品だけが出る(app, client):
    takahashi_id = add_producer(app, name="高橋農園")
    matsuo_id = add_producer(app, name="松尾きのこ園")
    add_product(app, takahashi_id, name="りんご")
    add_product(app, matsuo_id, name="マッシュルーム")

    response = client.get(f"/producers/{takahashi_id}")
    assert response.status_code == 200
    assert "りんご" in response.text
    assert "マッシュルーム" not in response.text
