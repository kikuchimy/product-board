import pytest

from app import Product, create_app, db


@pytest.fixture
def app():
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


def add_product(app, name="りんご", price=300):
    with app.app_context():
        product = Product(name=name, price=price, producer_name="高橋農園")
        db.session.add(product)
        db.session.commit()
        return product.id


def test_一覧ページが表示される(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "商品一覧" in response.text


def test_商品を登録できる(app, client):
    response = client.post(
        "/products/new",
        data={
            "name": "りんご",
            "price": "300",
            "producer_name": "高橋農園",
            "description": "",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "りんご" in response.text
    with app.app_context():
        assert db.session.scalar(db.select(db.func.count(Product.id))) == 1


def test_商品名が空だと登録できない(app, client):
    response = client.post(
        "/products/new",
        data={"name": "", "price": "300", "producer_name": "高橋農園"},
    )
    assert response.status_code == 422
    assert "商品名を入力してください" in response.text
    with app.app_context():
        assert db.session.scalar(db.select(db.func.count(Product.id))) == 0


def test_商品を削除できる(app, client):
    product_id = add_product(app)
    client.post(f"/products/{product_id}/delete")
    with app.app_context():
        assert db.session.get(Product, product_id) is None


def test_存在しない商品は404(client):
    response = client.get("/products/999")
    assert response.status_code == 404


def test_商品を編集できる(app, client):
    product_id = add_product(app)
    response = client.post(
        f"/products/{product_id}/edit",
        data={"name": "ふじりんご", "price": "350", "producer_name": "高橋農園"},
    )
    assert response.status_code == 302
    with app.app_context():
        product = db.session.get(Product, product_id)
        assert product.name == "ふじりんご"
        assert product.price == 350
