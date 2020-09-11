from flask_restplus import Resource, fields
from app import api, models, db
from datetime import datetime

""" Constants """
RESOURCE_NAME = "Order"

""" Create Namspace """
order_ns = api.namespace("order", description="Order API")

""" Request Body Schema """
OrderRequestSchema = order_ns.model(
    "OrderRequestSchema",
    {
        "cart_id": fields.Integer,
        "user_id": fields.Integer,
        "billing_address1": fields.String,
        "billing_address2": fields.String,
        "billing_city": fields.String,
        "billing_state": fields.String,
        "billing_zip": fields.Integer,
        "shipping_address1": fields.String,
        "shipping_address2": fields.String,
        "shipping_city": fields.String,
        "shipping_state": fields.String,
        "shipping_zip": fields.Integer,
        "contact": fields.String,
        "payment_token": fields.String,
    },
)

""" Order Resource """


@order_ns.route("")
class OrderCreate(Resource):
    @classmethod
    @order_ns.doc("create_order")
    @order_ns.expect(OrderRequestSchema)
    def post(cls):
        data = api.payload

        new_order = models.Order()
        if data["cart_id"] > 0:
            cart_id = data["cart_id"]
            cart = models.Cart.query.get(cart_id)
            if cart:
                for cartline in cart.cart_lines:
                    new_orderline = models.OrderLine()
                    new_orderline.order = new_order
                    new_orderline.product_id = cartline.product_id
                    new_orderline.quantity = cartline.quantity
                    db.session.add(new_orderline)

            if data["user_id"] > 0:
                user_id = data["user_id"]
                user = models.User.query.get(user_id)
                if user:
                    new_order.user = user

            new_order.billing_address1 = data["billing_address1"]
            new_order.billing_address2 = data["billing_address2"]
            new_order.billing_city = data["billing_city"]
            new_order.billing_state = data["billing_state"]
            new_order.billing_zip = data["billing_zip"]
            new_order.shipping_address1 = data["shipping_address1"]
            new_order.shipping_address2 = data["shipping_address2"]
            new_order.shipping_city = data["shipping_city"]
            new_order.shipping_state = data["shipping_state"]
            new_order.shipping_zip = data["shipping_zip"]
            new_order.contact = data["contact"]
            new_order.date_created = datetime.now()
            cart.status = models.Cart.CartStatus.CLOSE
        else:
            return api.abort(400)

        try:
            db.session.add(new_order)
            db.session.add(cart)
            db.session.commit()
        except Exception as ex:
            db.session.rollback()
            return api.abort(500, ex)
        return {"order_id": new_order.id}, 200
