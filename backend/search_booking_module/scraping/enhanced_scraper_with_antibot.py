"""
Enhanced Scraper with Full Anti-Bot Protection
Demonstrates integration of proxy rotation, CAPTCHA solving, and anti-detection.
"""
import asyncio
import time
from typing import List, Dict, Any, Optional
from playwright.async_api import async_playwright, Page, Browser
import logging

from .proxy_manager import ProxyManager
from .captcha_solver import CaptchaSolver
from .anti_detection import AntiDetectionManager
from .anti_bot_config import get_config, AntiBotConfig

logger = logging.getLogger(__name__)


class AntiBotScraper:
    """
    Advanced scraper with built-in anti-bot protection.
    """
    
    def __init__(self, config: Optional[AntiBotConfig] = None):
        self.config = config or get_config("production_light")
        
        # Initialize components
        self.proxy_manager: Optional[ProxyManager] = None
        self.captcha_solver: Optional[CaptchaSolver] = None
        self.anti_detection = AntiDetectionManager()
        
        self.browser: Optional[Browser] = None
        self.requests_in_session = 0
        
        # Rate limiting
        self.request_times: List[float] = []
    
    async def initialize(self):
        """Initialize all anti-bot components."""
        logger.info("Initializing AntiBot Scraper...")
        
        # Setup proxy manager
        if self.config.enable_proxies:
            proxy_url = self.config.get_proxy_url()
            if proxy_url:
                self.proxy_manager = ProxyManager(
                    proxies=[proxy_url],
                    enable_health_checks=self.config.proxy_health_checks
                )
                await self.proxy_manager.start()
                logger.info("Proxy manager initialized")
        
        # Setup CAPTCHA solver
        if self.config.enable_captcha_solving and self.config.captcha_api_key:
            self.captcha_solver = CaptchaSolver(
                service=self.config.captcha_service,
                api_key=self.config.captcha_api_key
            )
            logger.info("CAPTCHA solver initialized")
        
        logger.info("AntiBot Scraper ready!")
    
    async def shutdown(self):
        """Cleanup resources."""
        if self.proxy_manager:
            await self.proxy_manager.stop()
        
        if self.browser:
            await self.browser.close()
        
        logger.info("AntiBot Scraper shut down")
    
    async def _wait_for_rate_limit(self):
        """Implement rate limiting."""
        if not self.config.requests_per_minute:
            return
        
        now = time.time()
        
        # Remove old timestamps (older than 1 minute)
        self.request_times = [t for t in self.request_times if now - t < 60]
        
        # Check if we've exceeded rate limit
        if len(self.request_times) >= self.config.requests_per_minute:
            # Wait until oldest request is > 1 minute old
            wait_time = 60 - (now - self.request_times[0]) + 0.1
            if wait_time > 0:
                logger.info(f"Rate limit reached, waiting {wait_time:.1f}s...")
                await asyncio.sleep(wait_time)
        
        # Add current request
        self.request_times.append(now)
    
    async def _apply_human_delay(self):
        """Add random delay to simulate human behavior."""
        if self.config.random_delays:
            delay = self.anti_detection.get_random_delay(
                self.config.min_delay,
                self.config.max_delay
            )
            await asyncio.sleep(delay)
    
    async def _check_session_rotation(self):
        """Check if browser session needs rotation."""
        if self.anti_detection.should_rotate_session(
            self.requests_in_session,
            self.config.max_requests_per_session
        ):
            logger.info("Session rotation triggered")
            if self.browser:
                await self.browser.close()
                self.browser = None
            self.requests_in_session = 0
    
    async def _get_browser_context(self):
        """Get or create browser with anti-detection settings."""
        if not self.browser:
            # Get proxy
            proxy = await self.proxy_manager.get_proxy() if self.proxy_manager else None
            
            # Get browser fingerprint
            fingerprint = self.anti_detection.get_browser_fingerprint()
            
            async with async_playwright() as p:
                # Launch options
                launch_options = {
                    "headless": True,
                }
                
                if proxy:
                    launch_options["proxy"] = {"server": proxy.url}
                    logger.info(f"Using proxy: {proxy.url[:30]}...")
                
                self.browser = await p.chromium.launch(**launch_options)
                
                # Create context with fingerprint
                context_options = fingerprint.playwright_context_options
                context = await self.browser.new_context(**context_options)
                
                return context, proxy
        
        return await self.browser.new_context(), None
    
    async def scrape_page(
        self,
        url: str,
        wait_selector: Optional[str] = None,
        retry_count: int = 0
    ) -> Optional[Dict[str, Any]]:
        """
        Scrape a page with full anti-bot protection.
        
        Args:
            url: URL to scrape
            wait_selector: CSS selector to wait for
            retry_count: Current retry attempt
            
        Returns:
            Dictionary with scraped data or None if failed
        """
        # Rate limiting
        await self._wait_for_rate_limit()
        
        # Human-like delay
        await self._apply_human_delay()
        
        # Check session rotation
        await self._check_session_rotation()
        
        try:
            context, proxy = await self._get_browser_context()
            page = await context.new_page()
            
            # Apply stealth mode
            if self.config.enable_stealth_mode:
                await self.anti_detection.apply_stealth_mode(page)
            
            # Navigate to page
            start_time = time.time()
            response = await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            response_time = time.time() - start_time
            
            # Record proxy result
            if proxy and self.proxy_manager:
                await self.proxy_manager.record_result(
                    proxy,
                    success=response.status < 400,
                    response_time=response_time
                )
            
            # Wait for content
            if wait_selector:
                await page.wait_for_selector(wait_selector, timeout=10000)
            
            # Check for CAPTCHA
            if await self._check_and_solve_captcha(page, url):
                logger.info("CAPTCHA solved, continuing...")
            
            # Extract data
            content = await page.content()
            title = await page.title()
            
            await page.close()
            
            self.requests_in_session += 1
            
            return {
                "url": url,
                "status": response.status,
                "title": title,
                "content": content,
                "response_time": response_time
            }
        
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            
            # Retry logic
            if retry_count < self.config.max_retries:
                wait_time = self.config.retry_delay * (2 ** retry_count if self.config.exponential_backoff else 1)
                logger.info(f"Retrying in {wait_time}s... (attempt {retry_count + 1}/{self.config.max_retries})")
                await asyncio.sleep(wait_time)
                return await self.scrape_page(url, wait_selector, retry_count + 1)
            
            return None
    
    async def _check_and_solve_captcha(self, page: Page, url: str) -> bool:
        """
        Check for CAPTCHA and solve if present.
        
        Returns:
            True if CAPTCHA was solved, False otherwise
        """
        if not self.captcha_solver:
            return False
        
        try:
            # Check for reCAPTCHA v2
            recaptcha_v2 = page.locator("iframe[src*='recaptcha/api2']")
            if await recaptcha_v2.count() > 0:
                logger.info("reCAPTCHA v2 detected")
                
                # Get site key
                iframe = await recaptcha_v2.first.get_attribute("src")
                site_key = iframe.split("k=")[1].split("&")[0] if "k=" in iframe else None
                
                if site_key:
                    token = await self.captcha_solver.solve_recaptcha_v2(site_key, url)
                    
                    if token:
                        # Inject token
                        await page.evaluate(f"""
                            document.getElementById('g-recaptcha-response').innerHTML = '{token}';
                        """)
                        
                        # Submit form
                        await page.click("button[type='submit']")
                        await page.wait_for_load_state("networkidle")
                        
                        return True
            
            # Check for reCAPTCHA v3 (usually invisible)
            recaptcha_v3 = page.locator(".grecaptcha-badge")
            if await recaptcha_v3.count() > 0:
                logger.info("reCAPTCHA v3 detected (may be invisible)")
                # v3 is usually handled automatically by the page
                # If challenges appear, solve similar to v2
            
            # Check for hCaptcha
            hcaptcha = page.locator("iframe[src*='hcaptcha.com']")
            if await hcaptcha.count() > 0:
                logger.info("hCaptcha detected")
                # Similar solving logic for hCaptcha
            
            return False
        
        except Exception as e:
            logger.error(f"Error checking/solving CAPTCHA: {e}")
            return False
    
    async def scrape_multiple(
        self,
        urls: List[str],
        max_concurrent: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Scrape multiple URLs concurrently with rate limiting.
        
        Args:
            urls: List of URLs to scrape
            max_concurrent: Maximum concurrent requests (uses config if None)
            
        Returns:
            List of scraped data dictionaries
        """
        max_concurrent = max_concurrent or self.config.max_concurrent_requests
        
        results = []
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def scrape_with_semaphore(url):
            async with semaphore:
                return await self.scrape_page(url)
        
        tasks = [scrape_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out None and exceptions
        return [r for r in results if isinstance(r, dict)]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get scraping statistics."""
        stats = {
            "requests_in_session": self.requests_in_session,
            "config": {
                "proxies_enabled": self.config.enable_proxies,
                "captcha_enabled": self.config.enable_captcha_solving,
                "stealth_enabled": self.config.enable_stealth_mode,
                "max_concurrent": self.config.max_concurrent_requests,
                "rate_limit": f"{self.config.requests_per_minute}/min"
            }
        }
        
        if self.proxy_manager:
            stats["proxy_stats"] = self.proxy_manager.get_stats()
        
        return stats


# Example usage
async def main():
    """Example usage of AntiBotScraper."""
    # Use production config
    config = get_config("production_light")
    
    scraper = AntiBotScraper(config)
    await scraper.initialize()
    
    try:
        # Scrape single page
        result = await scraper.scrape_page("https://www.booking.com")
        
        if result:
            print(f"✅ Successfully scraped: {result['title']}")
            print(f"   Status: {result['status']}")
            print(f"   Response time: {result['response_time']:.2f}s")
        
        # Scrape multiple pages
        urls = [
            "https://www.booking.com/hotel/gb/savoy.html",
            "https://www.booking.com/hotel/jp/park-hyatt-tokyo.html",
            "https://www.booking.com/hotel/us/the-plaza.html",
        ]
        
        results = await scraper.scrape_multiple(urls, max_concurrent=3)
        print(f"\n✅ Scraped {len(results)} pages successfully")
        
        # Get statistics
        stats = scraper.get_stats()
        print(f"\n📊 Stats: {stats}")
    
    finally:
        await scraper.shutdown()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())

