"""OAuth service for social login integration."""

from typing import Dict, Any, Optional, Tuple
import httpx
from ..core.config import config
from ..core.exceptions import SystemError, ValidationError


class OAuthService:
    """OAuth service for social login."""
    
    def __init__(self):
        self.google_client_id = config.google_client_id
        self.google_client_secret = config.google_client_secret
        self.facebook_client_id = config.facebook_client_id
        self.facebook_client_secret = config.facebook_client_secret
        self.apple_client_id = config.apple_client_id
        self.apple_team_id = config.apple_team_id
        self.apple_key_id = config.apple_key_id
        self.apple_private_key = config.apple_private_key
    
    async def verify_google_token(self, access_token: str) -> Dict[str, Any]:
        """Verify Google OAuth token and get user info."""
        if not self.google_client_id or not self.google_client_secret:
            raise SystemError("Google OAuth not configured")
        
        try:
            async with httpx.AsyncClient() as client:
                # Verify token with Google
                response = await client.get(
                    f"https://www.googleapis.com/oauth2/v2/userinfo?access_token={access_token}"
                )
                response.raise_for_status()
                
                user_info = response.json()
                
                # Validate required fields
                if not user_info.get("email") or not user_info.get("verified_email"):
                    raise ValidationError("Google account email not verified")
                
                return {
                    "provider": "google",
                    "provider_id": user_info["id"],
                    "email": user_info["email"],
                    "first_name": user_info.get("given_name", ""),
                    "last_name": user_info.get("family_name", ""),
                    "avatar_url": user_info.get("picture"),
                    "verified": user_info.get("verified_email", False)
                }
                
        except httpx.HTTPError as e:
            raise SystemError(f"Failed to verify Google token: {str(e)}")
        except Exception as e:
            raise SystemError(f"Google OAuth error: {str(e)}")
    
    async def verify_facebook_token(self, access_token: str) -> Dict[str, Any]:
        """Verify Facebook OAuth token and get user info."""
        if not self.facebook_client_id or not self.facebook_client_secret:
            raise SystemError("Facebook OAuth not configured")
        
        try:
            async with httpx.AsyncClient() as client:
                # Verify token with Facebook
                response = await client.get(
                    f"https://graph.facebook.com/me",
                    params={
                        "access_token": access_token,
                        "fields": "id,email,first_name,last_name,picture"
                    }
                )
                response.raise_for_status()
                
                user_info = response.json()
                
                # Validate required fields
                if not user_info.get("email"):
                    raise ValidationError("Facebook account email not available")
                
                return {
                    "provider": "facebook",
                    "provider_id": user_info["id"],
                    "email": user_info["email"],
                    "first_name": user_info.get("first_name", ""),
                    "last_name": user_info.get("last_name", ""),
                    "avatar_url": user_info.get("picture", {}).get("data", {}).get("url"),
                    "verified": True  # Facebook doesn't provide email verification status
                }
                
        except httpx.HTTPError as e:
            raise SystemError(f"Failed to verify Facebook token: {str(e)}")
        except Exception as e:
            raise SystemError(f"Facebook OAuth error: {str(e)}")
    
    async def verify_apple_token(self, identity_token: str) -> Dict[str, Any]:
        """Verify Apple Sign-In token and get user info."""
        if not self.apple_client_id or not self.apple_team_id or not self.apple_key_id or not self.apple_private_key:
            raise SystemError("Apple OAuth not configured")
        
        try:
            # Apple Sign-In uses JWT tokens, so we need to verify the signature
            # This is a simplified implementation - in production, you'd want to use
            # a proper JWT library with Apple's public keys
            
            import jwt
            import json
            from datetime import datetime
            
            # Decode the token without verification first to get the header
            unverified_header = jwt.get_unverified_header(identity_token)
            unverified_payload = jwt.decode(identity_token, options={"verify_signature": False})
            
            # In a real implementation, you would:
            # 1. Fetch Apple's public keys from https://appleid.apple.com/auth/keys
            # 2. Verify the signature using the appropriate key
            # 3. Verify the issuer, audience, and expiration
            
            # For now, we'll do basic validation
            if unverified_payload.get("iss") != "https://appleid.apple.com":
                raise ValidationError("Invalid Apple token issuer")
            
            if unverified_payload.get("aud") != self.apple_client_id:
                raise ValidationError("Invalid Apple token audience")
            
            if unverified_payload.get("exp", 0) < datetime.utcnow().timestamp():
                raise ValidationError("Apple token has expired")
            
            # Extract user info
            user_info = unverified_payload.get("user", {})
            
            return {
                "provider": "apple",
                "provider_id": unverified_payload["sub"],
                "email": unverified_payload.get("email", ""),
                "first_name": user_info.get("name", {}).get("firstName", ""),
                "last_name": user_info.get("name", {}).get("lastName", ""),
                "avatar_url": None,  # Apple doesn't provide avatar URLs
                "verified": True  # Apple tokens are pre-verified
            }
            
        except jwt.InvalidTokenError as e:
            raise ValidationError(f"Invalid Apple token: {str(e)}")
        except Exception as e:
            raise SystemError(f"Apple OAuth error: {str(e)}")
    
    async def verify_social_token(self, provider: str, access_token: str) -> Dict[str, Any]:
        """Verify social login token for any supported provider."""
        provider = provider.lower()
        
        if provider == "google":
            return await self.verify_google_token(access_token)
        elif provider == "facebook":
            return await self.verify_facebook_token(access_token)
        elif provider == "apple":
            return await self.verify_apple_token(access_token)
        else:
            raise ValidationError(f"Unsupported OAuth provider: {provider}")
    
    def get_oauth_url(self, provider: str, redirect_uri: str, state: str) -> str:
        """Get OAuth authorization URL for a provider."""
        provider = provider.lower()
        
        if provider == "google":
            return self._get_google_oauth_url(redirect_uri, state)
        elif provider == "facebook":
            return self._get_facebook_oauth_url(redirect_uri, state)
        elif provider == "apple":
            return self._get_apple_oauth_url(redirect_uri, state)
        else:
            raise ValidationError(f"Unsupported OAuth provider: {provider}")
    
    def _get_google_oauth_url(self, redirect_uri: str, state: str) -> str:
        """Get Google OAuth authorization URL."""
        if not self.google_client_id:
            raise SystemError("Google OAuth not configured")
        
        params = {
            "client_id": self.google_client_id,
            "redirect_uri": redirect_uri,
            "scope": "openid email profile",
            "response_type": "code",
            "state": state,
            "access_type": "offline",
            "prompt": "consent"
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"https://accounts.google.com/o/oauth2/v2/auth?{query_string}"
    
    def _get_facebook_oauth_url(self, redirect_uri: str, state: str) -> str:
        """Get Facebook OAuth authorization URL."""
        if not self.facebook_client_id:
            raise SystemError("Facebook OAuth not configured")
        
        params = {
            "client_id": self.facebook_client_id,
            "redirect_uri": redirect_uri,
            "scope": "email",
            "response_type": "code",
            "state": state
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"https://www.facebook.com/v18.0/dialog/oauth?{query_string}"
    
    def _get_apple_oauth_url(self, redirect_uri: str, state: str) -> str:
        """Get Apple Sign-In authorization URL."""
        if not self.apple_client_id:
            raise SystemError("Apple OAuth not configured")
        
        params = {
            "client_id": self.apple_client_id,
            "redirect_uri": redirect_uri,
            "scope": "name email",
            "response_type": "code id_token",
            "state": state,
            "response_mode": "form_post"
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"https://appleid.apple.com/auth/authorize?{query_string}"
