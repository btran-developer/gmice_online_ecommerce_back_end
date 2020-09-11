from flask_restplus import Resource, fields
from app import api
from app.models import ProductTag as TagModel
from . import INTERNAL_ERROR

""" Tag Response Schema """
TagSchema = api.model(
    "TagSchema",
    {"name": fields.String, "slug": fields.String, "total_products": fields.Integer},
)

""" Create Namespace """
tags_ns = api.namespace("tags", description="Tag API")

""" Tags Resource """


@tags_ns.route("")
class Tags(Resource):
    @classmethod
    @tags_ns.doc("list_tags")
    @tags_ns.marshal_with(TagSchema, envelope="tag_list")
    def get(cls):
        try:
            tags = TagModel.query.filter_by(active=True).all()
        except Exception as ex:
            return {"message": INTERNAL_ERROR}, 500
        return tags
