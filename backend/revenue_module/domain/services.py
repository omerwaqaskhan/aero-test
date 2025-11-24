"""Domain services for revenue management."""

from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from revenue_module.infrastructure.db.models import (
    SubscriptionModel, SubscriptionPaymentModel, LeadModel, HotelListingModel,
    ListingPaymentModel, SponsoredPlacementModel, AdRevenueModel, RevenueTransactionModel,
    SubscriptionTier, LeadStatus, ListingPackage, SponsorshipStatus
)
from auth_module.infrastructure.db.models import UserModel
from search_booking_module.infrastructure.db.models import HotelModel


class SubscriptionService:
    """Service for managing user subscriptions."""
    
    SUBSCRIPTION_PRICING = {
        SubscriptionTier.FREE: Decimal("0.00"),
        SubscriptionTier.PREMIUM: Decimal("9.99"),
        SubscriptionTier.PRO: Decimal("19.99")
    }
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def get_user_subscription(self, user_id: str) -> Optional[SubscriptionModel]:
        """Get active subscription for user."""
        return self.db.query(SubscriptionModel).filter(
            and_(
                SubscriptionModel.user_id == user_id,
                SubscriptionModel.status == "active"
            )
        ).first()
    
    def create_subscription(
        self,
        user_id: str,
        tier: SubscriptionTier,
        stripe_subscription_id: str,
        stripe_customer_id: str,
        period_start: datetime,
        period_end: datetime
    ) -> SubscriptionModel:
        """Create new subscription."""
        subscription = SubscriptionModel(
            user_id=user_id,
            tier=tier,
            stripe_subscription_id=stripe_subscription_id,
            stripe_customer_id=stripe_customer_id,
            status="active",
            current_period_start=period_start,
            current_period_end=period_end
        )
        self.db.add(subscription)
        self.db.commit()
        self.db.refresh(subscription)
        
        # Record revenue transaction
        self._record_revenue_transaction(
            revenue_type="subscription",
            reference_id=subscription.id,
            amount=self.SUBSCRIPTION_PRICING[tier],
            status="completed"
        )
        
        return subscription
    
    def cancel_subscription(self, subscription_id: str) -> SubscriptionModel:
        """Cancel subscription at period end."""
        subscription = self.db.query(SubscriptionModel).filter(
            SubscriptionModel.id == subscription_id
        ).first()
        
        if subscription:
            subscription.cancel_at_period_end = True
            subscription.canceled_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(subscription)
        
        return subscription
    
    def record_payment(
        self,
        subscription_id: str,
        stripe_payment_intent_id: str,
        amount: Decimal,
        currency: str,
        status: str
    ) -> SubscriptionPaymentModel:
        """Record subscription payment."""
        payment = SubscriptionPaymentModel(
            subscription_id=subscription_id,
            stripe_payment_intent_id=stripe_payment_intent_id,
            amount=amount,
            currency=currency,
            status=status,
            paid_at=datetime.utcnow() if status == "succeeded" else None
        )
        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)
        return payment
    
    def _record_revenue_transaction(
        self,
        revenue_type: str,
        reference_id: str,
        amount: Decimal,
        status: str,
        metadata: Optional[Dict] = None
    ):
        """Record revenue transaction."""
        transaction = RevenueTransactionModel(
            revenue_type=revenue_type,
            reference_id=reference_id,
            amount=amount,
            currency="USD",
            status=status,
            transaction_metadata=metadata or {}
        )
        self.db.add(transaction)
        self.db.commit()


