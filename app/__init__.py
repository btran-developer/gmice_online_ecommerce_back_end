from flask import Flask, redirect, url_for, flash, render_template, session
from flask_restplus import Api
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_admin import Admin, AdminIndexView
from flask_mail import Mail
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from app.redis_store import RedisStore
from app.config import Config
from app.resources import api_blueprint
from wtforms import SelectField
from app.search import Elastic
from werkzeug.middleware.shared_data import SharedDataMiddleware
from app.forms import AdminLoginForm

db = SQLAlchemy(session_options={"autoflush": False})
migrate = Migrate()
admin_app = Admin(template_mode="bootstrap3",)
api = Api(validate=True)
mail = Mail()
jwt = JWTManager()
cors = CORS()
redis_store = RedisStore()
es = Elastic()


def createApp(app_config=Config):
    app = Flask(__name__)
    app.config.from_object(app_config)

    db.init_app(app)
    migrate.init_app(app, db)
    from app.admin import views

    admin_app.init_app(
        app, index_view=views.AdminHomeView(name="Home", template="admin/index.html")
    )
    api.init_app(api_blueprint)
    cors.init_app(api_blueprint)
    mail.init_app(app)
    jwt.init_app(app)
    redis_store.init_app(app)
    es.init_app(app, db)

    with app.app_context():
        register_blueprint(app)
        setup_jwt(jwt, redis_store)
        register_apis(api)
        register_admin_views(admin_app, app, views)

    app.add_url_rule("/uploads/<filename>", "uploaded_file", build_only=True)
    app.wsgi_app = SharedDataMiddleware(
        app.wsgi_app, {"/uploads": app.config["UPLOAD_FOLDER"]}
    )

    return app


def setup_jwt(jwt, redis_store):
    @jwt.token_in_blacklist_loader
    def check_if_token_is_revoked(decrypted_token):
        jti = decrypted_token["jti"]
        entry = redis_store.object.get(jti)
        # In case when entry doesn't exist
        # we consider the token to be revoked
        # for safety purposes.
        if entry is None:
            return True
        return entry == "true"


def register_blueprint(app):
    app.register_blueprint(api_blueprint)

    from app.blueprints.user_activation import user_activation_bp

    app.register_blueprint(user_activation_bp)


def register_apis(api):
    from app.resources.user import user_ns

    api.add_namespace(user_ns)

    from app.resources.product import products_ns, product_ns

    api.add_namespace(products_ns)
    api.add_namespace(product_ns)

    from app.resources.brand import brand_ns

    api.add_namespace(brand_ns)

    from app.resources.tag import tags_ns

    api.add_namespace(tags_ns)

    from app.resources.contactus import contactus_ns

    api.add_namespace(contactus_ns)

    # from app.resources.address import address_ns

    # api.add_namespace(address_ns)

    from app.resources.cart import cart_ns

    api.add_namespace(cart_ns)

    from app.resources.order import order_ns

    api.add_namespace(order_ns)


def register_admin_views(admin, app, views):
    from app import models

    @app.route("/admin/login", methods=["GET", "POST"])
    def admin_login():
        form = AdminLoginForm()

        if form.validate_on_submit():
            user = models.User.query.filter_by(email=form.email.data).first()
            if user and user.check_password(form.password.data):
                session.clear()
                session["user_id"] = user.id
                return redirect(url_for("admin.index"))
            else:
                flash("Invalid email or password")
        return render_template("admin/login.html", title="Admin Login", form=form)

    @app.route("/admin/logout")
    def admin_logout():
        session.clear()
        return redirect(url_for("admin_login"))

    admin.add_view(
        views.ProductAdminView(models.Product, db.session, category="Product")
    )
    admin.add_view(
        views.ProductSpecificationsAdminView(
            models.ProductSpecifications, db.session, category="Product"
        )
    )
    admin.add_view(
        views.ProdudctFeatureAdminView(
            models.ProductFeature, db.session, category="Product"
        )
    )
    admin.add_view(
        views.ProductTagAdminView(models.ProductTag, db.session, category="Product")
    )
    admin.add_view(
        views.ProductImageAdminView(models.ProductImage, db.session, category="Product")
    )
    admin.add_view(
        views.BrandAdminView(models.ProductBrand, db.session, category="Product")
    )
    admin.add_view(views.UserAdminView(models.User, db.session, category="User"))
    admin.add_view(
        views.OrderManageAdminView(
            models.Order, db.session, inline_models=(models.OrderLine,)
        )
    )
    # admin.add_view(views.AddressAdminView(models.Address, db.session, category="User"))
    # admin.add_view(
    #     views.CartAdminView(models.Cart, db.session, inline_models=(models.CartLine,))
    # )
    # admin.add_view(
    #     views.OrderAdminView(
    #         models.Order,
    #         db.session,
    #         inline_models=(
    #             (
    #                 models.OrderLine,
    #                 dict(
    #                     form_extra_fields={
    #                         "status": SelectField(
    #                             choices=models.OrderLine.STATUSES, coerce=int
    #                         )
    #                     }
    #                 ),
    #             ),
    #         ),
    #     )
    # )
