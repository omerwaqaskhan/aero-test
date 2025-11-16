"""FastAPI routers for user features: favorites, bookings, price alerts, saved searches, reviews."""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
import json
import uuid as uuid_lib

from auth_module.infrastructure.db.database import get_db
from typing import Optional as Opt
from fastapi import Security, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from auth_module.infrastructure.db.models import UserModel
from auth_module.core.security import JWTManager
from auth_module.core.rate_limiter import rate_limit
from search_booking_module.api.user_schemas import (
    FavoriteResponse, CreateFavoriteRequest,
    BookingResponse, CreateBookingRequest, UpdateBookingStatusRequest,
    PriceAlertResponse, CreatePriceAlertRequest,
    SavedSearchResponse, CreateSavedSearchRequest,
    UserReviewResponse, CreateUserReviewRequest, MarkReviewHelpfulRequest
)
from search_booking_module.infrastructure.db.user_models import (
    FavoriteModel, BookingModel, PriceAlertModel, SavedSearchModel, UserReviewModel,
    BookingStatus, PriceAlertStatus
)
from search_booking_module.infrastructure.db.models import HotelModel, OfferModel

router = APIRouter(prefix="/api/v1/user", tags=["user-features"])

security = HTTPBearer(auto_error=False)

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db)
) -> UserModel:
    """Get current authenticated user."""
    try:
        token = credentials.credentials
        jwt_manager = JWTManager()
        payload = jwt_manager.verify_token(token, "access")
        
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        user = db.query(UserModel).filter(UserModel.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}"
        )

def get_current_user_optional(
    credentials: Opt[HTTPAuthorizationCredentials] = Security(security),
    db: Session = Depends(get_db)
) -> Opt[UserModel]:
    """Get current user if authenticated, otherwise return None."""
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        jwt_manager = JWTManager()
        payload = jwt_manager.verify_token(token, "access")
        
        if not payload:
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        user = db.query(UserModel).filter(UserModel.id == user_id).first()
        return user
    except Exception:
        return None


