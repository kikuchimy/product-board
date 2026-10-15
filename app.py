from datetime import datetime

from flask import Flask, flash, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    selectinload,
)


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)


class Producer(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    area: Mapped[str] = mapped_column(String(50), default="")
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)

    # この生産者の商品の一覧（1対多の「多」の側）
    products: Mapped[list[Product]] = relationship(back_populates="producer")


class Product(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    price: Mapped[int]
    producer_id: Mapped[int] = mapped_column(ForeignKey("producer.id"))
    description: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)

    # この商品の生産者（1対多の「1」の側）
    producer: Mapped[Producer] = relationship(back_populates="products")


def validate_product(form):
    """フォームの値をチェックして、エラーメッセージのリストを返す"""
    errors = []
    name = form.get("name", "").strip()
    price = form.get("price", "").strip()
    producer_id = form.get("producer_id", "").strip()

    if name == "":
        errors.append("商品名を入力してください")
    elif len(name) > 50:
        errors.append("商品名は50文字以内で入力してください")

    if not price.isdecimal():
        errors.append("価格は0以上の整数で入力してください")
    elif int(price) > 100000:
        errors.append("価格は100,000円以下で入力してください")

    if not producer_id.isdecimal():
        errors.append("生産者を選んでください")
    elif db.session.get(Producer, int(producer_id)) is None:
        errors.append("選んだ生産者が見つかりません")

    return errors


def validate_producer(form):
    """生産者フォームの値をチェックして、エラーメッセージのリストを返す"""
    errors = []
    name = form.get("name", "").strip()
    area = form.get("area", "").strip()

    if name == "":
        errors.append("生産者名を入力してください")
    elif len(name) > 50:
        errors.append("生産者名は50文字以内で入力してください")
    elif db.session.scalar(db.select(Producer).where(Producer.name == name)):
        errors.append("その生産者名はすでに登録されています")

    if len(area) > 50:
        errors.append("地域は50文字以内で入力してください")

    return errors


def all_producers():
    """商品フォームの選択肢に使う、生産者の一覧"""
    return db.session.scalars(db.select(Producer).order_by(Producer.name)).all()


def create_app(test_config=None):
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "dev"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///product_board.sqlite"
    if test_config is not None:
        app.config.update(test_config)

    db.init_app(app)
    with app.app_context():
        db.create_all()

    @app.route("/")
    def index():
        products = db.session.scalars(
            db.select(Product)
            .options(selectinload(Product.producer))
            .order_by(Product.created_at.desc())
        ).all()
        return render_template("products/index.html", products=products)

    @app.route("/products/new", methods=["GET", "POST"])
    def create():
        if request.method == "POST":
            errors = validate_product(request.form)
            if errors:
                return render_template(
                    "products/form.html",
                    errors=errors,
                    form=request.form,
                    product=None,
                    producers=all_producers(),
                ), 422

            product = Product(
                name=request.form["name"].strip(),
                price=int(request.form["price"]),
                producer_id=int(request.form["producer_id"]),
                description=request.form.get("description", "").strip(),
            )
            db.session.add(product)
            db.session.commit()
            flash("商品を登録しました")
            return redirect(url_for("index"))

        return render_template(
            "products/form.html",
            errors=[],
            form={},
            product=None,
            producers=all_producers(),
        )

    @app.route("/products/<int:product_id>")
    def show(product_id):
        product = db.get_or_404(Product, product_id)
        return render_template("products/show.html", product=product)

    @app.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
    def edit(product_id):
        product = db.get_or_404(Product, product_id)
        if request.method == "POST":
            errors = validate_product(request.form)
            if errors:
                return render_template(
                    "products/form.html",
                    errors=errors,
                    form=request.form,
                    product=product,
                    producers=all_producers(),
                ), 422

            product.name = request.form["name"].strip()
            product.price = int(request.form["price"])
            product.producer_id = int(request.form["producer_id"])
            product.description = request.form.get("description", "").strip()
            db.session.commit()
            flash("商品を更新しました")
            return redirect(url_for("show", product_id=product.id))

        form = {
            "name": product.name,
            "price": product.price,
            "producer_id": product.producer_id,
            "description": product.description,
        }
        return render_template(
            "products/form.html",
            errors=[],
            form=form,
            product=product,
            producers=all_producers(),
        )

    @app.route("/products/<int:product_id>/delete", methods=["POST"])
    def delete(product_id):
        product = db.get_or_404(Product, product_id)
        db.session.delete(product)
        db.session.commit()
        flash("商品を削除しました")
        return redirect(url_for("index"))

    @app.route("/producers")
    def producer_index():
        return render_template("producers/index.html", producers=all_producers())

    @app.route("/producers/new", methods=["GET", "POST"])
    def producer_create():
        if request.method == "POST":
            errors = validate_producer(request.form)
            if errors:
                return render_template(
                    "producers/form.html", errors=errors, form=request.form
                ), 422

            producer = Producer(
                name=request.form["name"].strip(),
                area=request.form.get("area", "").strip(),
            )
            db.session.add(producer)
            db.session.commit()
            flash("生産者を登録しました")
            return redirect(url_for("producer_index"))

        return render_template("producers/form.html", errors=[], form={})

    @app.route("/producers/<int:producer_id>")
    def producer_show(producer_id):
        producer = db.get_or_404(Producer, producer_id)
        return render_template("producers/show.html", producer=producer)

    @app.errorhandler(404)
    def not_found(error):
        return render_template("404.html"), 404

    return app
