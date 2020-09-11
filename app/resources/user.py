from flask_restplus import Resource, fields, reqparse
from app import api, db
from app.models import User as UserModel, Cart as CartModel, Order as OrderModel
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_raw_jwt,
    get_jwt_identity,
    jwt_refresh_token_required,
    get_jti,
)
from flask import current_app as app, request, url_for, render_template, make_response
from app import redis_store
from app.utils import send_email
from uuid import uuid4
from . import INTERNAL_ERROR, NOT_FOUND_ERROR

EMAIL_TAKEN = "Email is already taken."
CREATE_USER_SUCCESS = (
    "Account is successfully created. Please check email for activation"
)
INVALID_CREDENTIAL = "Invalid credentials."
LOGGED_OUT = "User {} successfully logged out."
ACCESS_EXPIRE = app.config["JWT_ACCESS_TOKEN_EXPIRES"]
REFRESH_EXPIRE = app.config["JWT_REFRESH_TOKEN_EXPIRES"]
NOT_CONFIRMED_ERROR = "You have not confirmed registration, please check your email<{}>"
ACTIVATION_LINK_EXPIRED = "Your activation link is expired."

user_ns = api.namespace("user", description="User API")

UserRegisterSchema = user_ns.model(
    "UserRegisterSchema",
    {
        "first_name": fields.String(required=True),
        "last_name": fields.String(required=True),
        "email": fields.String(required=True),
        "password": fields.String(required=True),
    },
)

UserLoginSchema = user_ns.model(
    "UserLoginSchema",
    {"email": fields.String(required=True), "password": fields.String(required=True)},
)

TokenRefreshParser = reqparse.RequestParser()
TokenRefreshParser.add_argument("Authorization", required=True, location="headers")

AccessTokenRevokeParser = reqparse.RequestParser()
AccessTokenRevokeParser.add_argument("Authorization", required=True, location="headers")

RefreshTokenRevokeParser = reqparse.RequestParser()
RefreshTokenRevokeParser.add_argument(
    "Authorization", required=True, location="headers"
)


@user_ns.route("")
class User(Resource):
    @classmethod
    @user_ns.doc("create_user")
    @user_ns.expect(UserRegisterSchema)
    @user_ns.expect(200, CREATE_USER_SUCCESS)
    @user_ns.response(400, EMAIL_TAKEN)
    @user_ns.response(500, INTERNAL_ERROR)
    def post(cls):
        data = api.payload
        try:
            existed_user = UserModel.query.filter_by(email=data["email"]).first()
            if existed_user:
                return {"message": EMAIL_TAKEN}, 400
            new_user = UserModel(active=False, **data)
            db.session.add(new_user)
            db.session.commit()
            activation_id = uuid4().hex
            redis_store.object.set(
                activation_id, str(new_user.id), app.config["ACTIVATION_EXPIRES"]
            )
            activation_link = (
                request.url_root[:-1]
                + url_for(
                    "user_activation.user_activation", activation_id=activation_id
                )
                + f"?email={new_user.email}"
            )
            send_email(
                subject="Account Activation",
                sender=app.config["ADMIN"],
                recipients=[new_user.email,],
                text_body=render_template(
                    "email/account_activation.txt", link=activation_link
                ),
                html_body=render_template(
                    "email/account_activation.html", link=activation_link
                ),
            )
        except Exception as ex:
            print(ex)
            db.session.rollback()
            return {"message": INTERNAL_ERROR}, 500
        return {"message": CREATE_USER_SUCCESS}, 201


@user_ns.route("/login")
class UserLogin(Resource):
    @classmethod
    @user_ns.doc("login_user")
    @user_ns.expect(UserLoginSchema)
    @user_ns.response(401, INVALID_CREDENTIAL)
    @user_ns.response(400, NOT_CONFIRMED_ERROR)
    def post(cls):
        data = api.payload
        user = UserModel.query.filter_by(email=data["email"]).first()
        if user and user.check_password(data["password"]):
            if user.active:
                access_token = create_access_token(identity=user.id, fresh=True)
                refresh_token = create_refresh_token(user.id)

                access_jti = get_jti(encoded_token=access_token)
                refresh_jti = get_jti(encoded_token=refresh_token)
                cart = (
                    CartModel.query.filter_by(user_id=user.id)
                    .filter_by(status=CartModel.CartStatus.OPEN)
                    .all()
                )
                user_data = {
                    "user_id": user.id,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "email": user.email,
                    "active_cart_id": cart.id if cart else None,
                }

                # Store token jti in Redis with revoked set to false
                # also set the records to be automatically removed
                # shortly after the actual token exspirations
                redis_store.object.set(access_jti, "false", ACCESS_EXPIRE * 1.2)
                redis_store.object.set(refresh_jti, "false", REFRESH_EXPIRE * 1.2)
                return (
                    {
                        "access_token": access_token,
                        "refresh_token": refresh_token,
                        "user": user_data,
                    },
                    200,
                )
            return {"message": NOT_CONFIRMED_ERROR.format(user.email)}, 400

        return {"message": INVALID_CREDENTIAL}, 401


@user_ns.route("/refresh")
class TokenRefresh(Resource):
    @classmethod
    @jwt_refresh_token_required
    @user_ns.expect(TokenRefreshParser)
    def post(cls):
        current_user_id = get_jwt_identity()
        new_access_token = create_access_token(identity=current_user_id, fresh=False)
        access_jti = get_jti(encoded_token=new_access_token)
        redis_store.object.set(access_jti, "false", ACCESS_EXPIRE * 1.2)
        user = UserModel.query.get(current_user_id)
        cart = (
            CartModel.query.filter_by(user_id=user.id)
            .filter_by(status=CartModel.CartStatus.OPEN)
            .first()
        )
        user_data = {
            "user_id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "active_cart_id": cart.id if cart else None,
        }
        return {"access_token": new_access_token, "user": user_data}, 200


@user_ns.route("/revoke-access")
class UserLogout1(Resource):
    @classmethod
    @jwt_required
    @user_ns.expect(AccessTokenRevokeParser)
    def post(cls):
        jti = get_raw_jwt()["jti"]
        user_id = get_jwt_identity()
        redis_store.object.set(jti, "true", ACCESS_EXPIRE * 1.2)

        return {"message": LOGGED_OUT.format(user_id)}, 200


@user_ns.route("/revoke-refresh")
class UserLogout2(Resource):
    @classmethod
    @jwt_refresh_token_required
    @user_ns.expect(AccessTokenRevokeParser)
    def post(cls):
        jti = get_raw_jwt()["jti"]
        user_id = get_jwt_identity()
        redis_store.object.set(jti, "true", REFRESH_EXPIRE * 1.2)

        return {"message": LOGGED_OUT.format(user_id)}, 200


@user_ns.route("/<int:id>/orders")
class UserOrders(Resource):
    @classmethod
    @jwt_required
    def get(cls, id):
        user = UserModel.query.filter_by(id=id).first()
        orders = OrderModel.query.filter_by(user_id=user.id).all()

        return {"orders": orders}, 200
