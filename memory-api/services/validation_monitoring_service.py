# ABOUTME: Real-time monitoring and alerting service for Source Validation & Verification System
# ABOUTME: Provides continuous monitoring, pattern drift detection, and enterprise alerting capabilities

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import structlog
import statistics
import aiohttp
import uuid

from core.database import DatabaseManager
from services.source_validation_service import ValidationResult, ValidationStatus

logger = structlog.get_logger(__name__)

class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class MonitoringMetric(Enum):
    VALIDATION_LATENCY = "validation_latency"
    SUCCESS_RATE = "success_rate"
    QUALITY_SCORE = "quality_score"
    SECURITY_THREATS = "security_threats"
    PATTERN_DRIFT = "pattern_drift"
    ERROR_RATE = "error_rate"
    THROUGHPUT = "throughput"

@dataclass
class AlertThreshold:
    """Configuration for monitoring alert thresholds"""
    metric: MonitoringMetric
    warning_threshold: float
    critical_threshold: float
    evaluation_window: timedelta
    minimum_samples: int = 10

@dataclass
class MonitoringAlert:
    """Real-time monitoring alert"""
    alert_id: str
    alert_type: str
    severity: AlertSeverity
    title: str
    message: str
    source_name: Optional[str]
    item_id: Optional[str]
    metrics: Dict[str, Any]
    thresholds: Dict[str, Any]
    recommendations: List[str]
    timestamp: datetime
    correlation_id: Optional[str] = None

@dataclass
class ValidationMetrics:
    """Aggregated validation metrics for monitoring"""
    timestamp: datetime
    source_name: str
    validation_count: int
    success_count: int
    failure_count: int
    quarantine_count: int
    avg_latency: float
    avg_quality_score: float
    avg_credibility_score: float
    security_threats: int
    error_count: int

class PatternDriftDetector:
    """Detects significant changes in validation patterns"""
    
    def __init__(self, window_size: int = 100, drift_threshold: float = 0.2):
        self.window_size = window_size
        self.drift_threshold = drift_threshold
        self.baseline_metrics = {}
        self.recent_metrics = defaultdict(lambda: deque(maxlen=window_size))
        
    async def detect_drift(self, source_name: str, metrics: ValidationMetrics) -> Optional[MonitoringAlert]:
        """Detect if validation patterns have drifted significantly"""
        try:
            # Store recent metrics
            self.recent_metrics[source_name].append(metrics)
            
            # Need enough data for comparison
            if len(self.recent_metrics[source_name]) < self.window_size // 2:
                return None
            
            # Calculate current averages
            recent_data = list(self.recent_metrics[source_name])
            current_success_rate = sum(m.success_count / max(1, m.validation_count) for m in recent_data) / len(recent_data)
            current_quality_score = sum(m.avg_quality_score for m in recent_data) / len(recent_data)
            current_latency = sum(m.avg_latency for m in recent_data) / len(recent_data)
            
            # Get or establish baseline
            if source_name not in self.baseline_metrics:
                self.baseline_metrics[source_name] = {
                    'success_rate': current_success_rate,
                    'quality_score': current_quality_score,
                    'latency': current_latency,
                    'established_at': datetime.utcnow()
                }
                return None
            
            baseline = self.baseline_metrics[source_name]
            
            # Calculate drift percentages
            success_rate_drift = abs(current_success_rate - baseline['success_rate']) / max(0.01, baseline['success_rate'])
            quality_drift = abs(current_quality_score - baseline['quality_score']) / max(0.01, baseline['quality_score'])
            latency_drift = abs(current_latency - baseline['latency']) / max(0.01, baseline['latency'])
            
            # Check for significant drift
            max_drift = max(success_rate_drift, quality_drift, latency_drift)
            
            if max_drift > self.drift_threshold:
                severity = AlertSeverity.CRITICAL if max_drift > 0.5 else AlertSeverity.WARNING
                
                return MonitoringAlert(
                    alert_id=str(uuid.uuid4()),
                    alert_type="pattern_drift",
                    severity=severity,
                    title=f"Pattern Drift Detected: {source_name}",
                    message=f"Validation patterns for {source_name} have drifted {max_drift:.1%} from baseline",
                    source_name=source_name,
                    item_id=None,
                    metrics={
                        "max_drift": max_drift,
                        "success_rate_drift": success_rate_drift,
                        "quality_drift": quality_drift,
                        "latency_drift": latency_drift,
                        "current_success_rate": current_success_rate,
                        "baseline_success_rate": baseline['success_rate'],
                        "current_quality": current_quality_score,
                        "baseline_quality": baseline['quality_score']
                    },
                    thresholds={
                        "drift_threshold": self.drift_threshold,
                        "evaluation_window": self.window_size
                    },
                    recommendations=[
                        "Investigate source reliability changes",
                        "Review recent validation failures",
                        "Check for external factors affecting source quality",
                        "Consider updating baseline metrics if change is permanent"
                    ],
                    timestamp=datetime.utcnow()
                )
            
            return None
            
        except Exception as e:
            logger.error("Pattern drift detection failed", source=source_name, error=str(e))
            return None

