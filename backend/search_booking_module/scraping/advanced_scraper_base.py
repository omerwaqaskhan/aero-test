"""Advanced base scraper with retry logic, proxy support, and enhanced error handling."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Callable
from datetime import date, datetime
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import logging
import random
import time
from functools import wraps
import json

logger = logging.getLogger(__name__)


def retry_with_backoff(max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0, backoff_factor: float = 2.0):
    """Decorator for retrying functions with exponential backoff."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        delay = min(base_delay * (backoff_factor ** attempt), max_delay)
                        # Add jitter to avoid thundering herd
                        jitter = random.uniform(0, delay * 0.1)
                        total_delay = delay + jitter
                        logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}. Retrying in {total_delay:.2f}s...")
                        await asyncio.sleep(total_delay)
                    else:
                        logger.error(f"All {max_retries} attempts failed for {func.__name__}: {e}")
            raise last_exception
        return wrapper
    return decorator


class ProxyManager:
    """Manages proxy rotation for scraping."""
    
    def __init__(self, proxies: Optional[List[str]] = None):
        """Initialize proxy manager.
        
        Args:
            proxies: List of proxy URLs in format 'http://user:pass@host:port'
        """
        self.proxies = proxies or []
        self.current_index = 0
        self.failed_proxies = set()
        self.proxy_stats = {}  # Track success/failure rates
    
    def get_proxy(self) -> Optional[str]:
        """Get next proxy in rotation."""
        if not self.proxies:
            return None
        
        # Filter out failed proxies (can be reset periodically)
        available_proxies = [p for p in self.proxies if p not in self.failed_proxies]
        if not available_proxies:
            # Reset failed proxies if all are marked as failed
            logger.warning("All proxies marked as failed, resetting...")
            self.failed_proxies.clear()
            available_proxies = self.proxies
        
        if available_proxies:
            proxy = available_proxies[self.current_index % len(available_proxies)]
            self.current_index += 1
            return proxy
        return None
    
    def mark_proxy_failed(self, proxy: str):
        """Mark a proxy as failed."""
        self.failed_proxies.add(proxy)
        if proxy in self.proxy_stats:
            self.proxy_stats[proxy]['failures'] = self.proxy_stats[proxy].get('failures', 0) + 1
        else:
            self.proxy_stats[proxy] = {'failures': 1, 'successes': 0}
    
    def mark_proxy_success(self, proxy: str):
        """Mark a proxy as successful."""
        if proxy in self.failed_proxies:
            # Remove from failed list if it's working again
            self.failed_proxies.discard(proxy)
        
        if proxy in self.proxy_stats:
            self.proxy_stats[proxy]['successes'] = self.proxy_stats[proxy].get('successes', 0) + 1
        else:
            self.proxy_stats[proxy] = {'successes': 1, 'failures': 0}


class RateLimiter:
    """Manages rate limiting for requests."""
    
    def __init__(self, requests_per_second: float = 1.0, burst_size: int = 5):
        """Initialize rate limiter.
        
        Args:
            requests_per_second: Maximum requests per second
            burst_size: Maximum burst of requests allowed
        """
        self.requests_per_second = requests_per_second
        self.burst_size = burst_size
        self.min_interval = 1.0 / requests_per_second if requests_per_second > 0 else 0
        self.last_request_time = 0.0
        self.request_times = []
    
    async def wait_if_needed(self):
        """Wait if rate limit would be exceeded."""
        now = time.time()
        
        # Remove old request times (older than 1 second)
        self.request_times = [t for t in self.request_times if now - t < 1.0]
        
        # Check if we're at burst limit
        if len(self.request_times) >= self.burst_size:
            # Wait until oldest request is 1 second old
            oldest_time = min(self.request_times)
            wait_time = 1.0 - (now - oldest_time)
            if wait_time > 0:
                await asyncio.sleep(wait_time)
                now = time.time()
        
        # Check minimum interval
        time_since_last = now - self.last_request_time
        if time_since_last < self.min_interval:
            wait_time = self.min_interval - time_since_last
            await asyncio.sleep(wait_time)
        
        # Record this request
        self.last_request_time = time.time()
        self.request_times.append(self.last_request_time)