class LeadService:
    """Service for managing leads."""
    
    LEAD_FEE = Decimal("15.00")  # Fee per lead
    COMMISSION_RATE = Decimal("0.10")  # 10% commission on bookings
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def create_lead(
        self,
        hotel_id: str,
        email: str,
        check_in: date,
        check_out: date,
        user_id: Optional[str] = None,
        name: Optional[str] = None,
        phone: Optional[str] = None,
        guests: Optional[int] = None,
        rooms: Optional[int] = None,
        budget_range: Optional[str] = None,
        special_requests: Optional[str] = None
    ) -> LeadModel:
        """Create new lead."""
        lead = LeadModel(
            hotel_id=hotel_id,
            user_id=user_id,
            email=email,
            phone=phone,
            name=name,
            check_in=check_in,
            check_out=check_out,
            guests=guests,
            rooms=rooms,
            budget_range=budget_range,
            special_requests=special_requests,
            status=LeadStatus.NEW,
            lead_fee=self.LEAD_FEE
        )
        self.db.add(lead)
        self.db.commit()
        self.db.refresh(lead)
        
        # Record revenue transaction
        self._record_revenue_transaction(
            revenue_type="lead",
            reference_id=lead.id,
            amount=self.LEAD_FEE,
            status="completed"
        )
        
        return lead
    
    def get_leads_by_hotel_id(self, hotel_id: str, limit: int = 100) -> List[LeadModel]:
        """Get leads for a hotel."""
        return self.db.query(LeadModel).filter(
            LeadModel.hotel_id == hotel_id
        ).order_by(LeadModel.created_at.desc()).limit(limit).all()
    
    def get_lead_by_id(self, lead_id: str) -> Optional[LeadModel]:
        """Get lead by ID."""
        return self.db.query(LeadModel).filter(
            LeadModel.id == lead_id
        ).first()
    
    async def mark_lead_sent(self, lead_id: str) -> LeadModel:
        """Mark lead as sent to hotel and send email notification."""
        lead = self.db.query(LeadModel).filter(LeadModel.id == lead_id).first()
        if lead:
            lead.status = LeadStatus.SENT
            lead.sent_to_hotel_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(lead)
            
            # Send email notification to hotel
            await self._send_lead_notification_email(lead)
            
            # Send confirmation email to user
            await self._send_lead_confirmation_email(lead)
        
        return lead
    
    async def _send_lead_notification_email(self, lead: LeadModel):
        """Send lead notification email to hotel."""
        try:
            from auth_module.infrastructure.messaging import EmailService
            from search_booking_module.infrastructure.db.models import HotelModel
            
            email_service = EmailService()
            hotel = self.db.query(HotelModel).filter(HotelModel.id == lead.hotel_id).first()
            
            if not hotel:
                return
            
            # Get hotel email from source_url or use a default
            hotel_email = getattr(hotel, 'hotel_email', None) or hotel.source_url or "info@luftway.com"
            
            subject = f"New Booking Inquiry - {hotel.name}"
            
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #007bff;">New Booking Inquiry</h2>
                    <p>You have received a new booking inquiry for <strong>{hotel.name}</strong>.</p>
                    
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <h3 style="margin-top: 0;">Guest Information</h3>
                        <p><strong>Name:</strong> {lead.name or 'Not provided'}</p>
                        <p><strong>Email:</strong> <a href="mailto:{lead.email}">{lead.email}</a></p>
                        <p><strong>Phone:</strong> {lead.phone or 'Not provided'}</p>
                    </div>
                    
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <h3 style="margin-top: 0;">Booking Details</h3>
                        <p><strong>Check-in:</strong> {lead.check_in}</p>
                        <p><strong>Check-out:</strong> {lead.check_out}</p>
                        <p><strong>Guests:</strong> {lead.guests or 'Not specified'}</p>
                        <p><strong>Rooms:</strong> {lead.rooms or 'Not specified'}</p>
                        <p><strong>Budget Range:</strong> {lead.budget_range or 'Flexible'}</p>
                    </div>
                    
                    {lead.special_requests and f'''
                    <div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <h3 style="margin-top: 0;">Special Requests</h3>
                        <p>{lead.special_requests}</p>
                    </div>
                    ''' or ''}
                    
                    <p style="margin-top: 20px;">
                        <a href="mailto:{lead.email}" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">
                            Reply to Guest
                        </a>
                    </p>
                    
                    <p style="color: #666; font-size: 12px; margin-top: 30px;">
                        This inquiry was generated through Luftway travel platform.
                    </p>
                </div>
            </body>
            </html>
            """
            
            text_content = f"""
            New Booking Inquiry
            
            You have received a new booking inquiry for {hotel.name}.
            
            Guest Information:
            Name: {lead.name or 'Not provided'}
            Email: {lead.email}
            Phone: {lead.phone or 'Not provided'}
            
            Booking Details:
            Check-in: {lead.check_in}
            Check-out: {lead.check_out}
            Guests: {lead.guests or 'Not specified'}
            Rooms: {lead.rooms or 'Not specified'}
            Budget Range: {lead.budget_range or 'Flexible'}
            
            {lead.special_requests and f'Special Requests: {lead.special_requests}' or ''}
            
            Reply to guest: {lead.email}
            
            This inquiry was generated through Luftway travel platform.
            """
            
            await email_service.send_email(
                to_email=hotel_email,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
        except Exception as e:
            # Log error but don't fail lead creation
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send lead notification email: {e}")
    
    async def _send_lead_confirmation_email(self, lead: LeadModel):
        """Send confirmation email to user."""
        try:
            from auth_module.infrastructure.messaging import EmailService
            from search_booking_module.infrastructure.db.models import HotelModel
            
            email_service = EmailService()
            hotel = self.db.query(HotelModel).filter(HotelModel.id == lead.hotel_id).first()
            
            if not hotel:
                return
            
            subject = f"Your inquiry has been sent to {hotel.name}"
            
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #007bff;">Inquiry Confirmed</h2>
                    <p>Thank you for your interest in <strong>{hotel.name}</strong>!</p>
                    
                    <p>We've sent your inquiry directly to the hotel. They will contact you shortly with their best available rate and availability.</p>
                    
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <h3 style="margin-top: 0;">Your Inquiry Details</h3>
                        <p><strong>Hotel:</strong> {hotel.name}</p>
                        <p><strong>Check-in:</strong> {lead.check_in}</p>
                        <p><strong>Check-out:</strong> {lead.check_out}</p>
                        <p><strong>Guests:</strong> {lead.guests or 'Not specified'}</p>
                    </div>
                    
                    <p>You should receive a response from the hotel within 24 hours.</p>
                    
                    <p style="color: #666; font-size: 12px; margin-top: 30px;">
                        If you have any questions, please contact us at support@luftway.com
                    </p>
                </div>
            </body>
            </html>
            """
            
            text_content = f"""
            Inquiry Confirmed
            
            Thank you for your interest in {hotel.name}!
            
            We've sent your inquiry directly to the hotel. They will contact you shortly with their best available rate and availability.
            
            Your Inquiry Details:
            Hotel: {hotel.name}
            Check-in: {lead.check_in}
            Check-out: {lead.check_out}
            Guests: {lead.guests or 'Not specified'}
            
            You should receive a response from the hotel within 24 hours.
            
            If you have any questions, please contact us at support@luftway.com
            """
            
            await email_service.send_email(
                to_email=lead.email,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
        except Exception as e:
            # Log error but don't fail lead creation
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send lead confirmation email: {e}")
    
    def mark_lead_converted(self, lead_id: str, booking_value: Decimal) -> LeadModel:
        """Mark lead as converted to booking."""
        lead = self.db.query(LeadModel).filter(LeadModel.id == lead_id).first()
        if lead:
            lead.status = LeadStatus.BOOKED
            lead.booking_value = booking_value
            lead.commission = booking_value * self.COMMISSION_RATE
            lead.converted_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(lead)
            
            # Record commission revenue
            self._record_revenue_transaction(
                revenue_type="lead",
                reference_id=lead.id,
                amount=lead.commission,
                status="completed",
                transaction_metadata={"type": "commission", "booking_value": float(booking_value)}
            )
        
        return lead
    
    def _record_revenue_transaction(
        self,
        revenue_type: str,
        reference_id: str,
        amount: Decimal,
        status: str,
        metadata: Optional[Dict] = None
    ):
        """Record revenue transaction."""
        transaction = RevenueTransactionModel(
            revenue_type=revenue_type,
            reference_id=reference_id,
            amount=amount,
            currency="USD",
            status=status,
            transaction_metadata=metadata or {}
        )
        self.db.add(transaction)
        self.db.commit()


class HotelListingService:
    """Service for managing hotel listings."""
    
    LISTING_PRICING = {
        ListingPackage.BASIC: Decimal("0.00"),
        ListingPackage.ENHANCED: Decimal("99.00"),
        ListingPackage.PREMIUM: Decimal("299.00")
    }
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def create_listing(
        self,
        hotel_id: str,
        package: ListingPackage,
        owner_email: str,
        owner_name: Optional[str] = None,
        owner_phone: Optional[str] = None
    ) -> HotelListingModel:
        """Create hotel listing."""
        import secrets
        verification_token = secrets.token_urlsafe(32)
        
        listing = HotelListingModel(
            hotel_id=hotel_id,
            package=package,
            owner_email=owner_email,
            owner_name=owner_name,
            owner_phone=owner_phone,
            verification_token=verification_token,
            status="pending"
        )
        self.db.add(listing)
        self.db.commit()
        self.db.refresh(listing)
        return listing
    
    def verify_listing(self, verification_token: str) -> HotelListingModel:
        """Verify hotel listing ownership."""
        listing = self.db.query(HotelListingModel).filter(
            HotelListingModel.verification_token == verification_token
        ).first()
        
        if listing:
            listing.verified = True
            listing.status = "active"
            listing.verification_token = None
            self.db.commit()
            self.db.refresh(listing)
        
        return listing
    
    def upgrade_listing(
        self,
        listing_id: str,
        new_package: ListingPackage,
        stripe_customer_id: str,
        period_start: datetime,
        period_end: datetime
    ) -> HotelListingModel:
        """Upgrade listing package."""
        listing = self.db.query(HotelListingModel).filter(
            HotelListingModel.id == listing_id
        ).first()
        
        if listing:
            listing.package = new_package
            listing.stripe_customer_id = stripe_customer_id
            listing.current_period_start = period_start
            listing.current_period_end = period_end
            listing.status = "active"
            self.db.commit()
            self.db.refresh(listing)
            
            # Record revenue transaction
            self._record_revenue_transaction(
                revenue_type="listing",
                reference_id=listing.id,
                amount=self.LISTING_PRICING[new_package],
                status="completed"
            )
        
        return listing
    
    def get_listing_by_email(self, owner_email: str) -> Optional[HotelListingModel]:
        """Get listing by owner email."""
        return self.db.query(HotelListingModel).filter(
            HotelListingModel.owner_email == owner_email
        ).first()
    
    def get_listing_by_hotel_id(self, hotel_id: str) -> Optional[HotelListingModel]:
        """Get listing by hotel ID."""
        return self.db.query(HotelListingModel).filter(
            HotelListingModel.hotel_id == hotel_id
        ).first()
    
    def get_listing_by_id(self, listing_id: str) -> Optional[HotelListingModel]:
        """Get listing by ID."""
        return self.db.query(HotelListingModel).filter(
            HotelListingModel.id == listing_id
        ).first()
    
    def record_listing_payment(
        self,
        listing_id: str,
        stripe_payment_intent_id: str,
        amount: Decimal,
        currency: str,
        status: str,
        period_start: datetime,
        period_end: datetime
    ) -> ListingPaymentModel:
        """Record listing payment."""
        payment = ListingPaymentModel(
            listing_id=listing_id,
            stripe_payment_intent_id=stripe_payment_intent_id,
            amount=amount,
            currency=currency,
            status=status,
            period_start=period_start,
            period_end=period_end,
            paid_at=datetime.utcnow() if status == "succeeded" else None
        )
        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)
        return payment
    
    def _record_revenue_transaction(
        self,
        revenue_type: str,
        reference_id: str,
        amount: Decimal,
        status: str,
        metadata: Optional[Dict] = None
    ):
        """Record revenue transaction."""
        transaction = RevenueTransactionModel(
            revenue_type=revenue_type,
            reference_id=reference_id,
            amount=amount,
            currency="USD",
            status=status,
            transaction_metadata=metadata or {}
        )
        self.db.add(transaction)
        self.db.commit()


