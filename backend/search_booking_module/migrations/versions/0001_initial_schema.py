"""Initial schema for search_booking_module

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2024-11-06 16:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create hotels table
    op.create_table(
        'hotels',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('provider_hotel_id', sa.String(length=255), nullable=False),
        sa.Column('provider', sa.Enum('booking_com', 'expedia', 'direct', 'agoda', name='provider'), nullable=False),
        sa.Column('name', sa.String(length=500), nullable=False),
        sa.Column('address', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('city', sa.String(length=255), nullable=False),
        sa.Column('country', sa.String(length=100), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('stars', sa.Integer(), nullable=False),
        sa.Column('rating', sa.Float(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('images', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('amenities', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('source_url', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_hotels_provider_hotel_id'), 'hotels', ['provider_hotel_id'], unique=False)
    op.create_index(op.f('ix_hotels_provider'), 'hotels', ['provider'], unique=False)
    op.create_index(op.f('ix_hotels_city'), 'hotels', ['city'], unique=False)
    op.create_index(op.f('ix_hotels_country'), 'hotels', ['country'], unique=False)

    # Create rooms table
    op.create_table(
        'rooms',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('hotel_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('room_type_name', sa.String(length=255), nullable=False),
        sa.Column('occupancy', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('amenities', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['hotel_id'], ['hotels.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_rooms_hotel_id'), 'rooms', ['hotel_id'], unique=False)

    # Create offers table
    op.create_table(
        'offers',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('hotel_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('room_id', postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column('provider', sa.Enum('booking_com', 'expedia', 'direct', 'agoda', name='provider'), nullable=False),
        sa.Column('provider_rate_id', sa.String(length=255), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('taxes_included', sa.Boolean(), nullable=False),
        sa.Column('check_in', sa.Date(), nullable=False),
        sa.Column('check_out', sa.Date(), nullable=False),
        sa.Column('availability_count', sa.Integer(), nullable=False),
        sa.Column('cancellation_policy', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('raw_response', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('fetched_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['hotel_id'], ['hotels.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['room_id'], ['rooms.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_offers_hotel_id'), 'offers', ['hotel_id'], unique=False)
    op.create_index(op.f('ix_offers_room_id'), 'offers', ['room_id'], unique=False)
    op.create_index(op.f('ix_offers_provider'), 'offers', ['provider'], unique=False)
    op.create_index(op.f('ix_offers_provider_rate_id'), 'offers', ['provider_rate_id'], unique=False)
    op.create_index(op.f('ix_offers_check_in'), 'offers', ['check_in'], unique=False)
    op.create_index(op.f('ix_offers_check_out'), 'offers', ['check_out'], unique=False)
    op.create_index(op.f('ix_offers_fetched_at'), 'offers', ['fetched_at'], unique=False)
    op.create_index(op.f('ix_offers_expires_at'), 'offers', ['expires_at'], unique=False)

    # Create bookings_clicks table
    op.create_table(
        'bookings_clicks',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column('offer_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('provider', sa.Enum('booking_com', 'expedia', 'direct', 'agoda', name='provider'), nullable=False),
        sa.Column('affiliate_link', sa.Text(), nullable=False),
        sa.Column('clicked_at', sa.DateTime(), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=False),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('converted', sa.Boolean(), nullable=False),
        sa.Column('converted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['offer_id'], ['offers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_bookings_clicks_user_id'), 'bookings_clicks', ['user_id'], unique=False)
    op.create_index(op.f('ix_bookings_clicks_offer_id'), 'bookings_clicks', ['offer_id'], unique=False)
    op.create_index(op.f('ix_bookings_clicks_provider'), 'bookings_clicks', ['provider'], unique=False)
    op.create_index(op.f('ix_bookings_clicks_clicked_at'), 'bookings_clicks', ['clicked_at'], unique=False)
    op.create_index(op.f('ix_bookings_clicks_converted'), 'bookings_clicks', ['converted'], unique=False)

    # Create reviews table
    op.create_table(
        'reviews',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('hotel_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('provider', sa.Enum('booking_com', 'expedia', 'direct', 'agoda', name='provider'), nullable=False),
        sa.Column('rating', sa.Float(), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=True),
        sa.Column('text', sa.Text(), nullable=True),
        sa.Column('author', sa.String(length=255), nullable=True),
        sa.Column('pros', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('cons', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('category_ratings', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('fetched_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['hotel_id'], ['hotels.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reviews_hotel_id'), 'reviews', ['hotel_id'], unique=False)
    op.create_index(op.f('ix_reviews_provider'), 'reviews', ['provider'], unique=False)
    op.create_index(op.f('ix_reviews_fetched_at'), 'reviews', ['fetched_at'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index(op.f('ix_reviews_fetched_at'), table_name='reviews')
    op.drop_index(op.f('ix_reviews_provider'), table_name='reviews')
    op.drop_index(op.f('ix_reviews_hotel_id'), table_name='reviews')
    op.drop_table('reviews')
    
    op.drop_index(op.f('ix_bookings_clicks_converted'), table_name='bookings_clicks')
    op.drop_index(op.f('ix_bookings_clicks_clicked_at'), table_name='bookings_clicks')
    op.drop_index(op.f('ix_bookings_clicks_provider'), table_name='bookings_clicks')
    op.drop_index(op.f('ix_bookings_clicks_offer_id'), table_name='bookings_clicks')
    op.drop_index(op.f('ix_bookings_clicks_user_id'), table_name='bookings_clicks')
    op.drop_table('bookings_clicks')
    
    op.drop_index(op.f('ix_offers_expires_at'), table_name='offers')
    op.drop_index(op.f('ix_offers_fetched_at'), table_name='offers')
    op.drop_index(op.f('ix_offers_check_out'), table_name='offers')
    op.drop_index(op.f('ix_offers_check_in'), table_name='offers')
    op.drop_index(op.f('ix_offers_provider_rate_id'), table_name='offers')
    op.drop_index(op.f('ix_offers_provider'), table_name='offers')
    op.drop_index(op.f('ix_offers_room_id'), table_name='offers')
    op.drop_index(op.f('ix_offers_hotel_id'), table_name='offers')
    op.drop_table('offers')
    
    op.drop_index(op.f('ix_rooms_hotel_id'), table_name='rooms')
    op.drop_table('rooms')
    
    op.drop_index(op.f('ix_hotels_country'), table_name='hotels')
    op.drop_index(op.f('ix_hotels_city'), table_name='hotels')
    op.drop_index(op.f('ix_hotels_provider'), table_name='hotels')
    op.drop_index(op.f('ix_hotels_provider_hotel_id'), table_name='hotels')
    op.drop_table('hotels')
    
    # Drop enum types
    op.execute("DROP TYPE IF EXISTS provider")

