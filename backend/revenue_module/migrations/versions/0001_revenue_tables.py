"""Create revenue tracking tables

Revision ID: 0001_revenue_tables
Revises: 
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = '0001_revenue_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Subscriptions
    op.create_table(
        'subscriptions',
        sa.Column('id', UUID(as_uuid=False), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=False), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tier', sa.Enum('free', 'premium', 'pro', name='subscriptiontier'), nullable=False),
        sa.Column('stripe_subscription_id', sa.String(255), unique=True, nullable=True),
        sa.Column('stripe_customer_id', sa.String(255), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, default='active'),
        sa.Column('current_period_start', sa.DateTime(), nullable=True),
        sa.Column('current_period_end', sa.DateTime(), nullable=True),
        sa.Column('cancel_at_period_end', sa.Boolean(), nullable=False, default=False),
        sa.Column('canceled_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_subscriptions_user_id', 'subscriptions', ['user_id'])
    op.create_index('ix_subscriptions_tier', 'subscriptions', ['tier'])
    op.create_index('ix_subscriptions_status', 'subscriptions', ['status'])
    
    # Subscription payments
    op.create_table(
        'subscription_payments',
        sa.Column('id', UUID(as_uuid=False), primary_key=True),
        sa.Column('subscription_id', UUID(as_uuid=False), sa.ForeignKey('subscriptions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('stripe_payment_intent_id', sa.String(255), unique=True, nullable=True),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('currency', sa.String(10), nullable=False, default='USD'),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('paid_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_subscription_payments_subscription_id', 'subscription_payments', ['subscription_id'])
    
    # Leads
    op.create_table(
        'leads',
        sa.Column('id', UUID(as_uuid=False), primary_key=True),
        sa.Column('hotel_id', UUID(as_uuid=False), sa.ForeignKey('hotels.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', UUID(as_uuid=False), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('check_in', sa.Date(), nullable=False),
        sa.Column('check_out', sa.Date(), nullable=False),
        sa.Column('guests', sa.Integer(), nullable=True),
        sa.Column('rooms', sa.Integer(), nullable=True),
        sa.Column('budget_range', sa.String(50), nullable=True),
        sa.Column('special_requests', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('new', 'sent', 'responded', 'booked', 'lost', name='leadstatus'), nullable=False, default='new'),
        sa.Column('sent_to_hotel_at', sa.DateTime(), nullable=True),
        sa.Column('hotel_responded_at', sa.DateTime(), nullable=True),
        sa.Column('converted_at', sa.DateTime(), nullable=True),
        sa.Column('lead_fee', sa.Numeric(10, 2), nullable=True),
        sa.Column('booking_value', sa.Numeric(10, 2), nullable=True),
        sa.Column('commission', sa.Numeric(10, 2), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_leads_hotel_id', 'leads', ['hotel_id'])
    op.create_index('ix_leads_user_id', 'leads', ['user_id'])
    op.create_index('ix_leads_email', 'leads', ['email'])
    op.create_index('ix_leads_status', 'leads', ['status'])
    op.create_index('ix_leads_created_at', 'leads', ['created_at'])
    
    # Hotel listings
    op.create_table(
        'hotel_listings',
        sa.Column('id', UUID(as_uuid=False), primary_key=True),
        sa.Column('hotel_id', UUID(as_uuid=False), sa.ForeignKey('hotels.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('package', sa.Enum('basic', 'enhanced', 'premium', name='listingpackage'), nullable=False),
        sa.Column('owner_email', sa.String(255), nullable=False),
        sa.Column('owner_name', sa.String(255), nullable=True),
        sa.Column('owner_phone', sa.String(50), nullable=True),
        sa.Column('verified', sa.Boolean(), nullable=False, default=False),
        sa.Column('verification_token', sa.String(255), unique=True, nullable=True),
        sa.Column('stripe_customer_id', sa.String(255), nullable=True),
        sa.Column('current_period_start', sa.DateTime(), nullable=True),
        sa.Column('current_period_end', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, default='pending'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_hotel_listings_hotel_id', 'hotel_listings', ['hotel_id'])
    op.create_index('ix_hotel_listings_package', 'hotel_listings', ['package'])
    op.create_index('ix_hotel_listings_verified', 'hotel_listings', ['verified'])
    op.create_index('ix_hotel_listings_status', 'hotel_listings', ['status'])
    
    # Listing payments
    op.create_table(
        'listing_payments',
        sa.Column('id', UUID(as_uuid=False), primary_key=True),
        sa.Column('listing_id', UUID(as_uuid=False), sa.ForeignKey('hotel_listings.id', ondelete='CASCADE'), nullable=False),
        sa.Column('stripe_payment_intent_id', sa.String(255), unique=True, nullable=True),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('currency', sa.String(10), nullable=False, default='USD'),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('period_start', sa.DateTime(), nullable=False),
        sa.Column('period_end', sa.DateTime(), nullable=False),
        sa.Column('paid_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_listing_payments_listing_id', 'listing_payments', ['listing_id'])
    
    # Sponsored placements
    op.create_table(
        'sponsored_placements',
        sa.Column('id', UUID(as_uuid=False), primary_key=True),
        sa.Column('hotel_id', UUID(as_uuid=False), sa.ForeignKey('hotels.id', ondelete='CASCADE'), nullable=False),
        sa.Column('listing_id', UUID(as_uuid=False), sa.ForeignKey('hotel_listings.id', ondelete='CASCADE'), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=False, default=0),
        sa.Column('placement_type', sa.String(50), nullable=False),
        sa.Column('start_date', sa.DateTime(), nullable=False),
        sa.Column('end_date', sa.DateTime(), nullable=False),
        sa.Column('status', sa.Enum('active', 'paused', 'expired', name='sponsorshipstatus'), nullable=False, default='active'),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('currency', sa.String(10), nullable=False, default='USD'),
        sa.Column('stripe_payment_intent_id', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_sponsored_placements_hotel_id', 'sponsored_placements', ['hotel_id'])
    op.create_index('ix_sponsored_placements_priority', 'sponsored_placements', ['priority'])
    op.create_index('ix_sponsored_placements_status', 'sponsored_placements', ['status'])
    
    # Ad revenue
    op.create_table(
        'ad_revenue',
        sa.Column('id', UUID(as_uuid=False), primary_key=True),
        sa.Column('ad_slot', sa.String(100), nullable=False),
        sa.Column('page_type', sa.String(50), nullable=False),
        sa.Column('impressions', sa.Integer(), nullable=False, default=0),
        sa.Column('clicks', sa.Integer(), nullable=False, default=0),
        sa.Column('revenue', sa.Numeric(10, 2), nullable=False, default=0),
        sa.Column('currency', sa.String(10), nullable=False, default='USD'),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_ad_revenue_ad_slot', 'ad_revenue', ['ad_slot'])
    op.create_index('ix_ad_revenue_page_type', 'ad_revenue', ['page_type'])
    op.create_index('ix_ad_revenue_date', 'ad_revenue', ['date'])
    
    # Revenue transactions
    op.create_table(
        'revenue_transactions',
        sa.Column('id', UUID(as_uuid=False), primary_key=True),
        sa.Column('revenue_type', sa.String(50), nullable=False),
        sa.Column('reference_id', UUID(as_uuid=False), nullable=True),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('currency', sa.String(10), nullable=False, default='USD'),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=False, default={}),
        sa.Column('occurred_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_revenue_transactions_revenue_type', 'revenue_transactions', ['revenue_type'])
    op.create_index('ix_revenue_transactions_reference_id', 'revenue_transactions', ['reference_id'])
    op.create_index('ix_revenue_transactions_status', 'revenue_transactions', ['status'])
    op.create_index('ix_revenue_transactions_occurred_at', 'revenue_transactions', ['occurred_at'])


def downgrade() -> None:
    op.drop_table('revenue_transactions')
    op.drop_table('ad_revenue')
    op.drop_table('sponsored_placements')
    op.drop_table('listing_payments')
    op.drop_table('hotel_listings')
    op.drop_table('leads')
    op.drop_table('subscription_payments')
    op.drop_table('subscriptions')
    op.execute('DROP TYPE IF EXISTS subscriptiontier')
    op.execute('DROP TYPE IF EXISTS leadstatus')
    op.execute('DROP TYPE IF EXISTS listingpackage')
    op.execute('DROP TYPE IF EXISTS sponsorshipstatus')