class SponsoredPlacementService:
    """Service for managing sponsored placements."""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def create_sponsorship(
        self,
        hotel_id: str,
        listing_id: Optional[str],
        priority: int,
        placement_type: str,
        start_date: datetime,
        end_date: datetime,
        amount: Decimal,
        stripe_payment_intent_id: Optional[str] = None
    ) -> SponsoredPlacementModel:
        """Create sponsored placement."""
        sponsorship = SponsoredPlacementModel(
            hotel_id=hotel_id,
            listing_id=listing_id,
            priority=priority,
            placement_type=placement_type,
            start_date=start_date,
            end_date=end_date,
            status=SponsorshipStatus.ACTIVE,
            amount=amount,
            stripe_payment_intent_id=stripe_payment_intent_id
        )
        self.db.add(sponsorship)
        self.db.commit()
        self.db.refresh(sponsorship)
        
        # Record revenue transaction
        self._record_revenue_transaction(
            revenue_type="sponsorship",
            reference_id=sponsorship.id,
            amount=amount,
            status="completed"
        )
        
        return sponsorship
    
    def get_active_sponsorships(
        self,
        placement_type: Optional[str] = None
    ) -> List[SponsoredPlacementModel]:
        """Get active sponsorships."""
        query = self.db.query(SponsoredPlacementModel).filter(
            and_(
                SponsoredPlacementModel.status == SponsorshipStatus.ACTIVE,
                SponsoredPlacementModel.start_date <= datetime.utcnow(),
                SponsoredPlacementModel.end_date >= datetime.utcnow()
            )
        )
        
        if placement_type:
            query = query.filter(SponsoredPlacementModel.placement_type == placement_type)
        
        return query.order_by(SponsoredPlacementModel.priority.desc()).all()
    
    def _record_revenue_transaction(
        self,
        revenue_type: str,
        reference_id: str,
        amount: Decimal,
        status: str,
        metadata: Optional[Dict] = None
    ):
        """Record revenue transaction."""
        transaction = RevenueTransactionModel(
            revenue_type=revenue_type,
            reference_id=reference_id,
            amount=amount,
            currency="USD",
            status=status,
            transaction_metadata=metadata or {}
        )
        self.db.add(transaction)
        self.db.commit()


