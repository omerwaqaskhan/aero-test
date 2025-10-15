"""Security utilities for password hashing, JWT tokens, MFA, and rate limiting."""

import hashlib
import hmac
import secrets
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import bcrypt
import pyotp
import qrcode
from io import BytesIO
import base64
import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError
import redis
from .config import config


class PasswordManager:
    """Password hashing and validation utilities."""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt."""
        salt = bcrypt.gensalt(rounds=config.bcrypt_rounds)
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify a password against its hash."""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    @staticmethod
    def validate_password_strength(password: str) -> Dict[str, Any]:
        """Validate password against strength requirements."""
        errors = []
        requirements = {
            "min_length": config.password_min_length,
            "max_length": config.password_max_length,
            "require_uppercase": config.password_require_uppercase,
            "require_lowercase": config.password_require_lowercase,
            "require_numbers": config.password_require_numbers,
            "require_special_chars": config.password_require_special_chars,
        }
        
        if len(password) < requirements["min_length"]:
            errors.append(f"Password must be at least {requirements['min_length']} characters long")
        
        if len(password) > requirements["max_length"]:
            errors.append(f"Password must be no more than {requirements['max_length']} characters long")
        
        if requirements["require_uppercase"] and not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")
        
        if requirements["require_lowercase"] and not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")
        
        if requirements["require_numbers"] and not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one number")
        
        if requirements["require_special_chars"] and not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            errors.append("Password must contain at least one special character")
        
        # Check forbidden patterns
        password_lower = password.lower()
        for pattern in config.password_forbidden_patterns:
            if pattern.lower() in password_lower:
                errors.append(f"Password cannot contain '{pattern}'")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "requirements": requirements
        }


class JWTManager:
    """JWT token generation and validation."""
    
    @staticmethod
    def generate_access_token(
        user_id: str,
        tenant_id: str,
        email: str,
        role: str,
        permissions: List[str],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Generate an access token."""
        if expires_delta is None:
            expires_delta = timedelta(minutes=config.jwt_access_token_expire_minutes)
        
        expire = datetime.utcnow() + expires_delta
        
        payload = {
            "sub": user_id,
            "tenant_id": tenant_id,
            "email": email,
            "role": role,
            "permissions": permissions,
            "iat": datetime.utcnow(),
            "exp": expire,
            "iss": config.jwt_issuer,
            "aud": config.jwt_audience,
            "type": "access"
        }
        
        return jwt.encode(payload, config.jwt_secret_key, algorithm=config.jwt_algorithm)
    
    @staticmethod
    def generate_refresh_token(
        user_id: str,
        tenant_id: str,
        device_info: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate a refresh token."""
        expires_delta = timedelta(days=config.jwt_refresh_token_expire_days)
        expire = datetime.utcnow() + expires_delta
        
        payload = {
            "sub": user_id,
            "tenant_id": tenant_id,
            "iat": datetime.utcnow(),
            "exp": expire,
            "iss": config.jwt_issuer,
            "aud": config.jwt_audience,
            "type": "refresh",
            "device_info": device_info or {}
        }
        
        return jwt.encode(payload, config.jwt_secret_key, algorithm=config.jwt_algorithm)
    
    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> Dict[str, Any]:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(
                token,
                config.jwt_secret_key,
                algorithms=[config.jwt_algorithm],
                issuer=config.jwt_issuer,
                audience=config.jwt_audience,
                options={"verify_exp": True}
            )
            
            if payload.get("type") != token_type:
                raise InvalidTokenError("Invalid token type")
            
            return payload
            
        except ExpiredSignatureError:
            raise InvalidTokenError("Token has expired")
        except InvalidTokenError:
            raise InvalidTokenError("Invalid token")
    
    @staticmethod
    def get_token_expiry(token: str) -> Optional[datetime]:
        """Get token expiry without verification (for logging)."""
        try:
            payload = jwt.decode(
                token,
                config.jwt_secret_key,
                algorithms=[config.jwt_algorithm],
                options={"verify_exp": False}
            )
            return datetime.fromtimestamp(payload.get("exp", 0))
        except:
            return None


class MFAManager:
    """Multi-factor authentication utilities."""
    
    @staticmethod
    def generate_totp_secret() -> str:
        """Generate a TOTP secret."""
        return pyotp.random_base32()
    
    @staticmethod
    def generate_totp_qr_code(secret: str, email: str, issuer: str = "Trivago Plus") -> str:
        """Generate QR code for TOTP setup."""
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=email,
            issuer_name=issuer
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        return base64.b64encode(buffer.getvalue()).decode()
    
    @staticmethod
    def verify_totp_code(secret: str, code: str, window: int = 1) -> bool:
        """Verify a TOTP code."""
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=window)
    
    @staticmethod
    def generate_backup_codes(count: int = 10) -> List[str]:
        """Generate backup codes for MFA."""
        return [secrets.token_hex(4).upper() for _ in range(count)]
    
    @staticmethod
    def generate_sms_code() -> str:
        """Generate a 6-digit SMS code."""
        return f"{secrets.randbelow(1000000):06d}"
    
    @staticmethod
    def generate_email_code() -> str:
        """Generate a 6-digit email code."""
        return f"{secrets.randbelow(1000000):06d}"


