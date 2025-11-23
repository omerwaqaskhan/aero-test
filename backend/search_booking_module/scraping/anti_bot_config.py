"""
Anti-Bot Configuration
Centralized configuration for proxy rotation, CAPTCHA solving, and anti-detection.
"""
import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class AntiBotConfig:
    """Configuration for anti-bot protection systems."""
    
    # Proxy Configuration
    enable_proxies: bool = True
    proxy_service: Optional[str] = None  # "brightdata", "oxylabs", "smartproxy", etc.
    proxy_username: Optional[str] = None
    proxy_password: Optional[str] = None
    proxy_host: Optional[str] = None
    proxy_port: Optional[int] = None
    proxy_type: str = "http"  # http, https, socks5
    proxy_rotation_enabled: bool = True
    proxy_health_checks: bool = True
    
    # CAPTCHA Solving Configuration
    enable_captcha_solving: bool = False
    captcha_service: str = "2captcha"  # 2captcha, anticaptcha, capmonster
    captcha_api_key: Optional[str] = None
    captcha_timeout: int = 120
    
    # Anti-Detection Configuration
    enable_stealth_mode: bool = True
    rotate_user_agents: bool = True
    randomize_browser_fingerprint: bool = True
    random_delays: bool = True
    min_delay: float = 1.0
    max_delay: float = 3.0
    
    # Rate Limiting
    max_concurrent_requests: int = 5
    requests_per_minute: int = 30
    max_requests_per_session: int = 50
    
    # Retry Configuration
    max_retries: int = 3
    retry_delay: float = 5.0
    exponential_backoff: bool = True
    
    @classmethod
    def from_env(cls) -> "AntiBotConfig":
        """Load configuration from environment variables."""
        return cls(
            # Proxies
            enable_proxies=os.getenv("ENABLE_PROXIES", "false").lower() == "true",
            proxy_service=os.getenv("PROXY_SERVICE"),
            proxy_username=os.getenv("PROXY_USERNAME"),
            proxy_password=os.getenv("PROXY_PASSWORD"),
            proxy_host=os.getenv("PROXY_HOST"),
            proxy_port=int(os.getenv("PROXY_PORT", "0")) or None,
            
            # CAPTCHA
            enable_captcha_solving=os.getenv("ENABLE_CAPTCHA", "false").lower() == "true",
            captcha_service=os.getenv("CAPTCHA_SERVICE", "2captcha"),
            captcha_api_key=os.getenv("CAPTCHA_API_KEY"),
            
            # Anti-Detection
            enable_stealth_mode=os.getenv("ENABLE_STEALTH", "true").lower() == "true",
            rotate_user_agents=os.getenv("ROTATE_USER_AGENTS", "true").lower() == "true",
            
            # Rate Limiting
            max_concurrent_requests=int(os.getenv("MAX_CONCURRENT_REQUESTS", "5")),
            requests_per_minute=int(os.getenv("REQUESTS_PER_MINUTE", "30")),
        )
    
    def get_proxy_url(self) -> Optional[str]:
        """Construct proxy URL from configuration."""
        if not self.enable_proxies or not self.proxy_host:
            return None
        
        auth = f"{self.proxy_username}:{self.proxy_password}@" if self.proxy_username else ""
        port = f":{self.proxy_port}" if self.proxy_port else ""
        
        return f"{self.proxy_type}://{auth}{self.proxy_host}{port}"


# Example configurations for different use cases
EXAMPLE_CONFIGS = {
    "development": AntiBotConfig(
        enable_proxies=False,
        enable_captcha_solving=False,
        enable_stealth_mode=True,
        max_concurrent_requests=2,
        requests_per_minute=10
    ),
    
    "production_light": AntiBotConfig(
        enable_proxies=True,
        proxy_service="geonode",
        enable_captcha_solving=False,
        enable_stealth_mode=True,
        max_concurrent_requests=5,
        requests_per_minute=30
    ),
    
    "production_full": AntiBotConfig(
        enable_proxies=True,
        proxy_service="brightdata",
        proxy_rotation_enabled=True,
        enable_captcha_solving=True,
        captcha_service="2captcha",
        enable_stealth_mode=True,
        randomize_browser_fingerprint=True,
        max_concurrent_requests=10,
        requests_per_minute=60,
        max_requests_per_session=100
    ),
    
    "aggressive": AntiBotConfig(
        enable_proxies=True,
        proxy_service="smartproxy",
        proxy_rotation_enabled=True,
        enable_captcha_solving=True,
        captcha_service="anticaptcha",
        enable_stealth_mode=True,
        randomize_browser_fingerprint=True,
        random_delays=True,
        max_concurrent_requests=20,
        requests_per_minute=120,
        max_requests_per_session=200
    )
}


def get_config(profile: str = "development") -> AntiBotConfig:
    """
    Get configuration by profile name.
    
    Args:
        profile: Configuration profile name
        
    Returns:
        AntiBotConfig instance
    """
    if profile in EXAMPLE_CONFIGS:
        return EXAMPLE_CONFIGS[profile]
    
    # Default to environment-based configuration
    return AntiBotConfig.from_env()


# Pre-configured profiles for popular proxy services
PROXY_SERVICE_CONFIGS = {
    "brightdata": {
        "host": "brd.superproxy.io",
        "port": 22225,
        "type": "http",
        "features": ["residential", "rotating", "geo-targeting"],
        "pricing": "$15/GB residential, $500/month unlimited datacenter"
    },
    "oxylabs": {
        "host": "pr.oxylabs.io",
        "port": 7777,
        "type": "http",
        "features": ["residential", "datacenter", "rotating"],
        "pricing": "$8/GB residential, $300/month datacenter"
    },
    "smartproxy": {
        "host": "gate.smartproxy.com",
        "port": 7000,
        "type": "http",
        "features": ["residential", "rotating", "40M+ IPs"],
        "pricing": "$12.50/GB, volume discounts available"
    },
    "geonode": {
        "host": "premium-residential.geonode.com",
        "port": 9000,
        "type": "http",
        "features": ["residential", "rotating", "geo-targeting"],
        "pricing": "$3/GB residential"
    },
    "proxyrack": {
        "host": "residential.proxyrack.net",
        "port": 10000,
        "type": "http",
        "features": ["residential", "rotating", "unmetered"],
        "pricing": "$65/month unlimited residential"
    }
}