class AdRevenueService:
    """Service for tracking ad revenue."""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def record_impression(
        self,
        ad_slot: str,
        page_type: str,
        revenue: Decimal
    ):
        """Record ad impression and revenue."""
        today = date.today()
        
        ad_revenue = self.db.query(AdRevenueModel).filter(
            and_(
                AdRevenueModel.ad_slot == ad_slot,
                AdRevenueModel.page_type == page_type,
                AdRevenueModel.date == today
            )
        ).first()
        
        if ad_revenue:
            ad_revenue.impressions += 1
            ad_revenue.revenue += revenue
        else:
            ad_revenue = AdRevenueModel(
                ad_slot=ad_slot,
                page_type=page_type,
                impressions=1,
                clicks=0,
                revenue=revenue,
                date=today
            )
            self.db.add(ad_revenue)
        
        self.db.commit()
        
        # Record revenue transaction
        self._record_revenue_transaction(
            revenue_type="ads",
            reference_id=None,
            amount=revenue,
            status="completed",
            transaction_metadata={"ad_slot": ad_slot, "page_type": page_type}
        )
    
    def record_click(
        self,
        ad_slot: str,
        page_type: str,
        revenue: Decimal
    ):
        """Record ad click and revenue."""
        today = date.today()
        
        ad_revenue = self.db.query(AdRevenueModel).filter(
            and_(
                AdRevenueModel.ad_slot == ad_slot,
                AdRevenueModel.page_type == page_type,
                AdRevenueModel.date == today
            )
        ).first()
        
        if ad_revenue:
            ad_revenue.clicks += 1
            ad_revenue.revenue += revenue
        else:
            ad_revenue = AdRevenueModel(
                ad_slot=ad_slot,
                page_type=page_type,
                impressions=0,
                clicks=1,
                revenue=revenue,
                date=today
            )
            self.db.add(ad_revenue)
        
        self.db.commit()
        
        # Record revenue transaction
        self._record_revenue_transaction(
            revenue_type="ads",
            reference_id=None,
            amount=revenue,
            status="completed",
            transaction_metadata={"ad_slot": ad_slot, "page_type": page_type, "type": "click"}
        )
    
    def _record_revenue_transaction(
        self,
        revenue_type: str,
        reference_id: Optional[str],
        amount: Decimal,
        status: str,
        transaction_metadata: Optional[Dict] = None
    ):
        """Record revenue transaction."""
        transaction = RevenueTransactionModel(
            revenue_type=revenue_type,
            reference_id=reference_id,
            amount=amount,
            currency="USD",
            status=status,
            transaction_metadata=transaction_metadata or {}
        )
        self.db.add(transaction)
        self.db.commit()


