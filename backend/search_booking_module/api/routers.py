"""FastAPI routers for search and booking module."""

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session, joinedload
from typing import Optional, List
from datetime import date

from auth_module.infrastructure.db.database import get_db
from auth_module.core.rate_limiter import rate_limit
from auth_module.core.cache import cached, get_cached, set_cached, cache_key
from search_booking_module.api.schemas import (
    SearchRequest,
    SearchResponse,
    SearchResultResponse,
    HotelDetailsRequest,
    HotelDetailsResponse,
    BookingClickRequest,
    BookingClickResponse,
    HotelResponse,
    RoomResponse,
    OfferResponse,
    ReviewResponse,
    ErrorResponse,
    SortByEnum,
    SortOrderEnum,
)
from search_booking_module.domain.models import SearchFilters, Provider
from search_booking_module.domain.services import SearchService, BookingService
from search_booking_module.infrastructure.providers.base import BaseProvider
from search_booking_module.infrastructure.db.models import HotelModel, RoomModel, OfferModel, ReviewModel

# Create router
router = APIRouter(prefix="/api/v1/search-booking", tags=["search-booking"])


def safe_provider_enum(provider_value):
    """Safely convert provider value to ProviderEnum.
    
    Handles invalid provider values by defaulting to ProviderEnum.BOOKING_COM.
    """
    try:
        # Import here to avoid circular imports
        from search_booking_module.api.schemas import ProviderEnum
        
        if hasattr(provider_value, 'value'):
            # It's an enum, get the value
            value = provider_value.value
        elif isinstance(provider_value, str):
            value = provider_value.lower()
        else:
            value = str(provider_value).lower()
        
        # Normalize the value
        value = value.replace('-', '_')
        
        # Check if it's a valid enum value and return the enum
        # Handle both uppercase (from database) and lowercase (from enum values)
        value_upper = value.upper()
        if value == 'booking_com' or value_upper == 'BOOKING_COM':
            return ProviderEnum.BOOKING_COM
        elif value == 'expedia' or value_upper == 'EXPEDIA':
            return ProviderEnum.EXPEDIA
        elif value == 'direct' or value_upper == 'DIRECT':
            return ProviderEnum.DIRECT
        elif value == 'agoda' or value_upper == 'AGODA':
            return ProviderEnum.AGODA
        else:
            # Default to booking_com for unknown providers
            return ProviderEnum.BOOKING_COM
    except Exception:
        # Fallback to default provider
        from search_booking_module.api.schemas import ProviderEnum
        return ProviderEnum.BOOKING_COM


# Initialize providers (in production, this would come from config)
def get_providers() -> List[BaseProvider]:
    """Get list of available providers."""
    # Mock API keys - in production, get from config
    providers = [
        # BookingComProvider(api_key="booking_mock_key"),
        # ExpediaProvider(api_key="expedia_mock_key")
    ]
    return providers


