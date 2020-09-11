from flask_admin.contrib.sqla import ModelView
from flask_admin.form import rules
from flask_admin.babel import gettext
from flask_admin import form, AdminIndexView
from datetime import datetime
from slugify import slugify
from jinja2 import Markup
from wtforms import MultipleFileField, FileField, PasswordField, SelectField
from wtforms import validators
from wtforms.fields.html5 import EmailField
from flask import request, flash, current_app as app
from werkzeug.utils import secure_filename
from PIL import Image
from flask import url_for, redirect, session
from app.models import User, ProductSpecifications, Product
from cloudinary.uploader import upload, destroy
from cloudinary.utils import cloudinary_url
import os


class AdminHomeView(AdminIndexView):
    def is_accessible(self):
        user_id = session.get("user_id")
        if user_id is not None:
            user = User.query.get(user_id)
            if user is not None and user.is_staff():
                return True
        return False


class AdminModelView(ModelView):
    def is_accessible(self):
        user_id = session.get("user_id")
        if user_id is not None:
            user = User.query.get(user_id)
            if user is not None and user.is_admin() and user.is_staff():
                return True
        return False

    def inaccessible_callback(self, name, **kwargs):
        flash("Admin privilege is required.", category="danger")
        return redirect(url_for("admin.index"))


class StaffModelView(ModelView):
    def is_accessible(self):
        user_id = session.get("user_id")
        if user_id is not None:
            user = User.query.get(user_id)
            if user is not None and user.is_staff():
                return True
        return False

    def inaccessible_callback(self, name, **kwargs):
        flash("Staff privilege is required", category="danger")
        return redirect(url_for("admin.index"))


class ProductAdminView(StaffModelView):
    column_list = (
        "name",
        "slug",
        "brand",
        "in_stock",
        "price",
        "date_updated",
        "date_created",
    )
    column_hide_backrefs = False
    column_filters = (
        "in_stock",
        "active",
    )
    column_editable_list = ("in_stock",)
    column_searchable_list = ("name",)
    column_sortable_list = (
        "name",
        "brand",
        "price",
        "date_created",
        "date_updated",
    )
    form_excluded_columns = (
        "date_updated",
        "date_created",
    )
    form_create_rules = (
        rules.Header("General"),
        "name",
        "brand",
        "slug",
        "tags",
        "description",
        "active",
        "in_stock",
        "price",
    )
    form_edit_rules = (
        rules.Header("General"),
        "name",
        "brand",
        "slug",
        "tags",
        "description",
        "active",
        "in_stock",
        "price",
    )

    def on_model_change(self, form, model, is_created):
        if not model.slug:
            model.slug = slugify(model.name)

        if is_created:
            model.date_created = datetime.utcnow()
        else:
            model.date_updated = datetime.utcnow()

    def after_model_change(self, form, model, is_created):
        Product.reindex()


class ProductSpecificationsAdminView(StaffModelView):
    column_list = ("product.name",)
    column_sortable_list = ("product.name",)
    column_filters = ("product.name",)


class ProdudctFeatureAdminView(StaffModelView):
    column_list = ("title", "description", "products")
    column_hide_backrefs = False
    column_sortable_list = ("title",)


class ProductTagAdminView(StaffModelView):
    column_list = (
        "name",
        "slug",
    )
    column_filters = ("active",)
    column_searchable_list = ("name",)
    column_sortable_list = ("name",)

    def on_model_change(self, form, model, is_created):
        if not model.slug:
            model.slug = slugify(model.name)

    def after_model_change(self, form, model, is_created):
        Product.reindex()


