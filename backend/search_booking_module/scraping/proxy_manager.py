"""
Advanced Proxy Pool Manager with automatic rotation, health checks, and failover.
Supports residential, datacenter, and rotating proxies.
"""
import asyncio
import random
import time
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import aiohttp
import logging

logger = logging.getLogger(__name__)


@dataclass
class ProxyStats:
    """Statistics for a single proxy."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    last_used: Optional[datetime] = None
    last_success: Optional[datetime] = None
    consecutive_failures: int = 0
    average_response_time: float = 0.0
    response_times: List[float] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_requests == 0:
            return 100.0
        return (self.successful_requests / self.total_requests) * 100
    
    @property
    def health_score(self) -> float:
        """
        Calculate overall health score (0-100).
        Factors: success rate, response time, recency, consecutive failures.
        """
        if self.total_requests == 0:
            return 100.0  # New proxies start with good score
        
        # Success rate component (50% weight)
        success_component = self.success_rate * 0.5
        
        # Response time component (20% weight) - faster is better
        # Normalize to 0-20 range (assuming 5s is worst, 1s is best)
        if self.average_response_time > 0:
            response_component = max(0, 20 - (self.average_response_time / 5 * 20))
        else:
            response_component = 20
        
        # Recency component (20% weight)
        if self.last_success:
            hours_since = (datetime.now() - self.last_success).total_seconds() / 3600
            recency_component = max(0, 20 - (hours_since / 24 * 20))  # Decay over 24h
        else:
            recency_component = 0
        
        # Penalty for consecutive failures (10% weight)
        failure_penalty = min(self.consecutive_failures * 2, 10)  # Max 10 point penalty
        
        return success_component + response_component + recency_component - failure_penalty


@dataclass
class Proxy:
    """Proxy configuration with health tracking."""
    url: str  # Format: http://user:pass@host:port or http://host:port
    proxy_type: str = "http"  # http, https, socks5
    country: Optional[str] = None
    provider: Optional[str] = None
    stats: ProxyStats = field(default_factory=ProxyStats)
    is_rotating: bool = False  # True for sticky session proxies
    session_duration: int = 300  # Seconds before rotation (for rotating proxies)
    last_rotation: Optional[datetime] = None
    
    @property
    def is_healthy(self) -> bool:
        """Check if proxy is considered healthy."""
        # Proxy is unhealthy if:
        # - Health score below 30
        # - More than 5 consecutive failures
        # - No successful requests in last hour (if used)
        if self.stats.health_score < 30:
            return False
        if self.stats.consecutive_failures > 5:
            return False
        if self.stats.last_success:
            hours_since = (datetime.now() - self.stats.last_success).total_seconds() / 3600
            if hours_since > 1 and self.stats.total_requests > 10:
                return False
        return True
    
    @property
    def needs_rotation(self) -> bool:
        """Check if rotating proxy needs to be rotated."""
        if not self.is_rotating or not self.last_rotation:
            return False
        elapsed = (datetime.now() - self.last_rotation).total_seconds()
        return elapsed >= self.session_duration
    
    def record_request(self, success: bool, response_time: float):
        """Record request result and update statistics."""
        self.stats.total_requests += 1
        self.stats.last_used = datetime.now()
        
        if success:
            self.stats.successful_requests += 1
            self.stats.consecutive_failures = 0
            self.stats.last_success = datetime.now()
            
            # Update average response time (rolling average of last 10)
            self.stats.response_times.append(response_time)
            if len(self.stats.response_times) > 10:
                self.stats.response_times.pop(0)
            self.stats.average_response_time = sum(self.stats.response_times) / len(self.stats.response_times)
        else:
            self.stats.failed_requests += 1
            self.stats.consecutive_failures += 1


class ProxyManager:
    """
    Advanced proxy pool manager with automatic health checks and intelligent rotation.
    """
    
    def __init__(
        self,
        proxies: Optional[List[str]] = None,
        enable_health_checks: bool = True,
        health_check_interval: int = 300,  # 5 minutes
        health_check_url: str = "https://httpbin.org/ip",
        max_consecutive_failures: int = 5
    ):
        self.proxies: List[Proxy] = []
        self.enable_health_checks = enable_health_checks
        self.health_check_interval = health_check_interval
        self.health_check_url = health_check_url
        self.max_consecutive_failures = max_consecutive_failures
        self._health_check_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
        
        # Initialize proxies if provided
        if proxies:
            for proxy_url in proxies:
                self.add_proxy(proxy_url)
        
        logger.info(f"ProxyManager initialized with {len(self.proxies)} proxies")
    
    def add_proxy(
        self,
        proxy_url: str,
        proxy_type: str = "http",
        country: Optional[str] = None,
        provider: Optional[str] = None,
        is_rotating: bool = False
    ):
        """Add a proxy to the pool."""
        proxy = Proxy(
            url=proxy_url,
            proxy_type=proxy_type,
            country=country,
            provider=provider,
            is_rotating=is_rotating
        )
        self.proxies.append(proxy)
        logger.info(f"Added proxy: {proxy_url[:30]}... (total: {len(self.proxies)})")
    
    def remove_proxy(self, proxy_url: str):
        """Remove a proxy from the pool."""
        self.proxies = [p for p in self.proxies if p.url != proxy_url]
        logger.info(f"Removed proxy: {proxy_url[:30]}...")
    
    async def get_proxy(self, prefer_country: Optional[str] = None) -> Optional[Proxy]:
        """
        Get the best available proxy using intelligent selection.
        
        Selection criteria:
        1. Filter out unhealthy proxies
        2. Prefer proxies from specified country (if provided)
        3. Select based on weighted health score
        4. Add randomness to avoid overusing best proxies
        """
        async with self._lock:
            if not self.proxies:
                logger.warning("No proxies available")
                return None
            
            # Filter healthy proxies
            healthy_proxies = [p for p in self.proxies if p.is_healthy]
            
            if not healthy_proxies:
                logger.warning("No healthy proxies available, using all proxies")
                healthy_proxies = self.proxies
            
            # Filter by country if specified
            if prefer_country:
                country_proxies = [p for p in healthy_proxies if p.country == prefer_country]
                if country_proxies:
                    healthy_proxies = country_proxies
            
            # Sort by health score
            healthy_proxies.sort(key=lambda p: p.stats.health_score, reverse=True)
            
            # Weighted random selection (favor top 50% but don't always pick #1)
            # This prevents overusing a single proxy
            top_half = healthy_proxies[:max(1, len(healthy_proxies) // 2)]
            
            # Weight by health score
            weights = [p.stats.health_score for p in top_half]
            total_weight = sum(weights)
            
            if total_weight == 0:
                selected = random.choice(top_half)
            else:
                normalized_weights = [w / total_weight for w in weights]
                selected = random.choices(top_half, weights=normalized_weights, k=1)[0]
            
            # Check if needs rotation
            if selected.needs_rotation:
                selected.last_rotation = datetime.now()
                logger.info(f"Rotating proxy session: {selected.url[:30]}...")
            
            return selected
    
    async def record_result(self, proxy: Proxy, success: bool, response_time: float):
        """Record the result of a request made with a proxy."""
        async with self._lock:
            proxy.record_request(success, response_time)
            
            if not success:
                logger.warning(
                    f"Proxy {proxy.url[:30]}... failed "
                    f"(consecutive: {proxy.stats.consecutive_failures}, "
                    f"health: {proxy.stats.health_score:.1f})"
                )
                
                # Auto-remove if too many consecutive failures
                if proxy.stats.consecutive_failures >= self.max_consecutive_failures:
                    logger.error(f"Removing unhealthy proxy: {proxy.url[:30]}...")
                    self.remove_proxy(proxy.url)
    
    async def check_proxy_health(self, proxy: Proxy) -> bool:
        """Check if a proxy is working by making a test request."""
        start_time = time.time()
        
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(
                    self.health_check_url,
                    proxy=proxy.url,
                    ssl=False
                ) as response:
                    response_time = time.time() - start_time
                    success = response.status == 200
                    
                    await self.record_result(proxy, success, response_time)
                    return success
        except Exception as e:
            response_time = time.time() - start_time
            await self.record_result(proxy, False, response_time)
            logger.debug(f"Health check failed for {proxy.url[:30]}...: {e}")
            return False
    
    async def run_health_checks(self):
        """Continuously run health checks on all proxies."""
        logger.info("Starting proxy health check background task")
        
        while True:
            try:
                await asyncio.sleep(self.health_check_interval)
                
                logger.info(f"Running health checks on {len(self.proxies)} proxies...")
                
                # Check all proxies concurrently
                tasks = [self.check_proxy_health(proxy) for proxy in self.proxies]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                healthy_count = sum(1 for r in results if r is True)
                logger.info(
                    f"Health check complete: {healthy_count}/{len(self.proxies)} proxies healthy"
                )
                
            except Exception as e:
                logger.error(f"Error in health check task: {e}")
    
    async def start(self):
        """Start the proxy manager and health check background task."""
        if self.enable_health_checks and self._health_check_task is None:
            self._health_check_task = asyncio.create_task(self.run_health_checks())
            logger.info("Proxy manager started with health checks")
    
    async def stop(self):
        """Stop the proxy manager and cancel health checks."""
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
            self._health_check_task = None
            logger.info("Proxy manager stopped")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics for all proxies."""
        return {
            "total_proxies": len(self.proxies),
            "healthy_proxies": sum(1 for p in self.proxies if p.is_healthy),
            "proxies": [
                {
                    "url": p.url[:30] + "...",
                    "health_score": round(p.stats.health_score, 2),
                    "success_rate": round(p.stats.success_rate, 2),
                    "total_requests": p.stats.total_requests,
                    "consecutive_failures": p.stats.consecutive_failures,
                    "avg_response_time": round(p.stats.average_response_time, 2),
                    "is_healthy": p.is_healthy
                }
                for p in sorted(self.proxies, key=lambda p: p.stats.health_score, reverse=True)
            ]
        }


# Example usage and configuration
EXAMPLE_PROXY_CONFIGS = {
    "free_proxies": [
        # Free proxy lists (unreliable, for testing only)
        # "http://proxy1.example.com:8080",
        # "http://proxy2.example.com:8080",
    ],
    "paid_residential": [
        # Residential proxy services (best for scraping)
        # "http://username:password@proxy.brightdata.com:22225",
        # "http://username:password@proxy.oxylabs.io:7777",
        # "http://username:password@proxy.smartproxy.com:10000",
    ],
    "paid_datacenter": [
        # Datacenter proxies (faster but more detectable)
        # "http://username:password@proxy.geonode.com:9000",
        # "http://username:password@proxy.proxyrack.com:10000",
    ],
    "rotating_proxies": [
        # Rotating proxy services (automatic IP rotation)
        # "http://username:password@rotating.brightdata.com:22225",
    ]
}

