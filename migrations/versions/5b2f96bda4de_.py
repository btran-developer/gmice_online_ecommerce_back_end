"""empty message

Revision ID: 5b2f96bda4de
Revises: 175dae9f0a12
Create Date: 2020-02-17 14:31:44.399674

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '5b2f96bda4de'
down_revision = '175dae9f0a12'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('cart_lines', 'quantity',
               existing_type=mysql.INTEGER(display_width=11),
               nullable=False)
    op.add_column('product_images', sa.Column('public_id', sa.String(length=50), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('product_images', 'public_id')
    op.alter_column('cart_lines', 'quantity',
               existing_type=mysql.INTEGER(display_width=11),
               nullable=True)
    # ### end Alembic commands ###
