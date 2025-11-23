"""Monitoring and metrics collection for scrapers."""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
import asyncio
import logging
from dataclasses import dataclass, field
import json

logger = logging.getLogger(__name__)


@dataclass
class ScrapingMetric:
    """Single scraping metric."""
    timestamp: datetime
    scraper_name: str
    metric_type: str  # 'request', 'success', 'failure', 'retry', 'rate_limit'
    value: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScraperHealth:
    """Health status of a scraper."""
    scraper_name: str
    is_healthy: bool
    success_rate: float
    avg_response_time: float
    last_success: Optional[datetime]
    last_failure: Optional[datetime]
    error_count: int
    total_requests: int
    issues: List[str] = field(default_factory=list)


class ScrapingMonitor:
    """Monitors scraping performance and health."""
    
    def __init__(self, retention_hours: Optional[int] = None):
        """Initialize monitor.
        
        Args:
            retention_hours: How long to keep metrics (defaults to config)
        """
        if retention_hours is None:
            from .config import MONITORING_RETENTION_HOURS
            retention_hours = MONITORING_RETENTION_HOURS
        
        self.retention_hours = retention_hours
        self.metrics: deque = deque(maxlen=10000)  # Keep last 10k metrics
        self.scraper_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'requests': 0,
            'successes': 0,
            'failures': 0,
            'retries': 0,
            'rate_limits': 0,
            'response_times': deque(maxlen=1000),
            'errors': defaultdict(int),
            'last_success': None,
            'last_failure': None,
        })
        self.alert_callbacks: List[callable] = []
        # Load thresholds from config
        from .config import (
            MONITORING_SUCCESS_RATE_MIN,
            MONITORING_RESPONSE_TIME_MAX,
            MONITORING_ERROR_RATE_MAX,
            MONITORING_CONSECUTIVE_FAILURES_MAX
        )
        
        self.thresholds = {
            'success_rate_min': MONITORING_SUCCESS_RATE_MIN,
            'response_time_max': MONITORING_RESPONSE_TIME_MAX,
            'error_rate_max': MONITORING_ERROR_RATE_MAX,
            'consecutive_failures_max': MONITORING_CONSECUTIVE_FAILURES_MAX,
        }
    
    def record_metric(
        self,
        scraper_name: str,
        metric_type: str,
        value: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Record a metric.
        
        Args:
            scraper_name: Name of the scraper
            metric_type: Type of metric (request, success, failure, retry, rate_limit)
            value: Metric value
            metadata: Additional metadata
        """
        metric = ScrapingMetric(
            timestamp=datetime.utcnow(),
            scraper_name=scraper_name,
            metric_type=metric_type,
            value=value,
            metadata=metadata or {}
        )
        
        self.metrics.append(metric)
        
        # Update scraper stats
        stats = self.scraper_stats[scraper_name]
        
        if metric_type == 'request':
            stats['requests'] += 1
            if 'response_time' in metadata:
                stats['response_times'].append(metadata['response_time'])
        elif metric_type == 'success':
            stats['successes'] += 1
            stats['last_success'] = metric.timestamp
        elif metric_type == 'failure':
            stats['failures'] += 1
            stats['last_failure'] = metric.timestamp
            error_type = metadata.get('error_type', 'unknown')
            stats['errors'][error_type] += 1
        elif metric_type == 'retry':
            stats['retries'] += 1
        elif metric_type == 'rate_limit':
            stats['rate_limits'] += 1
        
        # Check for alerts
        self._check_alerts(scraper_name)
    
    def _check_alerts(self, scraper_name: str):
        """Check if alerts should be triggered."""
        stats = self.scraper_stats[scraper_name]
        
        if stats['requests'] == 0:
            return
        
        # Calculate rates
        success_rate = stats['successes'] / stats['requests'] if stats['requests'] > 0 else 0.0
        error_rate = stats['failures'] / stats['requests'] if stats['requests'] > 0 else 0.0
        
        # Calculate average response time
        response_times = list(stats['response_times'])
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0.0
        
        # Check thresholds
        alerts = []
        
        if success_rate < self.thresholds['success_rate_min']:
            alerts.append({
                'type': 'low_success_rate',
                'severity': 'warning',
                'message': f"{scraper_name}: Success rate {success_rate:.2%} below threshold {self.thresholds['success_rate_min']:.2%}",
                'value': success_rate,
                'threshold': self.thresholds['success_rate_min']
            })
        
        if avg_response_time > self.thresholds['response_time_max']:
            alerts.append({
                'type': 'high_response_time',
                'severity': 'warning',
                'message': f"{scraper_name}: Average response time {avg_response_time:.2f}s exceeds threshold {self.thresholds['response_time_max']:.2f}s",
                'value': avg_response_time,
                'threshold': self.thresholds['response_time_max']
            })
        
        if error_rate > self.thresholds['error_rate_max']:
            alerts.append({
                'type': 'high_error_rate',
                'severity': 'error',
                'message': f"{scraper_name}: Error rate {error_rate:.2%} exceeds threshold {self.thresholds['error_rate_max']:.2%}",
                'value': error_rate,
                'threshold': self.thresholds['error_rate_max']
            })
        
        # Check consecutive failures
        if stats['last_failure'] and stats['last_success']:
            if stats['last_failure'] > stats['last_success']:
                # Count recent failures
                recent_failures = sum(
                    1 for m in self.metrics
                    if m.scraper_name == scraper_name
                    and m.metric_type == 'failure'
                    and m.timestamp > datetime.utcnow() - timedelta(minutes=5)
                )
                
                if recent_failures >= self.thresholds['consecutive_failures_max']:
                    alerts.append({
                        'type': 'consecutive_failures',
                        'severity': 'error',
                        'message': f"{scraper_name}: {recent_failures} consecutive failures detected",
                        'value': recent_failures,
                        'threshold': self.thresholds['consecutive_failures_max']
                    })
        
        # Trigger alert callbacks
        for alert in alerts:
            for callback in self.alert_callbacks:
                try:
                    callback(alert)
                except Exception as e:
                    logger.error(f"Error in alert callback: {e}")
    
    def register_alert_callback(self, callback: callable):
        """Register a callback for alerts.
        
        Args:
            callback: Function that takes an alert dict as argument
        """
        self.alert_callbacks.append(callback)
    
    def get_scraper_health(self, scraper_name: str) -> ScraperHealth:
        """Get health status for a scraper.
        
        Args:
            scraper_name: Name of the scraper
            
        Returns:
            ScraperHealth object
        """
        stats = self.scraper_stats[scraper_name]
        
        if stats['requests'] == 0:
            return ScraperHealth(
                scraper_name=scraper_name,
                is_healthy=False,
                success_rate=0.0,
                avg_response_time=0.0,
                last_success=None,
                last_failure=None,
                error_count=0,
                total_requests=0,
                issues=['No requests made']
            )
        
        success_rate = stats['successes'] / stats['requests']
        error_rate = stats['failures'] / stats['requests']
        
        response_times = list(stats['response_times'])
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0.0
        
        # Determine health
        is_healthy = (
            success_rate >= self.thresholds['success_rate_min']
            and avg_response_time <= self.thresholds['response_time_max']
            and error_rate <= self.thresholds['error_rate_max']
        )
        
        # Collect issues
        issues = []
        if success_rate < self.thresholds['success_rate_min']:
            issues.append(f"Low success rate: {success_rate:.2%}")
        if avg_response_time > self.thresholds['response_time_max']:
            issues.append(f"High response time: {avg_response_time:.2f}s")
        if error_rate > self.thresholds['error_rate_max']:
            issues.append(f"High error rate: {error_rate:.2%}")
        
        return ScraperHealth(
            scraper_name=scraper_name,
            is_healthy=is_healthy,
            success_rate=success_rate,
            avg_response_time=avg_response_time,
            last_success=stats['last_success'],
            last_failure=stats['last_failure'],
            error_count=stats['failures'],
            total_requests=stats['requests'],
            issues=issues
        )
    
    def get_all_health(self) -> Dict[str, ScraperHealth]:
        """Get health status for all scrapers."""
        return {
            name: self.get_scraper_health(name)
            for name in self.scraper_stats.keys()
        }
    
    def get_metrics_summary(
        self,
        scraper_name: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get metrics summary.
        
        Args:
            scraper_name: Filter by scraper name (optional)
            start_time: Start time for filtering (optional)
            end_time: End time for filtering (optional)
            
        Returns:
            Dictionary with metrics summary
        """
        if start_time is None:
            start_time = datetime.utcnow() - timedelta(hours=self.retention_hours)
        if end_time is None:
            end_time = datetime.utcnow()
        
        # Filter metrics
        filtered_metrics = [
            m for m in self.metrics
            if (scraper_name is None or m.scraper_name == scraper_name)
            and start_time <= m.timestamp <= end_time
        ]
        
        # Aggregate by type
        by_type = defaultdict(lambda: {'count': 0, 'total_value': 0.0})
        for metric in filtered_metrics:
            by_type[metric.metric_type]['count'] += 1
            by_type[metric.metric_type]['total_value'] += metric.value
        
        summary = {
            'period': {
                'start': start_time.isoformat(),
                'end': end_time.isoformat()
            },
            'total_metrics': len(filtered_metrics),
            'by_type': {
                metric_type: {
                    'count': data['count'],
                    'avg_value': data['total_value'] / data['count'] if data['count'] > 0 else 0.0
                }
                for metric_type, data in by_type.items()
            }
        }
        
        return summary
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for monitoring dashboard."""
        all_health = self.get_all_health()
        
        # Calculate overall stats
        total_requests = sum(h.total_requests for h in all_health.values())
        total_successes = sum(int(h.success_rate * h.total_requests) for h in all_health.values())
        total_failures = sum(h.error_count for h in all_health.values())
        overall_success_rate = total_successes / total_requests if total_requests > 0 else 0.0
        
        # Get recent metrics (last hour)
        recent_metrics = [
            m for m in self.metrics
            if m.timestamp > datetime.utcnow() - timedelta(hours=1)
        ]
        
        return {
            'overall': {
                'total_requests': total_requests,
                'total_successes': total_successes,
                'total_failures': total_failures,
                'success_rate': overall_success_rate,
                'healthy_scrapers': sum(1 for h in all_health.values() if h.is_healthy),
                'total_scrapers': len(all_health),
            },
            'scrapers': {
                name: {
                    'is_healthy': health.is_healthy,
                    'success_rate': health.success_rate,
                    'avg_response_time': health.avg_response_time,
                    'total_requests': health.total_requests,
                    'error_count': health.error_count,
                    'issues': health.issues,
                    'last_success': health.last_success.isoformat() if health.last_success else None,
                    'last_failure': health.last_failure.isoformat() if health.last_failure else None,
                }
                for name, health in all_health.items()
            },
            'recent_activity': {
                'metrics_last_hour': len(recent_metrics),
                'requests_last_hour': sum(1 for m in recent_metrics if m.metric_type == 'request'),
                'successes_last_hour': sum(1 for m in recent_metrics if m.metric_type == 'success'),
                'failures_last_hour': sum(1 for m in recent_metrics if m.metric_type == 'failure'),
            },
            'timestamp': datetime.utcnow().isoformat()
        }


# Global monitor instance
_global_monitor: Optional[ScrapingMonitor] = None


def get_monitor() -> ScrapingMonitor:
    """Get global monitor instance."""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = ScrapingMonitor()
    return _global_monitor


def set_monitor(monitor: ScrapingMonitor):
    """Set global monitor instance."""
    global _global_monitor
    _global_monitor = monitor