# Favorites Endpoints
@router.post("/favorites", response_model=FavoriteResponse)
async def create_favorite(
    request: CreateFavoriteRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Add a hotel to favorites."""
    # Check if hotel exists
    hotel = db.query(HotelModel).filter(HotelModel.id == request.hotel_id).first()
    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")
    
    # Check if already favorited
    existing = db.query(FavoriteModel).filter(
        FavoriteModel.user_id == str(current_user.id),
        FavoriteModel.hotel_id == request.hotel_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Hotel already in favorites")
    
    # Create favorite using raw SQL to avoid FK resolution issues
    from sqlalchemy import text
    import uuid as uuid_lib
    favorite_id = str(uuid_lib.uuid4())
    
    try:
        db.execute(text("""
            INSERT INTO favorites (id, user_id, hotel_id, created_at)
            VALUES (:id, :user_id, :hotel_id, NOW())
        """), {
            "id": favorite_id,
            "user_id": str(current_user.id),
            "hotel_id": request.hotel_id
        })
        db.commit()
        
        # Fetch the created favorite
        result = db.execute(text("""
            SELECT id, user_id, hotel_id, created_at
            FROM favorites
            WHERE id = :id
        """), {"id": favorite_id})
        row = result.fetchone()
        
        return FavoriteResponse(
            id=row[0],
            user_id=row[1],
            hotel_id=row[2],
            created_at=row[3]
        )
    except Exception as e:
        db.rollback()
        # If it's a unique constraint violation, hotel is already favorited
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            raise HTTPException(status_code=400, detail="Hotel already in favorites")
        raise


@router.delete("/favorites/{hotel_id}")
async def delete_favorite(
    hotel_id: str,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Remove a hotel from favorites."""
    favorite = db.query(FavoriteModel).filter(
        FavoriteModel.user_id == str(current_user.id),
        FavoriteModel.hotel_id == hotel_id
    ).first()
    
    if not favorite:
        raise HTTPException(status_code=404, detail="Favorite not found")
    
    db.delete(favorite)
    db.commit()
    
    return {"message": "Favorite removed successfully"}


@router.get("/favorites", response_model=List[FavoriteResponse])
async def get_favorites(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Get user's favorites."""
    favorites = db.query(FavoriteModel).filter(
        FavoriteModel.user_id == str(current_user.id)
    ).order_by(FavoriteModel.created_at.desc()).all()
    
    return [
        FavoriteResponse(
            id=f.id,
            user_id=f.user_id,
            hotel_id=f.hotel_id,
            created_at=f.created_at
        )
        for f in favorites
    ]


@router.get("/favorites/{hotel_id}/check")
async def check_favorite(
    hotel_id: str,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Check if a hotel is in favorites."""
    favorite = db.query(FavoriteModel).filter(
        FavoriteModel.user_id == str(current_user.id),
        FavoriteModel.hotel_id == hotel_id
    ).first()
    
    return {"is_favorite": favorite is not None}


# Booking Endpoints
@router.post("/bookings", response_model=BookingResponse)
@rate_limit("10/minute")  # Rate limit booking creation
async def create_booking(
    http_request: Request,  # Required for rate_limit decorator
    request: CreateBookingRequest,
    db: Session = Depends(get_db),
    current_user: Opt[UserModel] = Depends(get_current_user_optional)
):
    """Create a booking."""
    # Validate dates
    if request.check_out <= request.check_in:
        raise HTTPException(status_code=400, detail="Check-out must be after check-in")
    
    # Check if hotel exists
    hotel = db.query(HotelModel).filter(HotelModel.id == request.hotel_id).first()
    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")
    
    # Get offer if specified
    offer = None
    if getattr(request, 'offer_id', None):
        offer = db.query(OfferModel).filter(OfferModel.id == request.offer_id).first()
        if not offer:
            raise HTTPException(status_code=404, detail="Offer not found")
        total_price = float(offer.price) * (request.check_out - request.check_in).days
    else:
        # Estimate price (in production, would fetch from provider)
        total_price = 100.0 * (request.check_out - request.check_in).days
    
    # Generate booking reference
    booking_reference = f"BK{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{str(current_user.id)[:8] if current_user else 'GUEST'}"
    booking_id = str(uuid_lib.uuid4())
    
    # Create booking using raw SQL to avoid FK resolution issues
    from sqlalchemy import text
    try:
        db.execute(text("""
            INSERT INTO bookings (
                id, user_id, hotel_id, offer_id, booking_reference,
                check_in, check_out, guests, rooms,
                guest_name, guest_email, guest_phone,
                total_price, currency, taxes_included, status,
                provider, provider_booking_id, affiliate_link,
                special_requests, cancellation_policy, booking_metadata,
                booked_at, created_at, updated_at
            )
            VALUES (
                :id, :user_id, :hotel_id, :offer_id, :booking_reference,
                :check_in, :check_out, :guests, :rooms,
                :guest_name, :guest_email, :guest_phone,
                :total_price, :currency, :taxes_included, :status,
                :provider, :provider_booking_id, :affiliate_link,
                :special_requests, :cancellation_policy, :booking_metadata,
                NOW(), NOW(), NOW()
            )
        """), {
            "id": booking_id,
            "user_id": str(current_user.id) if current_user else None,
            "hotel_id": request.hotel_id,
            "offer_id": request.offer_id,
            "booking_reference": booking_reference,
            "check_in": request.check_in,
            "check_out": request.check_out,
            "guests": request.guests,
            "rooms": request.rooms,
            "guest_name": request.guest_name,
            "guest_email": request.guest_email,
            "guest_phone": request.guest_phone,
            "total_price": str(total_price),
            "currency": getattr(offer, 'currency', 'USD') if offer else "USD",
            "taxes_included": getattr(offer, 'taxes_included', False) if offer else False,
            "status": BookingStatus.PENDING.value,
            "provider": offer.provider.value if offer and hasattr(offer, 'provider') and offer.provider else None,
            "provider_booking_id": getattr(request, 'provider_booking_id', None),
            "affiliate_link": getattr(request, 'affiliate_link', None),
            "special_requests": getattr(request, 'special_requests', None),
            "cancellation_policy": json.dumps(getattr(offer, 'cancellation_policy', {}) if offer else {}),
            "booking_metadata": json.dumps(getattr(request, 'booking_metadata', None) or {})
        })
        db.commit()
        
        # Fetch the created booking
        result = db.execute(text("""
            SELECT id, user_id, hotel_id, offer_id, booking_reference,
                   check_in, check_out, guests, rooms,
                   guest_name, guest_email, guest_phone,
                   total_price, currency, taxes_included, status,
                   provider, provider_booking_id, affiliate_link,
                   special_requests, cancellation_policy, booking_metadata,
                   booked_at, confirmed_at, cancelled_at, created_at, updated_at
            FROM bookings
            WHERE id = :id
        """), {"id": booking_id})
        row = result.fetchone()
        
        booking = {
            "id": row[0],
            "user_id": row[1],
            "hotel_id": row[2],
            "offer_id": row[3],
            "booking_reference": row[4],
            "check_in": row[5],
            "check_out": row[6],
            "guests": row[7],
            "rooms": row[8],
            "guest_name": row[9],
            "guest_email": row[10],
            "guest_phone": row[11],
            "total_price": float(row[12]),
            "currency": row[13],
            "taxes_included": row[14],
            "status": row[15],
            "provider": row[16],
            "provider_booking_id": row[17],
            "affiliate_link": row[18],
            "special_requests": row[19],
            "cancellation_policy": json.loads(row[20]) if row[20] else {},
            "booking_metadata": json.loads(row[21]) if row[21] else {},
            "booked_at": row[22],
            "confirmed_at": row[23],
            "cancelled_at": row[24],
            "created_at": row[25],
            "updated_at": row[26]
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create booking: {str(e)}")
    
    return BookingResponse(
        id=booking["id"],
        user_id=booking["user_id"],
        hotel_id=booking["hotel_id"],
        offer_id=booking["offer_id"],
        booking_reference=booking["booking_reference"],
        check_in=booking["check_in"],
        check_out=booking["check_out"],
        guests=booking["guests"],
        rooms=booking["rooms"],
        guest_name=booking["guest_name"],
        guest_email=booking["guest_email"],
        guest_phone=booking["guest_phone"],
        total_price=Decimal(str(booking["total_price"])),
        currency=booking["currency"],
        taxes_included=booking["taxes_included"],
        status=booking["status"],
        provider=booking["provider"],
        provider_booking_id=booking["provider_booking_id"],
        affiliate_link=booking["affiliate_link"],
        special_requests=booking["special_requests"],
        cancellation_policy=booking["cancellation_policy"],
        booking_metadata=booking["booking_metadata"],
        booked_at=booking["booked_at"],
        confirmed_at=booking["confirmed_at"],
        cancelled_at=booking["cancelled_at"],
        created_at=booking["created_at"],
        updated_at=booking["updated_at"]
    )


@router.get("/bookings", response_model=List[BookingResponse])
async def get_bookings(
    status: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Get user's bookings."""
    query = db.query(BookingModel).filter(BookingModel.user_id == str(current_user.id))
    
    if status:
        try:
            query = query.filter(BookingModel.status == BookingStatus(status))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid status")
    
    bookings = query.order_by(BookingModel.booked_at.desc()).all()
    
    return [
        BookingResponse(
            id=b.id,
            user_id=b.user_id,
            hotel_id=b.hotel_id,
            offer_id=b.offer_id,
            booking_reference=b.booking_reference,
            check_in=b.check_in,
            check_out=b.check_out,
            guests=b.guests,
            rooms=b.rooms,
            guest_name=b.guest_name,
            guest_email=b.guest_email,
            guest_phone=b.guest_phone,
            total_price=b.total_price,
            currency=b.currency,
            taxes_included=b.taxes_included,
            status=b.status.value,
            provider=b.provider,
            provider_booking_id=b.provider_booking_id,
            booked_at=b.booked_at,
            confirmed_at=b.confirmed_at,
            cancelled_at=b.cancelled_at,
            special_requests=b.special_requests,
            cancellation_policy=b.cancellation_policy,
            created_at=b.created_at,
            updated_at=b.updated_at
        )
        for b in bookings
    ]


@router.get("/bookings/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: str,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Get a specific booking."""
    booking = db.query(BookingModel).filter(
        BookingModel.id == booking_id,
        BookingModel.user_id == str(current_user.id)
    ).first()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    return BookingResponse(
        id=booking.id,
        user_id=booking.user_id,
        hotel_id=booking.hotel_id,
        offer_id=booking.offer_id,
        booking_reference=booking.booking_reference,
        check_in=booking.check_in,
        check_out=booking.check_out,
        guests=booking.guests,
        rooms=booking.rooms,
        guest_name=booking.guest_name,
        guest_email=booking.guest_email,
        guest_phone=booking.guest_phone,
        total_price=booking.total_price,
        currency=booking.currency,
        taxes_included=booking.taxes_included,
        status=booking.status.value,
        provider=booking.provider,
        provider_booking_id=booking.provider_booking_id,
        booked_at=booking.booked_at,
        confirmed_at=booking.confirmed_at,
        cancelled_at=booking.cancelled_at,
        special_requests=booking.special_requests,
        cancellation_policy=booking.cancellation_policy,
        created_at=booking.created_at,
        updated_at=booking.updated_at
    )


@router.patch("/bookings/{booking_id}/status")
async def update_booking_status(
    booking_id: str,
    request: UpdateBookingStatusRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Update booking status (e.g., cancel booking)."""
    booking = db.query(BookingModel).filter(
        BookingModel.id == booking_id,
        BookingModel.user_id == str(current_user.id)
    ).first()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    booking.status = BookingStatus(request.status.value)
    if request.status.value == "cancelled":
        booking.cancelled_at = datetime.utcnow()
    elif request.status.value == "confirmed":
        booking.confirmed_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": "Booking status updated successfully"}


# Price Alert Endpoints
@router.post("/price-alerts", response_model=PriceAlertResponse)
async def create_price_alert(
    request: CreatePriceAlertRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Create a price alert."""
    # Check if hotel exists
    hotel = db.query(HotelModel).filter(HotelModel.id == request.hotel_id).first()
    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")
    
    # Create price alert
    alert = PriceAlertModel(
        user_id=str(current_user.id),
        hotel_id=request.hotel_id,
        target_price=Decimal(str(request.target_price)),
        currency=request.currency,
        check_in=request.check_in,
        check_out=request.check_out,
        guests=request.guests,
        rooms=request.rooms,
        status=PriceAlertStatus.ACTIVE,
        notify_email=request.notify_email,
        notify_sms=request.notify_sms,
        expires_at=request.expires_at
    )
    
    db.add(alert)
    db.commit()
    db.refresh(alert)
    
    return PriceAlertResponse(
        id=alert.id,
        user_id=alert.user_id,
        hotel_id=alert.hotel_id,
        target_price=alert.target_price,
        currency=alert.currency,
        check_in=alert.check_in,
        check_out=alert.check_out,
        guests=alert.guests,
        rooms=alert.rooms,
        status=alert.status.value,
        triggered_at=alert.triggered_at,
        triggered_price=alert.triggered_price,
        notify_email=alert.notify_email,
        notify_sms=alert.notify_sms,
        created_at=alert.created_at,
        updated_at=alert.updated_at,
        expires_at=alert.expires_at
    )


@router.get("/price-alerts", response_model=List[PriceAlertResponse])
async def get_price_alerts(
    status: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Get user's price alerts."""
    query = db.query(PriceAlertModel).filter(PriceAlertModel.user_id == str(current_user.id))
    
    if status:
        try:
            query = query.filter(PriceAlertModel.status == PriceAlertStatus(status))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid status")
    
    alerts = query.order_by(PriceAlertModel.created_at.desc()).all()
    
    return [
        PriceAlertResponse(
            id=a.id,
            user_id=a.user_id,
            hotel_id=a.hotel_id,
            target_price=a.target_price,
            currency=a.currency,
            check_in=a.check_in,
            check_out=a.check_out,
            guests=a.guests,
            rooms=a.rooms,
            status=a.status.value,
            triggered_at=a.triggered_at,
            triggered_price=a.triggered_price,
            notify_email=a.notify_email,
            notify_sms=a.notify_sms,
            created_at=a.created_at,
            updated_at=a.updated_at,
            expires_at=a.expires_at
        )
        for a in alerts
    ]


@router.delete("/price-alerts/{alert_id}")
async def delete_price_alert(
    alert_id: str,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Delete a price alert."""
    alert = db.query(PriceAlertModel).filter(
        PriceAlertModel.id == alert_id,
        PriceAlertModel.user_id == str(current_user.id)
    ).first()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Price alert not found")
    
    db.delete(alert)
    db.commit()
    
    return {"message": "Price alert deleted successfully"}


# Saved Search Endpoints
@router.post("/saved-searches", response_model=SavedSearchResponse)
async def create_saved_search(
    request: CreateSavedSearchRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Save a search."""
    # Store search parameters in search_query JSONB
    search_query = {
        'destination': request.destination,
        'check_in': request.check_in.isoformat() if request.check_in else None,
        'check_out': request.check_out.isoformat() if request.check_out else None,
        'guests': request.guests,
        'rooms': request.rooms,
        'filters': request.filters
    }
    
    saved_search = SavedSearchModel(
        user_id=str(current_user.id),
        search_query=search_query,
        name=request.name,
        notification_enabled=request.notification_enabled
    )
    
    db.add(saved_search)
    db.commit()
    db.refresh(saved_search)
    
    return SavedSearchResponse(
        id=saved_search.id,
        user_id=saved_search.user_id,
        destination=saved_search.destination,
        check_in=saved_search.check_in,
        check_out=saved_search.check_out,
        guests=saved_search.guests,
        rooms=saved_search.rooms,
        filters=saved_search.filters,
        name=saved_search.name,
        notification_enabled=saved_search.notification_enabled,
        created_at=saved_search.created_at,
        updated_at=saved_search.updated_at,
        last_searched_at=saved_search.last_searched_at
    )


@router.get("/saved-searches", response_model=List[SavedSearchResponse])
async def get_saved_searches(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Get user's saved searches."""
    searches = db.query(SavedSearchModel).filter(
        SavedSearchModel.user_id == str(current_user.id)
    ).order_by(SavedSearchModel.created_at.desc()).all()
    
    return [
        SavedSearchResponse(
            id=s.id,
            user_id=s.user_id,
            destination=s.destination,
            check_in=s.check_in,
            check_out=s.check_out,
            guests=s.guests,
            rooms=s.rooms,
            filters=s.filters,
            name=s.name,
            notification_enabled=s.notification_enabled,
            created_at=s.created_at,
            updated_at=s.updated_at,
            last_searched_at=s.last_searched_at
        )
        for s in searches
    ]


@router.delete("/saved-searches/{search_id}")
async def delete_saved_search(
    search_id: str,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Delete a saved search."""
    search = db.query(SavedSearchModel).filter(
        SavedSearchModel.id == search_id,
        SavedSearchModel.user_id == str(current_user.id)
    ).first()
    
    if not search:
        raise HTTPException(status_code=404, detail="Saved search not found")
    
    db.delete(search)
    db.commit()
    
    return {"message": "Saved search deleted successfully"}


# User Review Endpoints
@router.post("/reviews", response_model=UserReviewResponse)
async def create_user_review(
    request: CreateUserReviewRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Create a user review."""
    # Check if hotel exists
    hotel = db.query(HotelModel).filter(HotelModel.id == request.hotel_id).first()
    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")
    
    # Check if user already reviewed this hotel
    existing = db.query(UserReviewModel).filter(
        UserReviewModel.user_id == str(current_user.id),
        UserReviewModel.hotel_id == request.hotel_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="You have already reviewed this hotel")
    
    # Verify booking if booking_id provided
    verified_booking = False
    if request.booking_id:
        booking = db.query(BookingModel).filter(
            BookingModel.id == request.booking_id,
            BookingModel.user_id == str(current_user.id),
            BookingModel.hotel_id == request.hotel_id,
            BookingModel.status == BookingStatus.COMPLETED
        ).first()
        verified_booking = booking is not None
    
    # Create review
    review = UserReviewModel(
        user_id=str(current_user.id),
        hotel_id=request.hotel_id,
        booking_id=request.booking_id,
        rating=request.rating,
        title=request.title,
        text=request.text,
        category_ratings=request.category_ratings,
        pros=request.pros,
        cons=request.cons,
        verified_booking=verified_booking
    )
    
    db.add(review)
    
    # Update hotel rating (average of all reviews)
    all_reviews = db.query(UserReviewModel).filter(
        UserReviewModel.hotel_id == request.hotel_id,
        UserReviewModel.published == True
    ).all()
    if all_reviews:
        avg_rating = sum(r.rating for r in all_reviews) / len(all_reviews)
        hotel.rating = avg_rating
    
    db.commit()
    db.refresh(review)
    
    return UserReviewResponse(
        id=review.id,
        user_id=review.user_id,
        hotel_id=review.hotel_id,
        booking_id=review.booking_id,
        rating=review.rating,
        title=review.title,
        text=review.text,
        category_ratings=review.category_ratings,
        pros=review.pros,
        cons=review.cons,
        verified_booking=review.verified_booking,
        published=review.published,
        helpful_count=review.helpful_count,
        created_at=review.created_at,
        updated_at=review.updated_at
    )


@router.get("/reviews", response_model=List[UserReviewResponse])
async def get_user_reviews(
    hotel_id: Optional[str] = Query(None, description="Filter by hotel ID"),
    db: Session = Depends(get_db),
    current_user: Opt[UserModel] = Depends(get_current_user_optional)
):
    """Get reviews (user's own or for a hotel)."""
    query = db.query(UserReviewModel).filter(UserReviewModel.published == True)
    
    if current_user and not hotel_id:
        # Get user's own reviews
        query = query.filter(UserReviewModel.user_id == str(current_user.id))
    elif hotel_id:
        # Get reviews for a hotel
        query = query.filter(UserReviewModel.hotel_id == hotel_id)
    else:
        raise HTTPException(status_code=400, detail="Either hotel_id or authentication required")
    
    reviews = query.order_by(UserReviewModel.created_at.desc()).all()
    
    return [
        UserReviewResponse(
            id=r.id,
            user_id=r.user_id,
            hotel_id=r.hotel_id,
            booking_id=r.booking_id,
            rating=r.rating,
            title=r.title,
            text=r.text,
            category_ratings=r.category_ratings,
            pros=r.pros,
            cons=r.cons,
            verified_booking=r.verified_booking,
            published=r.published,
            helpful_count=r.helpful_count,
            created_at=r.created_at,
            updated_at=r.updated_at
        )
        for r in reviews
    ]


@router.post("/reviews/{review_id}/helpful")
async def mark_review_helpful(
    review_id: str,
    request: MarkReviewHelpfulRequest,
    db: Session = Depends(get_db)
):
    """Mark a review as helpful."""
    review = db.query(UserReviewModel).filter(UserReviewModel.id == review_id).first()
    
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    if request.helpful:
        review.helpful_count += 1
    else:
        review.helpful_count = max(0, review.helpful_count - 1)
    
    db.commit()
    
    return {"message": "Review helpful count updated", "helpful_count": review.helpful_count}

