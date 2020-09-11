from flask import Blueprint

api_blueprint = Blueprint("api", __name__, url_prefix="/api")

""" Shared constant for resources """
NOT_FOUND_ERROR = "{} not found."
INTERNAL_ERROR = "Internal server error."