class RateLimiter:
    """Rate limiting using Redis."""
    
    def __init__(self):
        self.redis_client = redis.from_url(config.redis_url, decode_responses=True)
    
    def is_rate_limited(
        self, 
        key: str, 
        limit: str, 
        window_seconds: int = 60
    ) -> tuple[bool, int, int]:
        """
        Check if a key is rate limited.
        
        Args:
            key: Rate limit key (e.g., "login:user@example.com")
            limit: Rate limit (e.g., "5/minute")
            window_seconds: Time window in seconds
            
        Returns:
            (is_limited, current_count, reset_time)
        """
        try:
            # Parse limit (e.g., "5/minute" -> 5)
            limit_count = int(limit.split('/')[0])
            
            # Use sliding window counter
            now = int(time.time())
            window_start = now - window_seconds
            
            # Remove old entries
            self.redis_client.zremrangebyscore(key, 0, window_start)
            
            # Count current entries
            current_count = self.redis_client.zcard(key)
            
            if current_count >= limit_count:
                # Get oldest entry to calculate reset time
                oldest_entry = self.redis_client.zrange(key, 0, 0, withscores=True)
                if oldest_entry:
                    reset_time = int(oldest_entry[0][1]) + window_seconds
                else:
                    reset_time = now + window_seconds
                
                return True, current_count, reset_time
            
            # Add current request
            self.redis_client.zadd(key, {str(now): now})
            self.redis_client.expire(key, window_seconds)
            
            return False, current_count + 1, now + window_seconds
            
        except Exception:
            # If Redis is down, allow the request (fail open)
            return False, 0, 0
    
    def get_rate_limit_info(self, key: str) -> Dict[str, Any]:
        """Get current rate limit information."""
        try:
            current_count = self.redis_client.zcard(key)
            oldest_entry = self.redis_client.zrange(key, 0, 0, withscores=True)
            
            if oldest_entry:
                oldest_time = int(oldest_entry[0][1])
                ttl = self.redis_client.ttl(key)
                return {
                    "current_count": current_count,
                    "oldest_request": oldest_time,
                    "ttl": ttl
                }
            else:
                return {
                    "current_count": 0,
                    "oldest_request": None,
                    "ttl": -1
                }
        except Exception:
            return {
                "current_count": 0,
                "oldest_request": None,
                "ttl": -1
            }
    
    def clear_rate_limit(self, key: str) -> bool:
        """Clear rate limit for a key."""
        try:
            return bool(self.redis_client.delete(key))
        except Exception:
            return False


class SecurityHeaders:
    """Security headers for HTTP responses."""
    
    @staticmethod
    def get_security_headers() -> Dict[str, str]:
        """Get standard security headers."""
        headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
        }
        
        if config.enable_hsts:
            headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        if config.enable_csp:
            headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self'; "
                "connect-src 'self'; "
                "frame-ancestors 'none';"
            )
        
        return headers


class AuditLogger:
    """Audit logging for security events."""
    
    @staticmethod
    def log_security_event(
        event_type: str,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log a security event."""
        if not config.enable_audit_logging:
            return
        
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "tenant_id": tenant_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "details": details or {}
        }
        
        # In a real implementation, this would write to a secure audit log
        # For now, we'll just print it (replace with proper logging)
        print(f"AUDIT: {event}")
