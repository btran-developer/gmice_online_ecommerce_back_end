"""added user foreign key to order

Revision ID: a21fde1d5af3
Revises: 2192034a345e
Create Date: 2020-05-21 20:29:33.659054

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a21fde1d5af3'
down_revision = '2192034a345e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('orders', sa.Column('user_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'orders', 'users', ['user_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'orders', type_='foreignkey')
    op.drop_column('orders', 'user_id')
    # ### end Alembic commands ###