"""
Comprehensive test suite for all revenue functionality.
Run this to test everything works without glitches.
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import all test modules
from revenue_module.tests.unit.test_subscription_service import TestSubscriptionService
from revenue_module.tests.unit.test_lead_service import TestLeadService
from revenue_module.tests.unit.test_hotel_listing_service import TestHotelListingService
from revenue_module.tests.unit.test_sponsored_placement_service import TestSponsoredPlacementService
from revenue_module.tests.unit.test_ad_revenue_service import TestAdRevenueService
from revenue_module.tests.unit.test_revenue_analytics_service import TestRevenueAnalyticsService
from revenue_module.tests.unit.test_stripe_service import TestStripeService
from revenue_module.tests.unit.test_stripe_checkout import TestStripeCheckout
from revenue_module.tests.unit.test_edge_cases import TestEdgeCases


class TestAllFunctionality:
    """Test suite that runs all functionality tests."""
    
    def test_all_services_importable(self):
        """Test that all services can be imported."""
        from revenue_module.domain.services import (
            SubscriptionService, LeadService, HotelListingService,
            SponsoredPlacementService, AdRevenueService, RevenueAnalyticsService
        )
        from revenue_module.infrastructure.stripe_service import StripeService
        
        assert SubscriptionService is not None
        assert LeadService is not None
        assert HotelListingService is not None
        assert SponsoredPlacementService is not None
        assert AdRevenueService is not None
        assert RevenueAnalyticsService is not None
        assert StripeService is not None
    
    def test_all_models_importable(self):
        """Test that all models can be imported."""
        from revenue_module.infrastructure.db.models import (
            SubscriptionModel, SubscriptionPaymentModel, LeadModel,
            HotelListingModel, ListingPaymentModel, SponsoredPlacementModel,
            AdRevenueModel, RevenueTransactionModel
        )
        
        assert SubscriptionModel is not None
        assert LeadModel is not None
        assert HotelListingModel is not None
        assert SponsoredPlacementModel is not None
        assert AdRevenueModel is not None
    
    def test_all_api_endpoints_importable(self):
        """Test that all API routers can be imported."""
        from revenue_module.api.routers import router as revenue_router
        from revenue_module.api.stripe_routers import router as stripe_router
        
        assert revenue_router is not None
        assert stripe_router is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