class ProductImageAdminView(StaffModelView):
    def _list_thumbnail(view, context, model, name):
        if model.thumbnail_url:
            # url = url_for(
            #     "uploaded_file", filename=model.thumbnail_url.split(os.path.sep)[1]
            # )
            return Markup(
                f'<img src="{model.thumbnail_url}" style="max-height: 45px; max-width: 65px;" />'
            )
        return "-"

    column_formatters = {"thumbnail": _list_thumbnail}
    column_list = (
        "thumbnail",
        "product.name",
        "main",
    )
    column_hide_backrefs = False
    column_searchable_list = ("product.name",)
    column_sortable_list = ("product.name",)
    column_editable_list = ("main",)
    form_excluded_columns = ("image_url", "thumbnail_url")
    form_create_rules = (
        "product",
        "images",
    )
    form_edit_rules = (
        "product",
        "main",
        "image",
    )

    def get_column_names(self, only_columns, excluded_columns):
        formatted_columns = super().get_column_names(only_columns, excluded_columns)

        def format_instrumented_column_name(c):
            column_name = c
            if "." in c[1]:
                column_name = (
                    c[0],
                    " ".join(c[1].split(".")),
                )
            return column_name

        formatted_columns = tuple(
            [format_instrumented_column_name(c) for c in formatted_columns]
        )
        return formatted_columns

    def scaffold_form(self):
        form_class = super().scaffold_form()
        form_class.image = FileField("Image")
        form_class.images = MultipleFileField("Images")
        return form_class

    def allowed_file(self, filename):
        return (
            "." in filename
            and filename.rsplit(".", 1)[1].lower()
            in app.config["ALLOWED_IMAGE_EXTENSIONS"]
        )

    def save_image(self, file):
        secured_filename_with_ext = secure_filename(file.filename)
        image_url = os.path.join(app.config["UPLOAD_FOLDER"], secured_filename_with_ext)
        thumbnail_url = os.path.join(
            app.config["UPLOAD_FOLDER"],
            form.thumbgen_filename(secured_filename_with_ext),
        )
        file.save(image_url)
        image = Image.open(file)
        image = image.convert("RGB")
        image.thumbnail(app.config["THUMBNAIL_SIZE"], Image.ANTIALIAS)
        image.save(os.path.abspath(thumbnail_url))
        return image_url, thumbnail_url

    def upload_image(self, file):
        secured_filename_with_ext = secure_filename(file.filename)
        upload_result = upload(file)
        image_url, options = cloudinary_url(
            upload_result["public_id"], format=upload_result["format"]
        )
        thumnail_width = app.config["THUMBNAIL_SIZE"][0]
        thumnail_height = app.config["THUMBNAIL_SIZE"][1]
        thumbnail_url = image_url.split("/")
        thumbnail_url.insert(
            thumbnail_url.index("upload") + 1,
            f"h_{thumnail_height},w_{thumnail_width},c_fit",
        )
        thumbnail_url = "/".join(thumbnail_url)
        return image_url, thumbnail_url, upload_result["public_id"]

    def create_model(self, form):
        try:
            for image in form.images.data:
                if self.allowed_file(image.filename):
                    # image_url, thumbnail_url = self.save_image(image)
                    image_url, thumbnail_url, public_id = self.upload_image(image)
                    model = self.model(
                        image_url=image_url,
                        thumbnail_url=thumbnail_url,
                        public_id=public_id,
                    )
                    model.product = form.product.data
                    self.session.add(model)
                    self._on_model_change(form, model, True)
                    self.session.commit()
                else:
                    flash(
                        "Make sure all your images have the following extensions: jpg, jpeg, png or gif"
                    )
                    return False
        except Exception as ex:
            if not self.handle_view_exception(ex):
                flash(gettext("Failed to create record. %(error)s", error=str(ex)))
            self.session.rollback()
            return False
        else:
            self.after_model_change(form, model, True)

        return model

    def update_model(self, form, model):
        try:
            if hasattr(form, "image"):
                file = request.files[form.image.name]
                if form.image.data:
                    if self.allowed_file(file.filename):
                        image_url, thumbnail_url = self.save_image(file)
                        self.before_model_update(form, model)
                        model.image_url = image_url
                        model.thumbnail_url = thumbnail_url
                    else:
                        flash(
                            "Make sure you have file with the following extensions: jpg, jpeg, png or gif"
                        )
                        return False
            model.main = form.main.data

            if hasattr(form, "product"):
                model.product = form.product.data
            self._on_model_change(form, model, False)
            self.session.commit()
        except Exception as ex:
            if not self.handle_view_exception(ex):
                flash(gettext("Failed to create record. %(error)s", error=str(ex)))
            self.session.rollback()
            return False
        else:
            self.after_model_change(form, model, False)

        return True

    def before_model_update(self, form, model):
        if model.image_url:
            try:
                destroy(model.public_id)
            except OSError as ex:
                print(ex)

    def after_model_change(self, form, model, is_created):
        Product.reindex()


class BrandAdminView(StaffModelView):
    column_list = (
        "name",
        "slug",
    )
    column_filters = ("active",)
    column_searchable_list = ("name",)
    column_sortable_list = ("name",)

    def on_model_change(self, form, model, is_created):
        if not model.slug:
            model.slug = slugify(model.name)


class UserAdminView(AdminModelView):
    column_list = (
        "email",
        "first_name",
        "last_name",
        "active",
        "staff",
        "admin",
    )
    column_filters = (
        "active",
        "staff",
        "admin",
    )
    column_searchable_list = ("email",)
    column_sortable_list = ("active",)
    column_editable_list = (
        "active",
        "staff",
        "admin",
    )
    form_excluded_columns = ("hashed_password",)
    form_edit_rules = (
        "first_name",
        "last_name",
        "email",
        "active",
        "staff",
        "admin",
        rules.Header("Reset Password"),
        "new_password",
        "confirm",
    )
    form_create_rules = (
        "email",
        "password",
        "staff",
        "admin",
    )

    def scaffold_form(self):
        form_class = super().scaffold_form()
        form_class.email = EmailField(
            "Email", [validators.Email(), validators.DataRequired()]
        )
        form_class.password = PasswordField("Password", [validators.DataRequired(),])
        form_class.new_password = PasswordField("New Password")
        form_class.confirm = PasswordField("Confirm Password")
        return form_class

    def create_model(self, form):
        try:
            model = self.model(
                email=form.email.data,
                staff=form.staff.data,
                admin=form.admin.data,
                password=form.password.data,
            )
            self.session.add(model)
            self._on_model_change(form, model, True)
            self.session.commit()
        except Exception as ex:
            if not self.handle_view_exception(ex):
                flash(gettext("Failed to create record. %(error)s", error=str(ex)))
            self.session.rollback()
            return False
        else:
            self.after_model_change(form, model, True)
        return model

    def update_model(self, form, model):
        try:
            if hasattr(form, "new_password") and form.new_password:
                if form.new_password.data:
                    if form.new_password.data != form.confirm.data:
                        flash("New password and confirm password must match.")
                        return False
                    model.set_password(form.new_password.data)

            if hasattr(form, "staff") and form.staff:
                model.staff = form.staff.data

            if hasattr(form, "admin") and form.admin:
                model.admin = form.admin.data

            if hasattr(form, "active") and form.active:
                model.active = form.active.data

            if hasattr(form, "first_name") and form.first_name:
                model.first_name = form.first_name.data

            if hasattr(form, "last_name") and form.last_name:
                model.last_name = form.last_name.data

            self._on_model_change(form, model, False)
            self.session.commit()
        except Exception as ex:
            if not self.handle_view_exception(ex):
                flash(gettext("Failed to create record. %(error)s", error=str(ex)))
            self.session.rollback()
            return False
        else:
            self.after_model_change(form, model, False)
        return True

    def after_model_change(self, form, model, is_created):
        Product.reindex()


