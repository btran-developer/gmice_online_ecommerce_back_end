from flask_restplus import Resource, reqparse, fields
from app import api
from app.models import (
    Product as ProductModel,
    ProductTag as TagModel,
    product_and_tag_assoc as ProductTagAssoc,
)
from . import NOT_FOUND_ERROR

""" Constants """
RESOURCE_NAME = "Product"

""" Pagination parser """
_products_parser = reqparse.RequestParser()
_products_parser.add_argument("page", type=int, required=False)
_products_parser.add_argument(
    "per_page", type=int, required=False, choices=[5, 10, 20, 30, 40], default=10
)
_products_parser.add_argument("tags", action="append", required=False)

""" Product response model """
ProductSchema = api.model(
    "ProductSchema",
    {
        "id": fields.Integer,
        "name": fields.String,
        "brand": fields.Nested(
            api.model(
                "Product_BrandSchema", {"name": fields.String, "slug": fields.String}
            )
        ),
        "specifications": fields.Nested(
            api.model(
                "Product_SpecificationsSchema",
                {
                    "lighting_type": fields.String,
                    "minimum_sensitivity": fields.String,
                    "maximum_sensitivity": fields.String,
                    "total_buttons": fields.Integer,
                    "total_programmable_buttons": fields.Integer,
                    "wireless": fields.Boolean,
                    "height": fields.String,
                    "width": fields.String,
                    "weight": fields.String,
                },
            )
        ),
        "features": fields.Nested(
            api.model(
                "Product_FeatureSchema",
                {"title": fields.String, "description": fields.String},
            )
        ),
        "tags": fields.Nested(
            api.model(
                "Product_TagSchema", {"name": fields.String, "slug": fields.String},
            )
        ),
        "images": fields.Nested(
            api.model(
                "Product_ImageSchema",
                {
                    "image_url": fields.String,
                    "thumbnail_url": fields.String,
                    "main": fields.Boolean,
                },
            )
        ),
        "description": fields.String,
        "price": fields.Fixed(decimals=2),
        "slug": fields.String,
        "in_stock": fields.Boolean,
    },
)

""" Create Namespace """
products_ns = api.namespace("products", description="Products API")
product_ns = api.namespace("product", description="Product API")

""" Product List Resource """


@products_ns.route("")
class ProductList(Resource):
    @classmethod
    @products_ns.doc("list_products")
    @products_ns.expect(_products_parser)
    @products_ns.marshal_list_with(ProductSchema, envelope="product_list")
    def get(cls):
        data = _products_parser.parse_args()
        page = data.get("page")
        per_page = data.get("per_page")
        tags = data.get("tags")

        products_query = ProductModel.query

        if tags and len(tags) > 0:
            products_query = (
                products_query.join(ProductTagAssoc)
                .join(TagModel)
                .filter(TagModel.slug.in_(tags))
            )

        if page:
            products = (
                products_query.filter_by(active=True)
                .paginate(page, per_page, False)
                .items
            )
        else:
            products = products_query.filter_by(active=True).all()

        return products, 200


""" Product Resource """


@product_ns.route("/<string:slug>", doc={"params": {"slug": "slug name"}})
class Product(Resource):
    @classmethod
    @product_ns.doc("get_product")
    @product_ns.response(404, NOT_FOUND_ERROR.format(RESOURCE_NAME))
    @product_ns.marshal_with(ProductSchema, envelope="product_item")
    def get(cls, slug):
        product = ProductModel.query.filter_by(slug=slug).first()
        if not product:
            return api.abort(404, NOT_FOUND_ERROR.format(RESOURCE_NAME))
        return product, 200
