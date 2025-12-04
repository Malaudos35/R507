"""initial

Revision ID: 0001_initial
Revises: 
Create Date: 2025-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'ordinateur',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('mac', sa.String(), nullable=False, unique=True),
        sa.Column('ip', sa.String(), nullable=False, unique=True),
        sa.Column('hostname', sa.String(), nullable=True),
        sa.Column('taille_disque', sa.Integer(), nullable=False),
        sa.Column('os', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('ram', sa.Float(), nullable=True),
        sa.Column('joignable', sa.Boolean(), nullable=True),
    )

def downgrade():
    op.drop_table('ordinateur')
