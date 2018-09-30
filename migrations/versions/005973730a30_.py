"""empty message

Revision ID: 005973730a30
Revises: c70f414cdfcb
Create Date: 2018-09-29 16:31:26.137602

"""
from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils



# revision identifiers, used by Alembic.
revision = '005973730a30'
down_revision = 'c70f414cdfcb'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('phone_numbers', sa.Column('nickname', sa.String(length=30), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('phone_numbers', 'nickname')
    # ### end Alembic commands ###