class RevenueAnalyticsService:
    """Service for revenue analytics."""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def get_total_revenue(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Get total revenue by type."""
        query = self.db.query(
            RevenueTransactionModel.revenue_type,
            func.sum(RevenueTransactionModel.amount).label('total')
        ).filter(
            RevenueTransactionModel.status == "completed"
        )
        
        if start_date:
            query = query.filter(RevenueTransactionModel.occurred_at >= start_date)
        if end_date:
            query = query.filter(RevenueTransactionModel.occurred_at <= end_date)
        
        results = query.group_by(RevenueTransactionModel.revenue_type).all()
        
        revenue_by_type = {row.revenue_type: float(row.total) for row in results}
        total_revenue = sum(revenue_by_type.values())
        
        return {
            "total_revenue": total_revenue,
            "by_type": revenue_by_type,
            "period": {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None
            }
        }
    
    def get_monthly_revenue(self, months: int = 12) -> List[Dict[str, Any]]:
        """Get monthly revenue breakdown."""
        end_date = date.today()
        start_date = date(end_date.year, end_date.month, 1) - timedelta(days=30 * months)
        
        results = self.db.query(
            func.date_trunc('month', RevenueTransactionModel.occurred_at).label('month'),
            RevenueTransactionModel.revenue_type,
            func.sum(RevenueTransactionModel.amount).label('total')
        ).filter(
            and_(
                RevenueTransactionModel.status == "completed",
                RevenueTransactionModel.occurred_at >= start_date
            )
        ).group_by(
            func.date_trunc('month', RevenueTransactionModel.occurred_at),
            RevenueTransactionModel.revenue_type
        ).order_by('month').all()
        
        monthly_data = {}
        for row in results:
            month_key = row.month.strftime('%Y-%m')
            if month_key not in monthly_data:
                monthly_data[month_key] = {}
            monthly_data[month_key][row.revenue_type] = float(row.total)
        
        return [
            {
                "month": month,
                "revenue": monthly_data[month],
                "total": sum(monthly_data[month].values())
            }
            for month in sorted(monthly_data.keys())
        ]

