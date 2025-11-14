"""Alerting system for scraper failures and issues."""

from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
import logging
import json
import asyncio

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Alert:
    """Represents an alert."""
    id: str
    severity: AlertSeverity
    title: str
    message: str
    source: str  # scraper name or system component
    timestamp: datetime
    metadata: Dict[str, Any]
    resolved: bool = False
    resolved_at: Optional[datetime] = None


class AlertManager:
    """Manages alerts for scraping system."""
    
    def __init__(self, max_alerts: int = None):
        """Initialize alert manager.
        
        Args:
            max_alerts: Maximum number of alerts to keep in memory
        """
        if max_alerts is None:
            from .config import ALERT_MAX_ALERTS
            max_alerts = ALERT_MAX_ALERTS
        
        self.max_alerts = max_alerts
        self.alerts: List[Alert] = []
        self.alert_handlers: List[Callable] = []
        self.alert_filters: List[Callable] = []
        self.suppressed_alerts: set = set()  # Alert IDs to suppress
    
    def register_handler(self, handler: Callable):
        """Register an alert handler.
        
        Args:
            handler: Function that takes an Alert object
        """
        self.alert_handlers.append(handler)
        logger.info(f"Registered alert handler: {handler.__name__}")
    
    def register_filter(self, filter_func: Callable):
        """Register an alert filter.
        
        Args:
            filter_func: Function that takes an Alert and returns True to allow, False to suppress
        """
        self.alert_filters.append(filter_func)
        logger.info(f"Registered alert filter: {filter_func.__name__}")
    
    def create_alert(
        self,
        severity: AlertSeverity,
        title: str,
        message: str,
        source: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Alert:
        """Create and process an alert.
        
        Args:
            severity: Alert severity
            title: Alert title
            message: Alert message
            source: Source of the alert
            metadata: Additional metadata
            
        Returns:
            Created Alert object
        """
        alert = Alert(
            id=f"{source}_{datetime.utcnow().timestamp()}_{len(self.alerts)}",
            severity=severity,
            title=title,
            message=message,
            source=source,
            timestamp=datetime.utcnow(),
            metadata=metadata or {}
        )
        
        # Check filters
        should_alert = True
        for filter_func in self.alert_filters:
            try:
                if not filter_func(alert):
                    should_alert = False
                    break
            except Exception as e:
                logger.error(f"Error in alert filter: {e}")
        
        if not should_alert:
            logger.debug(f"Alert filtered out: {alert.title}")
            return alert
        
        # Check if suppressed
        if alert.id in self.suppressed_alerts:
            logger.debug(f"Alert suppressed: {alert.title}")
            return alert
        
        # Add to alerts list
        self.alerts.append(alert)
        
        # Keep only recent alerts
        if len(self.alerts) > self.max_alerts:
            self.alerts = self.alerts[-self.max_alerts:]
        
        # Trigger handlers
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Error in alert handler {handler.__name__}: {e}")
        
        logger.info(f"Alert created: {severity.value.upper()} - {title} from {source}")
        
        return alert
    
    def resolve_alert(self, alert_id: str):
        """Mark an alert as resolved.
        
        Args:
            alert_id: Alert ID
        """
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.resolved = True
                alert.resolved_at = datetime.utcnow()
                logger.info(f"Alert resolved: {alert.title}")
                break
    
    def suppress_alert(self, alert_id: str):
        """Suppress an alert (prevent future similar alerts).
        
        Args:
            alert_id: Alert ID
        """
        self.suppressed_alerts.add(alert_id)
        logger.info(f"Alert suppressed: {alert_id}")
    
    def get_alerts(
        self,
        severity: Optional[AlertSeverity] = None,
        source: Optional[str] = None,
        resolved: Optional[bool] = None,
        limit: int = 100
    ) -> List[Alert]:
        """Get alerts matching criteria.
        
        Args:
            severity: Filter by severity
            source: Filter by source
            resolved: Filter by resolved status
            limit: Maximum number of alerts to return
            
        Returns:
            List of matching alerts
        """
        filtered = self.alerts
        
        if severity:
            filtered = [a for a in filtered if a.severity == severity]
        
        if source:
            filtered = [a for a in filtered if a.source == source]
        
        if resolved is not None:
            filtered = [a for a in filtered if a.resolved == resolved]
        
        # Sort by timestamp (newest first)
        filtered.sort(key=lambda a: a.timestamp, reverse=True)
        
        return filtered[:limit]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get alert statistics."""
        total = len(self.alerts)
        resolved = sum(1 for a in self.alerts if a.resolved)
        unresolved = total - resolved
        
        by_severity = {}
        for severity in AlertSeverity:
            count = sum(1 for a in self.alerts if a.severity == severity)
            by_severity[severity.value] = count
        
        by_source = {}
        for alert in self.alerts:
            source = alert.source
            by_source[source] = by_source.get(source, 0) + 1
        
        return {
            'total': total,
            'resolved': resolved,
            'unresolved': unresolved,
            'by_severity': by_severity,
            'by_source': by_source,
            'suppressed': len(self.suppressed_alerts)
        }


# Alert handlers

def log_alert_handler(alert: Alert):
    """Log alert to logger."""
    log_level = {
        AlertSeverity.INFO: logging.INFO,
        AlertSeverity.WARNING: logging.WARNING,
        AlertSeverity.ERROR: logging.ERROR,
        AlertSeverity.CRITICAL: logging.CRITICAL,
    }.get(alert.severity, logging.INFO)
    
    logger.log(
        log_level,
        f"[{alert.severity.value.upper()}] {alert.title}: {alert.message} (Source: {alert.source})"
    )


def email_alert_handler(alert: Alert):
    """Send alert via email (placeholder - would need email service)."""
    # This would integrate with your email service
    if alert.severity in [AlertSeverity.ERROR, AlertSeverity.CRITICAL]:
        logger.info(f"Would send email alert: {alert.title}")
        # TODO: Implement email sending
        pass


def webhook_alert_handler(alert: Alert, webhook_url: str):
    """Send alert via webhook."""
    async def send_webhook():
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                payload = {
                    'id': alert.id,
                    'severity': alert.severity.value,
                    'title': alert.title,
                    'message': alert.message,
                    'source': alert.source,
                    'timestamp': alert.timestamp.isoformat(),
                    'metadata': alert.metadata
                }
                async with session.post(webhook_url, json=payload) as response:
                    if response.status == 200:
                        logger.debug(f"Webhook alert sent: {alert.title}")
                    else:
                        logger.warning(f"Failed to send webhook alert: {response.status}")
        except Exception as e:
            logger.error(f"Error sending webhook alert: {e}")
    
    asyncio.create_task(send_webhook())


# Global alert manager instance
_global_alert_manager: Optional[AlertManager] = None


def get_alert_manager() -> AlertManager:
    """Get global alert manager instance."""
    global _global_alert_manager
    if _global_alert_manager is None:
        _global_alert_manager = AlertManager()
        # Register default handler
        _global_alert_manager.register_handler(log_alert_handler)
        
        # Register webhook handler if configured
        from .config import ALERT_WEBHOOK_URL
        if ALERT_WEBHOOK_URL:
            webhook_handler = lambda alert: webhook_alert_handler(alert, ALERT_WEBHOOK_URL)
            _global_alert_manager.register_handler(webhook_handler)
            logger.info(f"Registered webhook alert handler: {ALERT_WEBHOOK_URL}")
        
        # Register email handler if enabled
        from .config import ALERT_EMAIL_ENABLED
        if ALERT_EMAIL_ENABLED:
            _global_alert_manager.register_handler(email_alert_handler)
            logger.info("Registered email alert handler")
    return _global_alert_manager


def set_alert_manager(manager: AlertManager):
    """Set global alert manager instance."""
    global _global_alert_manager
    _global_alert_manager = manager