class AdvancedBaseScraper(ABC):
    """Advanced base scraper with retry logic, proxy support, and rate limiting."""
    
    # Common user agents to rotate
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    ]
    
    def __init__(
        self,
        base_url: str,
        headers: Optional[Dict[str, str]] = None,
        proxies: Optional[List[str]] = None,
        rate_limit: float = 1.0,
        max_retries: int = 3,
        timeout: int = 30
    ):
        """Initialize advanced scraper.
        
        Args:
            base_url: Base URL for the scraper
            headers: Custom headers (will be merged with defaults)
            proxies: List of proxy URLs
            rate_limit: Requests per second
            max_retries: Maximum retry attempts
            timeout: Request timeout in seconds
        """
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.proxy_manager = ProxyManager(proxies)
        self.rate_limiter = RateLimiter(requests_per_second=rate_limit)
        
        # Setup headers with rotation
        default_headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        }
        
        if headers:
            default_headers.update(headers)
        
        self.default_headers = default_headers
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Statistics
        self.stats = {
            'requests_made': 0,
            'requests_failed': 0,
            'requests_succeeded': 0,
            'retries': 0,
            'proxy_rotations': 0,
        }
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers with random user agent."""
        headers = self.default_headers.copy()
        headers['User-Agent'] = random.choice(self.USER_AGENTS)
        return headers
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    @retry_with_backoff(max_retries=3, base_delay=1.0)
    async def fetch_page(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        use_proxy: bool = True
    ) -> Optional[str]:
        """Fetch a web page with retry logic and rate limiting.
        
        Args:
            url: URL to fetch
            params: Query parameters
            headers: Custom headers (merged with defaults)
            use_proxy: Whether to use proxy if available
            
        Returns:
            HTML content or None if failed
        """
        await self.rate_limiter.wait_if_needed()
        
        request_headers = self._get_headers()
        if headers:
            request_headers.update(headers)
        
        proxy = self.proxy_manager.get_proxy() if use_proxy else None
        
        try:
            self.stats['requests_made'] += 1
            
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with self.session.get(
                url,
                params=params,
                headers=request_headers,
                proxy=proxy,
                timeout=timeout,
                allow_redirects=True
            ) as response:
                if response.status == 200:
                    content = await response.text()
                    self.stats['requests_succeeded'] += 1
                    if proxy:
                        self.proxy_manager.mark_proxy_success(proxy)
                    return content
                elif response.status == 429:  # Too Many Requests
                    logger.warning(f"Rate limited (429) for {url}. Waiting longer...")
                    await asyncio.sleep(5)  # Wait longer for rate limits
                    self.stats['requests_failed'] += 1
                    if proxy:
                        self.proxy_manager.mark_proxy_failed(proxy)
                    raise Exception(f"Rate limited: {response.status}")
                else:
                    logger.warning(f"Failed to fetch {url}: Status {response.status}")
                    self.stats['requests_failed'] += 1
                    if proxy:
                        self.proxy_manager.mark_proxy_failed(proxy)
                    return None
        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching {url}")
            self.stats['requests_failed'] += 1
            if proxy:
                self.proxy_manager.mark_proxy_failed(proxy)
            raise
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            self.stats['requests_failed'] += 1
            if proxy:
                self.proxy_manager.mark_proxy_failed(proxy)
            raise
    
    async def fetch_json(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Optional[Dict]:
        """Fetch JSON data from an API endpoint."""
        await self.rate_limiter.wait_if_needed()
        
        request_headers = self._get_headers()
        request_headers['Accept'] = 'application/json'
        if headers:
            request_headers.update(headers)
        
        proxy = self.proxy_manager.get_proxy()
        
        try:
            self.stats['requests_made'] += 1
            
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with self.session.get(
                url,
                params=params,
                headers=request_headers,
                proxy=proxy,
                timeout=timeout
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.stats['requests_succeeded'] += 1
                    if proxy:
                        self.proxy_manager.mark_proxy_success(proxy)
                    return data
                else:
                    logger.warning(f"Failed to fetch JSON from {url}: Status {response.status}")
                    self.stats['requests_failed'] += 1
                    if proxy:
                        self.proxy_manager.mark_proxy_failed(proxy)
                    return None
        except Exception as e:
            logger.error(f"Error fetching JSON from {url}: {e}")
            self.stats['requests_failed'] += 1
            if proxy:
                self.proxy_manager.mark_proxy_failed(proxy)
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get scraper statistics."""
        success_rate = (
            self.stats['requests_succeeded'] / self.stats['requests_made']
            if self.stats['requests_made'] > 0
            else 0.0
        )
        
        return {
            **self.stats,
            'success_rate': success_rate,
            'proxy_stats': self.proxy_manager.proxy_stats,
        }
    
    @abstractmethod
    async def search_hotels(
        self,
        destination: str,
        check_in: Optional[date] = None,
        check_out: Optional[date] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Search for hotels in a destination."""
        pass
    
    @abstractmethod
    async def get_hotel_details(self, hotel_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific hotel."""
        pass
    
    async def delay(self, seconds: float = None):
        """Add delay between requests."""
        if seconds is None:
            seconds = self.rate_limiter.min_interval
        await asyncio.sleep(seconds)

