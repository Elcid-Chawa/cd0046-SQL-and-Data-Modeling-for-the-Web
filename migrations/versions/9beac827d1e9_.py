"""empty message

Revision ID: 9beac827d1e9
Revises: 6fa0d2cae5ba
Create Date: 2022-07-28 06:50:12.132031

"""
from email.policy import default
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9beac827d1e9'
down_revision = '6fa0d2cae5ba'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Artist', sa.Column('seeking_description', sa.Text(), nullable=True))
    op.add_column('Artist', sa.Column('seeking_venue', sa.Boolean(), nullable=False, default=sa.text('false')))
    op.alter_column('Artist', 'seeking_venue',
               existing_type=sa.BOOLEAN(),
               nullable=False,
               existing_server_default=sa.text('false'))
    op.add_column('Artist', sa.Column('website_link', sa.String(length=500), nullable=True))
    op.add_column('Venue', sa.Column('genres', sa.String(length=120), nullable=True))
    op.add_column('Venue', sa.Column('seeking_description', sa.Text(), nullable=True))
    op.add_column('Venue', sa.Column('seeking_talent', sa.Boolean(), nullable=False, default=sa.text('false')))
    op.add_column('Venue', sa.Column('website_link', sa.String(length=500), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('Venue', 'website_link')
    op.drop_column('Venue', 'seeking_talent')
    op.drop_column('Venue', 'seeking_description')
    op.drop_column('Venue', 'genres')
    op.drop_column('Artist', 'website_link')
    op.drop_column('Artist', 'seeking_venue')
    op.drop_column('Artist', 'seeking_desciption')
    # ### end Alembic commands ###
