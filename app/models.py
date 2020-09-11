from flask import current_app as app
from flask_sqlalchemy import event
from slugify import slugify
from werkzeug.security import generate_password_hash, check_password_hash
from cloudinary.uploader import destroy
from app import db, es
import os
import enum


class SearchableMixin(object):
    @classmethod
    def reindex(cls):
        if es.object.indices.exists(index=cls.__tablename__):
            es.object.indices.delete(cls.__tablename__)
        es.clear_bulk_queue()
        for obj in cls.query:
            es.add_to_bulk_queue(cls.__tablename__, obj, "index")
        es.perform_bulk()


product_and_tag_assoc = db.Table(
    "product_and_tag_assoc",
    db.metadata,
    db.Column("product_id", db.Integer, db.ForeignKey("products.id")),
    db.Column("product_tag_id", db.Integer, db.ForeignKey("product_tags.id")),
)

product_and_feature_assoc = db.Table(
    "product_and_feature_assoc",
    db.metadata,
    db.Column("product_id", db.Integer, db.ForeignKey("products.id")),
    db.Column("product_feature_id", db.Integer, db.ForeignKey("product_features.id")),
)


class Product(db.Model, SearchableMixin):
    __tablename__ = "products"
    __searchable__ = (
        "name",
        "slug",
        "price",
        ("brand", ("name",)),
        ("tags", ("name",)),
        ("images", ("image_url", "thumbnail_url", "main",)),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.Text)
    slug = db.Column(db.String(84))
    price = db.Column(db.Float(precision=2), nullable=False)
    in_stock = db.Column(db.Boolean, default=True)
    active = db.Column(db.Boolean, nullable=False, default=True)
    date_created = db.Column(db.DateTime)
    date_updated = db.Column(db.DateTime)
    brand_id = db.Column(db.Integer, db.ForeignKey("product_brands.id"))
    brand = db.relationship("ProductBrand", backref="products")
    specifications_id = db.Column(
        db.Integer, db.ForeignKey("product_specifications.id")
    )
    specifications = db.relationship("ProductSpecifications")
    images = db.relationship(
        "ProductImage", backref="product", lazy=True, cascade="all, delete-orphan"
    )
    tags = db.relationship(
        "ProductTag", secondary=product_and_tag_assoc, backref="products"
    )
    features = db.relationship(
        "ProductFeature", secondary=product_and_feature_assoc, backref="products"
    )
    cartlines = db.relationship("CartLine", lazy=True, cascade="all, delete-orphan")
    orderlines = db.relationship("OrderLine", lazy=True, cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        self.name = kwargs.get("name")
        self.slug = kwargs.get("slug", slugify(kwargs.get("name")))
        self.description = kwargs.get("description")
        self.price = kwargs.get("price")

    def __str__(self):
        return self.name


class ProductSpecifications(db.Model):
    __tablename__ = "product_specifications"

    id = db.Column(db.Integer, primary_key=True)
    lighting_type = db.Column(db.String(20))
    minimum_sensitivity = db.Column(db.String(20))
    maximum_sensitivity = db.Column(db.String(20))
    total_buttons = db.Column(db.Integer)
    total_programmable_buttons = db.Column(db.Integer)
    wireless = db.Column(db.Boolean)
    height = db.Column(db.String(20))
    width = db.Column(db.String(20))
    weight = db.Column(db.String(20))
    product = db.relationship("Product", uselist=False)


class ProductTag(db.Model):
    __tablename__ = "product_tags"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False)
    slug = db.Column(db.String(62))
    active = db.Column(db.Boolean, default=True)

    def __init__(self, **kwargs):
        self.name = kwargs.get("name")
        self.slug = kwargs.get("slug", slugify(kwargs.get("name")))

    def __str__(self):
        return self.name


class ProductImage(db.Model):
    __tablename__ = "product_images"

    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(50), nullable=False)
    image_url = db.Column(db.String(100), nullable=False)
    thumbnail_url = db.Column(db.String(120), nullable=False)
    main = db.Column(db.Boolean, nullable=False, default=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"))


@event.listens_for(ProductImage, "after_delete")
def delete_image_files(mapper, connection, target):
    destroy(target.public_id)


class ProductFeature(db.Model):
    __tablename__ = "product_features"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64), nullable=False)
    description = db.Column(db.Text, nullable=False)


class ProductBrand(db.Model):
    __tablename__ = "product_brands"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    slug = db.Column(db.String(84))
    active = db.Column(db.Boolean, default=True)

    def __init__(self, **kwargs):
        self.name = kwargs.get("name")
        self.slug = kwargs.get("slug", slugify(kwargs.get("name")))

    def __str__(self):
        return self.name


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(32))
    last_name = db.Column(db.String(32))
    email = db.Column(db.String(100), nullable=False)
    hashed_password = db.Column(db.String(100), nullable=False)
    active = db.Column(db.Boolean, nullable=False, default=True)
    staff = db.Column(db.Boolean, nullable=False, default=False)
    admin = db.Column(db.Boolean, nullable=False, default=False)
    carts = db.relationship(
        "Cart", backref="user", cascade="all, delete-orphan", lazy="dynamic"
    )

    def __init__(self, **kwargs):
        self.first_name = kwargs.get("first_name")
        self.last_name = kwargs.get("last_name")
        self.email = kwargs.get("email")
        self.hashed_password = generate_password_hash(kwargs.get("password"))
        self.active = kwargs.get("active")
        self.admin = kwargs.get("admin")
        self.staff = True if self.admin else kwargs.get("staff")

    def is_staff(self):
        return self.staff

    def is_admin(self):
        return self.admin

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)

    def __repr__(self):
        return f"{self.first_name}, {self.last_name} < {self.email} >"


class Cart(db.Model):
    __tablename__ = "carts"

    class CartStatus(enum.Enum):
        OPEN = "OPEN"
        CLOSE = "CLOSE"

    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.Enum(CartStatus), default=CartStatus.OPEN)
    date_created = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    cart_lines = db.relationship(
        "CartLine", backref="cart", cascade="all, delete-orphan", lazy=True
    )


class CartLine(db.Model):
    __tablename__ = "cart_lines"

    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"))
    product = db.relationship("Product")
    cart_id = db.Column(db.Integer, db.ForeignKey("carts.id"))


class Order(db.Model):
    __tablename__ = "orders"

    class OrderStatus(enum.Enum):
        NEW = "NEW"
        COMPLETE = "COMPLETE"

    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.Enum(OrderStatus), default=OrderStatus.NEW)
    billing_address1 = db.Column(db.Text, nullable=False)
    billing_address2 = db.Column(db.Text)
    billing_city = db.Column(db.String(60), nullable=False)
    billing_state = db.Column(db.String(60), nullable=False)
    billing_zip = db.Column(db.Integer, nullable=False)
    shipping_address1 = db.Column(db.Text, nullable=False)
    shipping_address2 = db.Column(db.Text)
    shipping_city = db.Column(db.String(60), nullable=False)
    shipping_state = db.Column(db.String(60), nullable=False)
    shipping_zip = db.Column(db.Integer, nullable=False)
    contact = db.Column(db.String(150), nullable=False)
    date_created = db.Column(db.DateTime)
    order_lines = db.relationship(
        "OrderLine", backref="order", cascade="all, delete-orphan", lazy=True
    )
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    user = db.relationship("User")


class OrderLine(db.Model):
    __tablename__ = "order_lines"

    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"))
    product = db.relationship("Product")
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"))