class OrderManageAdminView(StaffModelView):
    column_list = (
        "id",
        "status",
        "contact",
    )
    column_filters = ("status",)
    column_sortable_list = ("status",)
    column_searchable_list = (
        "id",
        "contact",
    )
    column_editable_list = ("status",)
    form_edit_rules = (
        "status",
        "billing_address1",
        "billing_address2",
        "billing_city",
        "billing_state",
        "billing_zip",
        "shipping_address1",
        "shipping_address2",
        "shipping_city",
        "shipping_state",
        "shipping_zip",
        "contact",
        "order_lines",
    )

    def __init__(self, *args, **kwargs):
        self.inline_models = kwargs.pop("inline_models")
        super().__init__(*args, **kwargs)


# class AddressAdminView(StaffModelView):
#     column_list = (
#         "name",
#         "address1",
#         "city",
#         "country",
#         "zip_code",
#     )
#     column_sortable_list = (
#         "name",
#         "city",
#         "country",
#     )
#     column_searchable_list = ("name",)

#     def scaffold_form(self):
#         self.form_choices = {"country": self.model.SUPPORTED_COUNTRIES}
#         return super().scaffold_form()


# class CartAdminView(StaffModelView):
#     form_rules = (
#         "user",
#         "status",
#         "cartlines",
#         rules.Header("Status Note"),
#         rules.HTML(
#             """
#                 <ul>
#                     <li>10 - Open</li>
#                     <li>20 - Submitted</li>
#                 </ul>
#             """
#         ),
#     )
#     column_list = (
#         "id",
#         "user",
#         "status",
#     )
#     column_filters = ("status",)
#     form_excluded_columns = ("cartlines",)
#     form_create_rules = form_rules
#     form_edit_rules = form_rules

#     def __init__(self, *args, **kwargs):
#         self.inline_models = kwargs.pop("inline_models")
#         super().__init__(*args, **kwargs)

#     def scaffold_form(self):
#         form_class = super().scaffold_form()
#         form_class.status = SelectField(choices=self.model.STATUSES, coerce=int)
#         return form_class


# class OrderAdminView(StaffModelView):
#     form_rules = (
#         "user",
#         "status",
#         rules.Header("Billing Info:"),
#         "billing_name",
#         "billing_address1",
#         "billing_address2",
#         "billing_city",
#         "billing_country",
#         "billing_zip_code",
#         rules.Header("Shipping Info:"),
#         "shipping_name",
#         "shipping_address1",
#         "shipping_address2",
#         "shipping_city",
#         "shipping_country",
#         "shipping_zip_code",
#         rules.Header("Contact Info:"),
#         "contact_email",
#         rules.Header("Order Item(s):"),
#         "orderlines",
#         rules.Header("Order Status Note:"),
#         rules.HTML(
#             """
#                 <ul>
#                     <li>10 - Open</li>
#                     <li>20 - Paid</li>
#                     <li>30 - Done</li>
#                 </ul>
#             """
#         ),
#         rules.Header("Order Line Status Note:"),
#         rules.HTML(
#             """
#                 <ul>
#                     <li>10 - New</li>
#                     <li>20 - Processing</li>
#                     <li>30 - Send</li>
#                     <li>40 - Done</li>
#                 </ul>
#             """
#         ),
#     )
#     column_list = (
#         "id",
#         "user",
#         "status",
#     )
#     column_filters = (
#         "status",
#         "shipping_country",
#         "date_created",
#         "date_updated",
#     )
#     form_create_rules = form_rules
#     form_edit_rules = form_rules

#     def __init__(self, *args, **kwargs):
#         self.inline_models = kwargs.pop("inline_models")
#         super().__init__(*args, **kwargs)

#     def scaffold_form(self):
#         form_class = super().scaffold_form()
#         form_class.status = SelectField(choices=self.model.STATUSES, coerce=int)
#         return form_class
