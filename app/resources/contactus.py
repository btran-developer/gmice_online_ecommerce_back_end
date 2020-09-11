from flask_restplus import Resource, fields, reqparse
from app import api
from app.utils import send_email
from flask import current_app as app, render_template, request
from . import INTERNAL_ERROR

""" Constants """
EMAIL_SENT = "Email is sent to customer service."

# """ Message parser """
# _message_parser = reqparse.RequestParser()
# _message_parser.add_argument(
#     "user_email", required=True,
# )
# _message_parser.add_argument(
#     "message", required=True,
# )


""" Create namespace """
contactus_ns = api.namespace("contactus", description="Send message API")

ContactUsMessageSchema = contactus_ns.model(
    "ContactUsMessageSchema",
    {
        "user_name": fields.String(required=True),
        "user_email": fields.String(required=True),
        "subject": fields.String(required=True),
        "order_id": fields.String,
        "message": fields.String(required=True),
    },
)

""" Contactus Resource """


@contactus_ns.route("")
class Contactus(Resource):
    @classmethod
    @contactus_ns.doc("send_email_from_c_to_cs")
    @contactus_ns.response(500, INTERNAL_ERROR)
    @contactus_ns.response(200, EMAIL_SENT)
    @contactus_ns.expect(ContactUsMessageSchema)
    def post(cls):
        # data = _message_parser.parse_args()
        data = api.payload
        user_name = data.get("user_name")
        user_email = data.get("user_email")
        subject = data.get("subject")
        order_id = data.get("order_id")
        message = data.get("message")
        try:
            send_email(
                "Contact Us Message",
                sender=app.config["ADMIN"],
                recipients=[app.config["CUSTOMERSERVICE"]],
                text_body=render_template(
                    "email/contact_us_message.txt",
                    user_name=user_name,
                    user_email=user_email,
                    subject=subject,
                    order_id=order_id,
                    message=message,
                ),
                html_body=render_template(
                    "email/contact_us_message.html",
                    user_name=user_name,
                    user_email=user_email,
                    subject=subject,
                    order_id=order_id,
                    message=message,
                ),
            )
        except Exception as ex:
            print(ex)
            return {"message": INTERNAL_ERROR}
        return {"message": EMAIL_SENT}, 200