@router.get("/search", response_model=SearchResponse)
@rate_limit("30/minute")  # Rate limit search endpoint
async def search_hotels(
    request: Request,  # Required for rate_limit decorator
    destination: str = Query(..., description="Destination city or location"),
    check_in: date = Query(..., description="Check-in date"),
    check_out: date = Query(..., description="Check-out date"),
    guests: int = Query(1, ge=1, le=10, description="Number of guests"),
    rooms: int = Query(1, ge=1, le=5, description="Number of rooms"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price per night"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price per night"),
    stars: Optional[List[int]] = Query(None, description="Filter by star rating"),
    amenities: Optional[List[str]] = Query(None, description="Filter by amenities"),
    rating_min: Optional[float] = Query(None, ge=0, le=5, description="Minimum rating"),
    latitude: Optional[float] = Query(None, ge=-90, le=90, description="Latitude"),
    longitude: Optional[float] = Query(None, ge=-180, le=180, description="Longitude"),
    radius: Optional[float] = Query(None, ge=0, description="Search radius in kilometers"),
    sort_by: SortByEnum = Query(SortByEnum.PRICE, description="Sort field"),
    sort_order: SortOrderEnum = Query(SortOrderEnum.ASC, description="Sort order"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Results per page"),
    db: Session = Depends(get_db),
    providers: List[BaseProvider] = Depends(get_providers)
):
    """Search for hotels across multiple providers.
    
    This endpoint searches for hotels across all configured providers,
    aggregates results, and returns sorted and filtered results.
    Results are cached for 10 minutes to improve performance.
    """
    try:
        # Generate cache key from search parameters
        cache_key_str = cache_key(
            "search",
            destination=destination,
            check_in=str(check_in),
            check_out=str(check_out),
            guests=guests,
            rooms=rooms,
            min_price=min_price,
            max_price=max_price,
            stars=tuple(sorted(stars)) if stars else None,
            amenities=tuple(sorted(amenities)) if amenities else None,
            rating_min=rating_min,
            latitude=latitude,
            longitude=longitude,
            radius=radius,
            sort_by=sort_by.value,
            sort_order=sort_order.value,
            page=page,
            page_size=page_size
        )
        
        # Try to get from cache (10 minutes TTL for search results)
        cached_result = get_cached(cache_key_str)
        if cached_result is not None:
            return SearchResponse(**cached_result)
        # Build search filters
        filters = SearchFilters(
            destination=destination,
            check_in=check_in,
            check_out=check_out,
            guests=guests,
            rooms=rooms,
            min_price=min_price,
            max_price=max_price,
            stars=stars,
            amenities=amenities,
            rating_min=rating_min,
            latitude=latitude,
            longitude=longitude,
            radius=radius
        )
        
        # Validate filters
        if not filters.is_valid():
            raise HTTPException(
                status_code=400,
                detail="Invalid search filters. Check-in must be before check-out."
            )
        
        # Create search service (use database by default)
        search_service = SearchService(providers=providers, db_session=db, use_database=True)
        
        # Perform search
        results = await search_service.search_hotels(
            filters=filters,
            sort_by=sort_by.value,
            sort_order=sort_order.value,
            page=page,
            page_size=page_size
        )
        
        # Convert to response format
        search_results = []
        for result in results:
            # Convert hotel
            hotel_response = HotelResponse(
                id=result.hotel.id,
                provider_hotel_id=result.hotel.provider_hotel_id,
                provider=safe_provider_enum(result.hotel.provider),
                name=result.hotel.name,
                address=result.hotel.address,
                city=result.hotel.city,
                country=result.hotel.country,
                latitude=result.hotel.latitude,
                longitude=result.hotel.longitude,
                stars=result.hotel.stars,
                description=result.hotel.description,
                images=result.hotel.images,
                amenities=result.hotel.amenities,
                created_at=result.hotel.created_at,
                updated_at=result.hotel.updated_at
            )
            
            # Convert offers with room information
            offers_response = []
            for offer in result.offers:
                # Get room details if room_id exists
                room_type = None
                if offer.room_id:
                    room = db.query(RoomModel).filter(RoomModel.id == offer.room_id).first()
                    if room:
                        room_type = room.room_type_name
                
                offer_response = OfferResponse(
                    id=offer.id,
                    hotel_id=offer.hotel_id,
                    room_id=offer.room_id,
                    provider=safe_provider_enum(offer.provider),
                    provider_rate_id=offer.provider_rate_id,
                    currency=offer.currency,
                    price=offer.price,
                    taxes_included=offer.taxes_included,
                    check_in=offer.check_in,
                    check_out=offer.check_out,
                    availability_count=offer.availability_count,
                    cancellation_policy=offer.cancellation_policy,
                    total_nights=offer.get_total_nights(),
                    total_price=offer.get_total_price(),
                    expires_at=offer.expires_at,
                    room_type=room_type
                )
                offers_response.append(offer_response)
            
            search_result = SearchResultResponse(
                hotel=hotel_response,
                offers=offers_response,
                best_price=result.best_price,
                average_rating=result.average_rating,
                review_count=result.review_count,
                is_sponsored=getattr(result, 'is_sponsored', False),
                sponsor_priority=getattr(result, 'sponsor_priority', 0)
            )
            search_results.append(search_result)
        
        # Calculate pagination
        total = len(search_results)  # In production, get from service
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        
        response = SearchResponse(
            results=search_results,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
        # Cache the result (10 minutes TTL for search results)
        set_cached(cache_key_str, response.dict(), ttl=600)
        
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/hotels", response_model=dict)
@rate_limit("60/minute")  # Rate limit hotels listing
async def get_all_hotels(
    request: Request,  # Required for rate_limit decorator
    city: Optional[str] = Query(None, description="Filter by city"),
    country: Optional[str] = Query(None, description="Filter by country"),
    min_stars: Optional[int] = Query(None, ge=0, le=5, description="Minimum star rating"),
    max_stars: Optional[int] = Query(None, ge=0, le=5, description="Maximum star rating"),
    min_rating: Optional[float] = Query(None, ge=0, le=5, description="Minimum rating"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Results per page"),
    db: Session = Depends(get_db)
):
    """Get all hotels from database.
    
    Returns a list of all hotels with optional filtering.
    """
    try:
        # Build query
        query = db.query(HotelModel)
        
        # Apply filters
        if city:
            query = query.filter(HotelModel.city.ilike(f"%{city}%"))
        if country:
            query = query.filter(HotelModel.country.ilike(f"%{country}%"))
        if min_stars is not None:
            query = query.filter(HotelModel.stars >= min_stars)
        if max_stars is not None:
            query = query.filter(HotelModel.stars <= max_stars)
        if min_rating is not None:
            query = query.filter(HotelModel.rating >= min_rating)
        
        # Get total count
        total = query.count()
        
        # Paginate
        offset = (page - 1) * page_size
        hotels = query.offset(offset).limit(page_size).all()
        
        # Convert to response format
        hotels_response = []
        for hotel in hotels:
            hotel_response = HotelResponse(
                id=hotel.id,
                provider_hotel_id=hotel.provider_hotel_id,
                provider=safe_provider_enum(hotel.provider),
                name=hotel.name,
                address=hotel.address if isinstance(hotel.address, dict) else {},
                city=hotel.city,
                country=hotel.country,
                latitude=hotel.latitude,
                longitude=hotel.longitude,
                stars=hotel.stars,
                rating=hotel.rating,
                description=hotel.description or "",
                images=hotel.images if isinstance(hotel.images, list) else [],
                amenities=hotel.amenities if isinstance(hotel.amenities, list) else [],
                created_at=hotel.created_at,
                updated_at=hotel.updated_at
            )
            hotels_response.append(hotel_response)
        
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        
        return {
            "hotels": hotels_response,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch hotels: {str(e)}")


@router.get("/hotels/{hotel_identifier}", response_model=HotelDetailsResponse)
async def get_hotel_details(
    hotel_identifier: str,
    check_in: Optional[date] = Query(None, description="Check-in date"),
    check_out: Optional[date] = Query(None, description="Check-out date"),
    guests: int = Query(1, ge=1, le=10, description="Number of guests"),
    rooms: int = Query(1, ge=1, le=5, description="Number of rooms"),
    db: Session = Depends(get_db),
    providers: List[BaseProvider] = Depends(get_providers)
):
    """Get detailed information about a specific hotel.
    
    This endpoint accepts either a hotel ID (UUID) or a slug (hotel name).
    Returns detailed information about a hotel including available rooms, offers, and reviews.
    Results are cached for 30 minutes to improve performance.
    """
    try:
        # Generate cache key from hotel identifier and query parameters
        cache_key_str = cache_key(
            "hotel_details",
            hotel_identifier=hotel_identifier,
            check_in=str(check_in) if check_in else None,
            check_out=str(check_out) if check_out else None,
            guests=guests,
            rooms=rooms
        )
        
        # Try to get from cache (30 minutes TTL for hotel details)
        cached_result = get_cached(cache_key_str)
        if cached_result is not None:
            return HotelDetailsResponse(**cached_result)
        
        import re
        from sqlalchemy import func
        
        # Check if it's a UUID format
        uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.I)
        
        if uuid_pattern.match(hotel_identifier):
            # It's a UUID, query by ID
            # Use raw SQL to avoid SQLAlchemy enum conversion issues
            try:
                hotel = db.query(HotelModel).filter(HotelModel.id == hotel_identifier).first()
            except (ValueError, AttributeError):
                # If enum conversion fails, query using raw SQL
                from sqlalchemy import text
                result = db.execute(
                    text("SELECT * FROM hotels WHERE id = :hotel_id"),
                    {"hotel_id": hotel_identifier}
                ).fetchone()
                if result:
                    # Create hotel object manually
                    hotel = HotelModel()
                    for key, value in result._mapping.items():
                        if key == 'provider' and value not in ['booking_com', 'expedia', 'direct', 'agoda']:
                            setattr(hotel, key, Provider.BOOKING_COM)  # Default to BOOKING_COM
                        else:
                            setattr(hotel, key, value)
                else:
                    hotel = None
        else:
            # It's a slug, generate slug from hotel name and match
            # Clean the incoming slug (remove "opens-in-new-window" etc.)
            cleaned_identifier = hotel_identifier.lower()
            cleaned_identifier = re.sub(r'\s*opens?\s*in\s*new\s*window\s*', '', cleaned_identifier, flags=re.IGNORECASE)
            cleaned_identifier = cleaned_identifier.strip('-')
            
            # Try to find hotel by matching slug pattern in name
            # Use raw SQL to avoid SQLAlchemy enum conversion issues with invalid provider values
            from sqlalchemy import text
            hotels_raw = db.execute(text("SELECT id, name, provider::text FROM hotels")).fetchall()
            hotel = None
            hotels = []
            
            def generate_slug(name):
                """Generate a slug from hotel name."""
                # Clean the name first
                slug = name.lower().strip()
                # Remove "Opens in new window" and similar text
                slug = re.sub(r'\s*opens?\s*in\s*new\s*window\s*', '', slug, flags=re.IGNORECASE)
                # Remove special chars except spaces and hyphens
                slug = re.sub(r'[^\w\s-]', '', slug)
                # Replace spaces/hyphens with single hyphen
                slug = re.sub(r'[-\s]+', '-', slug)
                # Trim hyphens
                slug = slug.strip('-')
                return slug
            
            # Match hotels by slug
            for row in hotels_raw:
                hotel_id, hotel_name, provider_value = row
                hotel_slug = generate_slug(hotel_name)
                
                if hotel_slug == cleaned_identifier:
                    # Found matching hotel, now load it safely with eager loading to avoid N+1
                    try:
                        hotel = db.query(HotelModel).options(
                            joinedload(HotelModel.rooms),
                            joinedload(HotelModel.offers),
                            joinedload(HotelModel.reviews)
                        ).filter(HotelModel.id == hotel_id).first()
                    except (ValueError, AttributeError):
                        # If enum conversion fails, query using raw SQL and create object
                        hotel_row = db.execute(
                            text("SELECT * FROM hotels WHERE id = :hotel_id"),
                            {"hotel_id": hotel_id}
                        ).fetchone()
                        if hotel_row:
                            hotel = HotelModel()
                            for key, value in hotel_row._mapping.items():
                                if key == 'provider':
                                    # Convert invalid provider to valid one
                                    if value not in ['booking_com', 'expedia', 'direct', 'agoda', 'BOOKING_COM', 'EXPEDIA', 'DIRECT', 'AGODA']:
                                        setattr(hotel, key, Provider.BOOKING_COM)
                                    else:
                                        try:
                                            setattr(hotel, key, Provider[value.upper()] if value.isupper() else Provider(value))
                                        except:
                                            setattr(hotel, key, Provider.BOOKING_COM)
                                else:
                                    setattr(hotel, key, value)
                    break
            
            # Fallback: try partial match if exact match fails
            if not hotel:
                for row in hotels_raw:
                    hotel_id, hotel_name, provider_value = row
                    hotel_slug = generate_slug(hotel_name)
                    
                    # Try matching cleaned versions
                    if cleaned_identifier in hotel_slug or hotel_slug in cleaned_identifier:
                        try:
                            hotel = db.query(HotelModel).filter(HotelModel.id == hotel_id).first()
                        except (ValueError, AttributeError):
                            hotel_row = db.execute(
                                text("SELECT * FROM hotels WHERE id = :hotel_id"),
                                {"hotel_id": hotel_id}
                            ).fetchone()
                            if hotel_row:
                                hotel = HotelModel()
                                for key, value in hotel_row._mapping.items():
                                    if key == 'provider':
                                        if value not in ['booking_com', 'expedia', 'direct', 'agoda', 'BOOKING_COM', 'EXPEDIA', 'DIRECT', 'AGODA']:
                                            setattr(hotel, key, Provider.BOOKING_COM)
                                        else:
                                            try:
                                                setattr(hotel, key, Provider[value.upper()] if value.isupper() else Provider(value))
                                            except:
                                                setattr(hotel, key, Provider.BOOKING_COM)
                                    else:
                                        setattr(hotel, key, value)
                        if hotel:
                            break
                    
                    # Also try matching the original identifier
                    if hotel_identifier in hotel_slug or hotel_slug in hotel_identifier:
                        if not hotel:
                            try:
                                hotel = db.query(HotelModel).filter(HotelModel.id == hotel_id).first()
                            except (ValueError, AttributeError):
                                hotel_row = db.execute(
                                    text("SELECT * FROM hotels WHERE id = :hotel_id"),
                                    {"hotel_id": hotel_id}
                                ).fetchone()
                                if hotel_row:
                                    hotel = HotelModel()
                                    for key, value in hotel_row._mapping.items():
                                        if key == 'provider':
                                            if value not in ['booking_com', 'expedia', 'direct', 'agoda', 'BOOKING_COM', 'EXPEDIA', 'DIRECT', 'AGODA']:
                                                setattr(hotel, key, Provider.BOOKING_COM)
                                            else:
                                                try:
                                                    setattr(hotel, key, Provider[value.upper()] if value.isupper() else Provider(value))
                                                except:
                                                    setattr(hotel, key, Provider.BOOKING_COM)
                                        else:
                                            setattr(hotel, key, value)
                        if hotel:
                            break
        
        if not hotel:
            raise HTTPException(status_code=404, detail="Hotel not found")
        
        # Convert hotel to response
        # Safely get provider value - handle cases where SQLAlchemy enum conversion fails
        try:
            hotel_provider = hotel.provider
        except (ValueError, AttributeError) as e:
            # If provider enum conversion fails, get raw value from database
            from sqlalchemy import text
            result = db.execute(text("SELECT provider::text FROM hotels WHERE id = :hotel_id"), {"hotel_id": hotel.id})
            raw_provider = result.scalar()
            hotel_provider = raw_provider if raw_provider else 'booking_com'
        
        hotel_response = HotelResponse(
            id=hotel.id,
            provider_hotel_id=hotel.provider_hotel_id,
            provider=safe_provider_enum(hotel_provider),
            name=hotel.name,
            address=hotel.address if isinstance(hotel.address, dict) else {},
            city=hotel.city,
            country=hotel.country,
            latitude=hotel.latitude,
            longitude=hotel.longitude,
            stars=hotel.stars,
            rating=hotel.rating,
            description=hotel.description or "",
            property_overview=hotel.property_overview or "",
            images=hotel.images if isinstance(hotel.images, list) else [],
            amenities=hotel.amenities if isinstance(hotel.amenities, list) else [],
            policies=hotel.policies if isinstance(hotel.policies, dict) else {},
            created_at=hotel.created_at,
            updated_at=hotel.updated_at
        )
        
        # Get rooms for this hotel
        # Use hotel.id instead of hotel_id variable to ensure we have the correct ID
        rooms = db.query(RoomModel).filter(RoomModel.hotel_id == hotel.id).all()
        rooms_response = []
        for room in rooms:
            room_response = RoomResponse(
                id=room.id,
                hotel_id=room.hotel_id,
                room_type_name=room.room_type_name,
                description=room.description or "",
                images=room.images if isinstance(room.images, list) else [],
                occupancy=room.occupancy if isinstance(room.occupancy, dict) else {},
                amenities=room.amenities if isinstance(room.amenities, list) else [],
                created_at=room.created_at,
                updated_at=room.updated_at
            )
            rooms_response.append(room_response)
        
        # Get offers for this hotel
        # Use hotel.id instead of hotel_id variable to ensure we have the correct ID
        offers_query = db.query(OfferModel).filter(OfferModel.hotel_id == hotel.id)
        
        if check_in and check_out:
            offers_query = offers_query.filter(
                OfferModel.check_in <= check_in,
                OfferModel.check_out >= check_out
            )
        
        offers = offers_query.all()
        
        # Convert offers to response
        offers_response = []
        for offer in offers:
            # Safely get provider value
            try:
                offer_provider = offer.provider
            except (ValueError, AttributeError):
                from sqlalchemy import text
                result = db.execute(text("SELECT provider::text FROM offers WHERE id = :offer_id"), {"offer_id": offer.id})
                raw_provider = result.scalar()
                offer_provider = raw_provider if raw_provider else 'booking_com'
            
            offer_response = OfferResponse(
                id=offer.id,
                hotel_id=offer.hotel_id,
                room_id=offer.room_id,
                provider=safe_provider_enum(offer_provider),
                provider_rate_id=offer.provider_rate_id,
                currency=offer.currency,
                price=offer.price,
                taxes_included=offer.taxes_included,
                check_in=offer.check_in,
                check_out=offer.check_out,
                availability_count=offer.availability_count,
                cancellation_policy=offer.cancellation_policy if isinstance(offer.cancellation_policy, dict) else {},
                total_nights=(offer.check_out - offer.check_in).days if offer.check_out and offer.check_in else 0,
                total_price=offer.price * ((offer.check_out - offer.check_in).days if offer.check_out and offer.check_in else 1),
                expires_at=offer.expires_at
            )
            offers_response.append(offer_response)
        
        # Get reviews for this hotel
        # Use hotel.id instead of hotel_id variable to ensure we have the correct ID
        reviews = db.query(ReviewModel).filter(ReviewModel.hotel_id == hotel.id).order_by(ReviewModel.fetched_at.desc()).limit(20).all()
        reviews_response = []
        for review in reviews:
            # Safely get provider value
            try:
                review_provider = review.provider
            except (ValueError, AttributeError):
                from sqlalchemy import text
                result = db.execute(text("SELECT provider::text FROM reviews WHERE id = :review_id"), {"review_id": review.id})
                raw_provider = result.scalar()
                review_provider = raw_provider if raw_provider else 'booking_com'
            
            review_response = ReviewResponse(
                id=review.id,
                hotel_id=review.hotel_id,
                provider=safe_provider_enum(review_provider),
                rating=review.rating,
                title=review.title or "",
                text=review.text or "",
                author=review.author or "",
                pros=review.pros if isinstance(review.pros, list) else [],
                cons=review.cons if isinstance(review.cons, list) else [],
                category_ratings=review.category_ratings if isinstance(review.category_ratings, dict) else {},
                fetched_at=review.fetched_at
            )
            reviews_response.append(review_response)
        
        response = HotelDetailsResponse(
            hotel=hotel_response,
            rooms=rooms_response,
            offers=offers_response,
            reviews=reviews_response
        )
        
        # Cache the result (30 minutes TTL for hotel details)
        set_cached(cache_key_str, response.dict(), ttl=1800)
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch hotel details: {str(e)}")


@router.post("/bookings/click", response_model=BookingClickResponse)
async def track_booking_click(
    request: BookingClickRequest,
    db: Session = Depends(get_db)
):
    """Track a booking click.
    
    This endpoint tracks when a user clicks on a booking link.
    """
    try:
        booking_service = BookingService(db_session=db)
        
        booking_click = await booking_service.track_booking_click(
            offer_id=request.offer_id,
            provider=Provider(request.provider),
            affiliate_link=request.affiliate_link,
            user_id=request.user_id,
            ip_address=request.ip_address or "",
            user_agent=request.user_agent
        )
        
        return BookingClickResponse(
            id=booking_click.id,
            offer_id=booking_click.offer_id,
            provider=booking_click.provider.value,
            affiliate_link=booking_click.affiliate_link,
            clicked_at=booking_click.clicked_at
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to track booking click: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "search-booking"}
