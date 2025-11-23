"""Add hotel details fields

Revision ID: 0002_add_hotel_details_fields
Revises: 0001_initial_schema
Create Date: 2025-11-07 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0002_add_hotel_details_fields'
down_revision = '0001_initial_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add property_overview and policies to hotels table
    op.add_column('hotels', sa.Column('property_overview', sa.Text(), nullable=True))
    op.add_column('hotels', sa.Column('policies', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='{}'))
    
    # Add description and images to rooms table
    op.add_column('rooms', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('rooms', sa.Column('images', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='[]'))
    
    # Add title, pros, cons, and category_ratings to reviews table
    op.add_column('reviews', sa.Column('title', sa.String(length=500), nullable=True))
    op.add_column('reviews', sa.Column('pros', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='[]'))
    op.add_column('reviews', sa.Column('cons', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='[]'))
    op.add_column('reviews', sa.Column('category_ratings', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='{}'))


def downgrade() -> None:
    # Remove columns from reviews table
    op.drop_column('reviews', 'category_ratings')
    op.drop_column('reviews', 'cons')
    op.drop_column('reviews', 'pros')
    op.drop_column('reviews', 'title')
    
    # Remove columns from rooms table
    op.drop_column('rooms', 'images')
    op.drop_column('rooms', 'description')
    
    # Remove columns from hotels table
    op.drop_column('hotels', 'policies')
    op.drop_column('hotels', 'property_overview')

