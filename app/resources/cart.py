from flask_restplus import Resource, reqparse, fields
from app import api, models, db
from . import NOT_FOUND_ERROR
from app.utils import get_or_create
import ast

""" Constants """
RESOURCE_NAME = "Cart"

""" Cart Request Parsers """
# _cart_parser = reqparse.RequestParser()
# _cart_parser.add_argument(
#     "use_uid", type=int, required=False, choices=[0, 1], default=0
# )
# _cart_parser.add_argument("cartlines", action="append", required=False)
_cart_parser = reqparse.RequestParser()
_cart_parser.add_argument("user_id", type=int, required=False)
_cart_parser.add_argument("cart_id", type=int, required=False)
_cart_parser.add_argument("cart_lines", action="append", type=dict, required=False)


""" Cart Response Model """
CartlineSchema = api.model(
    "CartlineSchema",
    {
        "id": fields.Integer,
        "product": fields.Nested(
            api.model(
                "Cartline_ProductSchema",
                {
                    "id": fields.Integer,
                    "name": fields.String,
                    "brand": fields.String,
                    "price": fields.Fixed(decimals=2),
                    "images": fields.Nested(
                        api.model(
                            "Cartline_ImageSchema",
                            {
                                "image_url": fields.String,
                                "thumbnail_url": fields.String,
                                "main": fields.Boolean,
                            },
                        )
                    ),
                },
            )
        ),
        "quantity": fields.Integer,
    },
)

CartSchema = api.model(
    "CartSchema",
    {
        "id": fields.Integer,
        "status": fields.String,
        "cart_lines": fields.Nested(
            api.model(
                "Cart_CartLineSchema",
                {
                    "id": fields.Integer,
                    "quantity": fields.Integer,
                    "product": fields.Nested(
                        api.model(
                            "Cart_ProductSchema",
                            {
                                "id": fields.Integer,
                                "name": fields.String,
                                "brand": fields.String,
                                "price": fields.Fixed(decimals=2),
                                "images": fields.Nested(
                                    api.model(
                                        "Cart_ImageSchema",
                                        {
                                            "image_url": fields.String,
                                            "thumbnail_url": fields.String,
                                            "main": fields.Boolean,
                                        },
                                    )
                                ),
                            },
                        )
                    ),
                },
            )
        ),
    },
)

""" Create Namespace """
cart_ns = api.namespace("cart", description="Cart API")

""" Cart Resource """


# @cart_ns.route("")
# class CartCreate(Resource):
#     @classmethod
#     @cart_ns.doc("create_or_update_cart")
#     @cart_ns.expect(_cart_parser)
#     def post(cls):
#         data = _cart_parser.parse_args()
#         user_id = data.get("user_id")
#         cart_id = data.get("cart_id")
#         cartlines = data.get("cart_lines")

#         if not cart_id:
#             cart = models.Cart()
#         else:
#             cart = models.Cart.query.get(cart_id)
#             if not cart:
#                 return api.abort(404, NOT_FOUND_ERROR.format(RESOURCE_NAME))

#         for cartline in cartlines:
#             product = models.Product.query.get(cartline["product_id"])
#             if not product:
#                 return api.abort(
#                     404, NOT_FOUND_ERROR.format(f"Product {cartline.product_id}")
#                 )
#             new_cartline, cartline_created = get_or_create(
#                 models.CartLine, db.session, product_id=product.id, cart_id=cart.id
#             )
#             new_cartline.product = product
#             new_cartline.quantity = cartline["quantity"]
#             cart.cart_lines.append(new_cartline)
#         if user_id:
#             cart.user_id = user_id
#         db.session.add(cart)
#         db.session.commit()
#         return {"cart_id": cart.id}, 200


# # @cart_ns.route("", defaults={"id": 0})
# @cart_ns.route("/<int:id>")
# class Cart(Resource):
#     @classmethod
#     @cart_ns.doc("get_cart")
#     @cart_ns.param("id", "cart or user id")
#     @cart_ns.expect(_cart_parser)
#     @cart_ns.marshal_with(CartSchema, envelope="cart")
#     def get(cls, id):
#         data = _cart_parser.parse_args()

#         cart_query = models.Cart.query.filter_by(id=id)

#         cart = cart_query.filter_by(status=models.Cart.CartStatus.OPEN).first()

#         if not cart:
#             return api.abort(404, NOT_FOUND_ERROR.format(RESOURCE_NAME))

#         return cart, 200

#     @classmethod
#     @cart_ns.doc("delete_line_from_cart")
#     @cart_ns.param("id", "cart id")
#     @cart_ns.response(404, NOT_FOUND_ERROR.format("Cart {id}"))
#     def delete(cls, id):
#         cart = models.Cart.query.get(id)
#         if not cart:
#             return api.abort(404, NOT_FOUND_ERROR.format(f"Cart {id}"))
#         db.session.delete(cart)
#         db.session.commit()
#         return "", 204

