from flask import Flask, current_app
from collections import Counter
from app.utils import get_or_create
from app import models, db
from werkzeug.utils import secure_filename
from flask_admin import form
from PIL import Image
from flask.cli import AppGroup
import click
import csv
import os
import re
import sys


app = current_app
mng_cli = AppGroup("mng")


@mng_cli.command("import-data", with_appcontext=True)
@click.argument("csvfile")
@click.argument("image_basedir")
def import_data(csvfile, image_basedir):
    print("importing data")
    counter = Counter()

    with open(csvfile, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            product, product_created = get_or_create(
                models.Product, db.session, name=row["name"], price=row["price"]
            )
            product.description = row["description"]

            brand, brand_created = get_or_create(
                models.Brand, db.session, name=row["brand"]
            )
            product.brand = brand
            counter["brands"] += 1
            if brand_created:
                counter["brands_created"] += 1

            for import_tag in row["tags"].split("|"):
                tag, tag_created = get_or_create(
                    models.ProductTag, db.session, name=import_tag
                )
                product.tags.append(tag)
                counter["tags"] += 1
                if tag_created:
                    counter["tags_created"] += 1

            secured_filename_with_ext = secure_filename(row["image_filename"])
            with open(os.path.join(image_basedir, row["image_filename"]), "rb") as f:
                image_url = os.path.join(
                    app.config["UPLOAD_FOLDER"], secured_filename_with_ext
                )
                thumbnail_url = os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    form.thumbgen_filename(secured_filename_with_ext),
                )
                full_image = Image.open(f)
                full_image = full_image.convert("RGB")
                full_image.save(os.path.abspath(image_url))
                thumbnail_image = Image.open(f)
                thumbnail_image = thumbnail_image.convert("RGB")
                thumbnail_image.thumbnail(app.config["THUMBNAIL_SIZE"], Image.ANTIALIAS)
                thumbnail_image.save(os.path.abspath(thumbnail_url))
                image = models.ProductImage(
                    image_url=image_url, thumbnail_url=thumbnail_url
                )
                image.product = product
                db.session.add(image)
                db.session.commit()
                counter["images"] += 1

            db.session.add(product)
            db.session.commit()
            counter["products"] += 1
            if product_created:
                counter["products_created"] += 1

    print(
        "Products processed=%d (created=%d)"
        % (counter["products"], counter["products_created"])
    )
    print(
        "Brands processed=%d (created=%d)"
        % (counter["brands"], counter["brands_created"])
    )
    print("Tags processed=%d (created=%d)" % (counter["tags"], counter["tags_created"]))
    print("Images processed=%d" % counter["images"])


@mng_cli.command("create-superuser", with_appcontext=True)
def create_superuser():
    email = click.prompt("Email")
    if not re.match(r"(\w+[.|\w])*@(\w+[.])*\w+", email):
        sys.exit("\nCould not create user: Invalid E-Mail addresss")
    if models.User.query.filter_by(email=email).scalar() is not None:
        sys.exit(f"\n{email} is taken")
    password = click.prompt("Password", hide_input=True, confirmation_prompt=True)
    user = models.User(email=email, password=password, admin=True)
    db.session.add(user)
    db.session.commit()
    print("Superuser is created")
