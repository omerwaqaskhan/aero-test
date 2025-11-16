"""
Hybrid Data Source Manager
Intelligently switches between API and scraping based on availability, cost, and quality.
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import date, datetime
from enum import Enum
from dataclasses import dataclass
import os

from ..domain.models import Hotel, Offer, Review, Provider
from ..infrastructure.providers.base import BaseProvider, ProviderError
from ..infrastructure.providers.booking_com import BookingComProvider
from ..infrastructure.providers.expedia import ExpediaProvider

logger = logging.getLogger(__name__)


class DataSourceType(Enum):
    """Type of data source."""
    API = "api"
    SCRAPING = "scraping"
    BOTH = "both"


class DataSourceStrategy(Enum):
    """Strategy for choosing data source."""
    API_FIRST = "api_first"  # Try API first, fall back to scraping
    SCRAPING_FIRST = "scraping_first"  # Try scraping first, fall back to API
    API_ONLY = "api_only"  # Only use API, fail if unavailable
    SCRAPING_ONLY = "scraping_only"  # Only use scraping
    PARALLEL = "parallel"  # Run both in parallel, merge results
    CHEAPEST = "cheapest"  # Choose based on cost
    FASTEST = "fastest"  # Choose based on speed


@dataclass
class DataSourceConfig:
    """Configuration for a data source."""
    enabled: bool = True
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    rate_limit: int = 60  # requests per minute
    cost_per_request: float = 0.0  # USD per request
    priority: int = 1  # Higher = more preferred
    timeout: int = 30  # seconds
    max_retries: int = 3


@dataclass
class DataSourceStats:
    """Statistics for a data source."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_cost: float = 0.0
    average_response_time: float = 0.0
    last_used: Optional[datetime] = None
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_requests == 0:
            return 100.0
        return (self.successful_requests / self.total_requests) * 100


