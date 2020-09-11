from flask_restplus import Resource, fields
from app.models import ProductBrand as BrandModel
from app import api
from . import INTERNAL_ERROR

brand_ns = api.namespace("brands", description="Brand API")

BrandSchema = brand_ns.model(
    "BrandSchema",
    {"name": fields.String, "slug": fields.String, "total_products": fields.Integer},
)


@brand_ns.route("")
class Brand(Resource):
    @classmethod
    @brand_ns.doc("list_brands")
    @brand_ns.marshal_list_with(BrandSchema, envelope="brand_list")
    def get(cls):
        try:
            brands = BrandModel.query.all()
        except Exception as ex:
            print(ex)
            return {"message": INTERNAL_ERROR}, 500
        return brands, 200
