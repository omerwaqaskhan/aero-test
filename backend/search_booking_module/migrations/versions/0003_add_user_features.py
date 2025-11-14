"""Add user features: favorites, bookings, price alerts, saved searches, user reviews

Revision ID: 0003_add_user_features
Revises: 0002_add_hotel_details_fields
Create Date: 2024-12-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0003_add_user_features'
down_revision = '0002_add_hotel_details_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create BookingStatus enum
    op.execute("""
        CREATE TYPE bookingstatus AS ENUM ('pending', 'confirmed', 'cancelled', 'completed', 'refunded')
    """)
    
    # Create PriceAlertStatus enum
    op.execute("""
        CREATE TYPE pricealertstatus AS ENUM ('active', 'triggered', 'expired', 'cancelled')
    """)
    
    # Create favorites table
    op.create_table(
        'favorites',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('hotel_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['hotel_id'], ['hotels.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_favorites_user_id', 'favorites', ['user_id'], unique=False)
    op.create_index('ix_favorites_hotel_id', 'favorites', ['hotel_id'], unique=False)
    op.create_index('ix_favorites_created_at', 'favorites', ['created_at'], unique=False)
    op.create_index('ix_favorites_user_hotel', 'favorites', ['user_id', 'hotel_id'], unique=True)
    
    # Create bookings table
    op.create_table(
        'bookings',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column('hotel_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('offer_id', postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column('booking_reference', sa.String(length=100), nullable=True),
        sa.Column('check_in', sa.Date(), nullable=False),
        sa.Column('check_out', sa.Date(), nullable=False),
        sa.Column('guests', sa.Integer(), nullable=False),
        sa.Column('rooms', sa.Integer(), nullable=False),
        sa.Column('guest_name', sa.String(length=255), nullable=False),
        sa.Column('guest_email', sa.String(length=255), nullable=False),
        sa.Column('guest_phone', sa.String(length=50), nullable=True),
        sa.Column('total_price', sa.Numeric(10, 2), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=False),
        sa.Column('taxes_included', sa.Boolean(), nullable=False),
        sa.Column('status', postgresql.ENUM('pending', 'confirmed', 'cancelled', 'completed', 'refunded', name='bookingstatus'), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=True),
        sa.Column('provider_booking_id', sa.String(length=255), nullable=True),
        sa.Column('affiliate_link', sa.Text(), nullable=True),
        sa.Column('booked_at', sa.DateTime(), nullable=False),
        sa.Column('confirmed_at', sa.DateTime(), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('special_requests', sa.Text(), nullable=True),
        sa.Column('cancellation_policy', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('booking_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['hotel_id'], ['hotels.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['offer_id'], ['offers.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_bookings_user_id', 'bookings', ['user_id'], unique=False)
    op.create_index('ix_bookings_hotel_id', 'bookings', ['hotel_id'], unique=False)
    op.create_index('ix_bookings_offer_id', 'bookings', ['offer_id'], unique=False)
    op.create_index('ix_bookings_booking_reference', 'bookings', ['booking_reference'], unique=True)
    op.create_index('ix_bookings_provider_booking_id', 'bookings', ['provider_booking_id'], unique=False)
    op.create_index('ix_bookings_status', 'bookings', ['status'], unique=False)
    op.create_index('ix_bookings_guest_email', 'bookings', ['guest_email'], unique=False)
    op.create_index('ix_bookings_check_in', 'bookings', ['check_in'], unique=False)
    op.create_index('ix_bookings_check_out', 'bookings', ['check_out'], unique=False)
    op.create_index('ix_bookings_booked_at', 'bookings', ['booked_at'], unique=False)
    
    # Create price_alerts table
    op.create_table(
        'price_alerts',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('hotel_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('target_price', sa.Numeric(10, 2), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=False),
        sa.Column('check_in', sa.Date(), nullable=True),
        sa.Column('check_out', sa.Date(), nullable=True),
        sa.Column('guests', sa.Integer(), nullable=True),
        sa.Column('rooms', sa.Integer(), nullable=True),
        sa.Column('status', postgresql.ENUM('active', 'triggered', 'expired', 'cancelled', name='pricealertstatus'), nullable=False),
        sa.Column('triggered_at', sa.DateTime(), nullable=True),
        sa.Column('triggered_price', sa.Numeric(10, 2), nullable=True),
        sa.Column('notify_email', sa.Boolean(), nullable=False),
        sa.Column('notify_sms', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['hotel_id'], ['hotels.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_price_alerts_user_id', 'price_alerts', ['user_id'], unique=False)
    op.create_index('ix_price_alerts_hotel_id', 'price_alerts', ['hotel_id'], unique=False)
    op.create_index('ix_price_alerts_status', 'price_alerts', ['status'], unique=False)
    op.create_index('ix_price_alerts_check_in', 'price_alerts', ['check_in'], unique=False)
    op.create_index('ix_price_alerts_created_at', 'price_alerts', ['created_at'], unique=False)
    op.create_index('ix_price_alerts_expires_at', 'price_alerts', ['expires_at'], unique=False)
    
    # Create saved_searches table
    op.create_table(
        'saved_searches',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('destination', sa.String(length=255), nullable=False),
        sa.Column('check_in', sa.Date(), nullable=True),
        sa.Column('check_out', sa.Date(), nullable=True),
        sa.Column('guests', sa.Integer(), nullable=True),
        sa.Column('rooms', sa.Integer(), nullable=True),
        sa.Column('filters', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('notification_enabled', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('last_searched_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_saved_searches_user_id', 'saved_searches', ['user_id'], unique=False)
    op.create_index('ix_saved_searches_created_at', 'saved_searches', ['created_at'], unique=False)
    
    # Create user_reviews table
    op.create_table(
        'user_reviews',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column('hotel_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('booking_id', postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column('rating', sa.Float(), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=True),
        sa.Column('text', sa.Text(), nullable=True),
        sa.Column('category_ratings', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('pros', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('cons', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('verified_booking', sa.Boolean(), nullable=False),
        sa.Column('published', sa.Boolean(), nullable=False),
        sa.Column('helpful_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['hotel_id'], ['hotels.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['booking_id'], ['bookings.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_user_reviews_user_id', 'user_reviews', ['user_id'], unique=False)
    op.create_index('ix_user_reviews_hotel_id', 'user_reviews', ['hotel_id'], unique=False)
    op.create_index('ix_user_reviews_booking_id', 'user_reviews', ['booking_id'], unique=False)
    op.create_index('ix_user_reviews_user_hotel', 'user_reviews', ['user_id', 'hotel_id'], unique=False)
    op.create_index('ix_user_reviews_created_at', 'user_reviews', ['created_at'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index('ix_user_reviews_created_at', table_name='user_reviews')
    op.drop_index('ix_user_reviews_user_hotel', table_name='user_reviews')
    op.drop_index('ix_user_reviews_booking_id', table_name='user_reviews')
    op.drop_index('ix_user_reviews_hotel_id', table_name='user_reviews')
    op.drop_index('ix_user_reviews_user_id', table_name='user_reviews')
    op.drop_table('user_reviews')
    
    op.drop_index('ix_saved_searches_created_at', table_name='saved_searches')
    op.drop_index('ix_saved_searches_user_id', table_name='saved_searches')
    op.drop_table('saved_searches')
    
    op.drop_index('ix_price_alerts_expires_at', table_name='price_alerts')
    op.drop_index('ix_price_alerts_created_at', table_name='price_alerts')
    op.drop_index('ix_price_alerts_check_in', table_name='price_alerts')
    op.drop_index('ix_price_alerts_status', table_name='price_alerts')
    op.drop_index('ix_price_alerts_hotel_id', table_name='price_alerts')
    op.drop_index('ix_price_alerts_user_id', table_name='price_alerts')
    op.drop_table('price_alerts')
    
    op.drop_index('ix_bookings_booked_at', table_name='bookings')
    op.drop_index('ix_bookings_check_out', table_name='bookings')
    op.drop_index('ix_bookings_check_in', table_name='bookings')
    op.drop_index('ix_bookings_guest_email', table_name='bookings')
    op.drop_index('ix_bookings_status', table_name='bookings')
    op.drop_index('ix_bookings_provider_booking_id', table_name='bookings')
    op.drop_index('ix_bookings_booking_reference', table_name='bookings')
    op.drop_index('ix_bookings_offer_id', table_name='bookings')
    op.drop_index('ix_bookings_hotel_id', table_name='bookings')
    op.drop_index('ix_bookings_user_id', table_name='bookings')
    op.drop_table('bookings')
    
    op.drop_index('ix_favorites_user_hotel', table_name='favorites')
    op.drop_index('ix_favorites_created_at', table_name='favorites')
    op.drop_index('ix_favorites_hotel_id', table_name='favorites')
    op.drop_index('ix_favorites_user_id', table_name='favorites')
    op.drop_table('favorites')
    
    # Drop enum types
    op.execute("DROP TYPE IF EXISTS pricealertstatus")
    op.execute("DROP TYPE IF EXISTS bookingstatus")

