"""GDPR compliance endpoints for data export and deletion."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from datetime import datetime
import json
import csv
import io

from ..infrastructure.db.database import get_db
from ..infrastructure.db.models import UserModel
from ..core.security import JWTManager
from ..core.rate_limiter import rate_limit
from fastapi import Request, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter(prefix="/api/v1/gdpr", tags=["gdpr"])

security = HTTPBearer()

def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db)
) -> str:
    """Get current user ID from JWT token."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        token = credentials.credentials
        payload = JWTManager.decode_token(token)
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Verify user exists
        user = db.query(UserModel).filter(UserModel.id == user_id).first()
        if not user or user.status != "active":
            raise HTTPException(status_code=401, detail="User not found or inactive")
        
        return user_id
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")


@router.get("/export")
@rate_limit("5/hour")  # Limit data exports
async def export_user_data(
    request: Request,
    format: str = "json",  # json or csv
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """
    Export all user data in compliance with GDPR.
    
    Returns all personal data associated with the user including:
    - Profile information
    - Bookings
    - Favorites
    - Reviews
    - Price alerts
    - Saved searches
    """
    try:
        # Get user
        user = db.query(UserModel).filter(UserModel.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Collect all user data
        user_data = {
            "export_date": datetime.utcnow().isoformat(),
            "user_id": user.id,
            "profile": {
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role,
                "status": user.status,
                "email_verified": user.email_verified,
                "mfa_enabled": user.mfa_enabled,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "updated_at": user.updated_at.isoformat() if user.updated_at else None,
                "last_login": user.last_login.isoformat() if user.last_login else None,
            }
        }
        
        # Get bookings
        try:
            from search_booking_module.infrastructure.db.user_models import BookingModel
            bookings = db.query(BookingModel).filter(BookingModel.user_id == user_id).all()
            user_data["bookings"] = [
                {
                    "id": str(booking.id),
                    "hotel_id": str(booking.hotel_id),
                    "check_in": booking.check_in.isoformat() if booking.check_in else None,
                    "check_out": booking.check_out.isoformat() if booking.check_out else None,
                    "guests": booking.guests,
                    "rooms": booking.rooms,
                    "status": booking.status.value if hasattr(booking.status, 'value') else str(booking.status),
                    "total_price": float(booking.total_price) if booking.total_price else None,
                    "currency": booking.currency,
                    "created_at": booking.created_at.isoformat() if booking.created_at else None,
                }
                for booking in bookings
            ]
        except Exception as e:
            user_data["bookings"] = []
            user_data["bookings_error"] = str(e)
        
        # Get favorites
        try:
            from search_booking_module.infrastructure.db.user_models import FavoriteModel
            favorites = db.query(FavoriteModel).filter(FavoriteModel.user_id == user_id).all()
            user_data["favorites"] = [
                {
                    "id": str(fav.id),
                    "hotel_id": str(fav.hotel_id),
                    "created_at": fav.created_at.isoformat() if fav.created_at else None,
                }
                for fav in favorites
            ]
        except Exception as e:
            user_data["favorites"] = []
            user_data["favorites_error"] = str(e)
        
        # Get reviews
        try:
            from search_booking_module.infrastructure.db.user_models import UserReviewModel
            reviews = db.query(UserReviewModel).filter(UserReviewModel.user_id == user_id).all()
            user_data["reviews"] = [
                {
                    "id": str(review.id),
                    "hotel_id": str(review.hotel_id),
                    "rating": review.rating,
                    "title": review.title,
                    "text": review.text,
                    "created_at": review.created_at.isoformat() if review.created_at else None,
                }
                for review in reviews
            ]
        except Exception as e:
            user_data["reviews"] = []
            user_data["reviews_error"] = str(e)
        
        # Get price alerts
        try:
            from search_booking_module.infrastructure.db.user_models import PriceAlertModel
            alerts = db.query(PriceAlertModel).filter(PriceAlertModel.user_id == user_id).all()
            user_data["price_alerts"] = [
                {
                    "id": str(alert.id),
                    "hotel_id": str(alert.hotel_id),
                    "target_price": float(alert.target_price) if alert.target_price else None,
                    "currency": alert.currency,
                    "status": alert.status.value if hasattr(alert.status, 'value') else str(alert.status),
                    "created_at": alert.created_at.isoformat() if alert.created_at else None,
                }
                for alert in alerts
            ]
        except Exception as e:
            user_data["price_alerts"] = []
            user_data["price_alerts_error"] = str(e)
        
        # Get saved searches
        try:
            from search_booking_module.infrastructure.db.user_models import SavedSearchModel
            searches = db.query(SavedSearchModel).filter(SavedSearchModel.user_id == user_id).all()
            user_data["saved_searches"] = [
                {
                    "id": str(search.id),
                    "destination": search.destination,
                    "check_in": search.check_in.isoformat() if search.check_in else None,
                    "check_out": search.check_out.isoformat() if search.check_out else None,
                    "guests": search.guests,
                    "rooms": search.rooms,
                    "created_at": search.created_at.isoformat() if search.created_at else None,
                }
                for search in searches
            ]
        except Exception as e:
            user_data["saved_searches"] = []
            user_data["saved_searches_error"] = str(e)
        
        # Return in requested format
        if format.lower() == "csv":
            # Convert to CSV
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write profile data
            writer.writerow(["Section", "Field", "Value"])
            for key, value in user_data["profile"].items():
                writer.writerow(["Profile", key, value])
            
            # Write bookings
            if user_data.get("bookings"):
                writer.writerow([])
                writer.writerow(["Bookings"])
                writer.writerow(["ID", "Hotel ID", "Check In", "Check Out", "Guests", "Rooms", "Status", "Total Price", "Currency", "Created At"])
                for booking in user_data["bookings"]:
                    writer.writerow([
                        booking.get("id"),
                        booking.get("hotel_id"),
                        booking.get("check_in"),
                        booking.get("check_out"),
                        booking.get("guests"),
                        booking.get("rooms"),
                        booking.get("status"),
                        booking.get("total_price"),
                        booking.get("currency"),
                        booking.get("created_at"),
                    ])
            
            output.seek(0)
            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f'attachment; filename="user_data_export_{user_id}_{datetime.utcnow().strftime("%Y%m%d")}.csv"'
                }
            )
        else:
            # Return JSON
            return JSONResponse(
                content=user_data,
                headers={
                    "Content-Disposition": f'attachment; filename="user_data_export_{user_id}_{datetime.utcnow().strftime("%Y%m%d")}.json"'
                }
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to export user data: {str(e)}"
        )


