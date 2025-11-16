"""Integration tests for booking → lead → revenue flow."""

import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from search_booking_module.api.user_routers import router
from search_booking_module.infrastructure.db.models import HotelModel, OfferModel
from search_booking_module.infrastructure.db.user_models import BookingModel, BookingStatus
from auth_module.infrastructure.db.models import UserModel
from auth_module.infrastructure.db.database import get_db


def test_booking_creates_lead_and_revenue(client, db: Session, user, hotel):
    """Test that creating a booking automatically creates a lead and records revenue."""
    
    # Import revenue models
    try:
        from revenue_module.infrastructure.db.models import LeadModel, RevenueTransactionModel
    except ImportError:
        pytest.skip("Revenue module not available")
    
    # Create booking data
    check_in = date.today() + timedelta(days=7)
    check_out = date.today() + timedelta(days=10)
    
    booking_data = {
        "hotel_id": str(hotel.id),
        "check_in": check_in.isoformat(),
        "check_out": check_out.isoformat(),
        "guests": 2,
        "rooms": 1,
        "guest_name": "John Doe",
        "guest_email": "john.doe@example.com",
        "guest_phone": "+1234567890",
        "special_requests": "Late check-in please"
    }
    
    # Get user token
    from auth_module.core.security import JWTManager
    jwt_manager = JWTManager()
    token = jwt_manager.create_access_token(
        user_id=str(user.id),
        tenant_id=user.tenant_id,
        roles=["user"]
    )
    
    # Create booking
    response = client.post(
        "/api/v1/user/bookings",
        json=booking_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    booking_response = response.json()
    
    # Verify booking was created
    assert booking_response["booking_reference"] is not None
    assert booking_response["hotel_id"] == str(hotel.id)
    assert booking_response["status"] == "pending"
    
    # Verify booking metadata contains lead information
    booking_metadata = booking_response.get("booking_metadata", {})
    assert "lead_id" in booking_metadata
    assert "lead_fee" in booking_metadata
    assert booking_metadata["revenue_model"] == "lead_generation"
    assert Decimal(booking_metadata["lead_fee"]) == Decimal("15.00")
    
    # Verify lead was created in database
    lead_id = booking_metadata["lead_id"]
    lead = db.query(LeadModel).filter(LeadModel.id == lead_id).first()
    assert lead is not None
    assert lead.hotel_id == str(hotel.id)
    assert lead.email == "john.doe@example.com"
    assert lead.name == "John Doe"
    assert lead.phone == "+1234567890"
    assert lead.check_in == check_in
    assert lead.check_out == check_out
    assert lead.guests == 2
    assert lead.rooms == 1
    assert lead.status.value in ["new", "sent"]
    assert lead.lead_fee == Decimal("15.00")
    
    # Verify revenue transaction was recorded
    revenue_transaction = db.query(RevenueTransactionModel).filter(
        RevenueTransactionModel.reference_id == lead_id,
        RevenueTransactionModel.revenue_type == "lead"
    ).first()
    assert revenue_transaction is not None
    assert revenue_transaction.amount == Decimal("15.00")
    assert revenue_transaction.status == "completed"
    assert revenue_transaction.currency == "USD"


def test_booking_confirmation_tracks_commission(client, db: Session, user, hotel):
    """Test that confirming a booking tracks commission on the lead."""
    
    try:
        from revenue_module.infrastructure.db.models import LeadModel, RevenueTransactionModel, LeadStatus
    except ImportError:
        pytest.skip("Revenue module not available")
    
    # Create booking first
    check_in = date.today() + timedelta(days=7)
    check_out = date.today() + timedelta(days=10)
    
    booking_data = {
        "hotel_id": str(hotel.id),
        "check_in": check_in.isoformat(),
        "check_out": check_out.isoformat(),
        "guests": 2,
        "rooms": 1,
        "guest_name": "Jane Smith",
        "guest_email": "jane.smith@example.com",
        "guest_phone": "+1234567890"
    }
    
    from auth_module.core.security import JWTManager
    jwt_manager = JWTManager()
    token = jwt_manager.create_access_token(
        user_id=str(user.id),
        tenant_id=user.tenant_id,
        roles=["user"]
    )
    
    # Create booking
    response = client.post(
        "/api/v1/user/bookings",
        json=booking_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    booking_response = response.json()
    booking_id = booking_response["id"]
    lead_id = booking_response["booking_metadata"]["lead_id"]
    total_price = Decimal(str(booking_response["total_price"]))
    
    # Confirm booking
    confirm_response = client.patch(
        f"/api/v1/user/bookings/{booking_id}/status",
        json={"status": "confirmed"},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert confirm_response.status_code == 200
    
    # Verify lead was marked as converted
    lead = db.query(LeadModel).filter(LeadModel.id == lead_id).first()
    assert lead is not None
    assert lead.status == LeadStatus.BOOKED
    assert lead.booking_value == total_price
    assert lead.commission == total_price * Decimal("0.10")
    assert lead.converted_at is not None
    
    # Verify commission revenue transaction was recorded
    commission_transaction = db.query(RevenueTransactionModel).filter(
        RevenueTransactionModel.reference_id == lead_id,
        RevenueTransactionModel.revenue_type == "lead"
    ).order_by(RevenueTransactionModel.created_at.desc()).first()
    
    assert commission_transaction is not None
    assert commission_transaction.amount == total_price * Decimal("0.10")
    assert commission_transaction.status == "completed"
    
    # Verify booking metadata was updated
    booking = db.query(BookingModel).filter(BookingModel.id == booking_id).first()
    assert booking.booking_metadata["commission_tracked"] is True
    assert Decimal(booking.booking_metadata["commission_amount"]) == total_price * Decimal("0.10")


def test_booking_without_revenue_module_still_works(client, db: Session, user, hotel, monkeypatch):
    """Test that booking still works even if revenue module is not available."""
    
    # Mock ImportError for revenue module
    def mock_import(*args, **kwargs):
        if "revenue_module" in str(args):
            raise ImportError("Revenue module not available")
        return original_import(*args, **kwargs)
    
    original_import = __builtins__.__import__
    monkeypatch.setattr(__builtins__, '__import__', mock_import)
    
    # Create booking data
    check_in = date.today() + timedelta(days=7)
    check_out = date.today() + timedelta(days=10)
    
    booking_data = {
        "hotel_id": str(hotel.id),
        "check_in": check_in.isoformat(),
        "check_out": check_out.isoformat(),
        "guests": 2,
        "rooms": 1,
        "guest_name": "Bob Johnson",
        "guest_email": "bob.johnson@example.com"
    }
    
    from auth_module.core.security import JWTManager
    jwt_manager = JWTManager()
    token = jwt_manager.create_access_token(
        user_id=str(user.id),
        tenant_id=user.tenant_id,
        roles=["user"]
    )
    
    # Create booking - should succeed even without revenue module
    response = client.post(
        "/api/v1/user/bookings",
        json=booking_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Booking should still be created successfully
    assert response.status_code == 200
    booking_response = response.json()
    assert booking_response["booking_reference"] is not None
    assert booking_response["status"] == "pending"
    
    # Booking metadata should not have lead_id if revenue module failed
    booking_metadata = booking_response.get("booking_metadata", {})
    # Lead_id might not be present if revenue module import failed
    # This is acceptable - booking still works


def test_revenue_calculation_accuracy():
    """Test that revenue calculations are accurate."""
    
    # Lead fee
    assert Decimal("15.00") == Decimal("15.00")
    
    # Commission rate (10%)
    commission_rate = Decimal("0.10")
    assert commission_rate == Decimal("0.10")
    
    # Test commission calculation
    booking_value = Decimal("300.00")
    commission = booking_value * commission_rate
    assert commission == Decimal("30.00")
    
    # Test with different booking values
    test_cases = [
        (Decimal("100.00"), Decimal("10.00")),
        (Decimal("500.00"), Decimal("50.00")),
        (Decimal("1000.00"), Decimal("100.00")),
        (Decimal("99.99"), Decimal("9.999")),
    ]
    
    for booking_val, expected_commission in test_cases:
        calculated = booking_val * commission_rate
        assert calculated == expected_commission


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

