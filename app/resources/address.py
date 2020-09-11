from flask_restplus import Resource, reqparse, fields
from app import api, db
from app.models import User as UserModel, Address as AddressModel
from . import NOT_FOUND_ERROR, INTERNAL_ERROR

""" Constants """
RESOURCE_NAME = "Address"
USER = "User"
ADDRESS_DELETED = "Address is successfully deleted."

# """ Address parser """
# _address_parser = reqparse.RequestParser()
# _address_parser.add_argument("name", required=True)
# _address_parser.add_argument("address1", required=True)
# _address_parser.add_argument("address2")
# _address_parser.add_argument("city", required=True)
# _address_parser.add_argument("country", required=True)
# _address_parser.add_argument("zip_code", required=True)

""" Address response model """
CreateUpdateAddressSchema = api.model(
    "CreateUpdateAddressSchema",
    {
        "id": fields.Integer,
        "name": fields.String,
        "address1": fields.String,
        "address2": fields.String,
        "city": fields.String,
        "country": fields.String,
        "zip_code": fields.String,
    },
)

AddressSchema = api.model(
    "AddressSchema",
    {
        "id": fields.Integer,
        "name": fields.String,
        "address1": fields.String,
        "address2": fields.String(default=""),
        "city": fields.String,
        "country": fields.String,
        "zip_code": fields.String,
    },
)

""" Create Namespace """
addresses_ns = api.namespace("addresses", description="Addresses API")
address_ns = api.namespace("address", description="Address API")


""" Addresses Resource """


@addresses_ns.route("/<int:user_id>", doc={"params": {"user_id": "id of a user"}})
class AddressList(Resource):
    @classmethod
    @addresses_ns.doc("list_addresses")
    @addresses_ns.marshal_list_with(AddressSchema)
    def get(cls, user_id):
        addresses = AddressModel.query.filter_by(user_id=user_id)
        return addresses, 200

    @classmethod
    @addresses_ns.doc("create_address")
    @addresses_ns.expect(CreateUpdateAddressSchema)
    @addresses_ns.response(500, INTERNAL_ERROR)
    @addresses_ns.response(404, NOT_FOUND_ERROR.format(USER + "{user_id}"))
    @addresses_ns.marshal_with(AddressSchema, code=201)
    def post(cls, user_id):
        user = UserModel.query.filter_by(active=True).filter_by(id=user_id).first()
        if not user:
            return {"message": NOT_FOUND_ERROR.format(f"{USER} {user_id}")}, 404
        try:
            data = api.payload
            address = AddressModel(**data)
            address.user = user
            db.session.add(address)
            db.session.commit()
        except Exception as ex:
            print(ex)
            db.session.rollback()
            return {"message": INTERNAL_ERROR}, 500
        return address, 201


""" Address Resource """


@address_ns.route(
    "/<int:address_id>", doc={"params": {"address_id": "id of a address"}}
)
class Address(Resource):
    @classmethod
    @address_ns.doc("get_address")
    @address_ns.response(404, NOT_FOUND_ERROR.format(RESOURCE_NAME + " {address_id}"))
    @addresses_ns.marshal_with(AddressSchema)
    def get(cls, address_id):
        address = AddressModel.query.get(address_id)
        if not address:
            return (
                {"message": NOT_FOUND_ERROR.format(f"{RESOURCE_NAME} {address_id}")},
                404,
            )
        return address, 200

    @classmethod
    @address_ns.doc("delete_address")
    @addresses_ns.response(500, INTERNAL_ERROR)
    @address_ns.response(404, NOT_FOUND_ERROR.format(RESOURCE_NAME + " {address_id}"))
    @addresses_ns.response(200, ADDRESS_DELETED)
    def delete(cls, address_id):
        address = AddressModel.query.get(address_id)
        if not address:
            return (
                {"message": NOT_FOUND_ERROR.format(f"{RESOURCE_NAME} {address_id}")},
                404,
            )
        try:
            db.session.delete(address)
            db.session.commit()
        except Exception as ex:
            print(ex)
            db.session.rollback()
            return {"message": INTERNAL_ERROR}, 500
        return {"message": ADDRESS_DELETED}, 200

    @classmethod
    @address_ns.doc("update_address")
    @addresses_ns.response(500, INTERNAL_ERROR)
    @address_ns.response(404, NOT_FOUND_ERROR.format(RESOURCE_NAME + " {address_id}"))
    @address_ns.marshal_with(AddressSchema)
    def patch(cls, address_id):
        address = AddressModel.query.get(address_id)
        if not address:
            return (
                {"message": NOT_FOUND_ERROR.format(f"{RESOURCE_NAME} {address_id}")},
                404,
            )
        data = api.payload
        try:
            db.session.add(address)
            address.name = data.get("name", address.name)
            address.address1 = data.get("address1", address.address1)
            address.address2 = data.get("address2", address.address2)
            address.city = data.get("city", address.city)
            address.country = data.get("country", address.country)
            address.zip_code = data.get("zip_code", address.zip_code)
            db.session.commit()
        except Exception as ex:
            print(ex)
            db.session.rollback()
            return {"message": INTERNAL_ERROR}, 500
        return address, 200