#     @classmethod
#     @cart_ns.doc("merge_carts")
#     @cart_ns.param("id", "anonymous cart id")
#     def put(cls, id):
#         data = _cart_parser.parse_args()
#         cart_id = data.get("cart_id")

#         anonymous_cart = models.Cart.query.get(id)
#         cart = models.Cart.query.get(cart_id)
#         if not anonymous_cart or not cart:
#             not_found_cart_id = id if anonymous_cart == None else cart_id
#             return api.abort(
#                 404, NOT_FOUND_ERROR.format(f"{RESOURCE_NAME} {not_found_cart_id}")
#             )
#         for cartline in anonymous_cart.cart_lines:
#             existed_cartline = (
#                 models.CartLine.query.filter_by(product_id=cartline.product_id)
#                 .filter_by(cart_id=cart.id)
#                 .first()
#             )
#             if existed_cartline:
#                 existed_cartline.quantity += cart_line.quantity
#                 db.session.add(existed_cartline)
#             else:
#                 cartline.cart = cart
#                 db.session.add(cartline)

#         try:
#             db.session.delete(anonymous_cart)
#             db.session.commit()
#         except Exception as ex:
#             print(ex)
#             db.session.rollback()
#             return api.abort(500, ex)
#         return {"message": "merge successfully"}, 200

#     @classmethod
#     @cart_ns.doc("assign_user_to_cart")
#     @cart_ns.param("id", "cart id")
#     def post(cls, id):
#         data = _cart_parser.parse_args()
#         user_id = data.get("user_id")

#         user = models.User.query.get(user_id)
#         cart = models.Cart.query.get(id)
#         if not user:
#             return api.abort(404, NOT_FOUND_ERROR.format(f"user {user_id}"))
#         if not cart:
#             return api.abort(404, NOT_FOUND_ERROR.format(f"{RESOURCE_NAME} {id}"))
#         cart.user_id = user_id
#         db.session.add(cart)
#         db.session.commit()
#         return {"message": "sucessfully bind user to cart"}, 200


# @classmethod
# @cart_ns.doc("update_cart")
# @cart_ns.param("id", "cart or user id")
# @cart_ns.expect(_cart_parser)
# @cart_ns.marshal_with(CartSchema, envelope="cart")
# def patch(cls, id):
#     data = _cart_parser.parse_args()
#     use_uid = data["use_uid"]
#     cartlines = [ast.literal_eval(cartline) for cartline in data["cartlines"]]

#     if use_uid == 1:
#         cart_query = models.Cart.query.filter_by(user_id=id)
#     else:
#         cart_query = models.Cart.query.filter_by(id=id)

#     cart = cart_query.filter_by(status=models.Cart.OPEN).first()

#     if not cart:
#         return api.abort(404, NOT_FOUND_ERROR.format(RESOURCE_NAME))

#     for line in cartlines:
#         cartline = models.CartLine.query.get(line["id"])
#         try:
#             # add new line to cart
#             if not cartline:
#                 product_id = line["product"]["id"]
#                 product = models.Product.query.get(product_id)
#                 if not product:
#                     return api.abort(
#                         404, NOT_FOUND_ERROR.format(f"Product {product_id}")
#                     )
#                 cartline = models.CartLine()
#                 cartline.cart = cart
#                 cartline.product = product
#             # cartline exists, update quantity
#             cartline.quantity = line["quantity"]
#             db.session.add(cartline)
#             db.session.commit()
#         except Exception as ex:
#             print(ex)
#             db.session.rollback()
#             return api.abort(500, ex)
#     return cart, 200

_create_cart_parser = reqparse.RequestParser()
_create_cart_parser.add_argument("user_id", required=True, type=int)


@cart_ns.route("")
class CartCreate(Resource):
    @classmethod
    def post(cls):
        data = _create_cart_parser.parse_args()

        new_cart = models.Cart()
        if data["user_id"] > 0:
            user_id = data["user_id"]
            user = models.User.query.get(user_id)
            if user:
                new_cart.user = user
            else:
                return api.abort(404, NOT_FOUND_ERROR.format(f"User {user_id}"))
        try:
            db.session.add(new_cart)
            db.session.commit()
        except Exception as ex:
            db.session.rollback()
            return api.abort(500, ex)
        return {"cart_id": new_cart.id}, 200


_merge_carts_parser = reqparse.RequestParser()
_merge_carts_parser.add_argument("from_cart_id", required=True, type=int)
_merge_carts_parser.add_argument("to_cart_id", required=False, type=int)
_merge_carts_parser.add_argument("user_id", required=True, type=int)


