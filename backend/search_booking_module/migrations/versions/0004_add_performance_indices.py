"""Add performance indices for common queries

Revision ID: 0004_add_performance_indices
Revises: 0003_add_user_features
Create Date: 2025-11-16 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0004_add_performance_indices'
down_revision = '0003_add_user_features'
branch_labels = None
depends_on = None


def upgrade():
    """Add performance indices."""
    # Hotels table indices
    op.create_index('idx_hotels_city', 'hotels', ['city'], unique=False)
    op.create_index('idx_hotels_country', 'hotels', ['country'], unique=False)
    op.create_index('idx_hotels_provider', 'hotels', ['provider'], unique=False)
    op.create_index('idx_hotels_provider_hotel_id', 'hotels', ['provider_hotel_id'], unique=False)
    op.create_index('idx_hotels_rating', 'hotels', ['rating'], unique=False)
    
    # Composite index for city + rating queries
    op.create_index('idx_hotels_city_rating', 'hotels', ['city', 'rating'], unique=False)
    
    # Rooms table indices
    op.create_index('idx_rooms_hotel_id', 'rooms', ['hotel_id'], unique=False)
    op.create_index('idx_rooms_room_type', 'rooms', ['room_type_name'], unique=False)
    
    # Offers table indices
    op.create_index('idx_offers_hotel_id', 'offers', ['hotel_id'], unique=False)
    op.create_index('idx_offers_room_id', 'offers', ['room_id'], unique=False)
    op.create_index('idx_offers_check_in', 'offers', ['check_in'], unique=False)
    op.create_index('idx_offers_check_out', 'offers', ['check_out'], unique=False)
    op.create_index('idx_offers_price', 'offers', ['price'], unique=False)
    
    # Composite index for hotel + date range queries (most common)
    op.create_index('idx_offers_hotel_dates', 'offers', ['hotel_id', 'check_in', 'check_out'], unique=False)
    
    # Reviews table indices
    op.create_index('idx_reviews_hotel_id', 'reviews', ['hotel_id'], unique=False)
    op.create_index('idx_reviews_rating', 'reviews', ['rating'], unique=False)
    op.create_index('idx_reviews_created_at', 'reviews', ['created_at'], unique=False)
    
    # Bookings table indices (from user_models)
    op.create_index('idx_bookings_user_id', 'bookings', ['user_id'], unique=False)
    op.create_index('idx_bookings_hotel_id', 'bookings', ['hotel_id'], unique=False)
    op.create_index('idx_bookings_status', 'bookings', ['status'], unique=False)
    op.create_index('idx_bookings_check_in', 'bookings', ['check_in'], unique=False)
    op.create_index('idx_bookings_created_at', 'bookings', ['created_at'], unique=False)
    
    # Favorites table indices
    op.create_index('idx_favorites_user_id', 'favorites', ['user_id'], unique=False)
    op.create_index('idx_favorites_hotel_id', 'favorites', ['hotel_id'], unique=False)
    op.create_index('idx_favorites_user_hotel', 'favorites', ['user_id', 'hotel_id'], unique=True)
    
    # Price alerts table indices
    op.create_index('idx_price_alerts_user_id', 'price_alerts', ['user_id'], unique=False)
    op.create_index('idx_price_alerts_hotel_id', 'price_alerts', ['hotel_id'], unique=False)
    op.create_index('idx_price_alerts_status', 'price_alerts', ['status'], unique=False)
    
    # Saved searches table indices
    op.create_index('idx_saved_searches_user_id', 'saved_searches', ['user_id'], unique=False)
    op.create_index('idx_saved_searches_created_at', 'saved_searches', ['created_at'], unique=False)


def downgrade():
    """Remove performance indices."""
    # Drop indices in reverse order
    op.drop_index('idx_saved_searches_created_at', table_name='saved_searches')
    op.drop_index('idx_saved_searches_user_id', table_name='saved_searches')
    op.drop_index('idx_price_alerts_status', table_name='price_alerts')
    op.drop_index('idx_price_alerts_hotel_id', table_name='price_alerts')
    op.drop_index('idx_price_alerts_user_id', table_name='price_alerts')
    op.drop_index('idx_favorites_user_hotel', table_name='favorites')
    op.drop_index('idx_favorites_hotel_id', table_name='favorites')
    op.drop_index('idx_favorites_user_id', table_name='favorites')
    op.drop_index('idx_bookings_created_at', table_name='bookings')
    op.drop_index('idx_bookings_check_in', table_name='bookings')
    op.drop_index('idx_bookings_status', table_name='bookings')
    op.drop_index('idx_bookings_hotel_id', table_name='bookings')
    op.drop_index('idx_bookings_user_id', table_name='bookings')
    op.drop_index('idx_reviews_created_at', table_name='reviews')
    op.drop_index('idx_reviews_rating', table_name='reviews')
    op.drop_index('idx_reviews_hotel_id', table_name='reviews')
    op.drop_index('idx_offers_hotel_dates', table_name='offers')
    op.drop_index('idx_offers_price', table_name='offers')
    op.drop_index('idx_offers_check_out', table_name='offers')
    op.drop_index('idx_offers_check_in', table_name='offers')
    op.drop_index('idx_offers_room_id', table_name='offers')
    op.drop_index('idx_offers_hotel_id', table_name='offers')
    op.drop_index('idx_rooms_room_type', table_name='rooms')
    op.drop_index('idx_rooms_hotel_id', table_name='rooms')
    op.drop_index('idx_hotels_city_rating', table_name='hotels')
    op.drop_index('idx_hotels_rating', table_name='hotels')
    op.drop_index('idx_hotels_provider_hotel_id', table_name='hotels')
    op.drop_index('idx_hotels_provider', table_name='hotels')
    op.drop_index('idx_hotels_country', table_name='hotels')
    op.drop_index('idx_hotels_city', table_name='hotels')

