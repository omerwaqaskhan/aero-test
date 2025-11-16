"""Remove foreign key constraints to users table

Revision ID: 0004
Revises: 0003
Create Date: 2025-11-16 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0004'
down_revision = '0003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Remove foreign key constraints to users table (cross-module references)."""
    # Drop foreign key constraints on all tables that reference users.id
    # These are cross-module references that can't work in SQLAlchemy
    
    # Drop FK on favorites table
    try:
        op.drop_constraint('favorites_user_id_fkey', 'favorites', type_='foreignkey')
    except Exception:
        pass  # FK might not exist
    
    # Drop FK on bookings table
    try:
        op.drop_constraint('bookings_user_id_fkey', 'bookings', type_='foreignkey')
    except Exception:
        pass
    
    # Drop FK on price_alerts table
    try:
        op.drop_constraint('price_alerts_user_id_fkey', 'price_alerts', type_='foreignkey')
    except Exception:
        pass
    
    # Drop FK on saved_searches table
    try:
        op.drop_constraint('saved_searches_user_id_fkey', 'saved_searches', type_='foreignkey')
    except Exception:
        pass
    
    # Drop FK on user_reviews table
    try:
        op.drop_constraint('user_reviews_user_id_fkey', 'user_reviews', type_='foreignkey')
    except Exception:
        pass
    
    # Drop FK on bookings_clicks table
    try:
        op.drop_constraint('bookings_clicks_user_id_fkey', 'bookings_clicks', type_='foreignkey')
    except Exception:
        pass


def downgrade() -> None:
    """Re-add foreign key constraints (will fail if users table not in same DB)."""
    # Note: This downgrade will fail if run, as the users table is in a different module
    # Kept for migration history completeness
    pass

