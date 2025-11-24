"""Configuration management for the authentication module."""

import os
from typing import Dict, List, Optional, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class AuthConfig(BaseSettings):
    """Authentication module configuration."""
    
    # Database
    database_url: str = Field(..., env="DATABASE_URL")
    database_pool_size: int = Field(10, env="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(20, env="DATABASE_MAX_OVERFLOW")
    
    # Redis/Cache
    redis_url: str = Field("redis://localhost:6379/0", env="REDIS_URL")
    cache_ttl: int = Field(3600, env="CACHE_TTL")
    
    # JWT Configuration
    jwt_secret_key: str = Field(..., env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field("HS256", env="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(60, env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    jwt_refresh_token_expire_days: int = Field(30, env="JWT_REFRESH_TOKEN_EXPIRE_DAYS")
    jwt_issuer: str = Field("luftway-auth", env="JWT_ISSUER")
    jwt_audience: str = Field("luftway-api", env="JWT_AUDIENCE")
    
    # Password Security (STRONG REQUIREMENTS)
    password_min_length: int = Field(10, env="PASSWORD_MIN_LENGTH")
    password_max_length: int = Field(128, env="PASSWORD_MAX_LENGTH")
    password_require_uppercase: bool = Field(True, env="PASSWORD_REQUIRE_UPPERCASE")
    password_require_lowercase: bool = Field(True, env="PASSWORD_REQUIRE_LOWERCASE")
    password_require_numbers: bool = Field(True, env="PASSWORD_REQUIRE_NUMBERS")
    password_require_special_chars: bool = Field(True, env="PASSWORD_REQUIRE_SPECIAL_CHARS")
    password_forbidden_patterns: List[str] = Field(
        ["password", "123456", "qwerty", "admin"], 
        env="PASSWORD_FORBIDDEN_PATTERNS"
    )
    password_history_count: int = Field(5, env="PASSWORD_HISTORY_COUNT")
    bcrypt_rounds: int = Field(12, env="BCRYPT_ROUNDS")
    
    # Rate Limiting
    rate_limit_login: str = Field("5/minute", env="RATE_LIMIT_LOGIN")
    rate_limit_register: str = Field("3/hour", env="RATE_LIMIT_REGISTER")
    rate_limit_forgot_password: str = Field("3/hour", env="RATE_LIMIT_FORGOT_PASSWORD")
    rate_limit_mfa_verify: str = Field("10/minute", env="RATE_LIMIT_MFA_VERIFY")
    rate_limit_refresh_token: str = Field("20/minute", env="RATE_LIMIT_REFRESH_TOKEN")
    rate_limit_tenant_creation: str = Field("5/hour", env="RATE_LIMIT_TENANT_CREATION")
    
    # Account Lockout
    max_failed_login_attempts: int = Field(5, env="MAX_FAILED_LOGIN_ATTEMPTS")
    lockout_duration_minutes: int = Field(30, env="LOCKOUT_DURATION_MINUTES")
    progressive_delay_enabled: bool = Field(True, env="PROGRESSIVE_DELAY_ENABLED")
    
    # Email Configuration
    smtp_host: Optional[str] = Field(None, env="SMTP_HOST")
    smtp_port: int = Field(587, env="SMTP_PORT")
    smtp_username: Optional[str] = Field(None, env="SMTP_USERNAME")
    smtp_password: Optional[str] = Field(None, env="SMTP_PASSWORD")
    smtp_use_tls: bool = Field(True, env="SMTP_USE_TLS")
    email_from: str = Field("noreply@luftway.com", env="EMAIL_FROM")
    email_from_name: str = Field("Luftway", env="EMAIL_FROM_NAME")
    
    # SMS Configuration (optional)
    sms_provider: Optional[str] = Field(None, env="SMS_PROVIDER")
    sms_api_key: Optional[str] = Field(None, env="SMS_API_KEY")
    sms_api_secret: Optional[str] = Field(None, env="SMS_API_SECRET")
    
    # OAuth Configuration
    google_client_id: Optional[str] = Field(None, env="GOOGLE_CLIENT_ID")
    google_client_secret: Optional[str] = Field(None, env="GOOGLE_CLIENT_SECRET")
    facebook_client_id: Optional[str] = Field(None, env="FACEBOOK_CLIENT_ID")
    facebook_client_secret: Optional[str] = Field(None, env="FACEBOOK_CLIENT_SECRET")
    apple_client_id: Optional[str] = Field(None, env="APPLE_CLIENT_ID")
    apple_team_id: Optional[str] = Field(None, env="APPLE_TEAM_ID")
    apple_key_id: Optional[str] = Field(None, env="APPLE_KEY_ID")
    apple_private_key: Optional[str] = Field(None, env="APPLE_PRIVATE_KEY")
    
    # Tenant Configuration
    tenant_resolution_strategy: str = Field("subdomain", env="TENANT_RESOLUTION_STRATEGY")
    default_tenant_slug: str = Field("luftway", env="DEFAULT_TENANT_SLUG")
    tenant_slug_pattern: str = Field(r"^[a-z0-9-]+$", env="TENANT_SLUG_PATTERN")
    
    # CORS Configuration
    cors_origins: Union[str, List[str]] = Field(
        default="http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173",
        env="CORS_ORIGINS"
    )
    
    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """Parse CORS origins from environment variable (comma-separated string or list)."""
        default_origins = [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173"
        ]
        
        if isinstance(v, list):
            return v if v else default_origins
        elif isinstance(v, str):
            # Parse comma-separated string
            origins = [origin.strip() for origin in v.split(",") if origin.strip()]
            return origins if origins else default_origins
        return default_origins
    
    cors_allow_credentials: bool = Field(True, env="CORS_ALLOW_CREDENTIALS")
    cors_allow_methods: List[str] = Field(
        default_factory=lambda: ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        env="CORS_ALLOW_METHODS"
    )
    cors_allow_headers: List[str] = Field(
        default_factory=lambda: ["*"],
        env="CORS_ALLOW_HEADERS"
    )
    
    # Security Headers
    enable_csrf_protection: bool = Field(False, env="ENABLE_CSRF_PROTECTION")
    enable_hsts: bool = Field(True, env="ENABLE_HSTS")
    enable_csp: bool = Field(True, env="ENABLE_CSP")
    
    # Monitoring & Logging
    log_level: str = Field("INFO", env="LOG_LEVEL")
    enable_audit_logging: bool = Field(True, env="ENABLE_AUDIT_LOGGING")
    enable_metrics: bool = Field(True, env="ENABLE_METRICS")
    
    # Sentry Error Tracking
    sentry_dsn: Optional[str] = Field(None, env="SENTRY_DSN")
    sentry_environment: str = Field("development", env="SENTRY_ENVIRONMENT")
    sentry_traces_sample_rate: float = Field(1.0, env="SENTRY_TRACES_SAMPLE_RATE")
    sentry_profiles_sample_rate: float = Field(1.0, env="SENTRY_PROFILES_SAMPLE_RATE")
    enable_sentry: bool = Field(False, env="ENABLE_SENTRY")
    
    # Feature Flags
    enable_mfa: bool = Field(True, env="ENABLE_MFA")
    enable_social_login: bool = Field(True, env="ENABLE_SOCIAL_LOGIN")
    enable_password_reset: bool = Field(True, env="ENABLE_PASSWORD_RESET")
    enable_user_registration: bool = Field(True, env="ENABLE_USER_REGISTRATION")
    enable_tenant_creation: bool = Field(True, env="ENABLE_TENANT_CREATION")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra environment variables (used by other modules)


# Global config instance
config = AuthConfig()