@cart_ns.route("/merge")
class CartMerge(Resource):
    @classmethod
    @cart_ns.marshal_with(CartSchema, envelope="cart")
    def post(cls):
        data = _merge_carts_parser.parse_args()
        from_cart_id = data.get("from_cart_id")
        to_cart_id = data.get("to_cart_id")
        user_id = data.get("user_id")
        from_cart = (
            models.Cart.query.filter_by(status=models.Cart.CartStatus.OPEN)
            .filter_by(id=from_cart_id)
            .first()
        )
        to_cart = (
            models.Cart.query.filter_by(status=models.Cart.CartStatus.OPEN)
            .filter_by(id=to_cart_id)
            .first()
        )
        user = models.User.query.filter_by(id=user_id).filter_by(active=True).first()

        if not from_cart:
            return api.abort(404, NOT_FOUND_ERROR.format("From cart"))

        if not user:
            return api.abort(404, NOT_FOUND_ERROR.format(f"User {user_id}"))

        if not to_cart:
            to_cart = from_cart
            to_cart.user = user
            db.session.add(to_cart)
        else:
            for line in from_cart.cart_lines:
                final_cart_line = (
                    models.CartLine.query.filter_by(cart_id=to_cart_id)
                    .filter_by(product_id=line.product_id)
                    .first()
                )
                if not final_cart_line:
                    final_cart_line = line
                    final_cart_line.cart = to_cart
                else:
                    final_cart_line.quantity += line.quantity
                db.session.add(final_cart_line)

        try:
            db.session.commit()
        except Exception as ex:
            db.session.rollback()
            return api.abort(500, ex)
        return to_cart, 200


_add_to_cart_parser = reqparse.RequestParser()
_add_to_cart_parser.add_argument("product_id", required=True, type=int)

_update_cart_parser = reqparse.RequestParser()
_update_cart_parser.add_argument("cartline_id", required=True, type=int)
_update_cart_parser.add_argument("quantity", required=True, type=int)

_delete_cart_parser = reqparse.RequestParser()
_delete_cart_parser.add_argument("cartline_id", required=True, type=int)


@cart_ns.route("/<int:id>")
class CartLineOperations(Resource):
    @classmethod
    @cart_ns.marshal_with(CartlineSchema, envelope="cartline")
    def patch(cls, id):
        cart = models.Cart.query.get(id)
        data = _add_to_cart_parser.parse_args()
        product_id = data["product_id"]
        if not cart:
            return api.report(404, NOT_FOUND_ERROR.format(f"Cart {id}"))

        cartline = (
            models.CartLine.query.filter_by(cart_id=id)
            .filter_by(product_id=product_id)
            .first()
        )
        if cartline:
            cartline.quantity += 1
        else:
            product = models.Product.query.get(product_id)
            if not product:
                return api.abort(404, NOT_FOUND_ERROR.format(f"Product {product_id}"))
            cartline = models.CartLine()
            cartline.product = product
            cartline.cart = cart
            cartline.quantity = 1
        try:
            db.session.add(cart)
            db.session.commit()
        except Exception as ex:
            db.session.rollback()
            print(ex)
            return api.abort(500, ex)
        return cartline, 200

    @classmethod
    @cart_ns.marshal_with(CartlineSchema, envelope="cartline")
    def put(cls, id):
        cart = models.Cart.query.get(id)
        data = _update_cart_parser.parse_args()
        cartline_id = data["cartline_id"]
        quantity = data["quantity"]

        if not cart:
            return api.abort(404, NOT_FOUND_ERROR.format(f"Cart {id}"))
        cartline = (
            models.CartLine.query.filter_by(id=cartline_id)
            .filter_by(cart_id=id)
            .first()
        )
        if not cartline:
            return api.abort(404, NOT_FOUND_ERROR.format(f"Cartline {cartline_id}"))
        if quantity <= 0:
            return api.abort(400, "0 or negative quantity is not allowed")
        cartline.quantity = quantity
        try:
            db.session.add(cartline)
            db.session.commit()
        except Exception as ex:
            db.session.rollback()
            print(ex)
            return api.abort(500, ex)
        return cartline, 200

    @classmethod
    def delete(cls, id):
        cart = models.Cart.query.get(id)
        data = _delete_cart_parser.parse_args()
        cartline_id = data["cartline_id"]

        if not cart:
            return api.abort(404, NOT_FOUND_ERROR.format(f"Cart {id}"))
        cartline = (
            models.CartLine.query.filter_by(id=cartline_id)
            .filter_by(cart_id=id)
            .first()
        )
        if not cartline:
            return api.abort(404, NOT_FOUND_ERROR.format(f"Cartline {cartline_id}"))
        try:
            db.session.delete(cartline)
            db.session.commit()
        except Exception as ex:
            db.session.rollback()
            print(ex)
            return api.abort(500, ex)
        return {"cartline_id": cartline_id}, 200

    @classmethod
    @cart_ns.marshal_with(CartSchema, envelope="cart")
    def get(cls, id):
        # cart = models.Cart.query.get(id)
        cart = (
            models.Cart.query.filter_by(id=id)
            .filter_by(status=models.Cart.CartStatus.OPEN)
            .first()
        )

        if not cart:
            return api.abort(404, NOT_FOUND_ERROR.format(f"Cart {id}"))
        return cart, 200
