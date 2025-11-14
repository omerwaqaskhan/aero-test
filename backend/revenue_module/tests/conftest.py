"""Pytest fixtures for revenue module tests."""

import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime, date, timedelta
from decimal import Decimal
import uuid

from revenue_module.infrastructure.db.models import (
    SubscriptionModel, SubscriptionPaymentModel, LeadModel, HotelListingModel,
    ListingPaymentModel, SponsoredPlacementModel, AdRevenueModel, RevenueTransactionModel,
    SubscriptionTier, LeadStatus, ListingPackage, SponsorshipStatus
)
from search_booking_module.infrastructure.db.models import HotelModel
from auth_module.infrastructure.db.models import UserModel


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    session = Mock()
    session.query = Mock()
    session.add = Mock()
    session.commit = Mock()
    session.refresh = Mock()
    session.delete = Mock()
    return session


@pytest.fixture
def mock_hotel():
    """Create a mock hotel."""
    return HotelModel(
        id=str(uuid.uuid4()),
        provider_hotel_id="hotel_123",
        name="Test Hotel",
        city="New York",
        country="USA",
        latitude=40.7580,
        longitude=-73.9855,
        stars=4,
        rating=4.5,
        source_url="https://example.com/hotel"
    )


@pytest.fixture
def mock_user():
    """Create a mock user."""
    return UserModel(
        id=str(uuid.uuid4()),
        tenant_id=str(uuid.uuid4()),
        email="test@example.com",
        first_name="Test",
        last_name="User"
    )


@pytest.fixture
def mock_subscription():
    """Create a mock subscription."""
    return SubscriptionModel(
        id=str(uuid.uuid4()),
        user_id=str(uuid.uuid4()),
        tier=SubscriptionTier.PREMIUM,
        stripe_subscription_id="sub_123",
        stripe_customer_id="cus_123",
        status="active",
        current_period_start=datetime.utcnow(),
        current_period_end=datetime.utcnow() + timedelta(days=30)
    )


@pytest.fixture
def mock_lead():
    """Create a mock lead."""
    return LeadModel(
        id=str(uuid.uuid4()),
        hotel_id=str(uuid.uuid4()),
        email="guest@example.com",
        name="Guest User",
        check_in=date.today() + timedelta(days=7),
        check_out=date.today() + timedelta(days=10),
        guests=2,
        rooms=1,
        status=LeadStatus.NEW,
        lead_fee=Decimal("15.00")
    )


@pytest.fixture
def mock_listing():
    """Create a mock hotel listing."""
    return HotelListingModel(
        id=str(uuid.uuid4()),
        hotel_id=str(uuid.uuid4()),
        package=ListingPackage.ENHANCED,
        owner_email="owner@hotel.com",
        verified=False,
        status="pending"
    )

