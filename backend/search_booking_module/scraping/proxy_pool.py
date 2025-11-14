"""Proxy pool management for scraping."""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import asyncio
import aiohttp
import logging
import random
from collections import deque

logger = logging.getLogger(__name__)


@dataclass
class Proxy:
    """Represents a proxy server."""
    url: str
    is_active: bool = True
    success_count: int = 0
    failure_count: int = 0
    last_used: Optional[datetime] = None
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    response_times: deque = None
    consecutive_failures: int = 0
    
    def __post_init__(self):
        if self.response_times is None:
            self.response_times = deque(maxlen=100)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 0.0
    
    @property
    def avg_response_time(self) -> float:
        """Calculate average response time."""
        if not self.response_times:
            return 0.0
        return sum(self.response_times) / len(self.response_times)
    
    @property
    def health_score(self) -> float:
        """Calculate health score (0-1)."""
        score = self.success_rate * 0.5  # 50% weight on success rate
        
        # Response time component (faster is better)
        if self.avg_response_time > 0:
            # Normalize response time (assume 10s is max acceptable)
            time_score = max(0, 1 - (self.avg_response_time / 10.0))
            score += time_score * 0.3  # 30% weight on response time
        
        # Consecutive failures penalty
        if self.consecutive_failures > 0:
            failure_penalty = min(0.2, self.consecutive_failures * 0.05)
            score -= failure_penalty  # Up to 20% penalty
        
        return max(0.0, min(1.0, score))