class ValidationMonitoringService:
    """Real-time monitoring service for validation system"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.is_monitoring = False
        self.monitoring_tasks = []
        self.drift_detector = PatternDriftDetector()
        
        # Alert configuration
        self.alert_thresholds = [
            AlertThreshold(
                metric=MonitoringMetric.VALIDATION_LATENCY,
                warning_threshold=0.5,  # 500ms
                critical_threshold=1.0,  # 1 second
                evaluation_window=timedelta(minutes=5)
            ),
            AlertThreshold(
                metric=MonitoringMetric.SUCCESS_RATE,
                warning_threshold=0.98,  # 98%
                critical_threshold=0.95,  # 95%
                evaluation_window=timedelta(minutes=10)
            ),
            AlertThreshold(
                metric=MonitoringMetric.QUALITY_SCORE,
                warning_threshold=0.6,  # Quality below 60%
                critical_threshold=0.4,  # Quality below 40%
                evaluation_window=timedelta(minutes=15)
            ),
            AlertThreshold(
                metric=MonitoringMetric.ERROR_RATE,
                warning_threshold=0.05,  # 5% error rate
                critical_threshold=0.1,   # 10% error rate
                evaluation_window=timedelta(minutes=5)
            ),
            AlertThreshold(
                metric=MonitoringMetric.SECURITY_THREATS,
                warning_threshold=1,     # Any security threats
                critical_threshold=5,    # Multiple threats
                evaluation_window=timedelta(minutes=5)
            )
        ]
        
        # Metrics storage
        self.metrics_buffer = defaultdict(list)
        self.active_alerts = {}
        self.alert_cooldowns = defaultdict(lambda: datetime.min)
        
        # NTFY configuration for notifications
        self.ntfy_topic = "da-tech-betty-validation"
        self.ntfy_url = f"https://ntfy.da-tech.io/{self.ntfy_topic}"
        
        logger.info("Validation Monitoring Service initialized")
    
    async def start_monitoring(self):
        """Start real-time monitoring"""
        if self.is_monitoring:
            logger.warning("Monitoring already active")
            return
        
        self.is_monitoring = True
        
        # Start monitoring tasks
        self.monitoring_tasks = [
            asyncio.create_task(self._metrics_collection_loop()),
            asyncio.create_task(self._alert_evaluation_loop()),
            asyncio.create_task(self._pattern_drift_monitoring_loop()),
            asyncio.create_task(self._performance_monitoring_loop())
        ]
        
        logger.info("Real-time monitoring started")
    
    async def stop_monitoring(self):
        """Stop real-time monitoring"""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        
        # Cancel monitoring tasks
        for task in self.monitoring_tasks:
            task.cancel()
        
        await asyncio.gather(*self.monitoring_tasks, return_exceptions=True)
        self.monitoring_tasks.clear()
        
        logger.info("Real-time monitoring stopped")
    
    async def _metrics_collection_loop(self):
        """Continuously collect validation metrics"""
        try:
            while self.is_monitoring:
                await self._collect_validation_metrics()
                await asyncio.sleep(30)  # Collect every 30 seconds
                
        except asyncio.CancelledError:
            logger.info("Metrics collection loop cancelled")
        except Exception as e:
            logger.error("Metrics collection loop failed", error=str(e))
    
    async def _alert_evaluation_loop(self):
        """Continuously evaluate alert conditions"""
        try:
            while self.is_monitoring:
                await self._evaluate_alert_conditions()
                await asyncio.sleep(15)  # Evaluate every 15 seconds
                
        except asyncio.CancelledError:
            logger.info("Alert evaluation loop cancelled")
        except Exception as e:
            logger.error("Alert evaluation loop failed", error=str(e))
    
    async def _pattern_drift_monitoring_loop(self):
        """Monitor for pattern drift in validation results"""
        try:
            while self.is_monitoring:
                await self._monitor_pattern_drift()
                await asyncio.sleep(60)  # Check every minute
                
        except asyncio.CancelledError:
            logger.info("Pattern drift monitoring cancelled")
        except Exception as e:
            logger.error("Pattern drift monitoring failed", error=str(e))
    
    async def _performance_monitoring_loop(self):
        """Monitor system performance and resource usage"""
        try:
            while self.is_monitoring:
                await self._monitor_system_performance()
                await asyncio.sleep(45)  # Check every 45 seconds
                
        except asyncio.CancelledError:
            logger.info("Performance monitoring cancelled")
        except Exception as e:
            logger.error("Performance monitoring failed", error=str(e))
    
    async def _collect_validation_metrics(self):
        """Collect validation metrics from database"""
        try:
            async with self.db_manager.get_postgres_pool().acquire() as conn:
                # Get metrics for the last 5 minutes by source
                metrics_data = await conn.fetch("""
                    SELECT 
                        source_name,
                        COUNT(*) as validation_count,
                        COUNT(CASE WHEN status = 'validated' THEN 1 END) as success_count,
                        COUNT(CASE WHEN status = 'failed' THEN 1 END) as failure_count,
                        COUNT(CASE WHEN status = 'quarantined' THEN 1 END) as quarantine_count,
                        AVG(validation_time) as avg_latency,
                        AVG(overall_score) as avg_quality_score,
                        AVG(credibility_score) as avg_credibility_score,
                        COUNT(CASE WHEN security_score < 1.0 THEN 1 END) as security_threats
                    FROM source_validations 
                    WHERE timestamp > $1
                    GROUP BY source_name
                """, datetime.utcnow() - timedelta(minutes=5))
                
                # Store metrics
                current_time = datetime.utcnow()
                for row in metrics_data:
                    metrics = ValidationMetrics(
                        timestamp=current_time,
                        source_name=row['source_name'],
                        validation_count=row['validation_count'],
                        success_count=row['success_count'],
                        failure_count=row['failure_count'],
                        quarantine_count=row['quarantine_count'],
                        avg_latency=float(row['avg_latency']) if row['avg_latency'] else 0.0,
                        avg_quality_score=float(row['avg_quality_score']) if row['avg_quality_score'] else 0.0,
                        avg_credibility_score=float(row['avg_credibility_score']) if row['avg_credibility_score'] else 0.0,
                        security_threats=row['security_threats'],
                        error_count=0  # Will be calculated from error tracking
                    )
                    
                    # Store in buffer (keep last 100 entries per source)
                    self.metrics_buffer[row['source_name']].append(metrics)
                    if len(self.metrics_buffer[row['source_name']]) > 100:
                        self.metrics_buffer[row['source_name']].pop(0)
                
                # Store metrics in database for historical analysis
                await self._store_performance_metrics(current_time, metrics_data)
                
        except Exception as e:
            logger.error("Failed to collect validation metrics", error=str(e))
    
    async def _evaluate_alert_conditions(self):
        """Evaluate all alert conditions against current metrics"""
        try:
            for source_name, metrics_list in self.metrics_buffer.items():
                if not metrics_list:
                    continue
                
                # Get recent metrics within evaluation windows
                for threshold in self.alert_thresholds:
                    cutoff_time = datetime.utcnow() - threshold.evaluation_window
                    recent_metrics = [m for m in metrics_list if m.timestamp >= cutoff_time]
                    
                    if len(recent_metrics) < threshold.minimum_samples:
                        continue
                    
                    # Evaluate specific metric
                    alert = await self._evaluate_metric_threshold(
                        source_name, threshold, recent_metrics
                    )
                    
                    if alert:
                        await self._handle_alert(alert)
            
        except Exception as e:
            logger.error("Failed to evaluate alert conditions", error=str(e))
    
    async def _evaluate_metric_threshold(
        self, 
        source_name: str, 
        threshold: AlertThreshold, 
        metrics: List[ValidationMetrics]
    ) -> Optional[MonitoringAlert]:
        """Evaluate a specific metric against its threshold"""
        try:
            if not metrics:
                return None
            
            # Calculate metric value based on type
            if threshold.metric == MonitoringMetric.VALIDATION_LATENCY:
                current_value = statistics.mean(m.avg_latency for m in metrics)
                is_critical = current_value > threshold.critical_threshold
                is_warning = current_value > threshold.warning_threshold
                direction = "above"
                
            elif threshold.metric == MonitoringMetric.SUCCESS_RATE:
                success_rates = [m.success_count / max(1, m.validation_count) for m in metrics]
                current_value = statistics.mean(success_rates)
                is_critical = current_value < threshold.critical_threshold
                is_warning = current_value < threshold.warning_threshold
                direction = "below"
                
            elif threshold.metric == MonitoringMetric.QUALITY_SCORE:
                current_value = statistics.mean(m.avg_quality_score for m in metrics)
                is_critical = current_value < threshold.critical_threshold
                is_warning = current_value < threshold.warning_threshold
                direction = "below"
                
            elif threshold.metric == MonitoringMetric.ERROR_RATE:
                error_rates = [m.error_count / max(1, m.validation_count) for m in metrics]
                current_value = statistics.mean(error_rates)
                is_critical = current_value > threshold.critical_threshold
                is_warning = current_value > threshold.warning_threshold
                direction = "above"
                
            elif threshold.metric == MonitoringMetric.SECURITY_THREATS:
                current_value = sum(m.security_threats for m in metrics)
                is_critical = current_value >= threshold.critical_threshold
                is_warning = current_value >= threshold.warning_threshold
                direction = "above"
                
            else:
                return None
            
            # Generate alert if threshold exceeded
            severity = None
            if is_critical:
                severity = AlertSeverity.CRITICAL
            elif is_warning:
                severity = AlertSeverity.WARNING
            
            if severity:
                # Check cooldown period
                alert_key = f"{source_name}_{threshold.metric.value}"
                if datetime.utcnow() < self.alert_cooldowns[alert_key]:
                    return None
                
                # Set cooldown (5 minutes for warnings, 15 minutes for critical)
                cooldown_minutes = 15 if severity == AlertSeverity.CRITICAL else 5
                self.alert_cooldowns[alert_key] = datetime.utcnow() + timedelta(minutes=cooldown_minutes)
                
                return MonitoringAlert(
                    alert_id=str(uuid.uuid4()),
                    alert_type=f"metric_threshold_{threshold.metric.value}",
                    severity=severity,
                    title=f"{threshold.metric.value.replace('_', ' ').title()} Alert: {source_name}",
                    message=f"{threshold.metric.value.replace('_', ' ').title()} is {direction} threshold ({current_value:.3f})",
                    source_name=source_name,
                    item_id=None,
                    metrics={
                        "current_value": current_value,
                        "warning_threshold": threshold.warning_threshold,
                        "critical_threshold": threshold.critical_threshold,
                        "evaluation_window_minutes": threshold.evaluation_window.total_seconds() / 60,
                        "sample_count": len(metrics)
                    },
                    thresholds={
                        "warning": threshold.warning_threshold,
                        "critical": threshold.critical_threshold
                    },
                    recommendations=self._get_metric_recommendations(threshold.metric, current_value),
                    timestamp=datetime.utcnow()
                )
            
            return None
            
        except Exception as e:
            logger.error("Failed to evaluate metric threshold", 
                        source=source_name, metric=threshold.metric.value, error=str(e))
            return None
    
    def _get_metric_recommendations(self, metric: MonitoringMetric, current_value: float) -> List[str]:
        """Get recommendations for specific metric alerts"""
        recommendations = {
            MonitoringMetric.VALIDATION_LATENCY: [
                "Check database connection pool configuration",
                "Review ML model performance and optimization",
                "Investigate network latency issues",
                "Consider horizontal scaling of validation workers"
            ],
            MonitoringMetric.SUCCESS_RATE: [
                "Review recent validation failures",
                "Check source reliability and availability",
                "Investigate quality threshold configurations",
                "Review security scanning false positives"
            ],
            MonitoringMetric.QUALITY_SCORE: [
                "Investigate source content quality degradation",
                "Review quality scoring algorithm parameters",
                "Check for changes in source data formats",
                "Consider updating quality baselines"
            ],
            MonitoringMetric.ERROR_RATE: [
                "Check application logs for error patterns",
                "Review database connection stability",
                "Investigate external API reliability",
                "Check resource utilization and limits"
            ],
            MonitoringMetric.SECURITY_THREATS: [
                "Investigate security scanning results",
                "Review threat detection accuracy",
                "Check for compromised sources",
                "Update security scanning rules if needed"
            ]
        }
        
        return recommendations.get(metric, ["Investigate metric anomaly", "Review system configuration"])
    
    async def _monitor_pattern_drift(self):
        """Monitor for pattern drift across sources"""
        try:
            for source_name, metrics_list in self.metrics_buffer.items():
                if not metrics_list:
                    continue
                
                latest_metrics = metrics_list[-1]
                drift_alert = await self.drift_detector.detect_drift(source_name, latest_metrics)
                
                if drift_alert:
                    await self._handle_alert(drift_alert)
                    
        except Exception as e:
            logger.error("Pattern drift monitoring failed", error=str(e))
    
    async def _monitor_system_performance(self):
        """Monitor overall system performance"""
        try:
            async with self.db_manager.get_postgres_pool().acquire() as conn:
                # Check database performance
                db_stats = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as active_connections,
                        AVG(EXTRACT(EPOCH FROM (NOW() - query_start))) as avg_query_time
                    FROM pg_stat_activity 
                    WHERE state = 'active' AND query NOT LIKE '%pg_stat_activity%'
                """)
                
                # Check validation queue size
                queue_stats = await conn.fetchrow("""
                    SELECT COUNT(*) as pending_validations
                    FROM source_validations 
                    WHERE status = 'pending' 
                    AND timestamp > $1
                """, datetime.utcnow() - timedelta(minutes=30))
                
                # Generate performance alerts
                if db_stats and db_stats['avg_query_time'] and db_stats['avg_query_time'] > 5.0:
                    alert = MonitoringAlert(
                        alert_id=str(uuid.uuid4()),
                        alert_type="database_performance",
                        severity=AlertSeverity.WARNING,
                        title="Database Performance Degradation",
                        message=f"Average query time is {db_stats['avg_query_time']:.2f}s",
                        source_name=None,
                        item_id=None,
                        metrics={
                            "avg_query_time": db_stats['avg_query_time'],
                            "active_connections": db_stats['active_connections']
                        },
                        thresholds={"warning": 5.0, "critical": 10.0},
                        recommendations=[
                            "Check database connection pool settings",
                            "Review slow query log",
                            "Consider database optimization",
                            "Monitor resource usage"
                        ],
                        timestamp=datetime.utcnow()
                    )
                    await self._handle_alert(alert)
                
                if queue_stats and queue_stats['pending_validations'] > 1000:
                    alert = MonitoringAlert(
                        alert_id=str(uuid.uuid4()),
                        alert_type="validation_queue_backlog",
                        severity=AlertSeverity.ERROR,
                        title="Validation Queue Backlog",
                        message=f"Large validation queue: {queue_stats['pending_validations']} pending items",
                        source_name=None,
                        item_id=None,
                        metrics={"pending_validations": queue_stats['pending_validations']},
                        thresholds={"warning": 500, "critical": 1000},
                        recommendations=[
                            "Increase validation worker capacity",
                            "Check validation service health",
                            "Review validation performance",
                            "Consider batch processing optimization"
                        ],
                        timestamp=datetime.utcnow()
                    )
                    await self._handle_alert(alert)
                    
        except Exception as e:
            logger.error("System performance monitoring failed", error=str(e))
    
    async def _handle_alert(self, alert: MonitoringAlert):
        """Handle generated alert"""
        try:
            # Store alert in database
            await self._store_alert(alert)
            
            # Send NTFY notification
            await self._send_ntfy_notification(alert)
            
            # Store in active alerts
            self.active_alerts[alert.alert_id] = alert
            
            logger.warning("Alert generated",
                          alert_id=alert.alert_id,
                          alert_type=alert.alert_type,
                          severity=alert.severity.value,
                          source=alert.source_name)
            
        except Exception as e:
            logger.error("Failed to handle alert", alert_id=alert.alert_id, error=str(e))
    
    async def _store_alert(self, alert: MonitoringAlert):
        """Store alert in database"""
        try:
            async with self.db_manager.get_postgres_pool().acquire() as conn:
                await conn.execute("""
                    INSERT INTO validation_alerts (
                        id, alert_type, alert_level, alert_title, alert_message,
                        source_name, item_id, metrics, thresholds, status, created_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                """, 
                uuid.UUID(alert.alert_id), alert.alert_type, alert.severity.value,
                alert.title, alert.message, alert.source_name, 
                uuid.UUID(alert.item_id) if alert.item_id else None,
                json.dumps(alert.metrics), json.dumps(alert.thresholds),
                "active", alert.timestamp)
                
        except Exception as e:
            logger.error("Failed to store alert", alert_id=alert.alert_id, error=str(e))
    
    async def _send_ntfy_notification(self, alert: MonitoringAlert):
        """Send alert notification via NTFY"""
        try:
            # Determine emoji based on severity
            emoji_map = {
                AlertSeverity.INFO: "ℹ️",
                AlertSeverity.WARNING: "⚠️", 
                AlertSeverity.ERROR: "❌",
                AlertSeverity.CRITICAL: "🚨"
            }
            
            emoji = emoji_map.get(alert.severity, "🔔")
            
            # Format notification
            notification = {
                "topic": self.ntfy_topic,
                "title": f"{emoji} Betty Validation Alert",
                "message": f"{alert.title}\n\n{alert.message}",
                "tags": [alert.severity.value, "validation", "betty"],
                "priority": 5 if alert.severity == AlertSeverity.CRITICAL else 3
            }
            
            # Add source context if available
            if alert.source_name:
                notification["message"] += f"\n\nSource: {alert.source_name}"
            
            # Send notification
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.ntfy_url,
                    json=notification,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        logger.info("NTFY notification sent", alert_id=alert.alert_id)
                    else:
                        logger.warning("NTFY notification failed", 
                                     alert_id=alert.alert_id, 
                                     status=response.status)
                        
        except asyncio.TimeoutError:
            logger.warning("NTFY notification timed out", alert_id=alert.alert_id)
        except Exception as e:
            logger.error("Failed to send NTFY notification", alert_id=alert.alert_id, error=str(e))
    
    async def _store_performance_metrics(self, timestamp: datetime, metrics_data: List[Dict]):
        """Store performance metrics in database"""
        try:
            async with self.db_manager.get_postgres_pool().acquire() as conn:
                for row in metrics_data:
                    source_name = row['source_name']
                    
                    # Store individual metrics
                    metrics_to_store = [
                        ('validation_count', row['validation_count'], 'count'),
                        ('success_rate', row['success_count'] / max(1, row['validation_count']), 'ratio'),
                        ('avg_latency', float(row['avg_latency']) if row['avg_latency'] else 0.0, 'seconds'),
                        ('avg_quality_score', float(row['avg_quality_score']) if row['avg_quality_score'] else 0.0, 'score'),
                        ('security_threats', row['security_threats'], 'count')
                    ]
                    
                    for metric_name, value, unit in metrics_to_store:
                        await conn.execute("""
                            INSERT INTO validation_performance_metrics (
                                time_bucket, metric_name, value, unit, source_name, recorded_at
                            ) VALUES ($1, $2, $3, $4, $5, $6)
                        """, timestamp, metric_name, value, unit, source_name, timestamp)
                        
        except Exception as e:
            logger.error("Failed to store performance metrics", error=str(e))
    
    async def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring system status"""
        try:
            active_alerts_count = len(self.active_alerts)
            sources_monitored = len(self.metrics_buffer)
            
            # Get recent statistics
            recent_metrics = []
            for metrics_list in self.metrics_buffer.values():
                recent_metrics.extend(metrics_list[-10:])  # Last 10 from each source
            
            total_validations = sum(m.validation_count for m in recent_metrics)
            avg_latency = statistics.mean([m.avg_latency for m in recent_metrics]) if recent_metrics else 0.0
            avg_quality = statistics.mean([m.avg_quality_score for m in recent_metrics]) if recent_metrics else 0.0
            
            return {
                "monitoring_active": self.is_monitoring,
                "active_alerts": active_alerts_count,
                "sources_monitored": sources_monitored,
                "metrics_buffer_size": sum(len(metrics) for metrics in self.metrics_buffer.values()),
                "recent_statistics": {
                    "total_validations": total_validations,
                    "avg_latency": avg_latency,
                    "avg_quality_score": avg_quality,
                    "meets_sla_latency": avg_latency < 0.5,
                    "meets_sla_accuracy": avg_quality > 0.7
                },
                "system_health": {
                    "pattern_drift_detector": "operational",
                    "alert_system": "operational",
                    "ntfy_notifications": "operational",
                    "database_monitoring": "operational"
                },
                "alert_thresholds": [
                    {
                        "metric": threshold.metric.value,
                        "warning": threshold.warning_threshold,
                        "critical": threshold.critical_threshold,
                        "window_minutes": threshold.evaluation_window.total_seconds() / 60
                    }
                    for threshold in self.alert_thresholds
                ]
            }
            
        except Exception as e:
            logger.error("Failed to get monitoring status", error=str(e))
            return {
                "monitoring_active": False,
                "error": str(e)
            }

# Service instance for dependency injection
_monitoring_service_instance = None

async def get_monitoring_service(db_manager: DatabaseManager) -> ValidationMonitoringService:
    """Get or create monitoring service instance"""
    global _monitoring_service_instance
    
    if _monitoring_service_instance is None:
        _monitoring_service_instance = ValidationMonitoringService(db_manager)
    
    return _monitoring_service_instance