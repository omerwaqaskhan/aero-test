"""
Advanced Anti-Detection Techniques for Web Scraping
Includes user-agent rotation, browser fingerprinting, and stealth mode.
"""
import random
from typing import Dict, List, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


# Realistic user agents from real browsers
USER_AGENTS = [
    # Chrome on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    
    # Chrome on Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    
    # Firefox on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    
    # Firefox on Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
    
    # Safari on Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    
    # Edge on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    
    # Chrome on Linux
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]


# Browser fingerprint configurations
BROWSER_PROFILES = {
    "chrome_windows": {
        "platform": "Win32",
        "vendor": "Google Inc.",
        "webgl_vendor": "Intel Inc.",
        "webgl_renderer": "Intel Iris OpenGL Engine",
        "languages": ["en-US", "en"],
        "plugins": ["Chrome PDF Plugin", "Chrome PDF Viewer", "Native Client"],
        "hardware_concurrency": random.choice([4, 8, 16]),
        "device_memory": random.choice([4, 8, 16]),
        "color_depth": 24,
        "pixel_ratio": random.choice([1, 1.25, 1.5, 2])
    },
    "chrome_mac": {
        "platform": "MacIntel",
        "vendor": "Google Inc.",
        "webgl_vendor": "Apple Inc.",
        "webgl_renderer": "Apple M1",
        "languages": ["en-US", "en"],
        "plugins": ["Chrome PDF Plugin", "Chrome PDF Viewer"],
        "hardware_concurrency": random.choice([8, 10]),
        "device_memory": random.choice([8, 16, 32]),
        "color_depth": 24,
        "pixel_ratio": 2
    },
    "firefox_windows": {
        "platform": "Win32",
        "vendor": "",
        "webgl_vendor": "Google Inc. (Intel)",
        "webgl_renderer": "ANGLE (Intel, Intel(R) UHD Graphics Direct3D11 vs_5_0 ps_5_0)",
        "languages": ["en-US", "en"],
        "plugins": [],
        "hardware_concurrency": random.choice([4, 8, 16]),
        "device_memory": random.choice([4, 8, 16]),
        "color_depth": 24,
        "pixel_ratio": 1
    }
}


@dataclass
class BrowserFingerprint:
    """Browser fingerprint configuration."""
    user_agent: str
    platform: str
    vendor: str
    webgl_vendor: str
    webgl_renderer: str
    languages: List[str]
    plugins: List[str]
    hardware_concurrency: int
    device_memory: int
    color_depth: int
    pixel_ratio: float
    
    @property
    def playwright_context_options(self) -> Dict:
        """Get Playwright browser context options."""
        return {
            "user_agent": self.user_agent,
            "viewport": {
                "width": random.choice([1366, 1920, 2560]),
                "height": random.choice([768, 1080, 1440])
            },
            "device_scale_factor": self.pixel_ratio,
            "locale": "en-US",
            "timezone_id": "America/New_York",
            "geolocation": {
                "latitude": 40.7128,
                "longitude": -74.0060
            },
            "permissions": ["geolocation"]
        }


