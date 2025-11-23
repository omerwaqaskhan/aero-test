"""
CAPTCHA Solving Service Integration
Supports multiple providers: 2Captcha, Anti-Captcha, CapMonster, and more.
"""
import asyncio
import aiohttp
import time
from typing import Optional, Dict, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class CaptchaType(Enum):
    """Supported CAPTCHA types."""
    RECAPTCHA_V2 = "recaptcha_v2"
    RECAPTCHA_V3 = "recaptcha_v3"
    HCAPTCHA = "hcaptcha"
    FUNCAPTCHA = "funcaptcha"
    IMAGE_CAPTCHA = "image"
    TEXT_CAPTCHA = "text"


class CaptchaSolver:
    """
    Universal CAPTCHA solver supporting multiple services.
    """
    
    def __init__(
        self,
        service: str = "2captcha",  # 2captcha, anticaptcha, capmonster
        api_key: Optional[str] = None,
        default_timeout: int = 120
    ):
        self.service = service.lower()
        self.api_key = api_key
        self.default_timeout = default_timeout
        
        # Service-specific endpoints
        self.endpoints = {
            "2captcha": {
                "submit": "https://2captcha.com/in.php",
                "result": "https://2captcha.com/res.php"
            },
            "anticaptcha": {
                "create": "https://api.anti-captcha.com/createTask",
                "result": "https://api.anti-captcha.com/getTaskResult"
            },
            "capmonster": {
                "create": "https://api.capmonster.cloud/createTask",
                "result": "https://api.capmonster.cloud/getTaskResult"
            }
        }
        
        if self.api_key:
            logger.info(f"CaptchaSolver initialized with {self.service}")
        else:
            logger.warning("CaptchaSolver initialized without API key - will not solve CAPTCHAs")
    
    async def solve_recaptcha_v2(
        self,
        site_key: str,
        page_url: str,
        timeout: Optional[int] = None
    ) -> Optional[str]:
        """
        Solve reCAPTCHA v2.
        
        Args:
            site_key: Site key from the webpage
            page_url: Full URL of the page with CAPTCHA
            timeout: Max time to wait for solution (seconds)
            
        Returns:
            CAPTCHA solution token or None if failed
        """
        if not self.api_key:
            logger.warning("No API key configured, skipping CAPTCHA solve")
            return None
        
        timeout = timeout or self.default_timeout
        
        try:
            if self.service == "2captcha":
                return await self._solve_2captcha_recaptcha_v2(site_key, page_url, timeout)
            elif self.service in ["anticaptcha", "capmonster"]:
                return await self._solve_anticaptcha_recaptcha_v2(site_key, page_url, timeout)
            else:
                logger.error(f"Unsupported service: {self.service}")
                return None
        except Exception as e:
            logger.error(f"Error solving reCAPTCHA v2: {e}")
            return None
    
    async def solve_recaptcha_v3(
        self,
        site_key: str,
        page_url: str,
        action: str = "submit",
        min_score: float = 0.3,
        timeout: Optional[int] = None
    ) -> Optional[str]:
        """Solve reCAPTCHA v3."""
        if not self.api_key:
            return None
        
        timeout = timeout or self.default_timeout
        
        try:
            if self.service == "2captcha":
                return await self._solve_2captcha_recaptcha_v3(
                    site_key, page_url, action, min_score, timeout
                )
            elif self.service in ["anticaptcha", "capmonster"]:
                return await self._solve_anticaptcha_recaptcha_v3(
                    site_key, page_url, action, min_score, timeout
                )
            else:
                logger.error(f"Unsupported service: {self.service}")
                return None
        except Exception as e:
            logger.error(f"Error solving reCAPTCHA v3: {e}")
            return None
    
    async def _solve_2captcha_recaptcha_v2(
        self,
        site_key: str,
        page_url: str,
        timeout: int
    ) -> Optional[str]:
        """Solve using 2Captcha service."""
        async with aiohttp.ClientSession() as session:
            # Step 1: Submit CAPTCHA
            submit_url = self.endpoints["2captcha"]["submit"]
            submit_params = {
                "key": self.api_key,
                "method": "userrecaptcha",
                "googlekey": site_key,
                "pageurl": page_url,
                "json": 1
            }
            
            async with session.get(submit_url, params=submit_params) as response:
                result = await response.json()
                
                if result.get("status") != 1:
                    logger.error(f"2Captcha submit failed: {result}")
                    return None
                
                captcha_id = result.get("request")
                logger.info(f"2Captcha task submitted: {captcha_id}")
            
            # Step 2: Poll for result
            result_url = self.endpoints["2captcha"]["result"]
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                await asyncio.sleep(5)  # Check every 5 seconds
                
                result_params = {
                    "key": self.api_key,
                    "action": "get",
                    "id": captcha_id,
                    "json": 1
                }
                
                async with session.get(result_url, params=result_params) as response:
                    result = await response.json()
                    
                    if result.get("status") == 1:
                        solution = result.get("request")
                        logger.info("2Captcha solved successfully")
                        return solution
                    elif result.get("request") != "CAPCHA_NOT_READY":
                        logger.error(f"2Captcha error: {result}")
                        return None
            
            logger.error("2Captcha timeout")
            return None
    
    async def _solve_2captcha_recaptcha_v3(
        self,
        site_key: str,
        page_url: str,
        action: str,
        min_score: float,
        timeout: int
    ) -> Optional[str]:
        """Solve reCAPTCHA v3 using 2Captcha."""
        async with aiohttp.ClientSession() as session:
            submit_url = self.endpoints["2captcha"]["submit"]
            submit_params = {
                "key": self.api_key,
                "method": "userrecaptcha",
                "version": "v3",
                "googlekey": site_key,
                "pageurl": page_url,
                "action": action,
                "min_score": min_score,
                "json": 1
            }
            
            async with session.get(submit_url, params=submit_params) as response:
                result = await response.json()
                
                if result.get("status") != 1:
                    logger.error(f"2Captcha v3 submit failed: {result}")
                    return None
                
                captcha_id = result.get("request")
            
            # Poll for result
            result_url = self.endpoints["2captcha"]["result"]
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                await asyncio.sleep(5)
                
                result_params = {
                    "key": self.api_key,
                    "action": "get",
                    "id": captcha_id,
                    "json": 1
                }
                
                async with session.get(result_url, params=result_params) as response:
                    result = await response.json()
                    
                    if result.get("status") == 1:
                        return result.get("request")
                    elif result.get("request") != "CAPCHA_NOT_READY":
                        logger.error(f"2Captcha v3 error: {result}")
                        return None
            
            return None
    
    async def _solve_anticaptcha_recaptcha_v2(
        self,
        site_key: str,
        page_url: str,
        timeout: int
    ) -> Optional[str]:
        """Solve using Anti-Captcha or CapMonster service."""
        async with aiohttp.ClientSession() as session:
            # Step 1: Create task
            create_url = self.endpoints[self.service]["create"]
            create_payload = {
                "clientKey": self.api_key,
                "task": {
                    "type": "NoCaptchaTaskProxyless",
                    "websiteURL": page_url,
                    "websiteKey": site_key
                }
            }
            
            async with session.post(create_url, json=create_payload) as response:
                result = await response.json()
                
                if result.get("errorId") != 0:
                    logger.error(f"{self.service} create task failed: {result}")
                    return None
                
                task_id = result.get("taskId")
                logger.info(f"{self.service} task created: {task_id}")
            
            # Step 2: Poll for result
            result_url = self.endpoints[self.service]["result"]
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                await asyncio.sleep(3)
                
                result_payload = {
                    "clientKey": self.api_key,
                    "taskId": task_id
                }
                
                async with session.post(result_url, json=result_payload) as response:
                    result = await response.json()
                    
                    if result.get("status") == "ready":
                        solution = result.get("solution", {}).get("gRecaptchaResponse")
                        logger.info(f"{self.service} solved successfully")
                        return solution
                    elif result.get("status") != "processing":
                        logger.error(f"{self.service} error: {result}")
                        return None
            
            logger.error(f"{self.service} timeout")
            return None
    
    async def _solve_anticaptcha_recaptcha_v3(
        self,
        site_key: str,
        page_url: str,
        action: str,
        min_score: float,
        timeout: int
    ) -> Optional[str]:
        """Solve reCAPTCHA v3 using Anti-Captcha or CapMonster."""
        async with aiohttp.ClientSession() as session:
            create_url = self.endpoints[self.service]["create"]
            create_payload = {
                "clientKey": self.api_key,
                "task": {
                    "type": "RecaptchaV3TaskProxyless",
                    "websiteURL": page_url,
                    "websiteKey": site_key,
                    "minScore": min_score,
                    "pageAction": action
                }
            }
            
            async with session.post(create_url, json=create_payload) as response:
                result = await response.json()
                
                if result.get("errorId") != 0:
                    logger.error(f"{self.service} v3 create failed: {result}")
                    return None
                
                task_id = result.get("taskId")
            
            # Poll for result
            result_url = self.endpoints[self.service]["result"]
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                await asyncio.sleep(3)
                
                result_payload = {
                    "clientKey": self.api_key,
                    "taskId": task_id
                }
                
                async with session.post(result_url, json=result_payload) as response:
                    result = await response.json()
                    
                    if result.get("status") == "ready":
                        solution = result.get("solution", {}).get("gRecaptchaResponse")
                        logger.info(f"{self.service} v3 solved successfully")
                        return solution
                    elif result.get("status") != "processing":
                        logger.error(f"{self.service} v3 error: {result}")
                        return None
            
            return None
    
    def get_balance(self) -> Optional[float]:
        """Get account balance (synchronous)."""
        # This would need to be implemented per service
        # For now, return None
        return None


# Configuration examples
CAPTCHA_SERVICES = {
    "2captcha": {
        "website": "https://2captcha.com",
        "pricing": "$2.99/1000 reCAPTCHA v2, $3.00/1000 reCAPTCHA v3",
        "features": ["reCAPTCHA v2/v3", "hCaptcha", "FunCaptcha", "Image CAPTCHA"],
        "pros": ["Most popular", "Good documentation", "Reasonable prices"],
        "cons": ["Can be slow during peak times"]
    },
    "anti-captcha": {
        "website": "https://anti-captcha.com",
        "pricing": "$1.80-$2.00/1000 reCAPTCHA",
        "features": ["reCAPTCHA v2/v3", "hCaptcha", "FunCaptcha", "GeeTest"],
        "pros": ["Fast solving", "Good API", "Chrome extension"],
        "cons": ["Slightly more expensive"]
    },
    "capmonster": {
        "website": "https://capmonster.cloud",
        "pricing": "$0.60-$2.40/1000 depending on type",
        "features": ["reCAPTCHA v2/v3", "hCaptcha", "FunCaptcha"],
        "pros": ["Cheapest option", "Good speed"],
        "cons": ["Less established"]
    }
}

