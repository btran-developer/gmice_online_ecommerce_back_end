import os
from datetime import timedelta
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))

load_dotenv(os.path.join(basedir, ".env"))


class Config(object):
    # Database settings:
    # SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(basedir, "data.db")
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:Billchan1995@localhost:3306/gmice"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Redis settings:
    REDIS_HOST = "localhost"
    REDIS_PORT = 6379
    # General settings:
    PROPAGATE_EXCEPTIONS = True
    SECRET_KEY = os.environ.get("SECRET_KEY")
    UPLOAD_FOLDER = "uploads"
    ALLOWED_IMAGE_EXTENSIONS = {"jpeg", "png", "jpg", "gif"}
    THUMBNAIL_SIZE = (65, 45)
    ADMIN = "admin@domain.com"
    CUSTOMERSERVICE = "redbill1995@gmail.com"
    ACTIVATION_EXPIRES = timedelta(minutes=30)
    # Flask-restplus settings:
    BUNDLE_ERRORS = True
    # Mail settings:
    # MAIL_SERVER = "localhost"
    # MAIL_PORT = 8025
    MAIL_SERVER = "smtp.mailgun.org"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = "postmaster@sandbox764707a6a9524473a1a12af7503bb643.mailgun.org"
    MAIL_PASSWORD = "0e7ae569706d2e562b9d8ba58e7045da-6f4beb0a-79043e81"
    # Jwt settings:
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
    JWT_BLACKLIST_ENABLED = True
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    # Elastic Search
    ELASTICSEARCH_URL = os.environ.get("ELASTICSEARCH_URL")
    ELASTICSEARCH_API_KEY = os.environ.get("ELASTICSEARCH_API_KEY")
    # Cloudinary
    CLOUDINARY_URL = os.environ.get("CLOUDINARY_URL")