class AntiDetectionManager:
    """
    Manages anti-detection techniques for web scraping.
    """
    
    def __init__(self):
        self.user_agents = USER_AGENTS.copy()
        self.browser_profiles = BROWSER_PROFILES.copy()
        logger.info("AntiDetectionManager initialized")
    
    def get_random_user_agent(self) -> str:
        """Get a random user agent string."""
        return random.choice(self.user_agents)
    
    def get_browser_fingerprint(self, browser_type: Optional[str] = None) -> BrowserFingerprint:
        """
        Generate a realistic browser fingerprint.
        
        Args:
            browser_type: Specific browser type or None for random
            
        Returns:
            BrowserFingerprint object
        """
        if browser_type and browser_type in self.browser_profiles:
            profile = self.browser_profiles[browser_type]
            user_agent = self._get_matching_user_agent(browser_type)
        else:
            # Random selection
            profile_name = random.choice(list(self.browser_profiles.keys()))
            profile = self.browser_profiles[profile_name]
            user_agent = self._get_matching_user_agent(profile_name)
        
        return BrowserFingerprint(
            user_agent=user_agent,
            platform=profile["platform"],
            vendor=profile["vendor"],
            webgl_vendor=profile["webgl_vendor"],
            webgl_renderer=profile["webgl_renderer"],
            languages=profile["languages"],
            plugins=profile["plugins"],
            hardware_concurrency=profile["hardware_concurrency"],
            device_memory=profile["device_memory"],
            color_depth=profile["color_depth"],
            pixel_ratio=profile["pixel_ratio"]
        )
    
    def _get_matching_user_agent(self, browser_type: str) -> str:
        """Get a user agent matching the browser type."""
        if "chrome_windows" in browser_type:
            matching = [ua for ua in self.user_agents if "Windows" in ua and "Chrome" in ua and "Edg" not in ua]
        elif "chrome_mac" in browser_type:
            matching = [ua for ua in self.user_agents if "Macintosh" in ua and "Chrome" in ua]
        elif "firefox" in browser_type:
            matching = [ua for ua in self.user_agents if "Firefox" in ua]
        elif "safari" in browser_type:
            matching = [ua for ua in self.user_agents if "Safari" in ua and "Chrome" not in ua]
        else:
            matching = self.user_agents
        
        return random.choice(matching) if matching else self.get_random_user_agent()
    
    def get_request_headers(self, referer: Optional[str] = None) -> Dict[str, str]:
        """
        Get realistic HTTP headers for requests.
        
        Args:
            referer: Optional referer URL
            
        Returns:
            Dictionary of headers
        """
        headers = {
            "User-Agent": self.get_random_user_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
        }
        
        if referer:
            headers["Referer"] = referer
        
        return headers
    
    async def apply_stealth_mode(self, page) -> None:
        """
        Apply stealth techniques to Playwright page.
        Makes the browser harder to detect as automated.
        """
        # Override navigator properties
        await page.add_init_script("""
            // Overwrite the `navigator.webdriver` property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            // Overwrite the `plugins` property
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            
            // Overwrite the `languages` property
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
            
            // Pass the Chrome Test
            window.chrome = {
                runtime: {},
            };
            
            // Pass the Permissions Test
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)
    
    def get_random_delay(self, min_seconds: float = 1.0, max_seconds: float = 3.0) -> float:
        """Get a random delay to simulate human behavior."""
        return random.uniform(min_seconds, max_seconds)
    
    def should_rotate_session(self, requests_count: int, max_requests: int = 50) -> bool:
        """
        Determine if session should be rotated based on request count.
        
        Args:
            requests_count: Number of requests made in current session
            max_requests: Maximum requests before rotation
            
        Returns:
            True if session should be rotated
        """
        # Add randomness to avoid predictable patterns
        threshold = max_requests + random.randint(-10, 10)
        return requests_count >= threshold


# Stealth mode JavaScript injections
STEALTH_SCRIPTS = {
    "navigator_webdriver": """
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
    """,
    
    "chrome_runtime": """
        window.chrome = {
            runtime: {},
            loadTimes: function() {},
            csi: function() {},
            app: {}
        };
    """,
    
    "permissions": """
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
    """,
    
    "plugins": """
        Object.defineProperty(navigator, 'plugins', {
            get: () => {
                return [
                    {
                        0: {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format"},
                        description: "Portable Document Format",
                        filename: "internal-pdf-viewer",
                        length: 1,
                        name: "Chrome PDF Plugin"
                    },
                    {
                        0: {type: "application/pdf", suffixes: "pdf", description: ""},
                        description: "",
                        filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai",
                        length: 1,
                        name: "Chrome PDF Viewer"
                    }
                ];
            }
        });
    """,
    
    "languages": """
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en']
        });
    """,
    
    "vendor": """
        Object.defineProperty(navigator, 'vendor', {
            get: () => 'Google Inc.'
        });
    """,
    
    "platform": """
        Object.defineProperty(navigator, 'platform', {
            get: () => 'Win32'
        });
    """,
    
    "hardware_concurrency": """
        Object.defineProperty(navigator, 'hardwareConcurrency', {
            get: () => 8
        });
    """,
    
    "device_memory": """
        Object.defineProperty(navigator, 'deviceMemory', {
            get: () => 8
        });
    """,
    
    "webgl": """
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {
            if (parameter === 37445) {
                return 'Intel Inc.';
            }
            if (parameter === 37446) {
                return 'Intel Iris OpenGL Engine';
            }
            return getParameter(parameter);
        };
    """,
    
    "canvas_fingerprint": """
        const toBlob = HTMLCanvasElement.prototype.toBlob;
        const toDataURL = HTMLCanvasElement.prototype.toDataURL;
        const getImageData = CanvasRenderingContext2D.prototype.getImageData;
        
        // Add slight noise to prevent exact fingerprinting
        const noisify = function(canvas, context) {
            const shift = {
                'r': Math.floor(Math.random() * 10) - 5,
                'g': Math.floor(Math.random() * 10) - 5,
                'b': Math.floor(Math.random() * 10) - 5,
                'a': Math.floor(Math.random() * 10) - 5
            };
            
            const width = canvas.width;
            const height = canvas.height;
            const imageData = getImageData.apply(context, [0, 0, width, height]);
            
            for (let i = 0; i < imageData.data.length; i += 4) {
                imageData.data[i + 0] = imageData.data[i + 0] + shift.r;
                imageData.data[i + 1] = imageData.data[i + 1] + shift.g;
                imageData.data[i + 2] = imageData.data[i + 2] + shift.b;
                imageData.data[i + 3] = imageData.data[i + 3] + shift.a;
            }
            
            context.putImageData(imageData, 0, 0);
        };
        
        Object.defineProperty(HTMLCanvasElement.prototype, 'toBlob', {
            value: function() {
                noisify(this, this.getContext('2d'));
                return toBlob.apply(this, arguments);
            }
        });
        
        Object.defineProperty(HTMLCanvasElement.prototype, 'toDataURL', {
            value: function() {
                noisify(this, this.getContext('2d'));
                return toDataURL.apply(this, arguments);
            }
        });
    """
}


def get_all_stealth_scripts() -> str:
    """Combine all stealth scripts into one."""
    return "\n".join(STEALTH_SCRIPTS.values())