class HybridDataSourceManager:
    """
    Manages multiple data sources (APIs and scrapers) with intelligent switching.
    """
    
    def __init__(
        self,
        strategy: DataSourceStrategy = DataSourceStrategy.API_FIRST,
        enable_api: bool = True,
        enable_scraping: bool = True
    ):
        self.strategy = strategy
        self.enable_api = enable_api
        self.enable_scraping = enable_scraping
        
        # Load configuration from environment
        self.api_configs = self._load_api_configs()
        self.scraping_config = self._load_scraping_config()
        
        # Initialize providers
        self.api_providers: Dict[str, BaseProvider] = {}
        self.scrapers: Dict[str, Any] = {}
        
        if enable_api:
            self._initialize_api_providers()
        
        if enable_scraping:
            self._initialize_scrapers()
        
        # Statistics
        self.stats: Dict[str, DataSourceStats] = {
            "api": DataSourceStats(),
            "scraping": DataSourceStats()
        }
        
        logger.info(f"HybridDataSourceManager initialized with strategy: {strategy.value}")
        logger.info(f"API providers: {len(self.api_providers)}, Scrapers: {len(self.scrapers)}")
    
    def _load_api_configs(self) -> Dict[str, DataSourceConfig]:
        """Load API configurations from environment."""
        configs = {}
        
        # Booking.com API
        if os.getenv("BOOKING_COM_API_KEY"):
            configs["booking_com"] = DataSourceConfig(
                enabled=True,
                api_key=os.getenv("BOOKING_COM_API_KEY"),
                api_secret=os.getenv("BOOKING_COM_API_SECRET"),
                rate_limit=int(os.getenv("BOOKING_COM_RATE_LIMIT", "60")),
                cost_per_request=float(os.getenv("BOOKING_COM_COST_PER_REQUEST", "0.01")),
                priority=int(os.getenv("BOOKING_COM_PRIORITY", "1"))
            )
        
        # Expedia Rapid API
        if os.getenv("EXPEDIA_API_KEY"):
            configs["expedia"] = DataSourceConfig(
                enabled=True,
                api_key=os.getenv("EXPEDIA_API_KEY"),
                api_secret=os.getenv("EXPEDIA_API_SECRET"),
                rate_limit=int(os.getenv("EXPEDIA_RATE_LIMIT", "300")),
                cost_per_request=float(os.getenv("EXPEDIA_COST_PER_REQUEST", "0.015")),
                priority=int(os.getenv("EXPEDIA_PRIORITY", "2"))
            )
        
        # Agoda API
        if os.getenv("AGODA_API_KEY"):
            configs["agoda"] = DataSourceConfig(
                enabled=True,
                api_key=os.getenv("AGODA_API_KEY"),
                rate_limit=int(os.getenv("AGODA_RATE_LIMIT", "100")),
                cost_per_request=float(os.getenv("AGODA_COST_PER_REQUEST", "0.02")),
                priority=int(os.getenv("AGODA_PRIORITY", "3"))
            )
        
        return configs
    
    def _load_scraping_config(self) -> DataSourceConfig:
        """Load scraping configuration from environment."""
        return DataSourceConfig(
            enabled=os.getenv("ENABLE_SCRAPING", "true").lower() == "true",
            rate_limit=int(os.getenv("SCRAPING_RATE_LIMIT", "10")),
            cost_per_request=float(os.getenv("SCRAPING_COST_PER_REQUEST", "0.0")),  # Proxies cost
            priority=int(os.getenv("SCRAPING_PRIORITY", "10")),  # Lower priority than APIs
            timeout=int(os.getenv("SCRAPING_TIMEOUT", "60"))
        )
    
    def _initialize_api_providers(self):
        """Initialize API providers based on configuration."""
        # Booking.com
        if "booking_com" in self.api_configs and self.api_configs["booking_com"].enabled:
            config = self.api_configs["booking_com"]
            self.api_providers["booking_com"] = BookingComProvider(
                api_key=config.api_key,
                api_secret=config.api_secret
            )
            logger.info("✓ Booking.com API provider initialized")
        
        # Expedia
        if "expedia" in self.api_configs and self.api_configs["expedia"].enabled:
            config = self.api_configs["expedia"]
            self.api_providers["expedia"] = ExpediaProvider(
                api_key=config.api_key,
                api_secret=config.api_secret
            )
            logger.info("✓ Expedia API provider initialized")
    
    def _initialize_scrapers(self):
        """Initialize web scrapers."""
        if not self.scraping_config.enabled:
            return
        
        try:
            from .enhanced_booking_scraper import EnhancedBookingScraper
            from .expedia_scraper import ExpediaScraper
            from .hotels_com_scraper import HotelsComScraper
            
            self.scrapers["booking_com"] = EnhancedBookingScraper(use_browser=True)
            self.scrapers["expedia"] = ExpediaScraper(use_browser=True)
            self.scrapers["hotels_com"] = HotelsComScraper(use_browser=True)
            
            logger.info(f"✓ {len(self.scrapers)} scrapers initialized")
        except Exception as e:
            logger.warning(f"Could not initialize scrapers: {e}")
    
    async def search_hotels(
        self,
        destination: str,
        check_in: date,
        check_out: date,
        guests: int = 1,
        rooms: int = 1,
        **kwargs
    ) -> Tuple[List[Hotel], DataSourceType]:
        """
        Search for hotels using configured strategy.
        
        Returns:
            Tuple of (hotels list, source type used)
        """
        if self.strategy == DataSourceStrategy.API_FIRST:
            return await self._search_api_first(destination, check_in, check_out, guests, rooms, **kwargs)
        elif self.strategy == DataSourceStrategy.SCRAPING_FIRST:
            return await self._search_scraping_first(destination, check_in, check_out, guests, rooms, **kwargs)
        elif self.strategy == DataSourceStrategy.API_ONLY:
            return await self._search_api_only(destination, check_in, check_out, guests, rooms, **kwargs)
        elif self.strategy == DataSourceStrategy.SCRAPING_ONLY:
            return await self._search_scraping_only(destination, check_in, check_out, guests, rooms, **kwargs)
        elif self.strategy == DataSourceStrategy.PARALLEL:
            return await self._search_parallel(destination, check_in, check_out, guests, rooms, **kwargs)
        elif self.strategy == DataSourceStrategy.CHEAPEST:
            return await self._search_cheapest(destination, check_in, check_out, guests, rooms, **kwargs)
        else:  # FASTEST
            return await self._search_fastest(destination, check_in, check_out, guests, rooms, **kwargs)
    
    async def _search_api_first(
        self,
        destination: str,
        check_in: date,
        check_out: date,
        guests: int,
        rooms: int,
        **kwargs
    ) -> Tuple[List[Hotel], DataSourceType]:
        """Try API first, fall back to scraping if API fails."""
        # Try all available APIs
        if self.api_providers:
            try:
                hotels = await self._search_with_apis(destination, check_in, check_out, guests, rooms, **kwargs)
                if hotels:
                    logger.info(f"✓ Found {len(hotels)} hotels via API")
                    self._record_success("api")
                    return hotels, DataSourceType.API
            except Exception as e:
                logger.warning(f"API search failed: {e}, falling back to scraping")
                self._record_failure("api")
        
        # Fall back to scraping
        if self.scrapers:
            try:
                hotels = await self._search_with_scrapers(destination, check_in, check_out, guests, rooms, **kwargs)
                logger.info(f"✓ Found {len(hotels)} hotels via scraping")
                self._record_success("scraping")
                return hotels, DataSourceType.SCRAPING
            except Exception as e:
                logger.error(f"Scraping also failed: {e}")
                self._record_failure("scraping")
        
        return [], DataSourceType.API  # Return empty if both fail
    
    async def _search_scraping_first(
        self,
        destination: str,
        check_in: date,
        check_out: date,
        guests: int,
        rooms: int,
        **kwargs
    ) -> Tuple[List[Hotel], DataSourceType]:
        """Try scraping first, fall back to API if scraping fails."""
        # Try scraping
        if self.scrapers:
            try:
                hotels = await self._search_with_scrapers(destination, check_in, check_out, guests, rooms, **kwargs)
                if hotels:
                    logger.info(f"✓ Found {len(hotels)} hotels via scraping")
                    self._record_success("scraping")
                    return hotels, DataSourceType.SCRAPING
            except Exception as e:
                logger.warning(f"Scraping failed: {e}, falling back to API")
                self._record_failure("scraping")
        
        # Fall back to API
        if self.api_providers:
            try:
                hotels = await self._search_with_apis(destination, check_in, check_out, guests, rooms, **kwargs)
                logger.info(f"✓ Found {len(hotels)} hotels via API")
                self._record_success("api")
                return hotels, DataSourceType.API
            except Exception as e:
                logger.error(f"API also failed: {e}")
                self._record_failure("api")
        
        return [], DataSourceType.SCRAPING
    
    async def _search_api_only(
        self,
        destination: str,
        check_in: date,
        check_out: date,
        guests: int,
        rooms: int,
        **kwargs
    ) -> Tuple[List[Hotel], DataSourceType]:
        """Use API only, fail if unavailable."""
        if not self.api_providers:
            raise ValueError("No API providers configured")
        
        hotels = await self._search_with_apis(destination, check_in, check_out, guests, rooms, **kwargs)
        self._record_success("api")
        return hotels, DataSourceType.API
    
    async def _search_scraping_only(
        self,
        destination: str,
        check_in: date,
        check_out: date,
        guests: int,
        rooms: int,
        **kwargs
    ) -> Tuple[List[Hotel], DataSourceType]:
        """Use scraping only."""
        if not self.scrapers:
            raise ValueError("No scrapers configured")
        
        hotels = await self._search_with_scrapers(destination, check_in, check_out, guests, rooms, **kwargs)
        self._record_success("scraping")
        return hotels, DataSourceType.SCRAPING
    
    async def _search_parallel(
        self,
        destination: str,
        check_in: date,
        check_out: date,
        guests: int,
        rooms: int,
        **kwargs
    ) -> Tuple[List[Hotel], DataSourceType]:
        """Run both API and scraping in parallel, merge results."""
        tasks = []
        
        if self.api_providers:
            tasks.append(self._search_with_apis(destination, check_in, check_out, guests, rooms, **kwargs))
        
        if self.scrapers:
            tasks.append(self._search_with_scrapers(destination, check_in, check_out, guests, rooms, **kwargs))
        
        if not tasks:
            return [], DataSourceType.BOTH
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Merge results, prioritizing API data
        all_hotels = []
        seen_ids = set()
        
        for result in results:
            if isinstance(result, list):
                for hotel in result:
                    if hotel.provider_hotel_id not in seen_ids:
                        all_hotels.append(hotel)
                        seen_ids.add(hotel.provider_hotel_id)
        
        logger.info(f"✓ Found {len(all_hotels)} hotels via parallel search")
        return all_hotels, DataSourceType.BOTH
    
    async def _search_cheapest(
        self,
        destination: str,
        check_in: date,
        check_out: date,
        guests: int,
        rooms: int,
        **kwargs
    ) -> Tuple[List[Hotel], DataSourceType]:
        """Choose based on cost."""
        # Scraping is usually cheaper (just proxy costs)
        if self.scrapers and self.scraping_config.cost_per_request <= min(
            [c.cost_per_request for c in self.api_configs.values()], default=999
        ):
            return await self._search_scraping_only(destination, check_in, check_out, guests, rooms, **kwargs)
        else:
            return await self._search_api_only(destination, check_in, check_out, guests, rooms, **kwargs)
    
    async def _search_fastest(
        self,
        destination: str,
        check_in: date,
        check_out: date,
        guests: int,
        rooms: int,
        **kwargs
    ) -> Tuple[List[Hotel], DataSourceType]:
        """Choose based on speed (APIs are usually faster)."""
        if self.api_providers:
            return await self._search_api_only(destination, check_in, check_out, guests, rooms, **kwargs)
        else:
            return await self._search_scraping_only(destination, check_in, check_out, guests, rooms, **kwargs)
    
    async def _search_with_apis(
        self,
        destination: str,
        check_in: date,
        check_out: date,
        guests: int,
        rooms: int,
        **kwargs
    ) -> List[Hotel]:
        """Search using all available API providers."""
        all_hotels = []
        seen_ids = set()
        
        # Sort providers by priority
        sorted_providers = sorted(
            self.api_providers.items(),
            key=lambda x: self.api_configs.get(x[0], DataSourceConfig()).priority
        )
        
        for provider_name, provider in sorted_providers:
            try:
                hotels = await provider.search_hotels(
                    destination, check_in, check_out, guests, rooms, **kwargs
                )
                
                # Deduplicate
                for hotel in hotels:
                    if hotel.provider_hotel_id not in seen_ids:
                        all_hotels.append(hotel)
                        seen_ids.add(hotel.provider_hotel_id)
                
                logger.info(f"✓ {provider_name} API returned {len(hotels)} hotels")
            except Exception as e:
                logger.warning(f"✗ {provider_name} API failed: {e}")
                continue
        
        return all_hotels
    
    async def _search_with_scrapers(
        self,
        destination: str,
        check_in: date,
        check_out: date,
        guests: int,
        rooms: int,
        **kwargs
    ) -> List[Hotel]:
        """Search using web scrapers."""
        # This would integrate with your existing scraper infrastructure
        # For now, return empty to avoid circular dependencies
        logger.warning("Scraper integration not yet implemented in hybrid manager")
        return []
    
    def _record_success(self, source_type: str):
        """Record successful request."""
        stats = self.stats[source_type]
        stats.total_requests += 1
        stats.successful_requests += 1
        stats.last_used = datetime.now()
        
        # Add cost
        if source_type == "api":
            total_cost = sum(c.cost_per_request for c in self.api_configs.values())
            stats.total_cost += total_cost
        else:
            stats.total_cost += self.scraping_config.cost_per_request
    
    def _record_failure(self, source_type: str):
        """Record failed request."""
        stats = self.stats[source_type]
        stats.total_requests += 1
        stats.failed_requests += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics for all data sources."""
        return {
            "api": {
                "enabled": self.enable_api,
                "providers": len(self.api_providers),
                "total_requests": self.stats["api"].total_requests,
                "success_rate": f"{self.stats['api'].success_rate:.1f}%",
                "total_cost": f"${self.stats['api'].total_cost:.2f}"
            },
            "scraping": {
                "enabled": self.enable_scraping,
                "scrapers": len(self.scrapers),
                "total_requests": self.stats["scraping"].total_requests,
                "success_rate": f"{self.stats['scraping'].success_rate:.1f}%",
                "total_cost": f"${self.stats['scraping'].total_cost:.2f}"
            },
            "strategy": self.strategy.value
        }
    
    def switch_strategy(self, new_strategy: DataSourceStrategy):
        """Dynamically switch data source strategy."""
        old_strategy = self.strategy
        self.strategy = new_strategy
        logger.info(f"Strategy switched: {old_strategy.value} → {new_strategy.value}")
    
    def disable_source(self, source_type: DataSourceType):
        """Disable a data source."""
        if source_type == DataSourceType.API:
            self.enable_api = False
            logger.info("API sources disabled")
        elif source_type == DataSourceType.SCRAPING:
            self.enable_scraping = False
            logger.info("Scraping sources disabled")
    
    def enable_source(self, source_type: DataSourceType):
        """Enable a data source."""
        if source_type == DataSourceType.API:
            self.enable_api = True
            if not self.api_providers:
                self._initialize_api_providers()
            logger.info("API sources enabled")
        elif source_type == DataSourceType.SCRAPING:
            self.enable_scraping = True
            if not self.scrapers:
                self._initialize_scrapers()
            logger.info("Scraping sources enabled")

