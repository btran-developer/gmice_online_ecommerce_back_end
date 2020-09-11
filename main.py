from app import createApp, db, models
from app.management.commands import mng_cli

app = createApp()

app.cli.add_command(mng_cli)


@app.shell_context_processor
def make_shell_context():
    return {"db": db, "Product": models.Product, "ProductImage": models.ProductImage, "User": models.User}
