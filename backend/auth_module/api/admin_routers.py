"""Admin API endpoints for managing all models in the system."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)

from ..infrastructure.db.database import get_db
from ..infrastructure.db.models import UserModel, TenantModel
from ..api.routers import get_current_user_id, require_permission
from .schemas import SuccessResponse, PaginationResponse

# Import models from other modules
try:
    from search_booking_module.infrastructure.db.models import (
        HotelModel, RoomModel, OfferModel, ReviewModel, BookingClickModel
    )
    SEARCH_BOOKING_AVAILABLE = True
except ImportError:
    SEARCH_BOOKING_AVAILABLE = False

try:
    from search_booking_module.infrastructure.db.user_models import (
        FavoriteModel, BookingModel, PriceAlertModel, SavedSearchModel, UserReviewModel
    )
    USER_MODELS_AVAILABLE = True
except ImportError:
    USER_MODELS_AVAILABLE = False

try:
    from revenue_module.infrastructure.db.models import (
        SubscriptionModel, SubscriptionPaymentModel, LeadModel,
        HotelListingModel, ListingPaymentModel, SponsoredPlacementModel
    )
    REVENUE_MODELS_AVAILABLE = True
except ImportError:
    REVENUE_MODELS_AVAILABLE = False

admin_router = APIRouter(prefix="/admin", tags=["Admin"])


# Helper function to serialize models
def serialize_model(model, exclude_fields=None):
    """Serialize a SQLAlchemy model to dict."""
    if exclude_fields is None:
        exclude_fields = []
    
    result = {}
    for column in model.__table__.columns:
        if column.name in exclude_fields:
            continue
        try:
            value = getattr(model, column.name)
            if isinstance(value, datetime):
                result[column.name] = value.isoformat()
            elif isinstance(value, uuid.UUID):
                result[column.name] = str(value)
            elif hasattr(value, 'value'):  # Handle enums
                result[column.name] = value.value
            elif hasattr(value, '__dict__'):  # Handle complex objects
                result[column.name] = str(value)
            else:
                result[column.name] = value
        except (ValueError, AttributeError) as e:
            # Skip fields that can't be serialized (e.g., invalid enum values)
            continue
    return result


# Users endpoints
@admin_router.get("/users", response_model=SuccessResponse)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """List all users with pagination and filtering."""
    query = db.query(UserModel)
    
    if search:
        query = query.filter(
            or_(
                UserModel.email.ilike(f"%{search}%"),
                UserModel.first_name.ilike(f"%{search}%"),
                UserModel.last_name.ilike(f"%{search}%")
            )
        )
    
    if role:
        query = query.filter(UserModel.role == role)
    
    if status:
        query = query.filter(UserModel.status == status)
    
    total = query.count()
    users = query.order_by(UserModel.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return SuccessResponse(
        data={
            "items": [serialize_model(user) for user in users],
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size
            }
        }
    )


@admin_router.get("/users/{user_id}", response_model=SuccessResponse)
async def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """Get user details."""
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return SuccessResponse(data=serialize_model(user))


# Hotels endpoints
@admin_router.get("/hotels", response_model=SuccessResponse)
async def list_hotels(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    provider: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """List all hotels with pagination and filtering."""
    if not SEARCH_BOOKING_AVAILABLE:
        raise HTTPException(status_code=503, detail="Search booking module not available")
    
    query = db.query(HotelModel)
    
    if search:
        query = query.filter(HotelModel.name.ilike(f"%{search}%"))
    
    if city:
        query = query.filter(HotelModel.city.ilike(f"%{city}%"))
    
    if country:
        query = query.filter(HotelModel.country.ilike(f"%{country}%"))
    
    if provider:
        query = query.filter(HotelModel.provider == provider)
    
    total = query.count()
    hotels = query.order_by(HotelModel.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return SuccessResponse(
        data={
            "items": [serialize_model(hotel) for hotel in hotels],
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size
            }
        }
    )


@admin_router.get("/hotels/{hotel_id}", response_model=SuccessResponse)
async def get_hotel(
    hotel_id: str,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """Get hotel details."""
    if not SEARCH_BOOKING_AVAILABLE:
        raise HTTPException(status_code=503, detail="Search booking module not available")
    
    hotel = db.query(HotelModel).filter(HotelModel.id == hotel_id).first()
    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")
    
    return SuccessResponse(data=serialize_model(hotel))


# Rooms endpoints
@admin_router.get("/rooms", response_model=SuccessResponse)
async def list_rooms(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    hotel_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """List all rooms with pagination and filtering."""
    if not SEARCH_BOOKING_AVAILABLE:
        raise HTTPException(status_code=503, detail="Search booking module not available")
    
    query = db.query(RoomModel)
    
    if hotel_id:
        query = query.filter(RoomModel.hotel_id == hotel_id)
    
    if search:
        query = query.filter(RoomModel.room_type_name.ilike(f"%{search}%"))
    
    total = query.count()
    rooms = query.order_by(RoomModel.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return SuccessResponse(
        data={
            "items": [serialize_model(room) for room in rooms],
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size
            }
        }
    )


# Offers endpoints
@admin_router.get("/offers", response_model=SuccessResponse)
async def list_offers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    hotel_id: Optional[str] = Query(None),
    room_id: Optional[str] = Query(None),
    provider: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """List all offers with pagination and filtering."""
    if not SEARCH_BOOKING_AVAILABLE:
        raise HTTPException(status_code=503, detail="Search booking module not available")
    
    query = db.query(OfferModel)
    
    if hotel_id:
        query = query.filter(OfferModel.hotel_id == hotel_id)
    
    if room_id:
        query = query.filter(OfferModel.room_id == room_id)
    
    if provider:
        query = query.filter(OfferModel.provider == provider)
    
    total = query.count()
    offers = query.order_by(OfferModel.fetched_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return SuccessResponse(
        data={
            "items": [serialize_model(offer) for offer in offers],
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size
            }
        }
    )


# Bookings endpoints
@admin_router.get("/bookings", response_model=SuccessResponse)
async def list_bookings(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id_filter: Optional[str] = Query(None, alias="user_id"),
    hotel_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """List all bookings with pagination and filtering."""
    if not USER_MODELS_AVAILABLE:
        raise HTTPException(status_code=503, detail="User models not available")
    
    try:
        query = db.query(BookingModel)
        
        if user_id_filter:
            query = query.filter(BookingModel.user_id == user_id_filter)
        
        if hotel_id:
            query = query.filter(BookingModel.hotel_id == hotel_id)
        
        if status:
            # Use raw SQL for status filter to avoid enum issues
            from sqlalchemy import text
            query = query.filter(text("status::text = :status")).params(status=status)
        
        total = query.count()
        bookings = query.order_by(BookingModel.booked_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        
        return SuccessResponse(
            data={
                "items": [serialize_model(booking) for booking in bookings],
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": total,
                    "total_pages": (total + page_size - 1) // page_size
                }
            }
        )
    except Exception as e:
        logger.error(f"Error fetching bookings: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch bookings: {str(e)}")


# Reviews endpoints
@admin_router.get("/reviews", response_model=SuccessResponse)
async def list_reviews(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    hotel_id: Optional[str] = Query(None),
    provider: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """List all reviews with pagination and filtering."""
    if not SEARCH_BOOKING_AVAILABLE:
        raise HTTPException(status_code=503, detail="Search booking module not available")
    
    query = db.query(ReviewModel)
    
    if hotel_id:
        query = query.filter(ReviewModel.hotel_id == hotel_id)
    
    if provider:
        query = query.filter(ReviewModel.provider == provider)
    
    total = query.count()
    reviews = query.order_by(ReviewModel.fetched_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return SuccessResponse(
        data={
            "items": [serialize_model(review) for review in reviews],
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size
            }
        }
    )


# Statistics endpoint
@admin_router.get("/stats", response_model=SuccessResponse)
async def get_stats(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """Get system statistics."""
    stats = {
        "users": {
            "total": db.query(UserModel).count(),
            "active": db.query(UserModel).filter(UserModel.status == "active").count(),
            "pending": db.query(UserModel).filter(UserModel.status == "pending").count(),
        },
        "tenants": {
            "total": db.query(TenantModel).count(),
            "active": db.query(TenantModel).filter(TenantModel.status == "active").count(),
        }
    }
    
    try:
        if SEARCH_BOOKING_AVAILABLE:
            stats["hotels"] = {
                "total": db.query(HotelModel).count(),
                "by_provider": {}
            }
            # Count by provider - use raw SQL to avoid enum issues
            from sqlalchemy import text
            try:
                providers = db.execute(
                    text("SELECT provider::text, COUNT(*) FROM hotels GROUP BY provider")
                ).fetchall()
                for provider, count in providers:
                    stats["hotels"]["by_provider"][str(provider)] = count
            except Exception:
                pass  # Skip if query fails
            
            stats["rooms"] = {"total": db.query(RoomModel).count()}
            stats["offers"] = {"total": db.query(OfferModel).count()}
            stats["reviews"] = {"total": db.query(ReviewModel).count()}
    except Exception as e:
        # If search booking models fail, just skip them
        pass
    
    try:
        if USER_MODELS_AVAILABLE:
            stats["bookings"] = {
                "total": db.query(BookingModel).count(),
                "by_status": {}
            }
            # Count by status - use raw SQL to avoid enum issues
            from sqlalchemy import text
            try:
                statuses = db.execute(
                    text("SELECT status::text, COUNT(*) FROM bookings GROUP BY status")
                ).fetchall()
                for status, count in statuses:
                    stats["bookings"]["by_status"][str(status)] = count
            except Exception:
                pass  # Skip if query fails
            
            stats["favorites"] = {"total": db.query(FavoriteModel).count()}
            stats["price_alerts"] = {"total": db.query(PriceAlertModel).count()}
            stats["saved_searches"] = {"total": db.query(SavedSearchModel).count()}
    except Exception as e:
        # If user models fail, just skip them
        pass
    
    return SuccessResponse(data=stats)