class ProxyPool:
    """Manages a pool of proxy servers."""
    
    def __init__(
        self,
        proxies: Optional[List[str]] = None,
        health_check_interval: Optional[int] = None,
        max_consecutive_failures: Optional[int] = None,
        min_success_rate: Optional[float] = None
    ):
        """Initialize proxy pool.
        
        Args:
            proxies: List of proxy URLs (defaults to config)
            health_check_interval: Interval between health checks (defaults to config)
            max_consecutive_failures: Max failures before marking proxy inactive (defaults to config)
            min_success_rate: Minimum success rate to keep proxy active (defaults to config)
        """
        from .config import (
            PROXY_POOL_HEALTH_CHECK_INTERVAL,
            PROXY_POOL_MAX_CONSECUTIVE_FAILURES,
            PROXY_POOL_MIN_SUCCESS_RATE
        )
        
        self.proxies: List[Proxy] = []
        self.health_check_interval = health_check_interval or PROXY_POOL_HEALTH_CHECK_INTERVAL
        self.max_consecutive_failures = max_consecutive_failures or PROXY_POOL_MAX_CONSECUTIVE_FAILURES
        self.min_success_rate = min_success_rate or PROXY_POOL_MIN_SUCCESS_RATE
        
        if proxies:
            for proxy_url in proxies:
                self.add_proxy(proxy_url)
        
        self.current_index = 0
        self.health_check_task: Optional[asyncio.Task] = None
        self.is_running = False
    
    def add_proxy(self, proxy_url: str):
        """Add a proxy to the pool."""
        proxy = Proxy(url=proxy_url)
        self.proxies.append(proxy)
        logger.info(f"Added proxy: {proxy_url}")
    
    def remove_proxy(self, proxy_url: str):
        """Remove a proxy from the pool."""
        self.proxies = [p for p in self.proxies if p.url != proxy_url]
        logger.info(f"Removed proxy: {proxy_url}")
    
    def get_proxy(self, strategy: str = 'round_robin') -> Optional[str]:
        """Get a proxy from the pool.
        
        Args:
            strategy: Selection strategy ('round_robin', 'random', 'health_based')
            
        Returns:
            Proxy URL or None if no active proxies
        """
        active_proxies = [p for p in self.proxies if p.is_active]
        
        if not active_proxies:
            logger.warning("No active proxies available")
            return None
        
        if strategy == 'round_robin':
            proxy = active_proxies[self.current_index % len(active_proxies)]
            self.current_index += 1
            return proxy.url
        
        elif strategy == 'random':
            proxy = random.choice(active_proxies)
            return proxy.url
        
        elif strategy == 'health_based':
            # Select proxy with highest health score
            proxy = max(active_proxies, key=lambda p: p.health_score)
            return proxy.url
        
        else:
            # Default to round robin
            return self.get_proxy('round_robin')
    
    def mark_success(self, proxy_url: str, response_time: float = 0.0):
        """Mark a proxy request as successful.
        
        Args:
            proxy_url: Proxy URL
            response_time: Response time in seconds
        """
        proxy = self._find_proxy(proxy_url)
        if proxy:
            proxy.success_count += 1
            proxy.last_success = datetime.utcnow()
            proxy.last_used = datetime.utcnow()
            proxy.consecutive_failures = 0
            if response_time > 0:
                proxy.response_times.append(response_time)
            
            # Reactivate if it was inactive
            if not proxy.is_active:
                proxy.is_active = True
                logger.info(f"Reactivated proxy: {proxy_url}")
    
    def mark_failure(self, proxy_url: str, reason: str = "unknown"):
        """Mark a proxy request as failed.
        
        Args:
            proxy_url: Proxy URL
            reason: Failure reason
        """
        proxy = self._find_proxy(proxy_url)
        if proxy:
            proxy.failure_count += 1
            proxy.last_failure = datetime.utcnow()
            proxy.last_used = datetime.utcnow()
            proxy.consecutive_failures += 1
            
            # Deactivate if too many consecutive failures
            if proxy.consecutive_failures >= self.max_consecutive_failures:
                proxy.is_active = False
                logger.warning(f"Deactivated proxy {proxy_url} after {proxy.consecutive_failures} consecutive failures")
            
            # Deactivate if success rate too low
            elif proxy.success_rate < self.min_success_rate and proxy.success_count + proxy.failure_count >= 10:
                proxy.is_active = False
                logger.warning(f"Deactivated proxy {proxy_url} due to low success rate: {proxy.success_rate:.2%}")
    
    def _find_proxy(self, proxy_url: str) -> Optional[Proxy]:
        """Find proxy by URL."""
        for proxy in self.proxies:
            if proxy.url == proxy_url:
                return proxy
        return None
    
    async def health_check(self, proxy: Proxy) -> bool:
        """Check if a proxy is healthy.
        
        Args:
            proxy: Proxy to check
            
        Returns:
            True if proxy is healthy
        """
        try:
            async with aiohttp.ClientSession() as session:
                start_time = asyncio.get_event_loop().time()
                async with session.get(
                    'https://httpbin.org/ip',
                    proxy=proxy.url,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    response_time = asyncio.get_event_loop().time() - start_time
                    
                    if response.status == 200:
                        self.mark_success(proxy.url, response_time)
                        return True
                    else:
                        self.mark_failure(proxy.url, f"HTTP {response.status}")
                        return False
        except asyncio.TimeoutError:
            self.mark_failure(proxy.url, "timeout")
            return False
        except Exception as e:
            self.mark_failure(proxy.url, str(e))
            return False
    
    async def check_all_proxies(self):
        """Check health of all proxies."""
        logger.info(f"Checking health of {len(self.proxies)} proxies...")
        
        tasks = [self.health_check(proxy) for proxy in self.proxies]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        healthy_count = sum(1 for r in results if r is True)
        logger.info(f"Health check complete: {healthy_count}/{len(self.proxies)} proxies healthy")
    
    async def start_health_monitoring(self):
        """Start continuous health monitoring."""
        self.is_running = True
        logger.info("Started proxy health monitoring")
        
        while self.is_running:
            try:
                await self.check_all_proxies()
                await asyncio.sleep(self.health_check_interval)
            except Exception as e:
                logger.error(f"Error in health monitoring: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    async def stop_health_monitoring(self):
        """Stop health monitoring."""
        self.is_running = False
        if self.health_check_task:
            self.health_check_task.cancel()
            try:
                await self.health_check_task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped proxy health monitoring")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get proxy pool statistics."""
        active_proxies = [p for p in self.proxies if p.is_active]
        
        return {
            'total_proxies': len(self.proxies),
            'active_proxies': len(active_proxies),
            'inactive_proxies': len(self.proxies) - len(active_proxies),
            'proxies': [
                {
                    'url': p.url,
                    'is_active': p.is_active,
                    'success_rate': p.success_rate,
                    'avg_response_time': p.avg_response_time,
                    'health_score': p.health_score,
                    'success_count': p.success_count,
                    'failure_count': p.failure_count,
                    'consecutive_failures': p.consecutive_failures,
                    'last_used': p.last_used.isoformat() if p.last_used else None,
                }
                for p in self.proxies
            ]
        }

