from datetime import datetime

from flask import Flask, flash, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)


class Product(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    price: Mapped[int]
    producer_name: Mapped[str] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)


def validate_product(form):
    """フォームの値をチェックして、エラーメッセージのリストを返す"""
    errors = []
    name = form.get("name", "").strip()
    price = form.get("price", "").strip()
    producer_name = form.get("producer_name", "").strip()

    if name == "":
        errors.append("商品名を入力してください")
    elif len(name) > 50:
        errors.append("商品名は50文字以内で入力してください")

    if not price.isdecimal():
        errors.append("価格は0以上の整数で入力してください")
    elif int(price) > 100000:
        errors.append("価格は100,000円以下で入力してください")

    if producer_name == "":
        errors.append("生産者名を入力してください")

    return errors

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
            db.select(Product).order_by(Product.created_at.desc())
        ).all()
        return render_template("products/index.html", products=products)

    @app.route("/products/new", methods=["GET", "POST"])
    def create():
        if request.method == "POST":
            errors = validate_product(request.form)
            if errors:
                return render_template(
                    "products/form.html", errors=errors, form=request.form, product=None
                ), 422

            product = Product(
                name=request.form["name"].strip(),
                price=int(request.form["price"]),
                producer_name=request.form["producer_name"].strip(),
                description=request.form.get("description", "").strip(),
            )
            db.session.add(product)
            db.session.commit()
            flash("商品を登録しました")
            return redirect(url_for("index"))

        return render_template("products/form.html", errors=[], form={}, product=None)

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
                ), 422

            product.name = request.form["name"].strip()
            product.price = int(request.form["price"])
            product.producer_name = request.form["producer_name"].strip()
            product.description = request.form.get("description", "").strip()
            db.session.commit()
            flash("商品を更新しました")
            return redirect(url_for("show", product_id=product.id))

        form = {
            "name": product.name,
            "price": product.price,
            "producer_name": product.producer_name,
            "description": product.description,
        }
        return render_template(
            "products/form.html", errors=[], form=form, product=product
        )

    @app.route("/products/<int:product_id>/delete", methods=["POST"])
    def delete(product_id):
        product = db.get_or_404(Product, product_id)
        db.session.delete(product)
        db.session.commit()
        flash("商品を削除しました")
        return redirect(url_for("index"))

    @app.errorhandler(404)
    def not_found(error):
        return render_template("404.html"), 404


    return app
