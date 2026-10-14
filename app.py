from datetime import datetime

from flask import Flask, render_template
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

    return app
