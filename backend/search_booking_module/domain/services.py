"""Domain services for search and booking module."""

from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from search_booking_module.domain.models import (
    Hotel, Offer, Review, BookingClick, SearchFilters, SearchResult, Provider
)
from search_booking_module.infrastructure.providers.base import BaseProvider
from search_booking_module.infrastructure.db.models import (
    HotelModel, OfferModel, ReviewModel, BookingClickModel
)


class SearchService:
    """Service for searching hotels and aggregating results."""
    
    def __init__(
        self,
        providers: List[BaseProvider],
        db_session: Session,
        use_database: bool = True  # New: Use database instead of providers
    ):
        """Initialize search service with providers and database session.
        
        Args:
            providers: List of provider adapters (for real-time data)
            db_session: Database session for querying stored hotels
            use_database: If True, query database. If False, use providers (legacy)
        """
        self.providers = providers
        self.db_session = db_session
        self.use_database = use_database
    
    async def search_hotels(
        self,
        filters: SearchFilters,
        sort_by: str = "price",
        sort_order: str = "asc",
        page: int = 1,
        page_size: int = 20
    ) -> List[SearchResult]:
        """Search hotels across all providers or database.
        
        Args:
            filters: Search filters
            sort_by: Sort field (price, rating, distance, stars)
            sort_order: Sort order (asc, desc)
            page: Page number (1-indexed)
            page_size: Number of results per page
            
        Returns:
            List of SearchResult objects
        """
        if not filters.is_valid():
            return []
        
        if self.use_database:
            return await self._search_database(filters, sort_by, sort_order, page, page_size)
        else:
            return await self._search_providers(filters, sort_by, sort_order, page, page_size)
    
    async def _search_database(
        self,
        filters: SearchFilters,
        sort_by: str,
        sort_order: str,
        page: int,
        page_size: int
    ) -> List[SearchResult]:
        """Search hotels from database."""
        try:
            # Build query
            query = self.db_session.query(HotelModel)
            
            # Filter by destination (city)
            if filters.destination:
                query = query.filter(
                    or_(
                        HotelModel.city.ilike(f"%{filters.destination}%"),
                        HotelModel.country.ilike(f"%{filters.destination}%"),
                        HotelModel.name.ilike(f"%{filters.destination}%")
                    )
                )
            
            # Filter by star rating
            if filters.stars:
                query = query.filter(HotelModel.stars.in_(filters.stars))
            
            # Filter by amenities
            if filters.amenities:
                # PostgreSQL JSONB contains check
                for amenity in filters.amenities:
                    query = query.filter(
                        func.jsonb_array_elements_text(HotelModel.amenities).contains(amenity)
                    )
            
            # Filter by rating
            if filters.rating_min:
                query = query.filter(HotelModel.rating >= filters.rating_min)
            
            # Filter by location (if coordinates provided)
            if filters.latitude and filters.longitude and filters.radius:
                # Simple distance calculation (Haversine would be better)
                # For now, use bounding box approximation
                lat_range = filters.radius / 111.0  # Approximate km to degrees
                lon_range = filters.radius / (111.0 * abs(filters.latitude / 90.0))
                
                query = query.filter(
                    and_(
                        HotelModel.latitude.between(
                            filters.latitude - lat_range,
                            filters.latitude + lat_range
                        ),
                        HotelModel.longitude.between(
                            filters.longitude - lon_range,
                            filters.longitude + lon_range
                        )
                    )
                )
            
            # Get hotels
            hotels = query.all()
            
            # Get offers for these hotels
            hotel_ids = [hotel.id for hotel in hotels]
            
            # Build offer query
            offer_query = self.db_session.query(OfferModel).filter(
                OfferModel.hotel_id.in_(hotel_ids)
            )
            
            # Filter offers by date range
            if filters.check_in and filters.check_out:
                offer_query = offer_query.filter(
                    and_(
                        OfferModel.check_in <= filters.check_in,
                        OfferModel.check_out >= filters.check_out
                    )
                )
            
            # Filter by price
            if filters.min_price:
                offer_query = offer_query.filter(OfferModel.price >= filters.min_price)
            if filters.max_price:
                offer_query = offer_query.filter(OfferModel.price <= filters.max_price)
            
            offers = offer_query.all()
            
            # Group offers by hotel
            offers_by_hotel: Dict[str, List[OfferModel]] = {}
            for offer in offers:
                if offer.hotel_id not in offers_by_hotel:
                    offers_by_hotel[offer.hotel_id] = []
                offers_by_hotel[offer.hotel_id].append(offer)
            
            # Get sponsored placements for priority sorting
            sponsored_map = {}
            try:
                from revenue_module.infrastructure.db.models import SponsoredPlacementModel, SponsorshipStatus
                from datetime import datetime
                from sqlalchemy.exc import OperationalError, ProgrammingError
                
                # Use a savepoint to isolate the query
                savepoint = self.db_session.begin_nested()
                try:
                    active_sponsorships = self.db_session.query(SponsoredPlacementModel).filter(
                        SponsoredPlacementModel.status == SponsorshipStatus.ACTIVE,
                        SponsoredPlacementModel.start_date <= datetime.utcnow(),
                        SponsoredPlacementModel.end_date >= datetime.utcnow()
                    ).all()
                    
                    for sponsorship in active_sponsorships:
                        if sponsorship.hotel_id not in sponsored_map:
                            sponsored_map[sponsorship.hotel_id] = []
                        sponsored_map[sponsorship.hotel_id].append(sponsorship.priority)
                    
                    savepoint.commit()
                except (OperationalError, ProgrammingError) as e:
                    # Table doesn't exist - rollback savepoint and continue
                    savepoint.rollback()
                    # Continue without sponsored placements
                    pass
                except Exception as e:
                    # Other error - rollback savepoint
                    savepoint.rollback()
                    print(f"Could not load sponsored placements: {e}")
            except ImportError:
                # Revenue module not available
                pass
            except Exception as e:
                # If revenue module not available, continue without sponsored placements
                print(f"Could not load sponsored placements: {e}")
            
            # Build search results
            results = []
            for hotel in hotels:
                hotel_offers = offers_by_hotel.get(hotel.id, [])
                
                # Skip if no offers match filters
                if not hotel_offers and (filters.min_price or filters.max_price):
                    continue
                
                # Convert to domain models
                hotel_domain = self._hotel_model_to_domain(hotel)
                offers_domain = [self._offer_model_to_domain(offer) for offer in hotel_offers]
                
                # Calculate best price
                best_price = None
                best_offer = None
                if offers_domain:
                    best_offer = min(offers_domain, key=lambda o: o.price)
                    best_price = best_offer.price
                
                # Get average rating
                average_rating = hotel.rating
                review_count = self.db_session.query(ReviewModel).filter(
                    ReviewModel.hotel_id == hotel.id
                ).count()
                
                # Apply rating filter
                if filters.rating_min and average_rating:
                    if average_rating < filters.rating_min:
                        continue
                
                # Check if hotel is sponsored
                is_sponsored = hotel.id in sponsored_map
                max_priority = max(sponsored_map[hotel.id]) if is_sponsored else 0
                
                result = SearchResult(
                    hotel=hotel_domain,
                    offers=offers_domain,
                    best_price=best_price,
                    best_offer=best_offer,
                    average_rating=average_rating,
                    review_count=review_count
                )
                # Add sponsored flag and priority for sorting
                result.is_sponsored = is_sponsored
                result.sponsor_priority = max_priority
                results.append(result)
            
            # Sort results - sponsored hotels first by priority, then by selected sort
            def sort_key(r):
                # Primary sort: sponsored status (sponsored first)
                # Secondary sort: priority (higher first)
                # Tertiary sort: selected sort field
                if sort_by == "price":
                    price = r.best_price or float('inf')
                    return (not r.is_sponsored, -r.sponsor_priority, price if sort_order == "asc" else -price)
                elif sort_by == "rating":
                    rating = r.average_rating or 0
                    return (not r.is_sponsored, -r.sponsor_priority, -rating if sort_order == "desc" else rating)
                elif sort_by == "stars":
                    stars = r.hotel.stars
                    return (not r.is_sponsored, -r.sponsor_priority, -stars if sort_order == "desc" else stars)
                else:
                    return (not r.is_sponsored, -r.sponsor_priority, 0)
            
            results.sort(key=sort_key)
            
            # Paginate
            start = (page - 1) * page_size
            end = start + page_size
            return results[start:end]
            
        except Exception as e:
            print(f"Error searching database: {e}")
            return []
    
    def _hotel_model_to_domain(self, hotel: HotelModel) -> Hotel:
        """Convert HotelModel to Hotel domain model."""
        return Hotel(
            id=hotel.id,
            provider_hotel_id=hotel.provider_hotel_id,
            provider=Provider(hotel.provider.value) if isinstance(hotel.provider, Provider) else Provider.BOOKING_COM,
            name=hotel.name,
            address=hotel.address if isinstance(hotel.address, dict) else {},
            city=hotel.city,
            country=hotel.country,
            latitude=hotel.latitude,
            longitude=hotel.longitude,
            stars=hotel.stars,
            description=hotel.description or "",
            images=hotel.images if isinstance(hotel.images, list) else [],
            amenities=hotel.amenities if isinstance(hotel.amenities, list) else [],
            created_at=hotel.created_at,
            updated_at=hotel.updated_at
        )
    
    def _offer_model_to_domain(self, offer: OfferModel) -> Offer:
        """Convert OfferModel to Offer domain model."""
        return Offer(
            id=offer.id,
            hotel_id=offer.hotel_id,
            room_id=offer.room_id,
            provider=Provider(offer.provider.value) if isinstance(offer.provider, Provider) else Provider.BOOKING_COM,
            provider_rate_id=offer.provider_rate_id,
            currency=offer.currency,
            price=offer.price,
            taxes_included=offer.taxes_included,
            check_in=offer.check_in,
            check_out=offer.check_out,
            availability_count=offer.availability_count,
            cancellation_policy=offer.cancellation_policy if isinstance(offer.cancellation_policy, dict) else {},
            expires_at=offer.expires_at
        )
    
    async def _search_providers(
        self,
        filters: SearchFilters,
        sort_by: str,
        sort_order: str,
        page: int,
        page_size: int
    ) -> List[SearchResult]:
        """Search hotels from providers (legacy method)."""
        # Original provider-based search logic
        all_hotels: Dict[str, Hotel] = {}
        all_offers: Dict[str, List[Offer]] = {}
        
        for provider in self.providers:
            try:
                hotels = await provider.search_hotels(
                    destination=filters.destination,
                    check_in=filters.check_in or date.today(),
                    check_out=filters.check_out or date.today() + timedelta(days=1),
                    guests=filters.guests,
                    rooms=filters.rooms
                )
                
                for hotel in hotels:
                    key = f"{hotel.provider.value}_{hotel.provider_hotel_id}"
                    
                    offers = await provider.get_offers(
                        provider_hotel_id=hotel.provider_hotel_id,
                        check_in=filters.check_in or date.today(),
                        check_out=filters.check_out or date.today() + timedelta(days=1),
                        guests=filters.guests,
                        rooms=filters.rooms
                    )
                    
                    if filters.min_price:
                        offers = [o for o in offers if o.price >= filters.min_price]
                    if filters.max_price:
                        offers = [o for o in offers if o.price <= filters.max_price]
                    
                    if offers:
                        all_hotels[key] = hotel
                        all_offers[key] = offers
                        
            except Exception as e:
                print(f"Error searching provider {provider.provider_name}: {e}")
                continue
        
        # Build search results
        results = []
        for key, hotel in all_hotels.items():
            offers = all_offers.get(key, [])
            
            if filters.stars and hotel.stars not in filters.stars:
                continue
            
            if filters.amenities:
                hotel_amenities_lower = [a.lower() for a in hotel.amenities]
                if not all(a.lower() in hotel_amenities_lower for a in filters.amenities):
                    continue
            
            best_price = None
            best_offer = None
            if offers:
                best_offer = min(offers, key=lambda o: o.price)
                best_price = best_offer.price
            
            average_rating = None
            review_count = 0
            
            if filters.rating_min and average_rating:
                if average_rating < filters.rating_min:
                    continue
            
            result = SearchResult(
                hotel=hotel,
                offers=offers,
                best_price=best_price,
                best_offer=best_offer,
                average_rating=average_rating,
                review_count=review_count
            )
            results.append(result)
        
        # Sort and paginate
        if sort_by == "price":
            results.sort(key=lambda r: r.best_price or float('inf'), reverse=(sort_order == "desc"))
        elif sort_by == "rating":
            results.sort(key=lambda r: r.average_rating or 0, reverse=(sort_order == "desc"))
        
        start = (page - 1) * page_size
        end = start + page_size
        return results[start:end]


class BookingService:
    """Service for tracking booking clicks."""
    
    def __init__(self, db_session: Session):
        """Initialize booking service with database session."""
        self.db_session = db_session
    
    async def track_booking_click(
        self,
        offer_id: str,
        provider: Provider,
        affiliate_link: str,
        user_id: Optional[str] = None,
        ip_address: str = "",
        user_agent: Optional[str] = None
    ) -> BookingClick:
        """Track a booking click.
        
        Args:
            offer_id: ID of the offer that was clicked
            provider: Provider of the offer
            affiliate_link: Affiliate link to redirect to
            user_id: ID of the user (if logged in)
            ip_address: IP address of the user
            user_agent: User agent string
            
        Returns:
            BookingClick object
        """
        booking_click = BookingClickModel(
            offer_id=offer_id,
            provider=provider.value,
            affiliate_link=affiliate_link,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.db_session.add(booking_click)
        self.db_session.commit()
        self.db_session.refresh(booking_click)
        
        return BookingClick(
            id=booking_click.id,
            offer_id=booking_click.offer_id,
            provider=provider,
            affiliate_link=booking_click.affiliate_link,
            user_id=booking_click.user_id,
            clicked_at=booking_click.clicked_at
        )