@router.delete("/delete-account")
@rate_limit("1/day")  # Very strict limit for account deletion
async def delete_user_account(
    request: Request,
    confirm: bool = False,  # Require explicit confirmation
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """
    Delete user account and all associated data (GDPR Right to be Forgotten).
    
    This will:
    - Soft delete the user account (mark as deleted)
    - Anonymize personal data
    - Delete or anonymize associated records
    """
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Account deletion requires explicit confirmation. Set confirm=true"
        )
    
    try:
        # Get user
        user = db.query(UserModel).filter(UserModel.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Soft delete user account
        user.status = "deleted"
        user.email = f"deleted_{user.id}@deleted.local"
        user.first_name = "Deleted"
        user.last_name = "User"
        user.updated_at = datetime.utcnow()
        
        # Anonymize or delete associated data
        try:
            from search_booking_module.infrastructure.db.user_models import (
                BookingModel, FavoriteModel, UserReviewModel, 
                PriceAlertModel, SavedSearchModel
            )
            
            # Anonymize bookings
            bookings = db.query(BookingModel).filter(BookingModel.user_id == user_id).all()
            for booking in bookings:
                # Mark as deleted or anonymize
                booking.status = "cancelled"  # Or create a deleted status
            
            # Delete favorites
            db.query(FavoriteModel).filter(FavoriteModel.user_id == user_id).delete()
            
            # Anonymize reviews (keep for hotel ratings but remove personal info)
            reviews = db.query(UserReviewModel).filter(UserReviewModel.user_id == user_id).all()
            for review in reviews:
                review.author = "Anonymous"
                review.user_id = None  # Disassociate from user
            
            # Delete price alerts
            db.query(PriceAlertModel).filter(PriceAlertModel.user_id == user_id).delete()
            
            # Delete saved searches
            db.query(SavedSearchModel).filter(SavedSearchModel.user_id == user_id).delete()
            
        except Exception as e:
            # Log error but continue with user deletion
            print(f"Error cleaning up user data: {e}")
        
        db.commit()
        
        return {
            "message": "Account deleted successfully",
            "deleted_at": datetime.utcnow().isoformat(),
            "note": "Your account has been deleted. Some anonymized data may be retained for business purposes."
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete account: {str(e)}"
        )

