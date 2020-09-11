from flask import Blueprint, render_template, request, url_for, current_app as app
from flask_restplus import reqparse
from uuid import uuid4
import urllib
from app import redis_store, db
from app.utils import send_email
from app.models import User as UserModel
from app.resources import INTERNAL_ERROR, NOT_FOUND_ERROR

user_activation_bp = Blueprint("user_activation", __name__)

ACTIVATION_LINK_EXPIRED = "Activation Link Expired"
INTERNAL_ERROR_MSG = "Something went wrong..."
USER_NOT_FOUND_MSG = "The user for link does not exist..."

query_parser = reqparse.RequestParser()
query_parser.add_argument("email", required=True)


@user_activation_bp.route("/<activation_id>")
def user_activation(activation_id):
    email = query_parser.parse_args()["email"]
    user_id = redis_store.object.get(activation_id)
    if not user_id:
        query_str = urllib.parse.urlencode({"email": email})
        new_link = (
            request.url_root[:-1]
            + url_for("user_activation.resend_user_activation")
            + f"?{query_str}"
        )
        return render_template(
            "activation_expired.html", title=ACTIVATION_LINK_EXPIRED, new_link=new_link
        )
    user_id = int(user_id)
    user = UserModel.query.get(user_id)
    if not user:
        return render_template(
            "error.html",
            title=NOT_FOUND_ERROR.format("User"),
            message=USER_NOT_FOUND_MSG,
        )

    user.active = True
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as ex:
        print(ex)
        db.session.rollback()
        return render_template(
            "error.html", title=INTERNAL_ERROR[:-1], message=INTERNAL_ERROR_MSG
        )
    return render_template("activation_page.html")


@user_activation_bp.route("/resend-activation")
def resend_user_activation():
    email = query_parser.parse_args()["email"]
    email = urllib.parse.unquote(email)
    user = UserModel.query.filter_by(email=email).first()
    activation_id = uuid4().hex
    redis_store.object.set(
        activation_id, str(user.id), app.config["ACTIVATION_EXPIRES"]
    )
    activation_link = (
        request.url_root[:-1]
        + url_for("user_activation.user_activation", activation_id=activation_id)
        + f"?email={email}"
    )
    send_email(
        subject="Account Activation",
        sender=app.config["ADMIN"],
        recipients=[user.email,],
        text_body=render_template("email/account_activation.txt", link=activation_link),
        html_body=render_template(
            "email/account_activation.html", link=activation_link
        ),
    )
    return render_template("new_activation_sent.html", title="Activation Resent")
