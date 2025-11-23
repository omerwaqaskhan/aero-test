"""API routes for monitoring and metrics."""

from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session

try:
    from auth_module.infrastructure.db.database import get_db
except ImportError:
    from ...auth_module.infrastructure.db.database import get_db

from search_booking_module.scraping.monitoring import get_monitor
from search_booking_module.scraping.alerting import get_alert_manager, AlertSeverity
from search_booking_module.scraping.proxy_pool import ProxyPool
from search_booking_module.scraping.price_checker import PriceChecker

router = APIRouter(prefix="/api/v1/monitoring", tags=["monitoring"])


@router.get("/dashboard")
async def get_dashboard():
    """Get dashboard data for monitoring."""
    monitor = get_monitor()
    dashboard_data = monitor.get_dashboard_data()
    return dashboard_data


@router.get("/health")
async def get_health(scraper_name: Optional[str] = None):
    """Get health status of scrapers."""
    monitor = get_monitor()
    
    if scraper_name:
        health = monitor.get_scraper_health(scraper_name)
        return {
            'scraper': scraper_name,
            'is_healthy': health.is_healthy,
            'success_rate': health.success_rate,
            'avg_response_time': health.avg_response_time,
            'total_requests': health.total_requests,
            'error_count': health.error_count,
            'issues': health.issues,
            'last_success': health.last_success.isoformat() if health.last_success else None,
            'last_failure': health.last_failure.isoformat() if health.last_failure else None,
        }
    else:
        all_health = monitor.get_all_health()
        return {
            'scrapers': {
                name: {
                    'is_healthy': health.is_healthy,
                    'success_rate': health.success_rate,
                    'avg_response_time': health.avg_response_time,
                    'total_requests': health.total_requests,
                    'error_count': health.error_count,
                    'issues': health.issues,
                }
                for name, health in all_health.items()
            }
        }


@router.get("/metrics")
async def get_metrics(
    scraper_name: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None
):
    """Get metrics summary."""
    monitor = get_monitor()
    
    start = datetime.fromisoformat(start_time) if start_time else None
    end = datetime.fromisoformat(end_time) if end_time else None
    
    summary = monitor.get_metrics_summary(
        scraper_name=scraper_name,
        start_time=start,
        end_time=end
    )
    return summary


@router.get("/alerts")
async def get_alerts(
    severity: Optional[str] = None,
    source: Optional[str] = None,
    resolved: Optional[bool] = None,
    limit: int = 100
):
    """Get alerts."""
    alert_manager = get_alert_manager()
    
    severity_enum = None
    if severity:
        try:
            severity_enum = AlertSeverity(severity)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid severity: {severity}")
    
    alerts = alert_manager.get_alerts(
        severity=severity_enum,
        source=source,
        resolved=resolved,
        limit=limit
    )
    
    return {
        'alerts': [
            {
                'id': alert.id,
                'severity': alert.severity.value,
                'title': alert.title,
                'message': alert.message,
                'source': alert.source,
                'timestamp': alert.timestamp.isoformat(),
                'resolved': alert.resolved,
                'resolved_at': alert.resolved_at.isoformat() if alert.resolved_at else None,
                'metadata': alert.metadata
            }
            for alert in alerts
        ],
        'total': len(alerts)
    }


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str):
    """Resolve an alert."""
    alert_manager = get_alert_manager()
    alert_manager.resolve_alert(alert_id)
    return {"status": "resolved", "alert_id": alert_id}


@router.get("/alerts/stats")
async def get_alert_stats():
    """Get alert statistics."""
    alert_manager = get_alert_manager()
    stats = alert_manager.get_stats()
    return stats


@router.get("/proxies")
async def get_proxy_stats():
    """Get proxy pool statistics."""
    # This would need to be integrated with the actual proxy pool instance
    # For now, return placeholder
    return {
        'message': 'Proxy pool statistics - requires proxy pool instance integration',
        'note': 'Proxy pool needs to be initialized and passed to this endpoint'
    }


@router.post("/price-check/{hotel_id}")
async def check_hotel_price(
    hotel_id: str,
    check_in: Optional[str] = None,
    check_out: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Check prices for a specific hotel."""
    from datetime import date
    
    check_in_date = date.fromisoformat(check_in) if check_in else None
    check_out_date = date.fromisoformat(check_out) if check_out else None
    
    price_checker = PriceChecker(db_session=db)
    await price_checker.start()
    
    try:
        result = await price_checker.check_hotel_prices(
            hotel_id=hotel_id,
            check_in=check_in_date,
            check_out=check_out_date
        )
        return result
    finally:
        await price_checker.stop()

