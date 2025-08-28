# ABOUTME: Real-time error monitoring and alerting service for Betty Memory System
# ABOUTME: Provides intelligent error pattern detection, alerting, and system health monitoring

import asyncio
import aiohttp
import json
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field, asdict
from collections import defaultdict, deque
from enum import Enum
import structlog

from core.error_classification import ErrorClassification, ErrorSeverity, ErrorCategory
from core.enhanced_logging import EnhancedStructuredLogger, ComponentType, get_enhanced_logger

logger = structlog.get_logger(__name__)

class AlertSeverity(Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class AlertChannel(Enum):
    """Alert delivery channels"""
    NTFY = "ntfy"
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    LOG = "log"

@dataclass
class ErrorPattern:
    """Detected error pattern information"""
    pattern_id: str
    pattern_type: str
    description: str
    first_occurrence: datetime
    last_occurrence: datetime
    occurrence_count: int
    affected_components: Set[str] = field(default_factory=set)
    error_rate_per_minute: float = 0.0
    severity_distribution: Dict[str, int] = field(default_factory=dict)
    user_impact_estimate: str = "unknown"

@dataclass 
class SystemHealthMetrics:
    """Current system health metrics"""
    timestamp: datetime
    overall_health_score: float  # 0-100
    error_rate_per_minute: float
    avg_response_time_ms: float
    memory_usage_percent: float
    cpu_usage_percent: float
    database_health: Dict[str, str]
    active_incidents: int
    services_degraded: List[str] = field(default_factory=list)
    services_down: List[str] = field(default_factory=list)

@dataclass
class Alert:
    """System alert with comprehensive information"""
    alert_id: str
    severity: AlertSeverity
    title: str
    description: str
    component: str
    created_at: datetime
    error_pattern: Optional[ErrorPattern] = None
    health_metrics: Optional[SystemHealthMetrics] = None
    recommended_actions: List[str] = field(default_factory=list)
    affected_users: int = 0
    estimated_downtime_minutes: Optional[int] = None
    recovery_eta: Optional[datetime] = None
    tags: Set[str] = field(default_factory=set)

class ErrorTrendAnalyzer:
    """Analyzes error trends and patterns over time"""
    
    def __init__(self, analysis_window_hours: int = 24):
        self.analysis_window_hours = analysis_window_hours
        self.error_history: deque = deque(maxlen=10000)  # Keep last 10k errors
        self.pattern_cache: Dict[str, ErrorPattern] = {}
        self.trend_thresholds = {
            "error_spike": 10,      # errors per minute
            "gradual_increase": 0.5, # 50% increase over 1 hour
            "service_degradation": 5000,  # avg response time ms
            "memory_leak": 0.1      # 10% increase per hour
        }
    
    def add_error(self, classification: ErrorClassification, context: Dict[str, Any]):
        """Add error to trend analysis"""
        error_data = {
            "timestamp": datetime.now(timezone.utc),
            "classification": classification,
            "context": context
        }
        
        self.error_history.append(error_data)
        self._update_patterns(classification, context)
    
    def _update_patterns(self, classification: ErrorClassification, context: Dict[str, Any]):
        """Update error patterns based on new error"""
        pattern_key = f"{classification.category.value}:{classification.subcategory.value if classification.subcategory else 'none'}"
        
        if pattern_key not in self.pattern_cache:
            self.pattern_cache[pattern_key] = ErrorPattern(
                pattern_id=pattern_key,
                pattern_type=classification.category.value,
                description=f"{classification.category.value} errors",
                first_occurrence=datetime.now(timezone.utc),
                last_occurrence=datetime.now(timezone.utc),
                occurrence_count=1
            )
        else:
            pattern = self.pattern_cache[pattern_key]
            pattern.last_occurrence = datetime.now(timezone.utc)
            pattern.occurrence_count += 1
            
            # Update component tracking
            if context.get("component"):
                pattern.affected_components.add(context["component"])
            
            # Update severity distribution
            severity = classification.severity.value
            if severity not in pattern.severity_distribution:
                pattern.severity_distribution[severity] = 0
            pattern.severity_distribution[severity] += 1
    
    def analyze_trends(self) -> Dict[str, Any]:
        """Analyze current error trends"""
        now = datetime.now(timezone.utc)
        analysis_window = now - timedelta(hours=self.analysis_window_hours)
        
        # Filter recent errors
        recent_errors = [
            error for error in self.error_history 
            if error["timestamp"] > analysis_window
        ]
        
        if not recent_errors:
            return {"trends": [], "patterns": [], "recommendations": []}
        
        trends = []
        recommendations = []
        
        # Analyze error spike
        error_spike = self._analyze_error_spike(recent_errors)
        if error_spike:
            trends.append(error_spike)
            recommendations.extend(error_spike.get("recommendations", []))
        
        # Analyze gradual increase
        gradual_increase = self._analyze_gradual_increase(recent_errors)
        if gradual_increase:
            trends.append(gradual_increase)
            recommendations.extend(gradual_increase.get("recommendations", []))
        
        # Analyze component-specific patterns
        component_patterns = self._analyze_component_patterns(recent_errors)
        trends.extend(component_patterns)
        
        return {
            "trends": trends,
            "patterns": list(self.pattern_cache.values()),
            "recommendations": list(set(recommendations)),  # Remove duplicates
            "analysis_window_hours": self.analysis_window_hours,
            "total_errors_analyzed": len(recent_errors)
        }
    
    def _analyze_error_spike(self, recent_errors: List[Dict]) -> Optional[Dict[str, Any]]:
        """Detect error spikes"""
        if len(recent_errors) < 10:
            return None
        
        # Calculate error rate per minute for last 15 minutes
        now = datetime.now(timezone.utc)
        last_15_min = now - timedelta(minutes=15)
        recent_spike_errors = [
            error for error in recent_errors 
            if error["timestamp"] > last_15_min
        ]
        
        error_rate = len(recent_spike_errors) / 15  # errors per minute
        
        if error_rate > self.trend_thresholds["error_spike"]:
            return {
                "trend_type": "error_spike",
                "severity": "high" if error_rate > 20 else "medium",
                "error_rate_per_minute": error_rate,
                "description": f"Error spike detected: {error_rate:.1f} errors/minute",
                "recommendations": [
                    "Check system resources and database connections",
                    "Review recent deployments or configuration changes",
                    "Monitor service health and consider scaling"
                ]
            }
        
        return None
    
    def _analyze_gradual_increase(self, recent_errors: List[Dict]) -> Optional[Dict[str, Any]]:
        """Detect gradual error increase"""
        if len(recent_errors) < 20:
            return None
        
        # Compare first hour vs last hour error counts
        now = datetime.now(timezone.utc)
        last_hour = now - timedelta(hours=1)
        two_hours_ago = now - timedelta(hours=2)
        
        last_hour_errors = len([
            error for error in recent_errors 
            if error["timestamp"] > last_hour
        ])
        
        previous_hour_errors = len([
            error for error in recent_errors 
            if two_hours_ago < error["timestamp"] <= last_hour
        ])
        
        if previous_hour_errors > 0:
            increase_ratio = last_hour_errors / previous_hour_errors
            if increase_ratio > (1 + self.trend_thresholds["gradual_increase"]):
                return {
                    "trend_type": "gradual_increase",
                    "severity": "medium",
                    "increase_ratio": increase_ratio,
                    "description": f"Error rate increased by {(increase_ratio - 1) * 100:.1f}% in last hour",
                    "recommendations": [
                        "Investigate recent system changes",
                        "Check for memory leaks or resource exhaustion",
                        "Review application performance metrics"
                    ]
                }
        
        return None
    
    def _analyze_component_patterns(self, recent_errors: List[Dict]) -> List[Dict[str, Any]]:
        """Analyze component-specific error patterns"""
        component_errors = defaultdict(list)
        
        for error in recent_errors:
            component = error["context"].get("component", "unknown")
            component_errors[component].append(error)
        
        patterns = []
        
        for component, errors in component_errors.items():
            if len(errors) > 5:  # Only analyze components with significant errors
                # Analyze error categories
                category_counts = defaultdict(int)
                for error in errors:
                    category = error["classification"].category.value
                    category_counts[category] += 1
                
                # Find dominant error category
                dominant_category = max(category_counts.items(), key=lambda x: x[1])
                
                if dominant_category[1] > len(errors) * 0.5:  # More than 50% of errors
                    patterns.append({
                        "trend_type": "component_pattern",
                        "component": component,
                        "dominant_error_category": dominant_category[0],
                        "error_count": len(errors),
                        "dominance_percent": (dominant_category[1] / len(errors)) * 100,
                        "description": f"Component '{component}' showing pattern of {dominant_category[0]} errors",
                        "recommendations": self._get_component_recommendations(component, dominant_category[0])
                    })
        
        return patterns
    
    def _get_component_recommendations(self, component: str, error_category: str) -> List[str]:
        """Get recommendations for component-specific error patterns"""
        recommendations = {
            "database_error": [
                "Check database connection pool settings",
                "Review query performance and indexes",
                "Monitor database server resources"
            ],
            "memory_corruption": [
                "Run memory integrity validation",
                "Check cross-database consistency",
                "Review recent data ingestion processes"
            ],
            "api_validation": [
                "Review API request validation rules",
                "Check client integration implementations",
                "Update API documentation if needed"
            ],
            "performance_degradation": [
                "Optimize query performance",
                "Review cache configuration",
                "Consider resource scaling"
            ]
        }
        
        return recommendations.get(error_category, ["Investigate component-specific issues"])

class AlertManager:
    """Manages alert generation, routing, and delivery"""
    
    def __init__(self):
        self.logger = get_enhanced_logger(__name__, ComponentType.HEALTH_MONITOR)
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: deque = deque(maxlen=1000)
        
        # Alert configuration
        self.notification_channels = {
            AlertSeverity.CRITICAL: [AlertChannel.NTFY, AlertChannel.LOG],
            AlertSeverity.HIGH: [AlertChannel.NTFY, AlertChannel.LOG],
            AlertSeverity.MEDIUM: [AlertChannel.LOG],
            AlertSeverity.LOW: [AlertChannel.LOG]
        }
        
        # NTFY configuration
        self.ntfy_url = "https://ntfy.da-tech.io/betty-alerts"
        self.ntfy_enabled = True
        
        # Rate limiting to prevent alert spam
        self.alert_rate_limits = {
            AlertSeverity.EMERGENCY: 0,      # No limit for emergency
            AlertSeverity.CRITICAL: 1,       # 1 per minute
            AlertSeverity.HIGH: 5,           # 5 per minute
            AlertSeverity.MEDIUM: 10,        # 10 per minute
            AlertSeverity.LOW: 20            # 20 per minute
        }
        
        self.last_alert_times: Dict[str, datetime] = {}
    
    async def create_alert(self, severity: AlertSeverity, title: str, description: str,
                          component: str, error_pattern: Optional[ErrorPattern] = None,
                          health_metrics: Optional[SystemHealthMetrics] = None,
                          **kwargs) -> Alert:
        """Create and process new alert"""
        
        alert_id = f"alert-{hash(f'{component}-{title}-{datetime.now().isoformat()}')}"
        
        alert = Alert(
            alert_id=alert_id,
            severity=severity,
            title=title,
            description=description,
            component=component,
            created_at=datetime.now(timezone.utc),
            error_pattern=error_pattern,
            health_metrics=health_metrics,
            **kwargs
        )
        
        # Check rate limiting
        if not self._check_rate_limit(alert):
            await self.logger.info(
                "Alert rate limited",
                alert_id=alert_id,
                severity=severity.value,
                title=title
            )
            return alert
        
        # Store alert
        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)
        
        # Log alert creation
        await self.logger.warning(
            "Alert created",
            alert_id=alert_id,
            severity=severity.value,
            title=title,
            component=component,
            description=description[:200] + "..." if len(description) > 200 else description
        )
        
        # Route alert to appropriate channels
        await self._route_alert(alert)
        
        return alert
    
    def _check_rate_limit(self, alert: Alert) -> bool:
        """Check if alert passes rate limiting"""
        rate_limit = self.alert_rate_limits.get(alert.severity, 10)
        if rate_limit == 0:  # No limit
            return True
        
        # Create rate limit key
        rate_key = f"{alert.component}-{alert.severity.value}"
        now = datetime.now(timezone.utc)
        
        # Check last alert time
        last_alert = self.last_alert_times.get(rate_key)
        if last_alert is None:
            self.last_alert_times[rate_key] = now
            return True
        
        # Calculate time since last alert
        time_since_last = (now - last_alert).total_seconds()
        min_interval = 60 / rate_limit  # seconds between alerts
        
        if time_since_last >= min_interval:
            self.last_alert_times[rate_key] = now
            return True
        
        return False
    
    async def _route_alert(self, alert: Alert):
        """Route alert to appropriate notification channels"""
        channels = self.notification_channels.get(alert.severity, [AlertChannel.LOG])
        
        for channel in channels:
            try:
                if channel == AlertChannel.NTFY:
                    await self._send_ntfy_alert(alert)
                elif channel == AlertChannel.LOG:
                    await self._log_alert(alert)
                # Additional channels can be added here
                
            except Exception as e:
                await self.logger.error(
                    "Alert routing failed",
                    alert_id=alert.alert_id,
                    channel=channel.value,
                    error=str(e)
                )
    
    async def _send_ntfy_alert(self, alert: Alert):
        """Send alert via NTFY"""
        if not self.ntfy_enabled:
            return
        
        # Determine emoji based on severity
        emoji_map = {
            AlertSeverity.EMERGENCY: "🚨",
            AlertSeverity.CRITICAL: "🔥",
            AlertSeverity.HIGH: "⚠️",
            AlertSeverity.MEDIUM: "⚡",
            AlertSeverity.LOW: "ℹ️"
        }
        
        emoji = emoji_map.get(alert.severity, "🔔")
        
        # Create notification message
        message = f"{emoji} BETTY Alert: {alert.title}\n\n"
        message += f"Component: {alert.component}\n"
        message += f"Severity: {alert.severity.value.upper()}\n"
        message += f"Time: {alert.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
        message += f"{alert.description}\n"
        
        if alert.recommended_actions:
            message += f"\n📋 Recommended Actions:\n"
            for i, action in enumerate(alert.recommended_actions[:3], 1):
                message += f"{i}. {action}\n"
        
        if alert.recovery_eta:
            message += f"\n⏱️ Estimated Recovery: {alert.recovery_eta.strftime('%H:%M UTC')}\n"
        
        # Prepare NTFY request
        headers = {
            "Title": f"BETTY Alert: {alert.title}",
            "Priority": self._get_ntfy_priority(alert.severity),
            "Tags": f"betty,{alert.component},{alert.severity.value}"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.ntfy_url,
                    data=message.encode('utf-8'),
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        await self.logger.info(
                            "NTFY alert sent successfully",
                            alert_id=alert.alert_id,
                            response_status=response.status
                        )
                    else:
                        await self.logger.error(
                            "NTFY alert failed",
                            alert_id=alert.alert_id,
                            response_status=response.status,
                            response_text=await response.text()
                        )
        
        except Exception as e:
            await self.logger.error(
                "NTFY request failed",
                alert_id=alert.alert_id,
                error=str(e)
            )
    
    def _get_ntfy_priority(self, severity: AlertSeverity) -> str:
        """Map alert severity to NTFY priority"""
        priority_map = {
            AlertSeverity.EMERGENCY: "max",
            AlertSeverity.CRITICAL: "high", 
            AlertSeverity.HIGH: "high",
            AlertSeverity.MEDIUM: "default",
            AlertSeverity.LOW: "low"
        }
        return priority_map.get(severity, "default")
    
    async def _log_alert(self, alert: Alert):
        """Log alert to system logs"""
        log_level = {
            AlertSeverity.EMERGENCY: "critical",
            AlertSeverity.CRITICAL: "critical",
            AlertSeverity.HIGH: "error",
            AlertSeverity.MEDIUM: "warning",
            AlertSeverity.LOW: "info"
        }.get(alert.severity, "info")
        
        # Use the appropriate log level
        if log_level == "critical":
            await self.logger.critical(
                f"ALERT: {alert.title}",
                alert_id=alert.alert_id,
                component=alert.component,
                description=alert.description,
                severity=alert.severity.value,
                recommended_actions=alert.recommended_actions
            )
        elif log_level == "error":
            await self.logger.error(
                f"ALERT: {alert.title}",
                alert_id=alert.alert_id,
                component=alert.component,
                description=alert.description
            )
        else:
            await self.logger.info(
                f"ALERT: {alert.title}",
                alert_id=alert.alert_id,
                component=alert.component,
                description=alert.description
            )
    
    async def resolve_alert(self, alert_id: str, resolution_notes: str = ""):
        """Resolve an active alert"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts.pop(alert_id)
            
            await self.logger.info(
                "Alert resolved",
                alert_id=alert_id,
                title=alert.title,
                resolution_notes=resolution_notes,
                duration_minutes=((datetime.now(timezone.utc) - alert.created_at).total_seconds() / 60)
            )
            
            return True
        
        return False
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts"""
        return list(self.active_alerts.values())
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Get alert summary statistics"""
        active_alerts = list(self.active_alerts.values())
        
        severity_counts = defaultdict(int)
        component_counts = defaultdict(int)
        
        for alert in active_alerts:
            severity_counts[alert.severity.value] += 1
            component_counts[alert.component] += 1
        
        return {
            "active_alerts_count": len(active_alerts),
            "alerts_by_severity": dict(severity_counts),
            "alerts_by_component": dict(component_counts),
            "oldest_alert": min(active_alerts, key=lambda a: a.created_at).created_at.isoformat() if active_alerts else None,
            "most_recent_alert": max(active_alerts, key=lambda a: a.created_at).created_at.isoformat() if active_alerts else None
        }

class ErrorMonitoringService:
    """Main error monitoring service that coordinates analysis and alerting"""
    
    def __init__(self):
        self.logger = get_enhanced_logger(__name__, ComponentType.HEALTH_MONITOR)
        self.trend_analyzer = ErrorTrendAnalyzer()
        self.alert_manager = AlertManager()
        
        # Monitoring configuration
        self.monitoring_enabled = True
        self.analysis_interval_seconds = 60  # Analyze trends every minute
        self.health_check_interval_seconds = 30  # Health checks every 30 seconds
        
        # Background tasks
        self._analysis_task: Optional[asyncio.Task] = None
        self._health_check_task: Optional[asyncio.Task] = None
        
        # System health tracking
        self.last_health_metrics: Optional[SystemHealthMetrics] = None
        self.health_history: deque = deque(maxlen=100)
    
    async def start_monitoring(self):
        """Start background monitoring tasks"""
        if not self.monitoring_enabled:
            return
        
        await self.logger.info("Starting error monitoring service")
        
        # Start trend analysis task
        self._analysis_task = asyncio.create_task(self._trend_analysis_loop())
        
        # Start health check task
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        
        await self.logger.info("Error monitoring service started successfully")
    
    async def stop_monitoring(self):
        """Stop background monitoring tasks"""
        await self.logger.info("Stopping error monitoring service")
        
        if self._analysis_task:
            self._analysis_task.cancel()
        
        if self._health_check_task:
            self._health_check_task.cancel()
        
        # Wait for tasks to complete
        tasks = [t for t in [self._analysis_task, self._health_check_task] if t]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        await self.logger.info("Error monitoring service stopped")
    
    async def report_error(self, classification: ErrorClassification, context: Dict[str, Any]):
        """Report error for monitoring and analysis"""
        if not self.monitoring_enabled:
            return
        
        # Add to trend analysis
        self.trend_analyzer.add_error(classification, context)
        
        # Check if this error should trigger immediate alerts
        await self._check_immediate_alerts(classification, context)
    
    async def _check_immediate_alerts(self, classification: ErrorClassification, context: Dict[str, Any]):
        """Check if error should trigger immediate alerts"""
        
        # Critical errors always trigger alerts
        if classification.severity == ErrorSeverity.CRITICAL:
            await self.alert_manager.create_alert(
                severity=AlertSeverity.CRITICAL,
                title=f"Critical Error: {classification.category.value}",
                description=f"Critical error detected in {context.get('component', 'unknown')} component: {classification.estimated_impact}",
                component=context.get('component', 'unknown'),
                error_pattern=None,
                recommended_actions=[
                    "Check system resources and database connections",
                    "Review error logs for additional context", 
                    "Consider activating incident response procedures"
                ],
                tags={"critical", "immediate", classification.category.value}
            )
        
        # Security events trigger high-priority alerts
        elif classification.category == ErrorCategory.AUTHENTICATION or classification.category == ErrorCategory.AUTHORIZATION:
            await self.alert_manager.create_alert(
                severity=AlertSeverity.HIGH,
                title=f"Security Event: {classification.category.value}",
                description=f"Security-related error in {context.get('component', 'unknown')}: {classification.estimated_impact}",
                component=context.get('component', 'unknown'),
                recommended_actions=[
                    "Review authentication logs",
                    "Check for suspicious activity patterns",
                    "Verify security configuration"
                ],
                tags={"security", classification.category.value}
            )
    
    async def _trend_analysis_loop(self):
        """Background loop for trend analysis"""
        try:
            while self.monitoring_enabled:
                await asyncio.sleep(self.analysis_interval_seconds)
                
                try:
                    # Analyze current trends
                    trend_analysis = self.trend_analyzer.analyze_trends()
                    
                    # Process detected trends
                    for trend in trend_analysis["trends"]:
                        await self._process_trend_alert(trend)
                    
                    # Log analysis summary
                    await self.logger.info(
                        "Trend analysis completed",
                        trends_detected=len(trend_analysis["trends"]),
                        patterns_active=len(trend_analysis["patterns"]),
                        recommendations_generated=len(trend_analysis["recommendations"])
                    )
                
                except Exception as e:
                    await self.logger.error(
                        "Trend analysis failed",
                        error=str(e)
                    )
        
        except asyncio.CancelledError:
            await self.logger.info("Trend analysis loop cancelled")
        except Exception as e:
            await self.logger.error("Trend analysis loop failed", error=str(e))
    
    async def _process_trend_alert(self, trend: Dict[str, Any]):
        """Process detected trend and create alert if necessary"""
        trend_type = trend.get("trend_type")
        severity_str = trend.get("severity", "medium")
        
        # Map string severity to AlertSeverity
        severity_mapping = {
            "low": AlertSeverity.LOW,
            "medium": AlertSeverity.MEDIUM,
            "high": AlertSeverity.HIGH,
            "critical": AlertSeverity.CRITICAL
        }
        severity = severity_mapping.get(severity_str, AlertSeverity.MEDIUM)
        
        # Create appropriate alert based on trend type
        if trend_type == "error_spike":
            await self.alert_manager.create_alert(
                severity=severity,
                title="Error Spike Detected",
                description=trend["description"],
                component="system",
                recommended_actions=trend.get("recommendations", []),
                tags={"trend", "error_spike", "performance"}
            )
        
        elif trend_type == "gradual_increase":
            await self.alert_manager.create_alert(
                severity=severity,
                title="Gradual Error Rate Increase",
                description=trend["description"],
                component="system",
                recommended_actions=trend.get("recommendations", []),
                tags={"trend", "gradual_increase", "performance"}
            )
        
        elif trend_type == "component_pattern":
            await self.alert_manager.create_alert(
                severity=severity,
                title=f"Component Error Pattern: {trend['component']}",
                description=trend["description"],
                component=trend["component"],
                recommended_actions=trend.get("recommendations", []),
                tags={"trend", "component_pattern", trend["component"]}
            )
    
    async def _health_check_loop(self):
        """Background loop for system health monitoring"""
        try:
            while self.monitoring_enabled:
                await asyncio.sleep(self.health_check_interval_seconds)
                
                try:
                    # Gather system health metrics
                    health_metrics = await self._gather_health_metrics()
                    
                    # Store health metrics
                    self.last_health_metrics = health_metrics
                    self.health_history.append(health_metrics)
                    
                    # Check for health-based alerts
                    await self._check_health_alerts(health_metrics)
                
                except Exception as e:
                    await self.logger.error(
                        "Health check failed",
                        error=str(e)
                    )
        
        except asyncio.CancelledError:
            await self.logger.info("Health check loop cancelled")
        except Exception as e:
            await self.logger.error("Health check loop failed", error=str(e))
    
    async def _gather_health_metrics(self) -> SystemHealthMetrics:
        """Gather current system health metrics"""
        import psutil
        
        # Get system metrics
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Calculate error rate from recent errors
        now = datetime.now(timezone.utc)
        last_minute = now - timedelta(minutes=1)
        recent_errors = [
            error for error in self.trend_analyzer.error_history 
            if error["timestamp"] > last_minute
        ]
        error_rate = len(recent_errors)
        
        # Calculate average response time (simplified)
        # In a real implementation, this would come from actual request metrics
        avg_response_time = 250.0  # Placeholder
        
        # Database health (simplified)
        database_health = {
            "postgresql": "healthy",
            "neo4j": "healthy", 
            "qdrant": "healthy",
            "redis": "healthy"
        }
        
        # Calculate overall health score
        health_score = self._calculate_health_score(
            error_rate, avg_response_time, memory.percent, cpu_percent
        )
        
        return SystemHealthMetrics(
            timestamp=now,
            overall_health_score=health_score,
            error_rate_per_minute=error_rate,
            avg_response_time_ms=avg_response_time,
            memory_usage_percent=memory.percent,
            cpu_usage_percent=cpu_percent,
            database_health=database_health,
            active_incidents=len(self.alert_manager.active_alerts)
        )
    
    def _calculate_health_score(self, error_rate: float, response_time: float, 
                              memory_percent: float, cpu_percent: float) -> float:
        """Calculate overall system health score (0-100)"""
        score = 100.0
        
        # Penalize high error rates
        if error_rate > 0:
            score -= min(error_rate * 2, 30)  # Max 30 point penalty
        
        # Penalize slow response times
        if response_time > 1000:  # Over 1 second
            score -= min((response_time - 1000) / 100, 20)  # Max 20 point penalty
        
        # Penalize high memory usage
        if memory_percent > 80:
            score -= (memory_percent - 80) * 2  # 2 points per percent over 80%
        
        # Penalize high CPU usage
        if cpu_percent > 80:
            score -= (cpu_percent - 80) * 1.5  # 1.5 points per percent over 80%
        
        return max(0.0, score)
    
    async def _check_health_alerts(self, health_metrics: SystemHealthMetrics):
        """Check if current health metrics warrant alerts"""
        
        # Critical health score
        if health_metrics.overall_health_score < 50:
            await self.alert_manager.create_alert(
                severity=AlertSeverity.CRITICAL,
                title="System Health Critical",
                description=f"Overall system health score dropped to {health_metrics.overall_health_score:.1f}%",
                component="system",
                health_metrics=health_metrics,
                recommended_actions=[
                    "Check system resources (CPU, Memory, Disk)",
                    "Review error logs for patterns",
                    "Consider scaling system resources"
                ],
                tags={"health", "critical", "system"}
            )
        
        # High error rate
        elif health_metrics.error_rate_per_minute > 15:
            await self.alert_manager.create_alert(
                severity=AlertSeverity.HIGH,
                title="High Error Rate Detected",
                description=f"Error rate: {health_metrics.error_rate_per_minute} errors/minute",
                component="system",
                health_metrics=health_metrics,
                recommended_actions=[
                    "Investigate error patterns and root causes",
                    "Check database and service health",
                    "Review recent deployments"
                ],
                tags={"health", "error_rate", "performance"}
            )
        
        # High memory usage
        elif health_metrics.memory_usage_percent > 95:
            await self.alert_manager.create_alert(
                severity=AlertSeverity.HIGH,
                title="Critical Memory Usage",
                description=f"Memory usage: {health_metrics.memory_usage_percent:.1f}%",
                component="system",
                health_metrics=health_metrics,
                recommended_actions=[
                    "Check for memory leaks",
                    "Review application memory usage",
                    "Consider adding more memory or restarting services"
                ],
                tags={"health", "memory", "resources"}
            )
    
    # Public API methods
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get current service status"""
        return {
            "monitoring_enabled": self.monitoring_enabled,
            "analysis_interval_seconds": self.analysis_interval_seconds,
            "health_check_interval_seconds": self.health_check_interval_seconds,
            "trend_analyzer": {
                "error_history_count": len(self.trend_analyzer.error_history),
                "patterns_tracked": len(self.trend_analyzer.pattern_cache)
            },
            "alert_manager": self.alert_manager.get_alert_summary(),
            "last_health_metrics": asdict(self.last_health_metrics) if self.last_health_metrics else None,
            "background_tasks": {
                "trend_analysis_running": self._analysis_task is not None and not self._analysis_task.done(),
                "health_check_running": self._health_check_task is not None and not self._health_check_task.done()
            }
        }
    
    def get_trend_analysis(self) -> Dict[str, Any]:
        """Get current trend analysis"""
        return self.trend_analyzer.analyze_trends()
    
    def get_health_metrics(self) -> Optional[SystemHealthMetrics]:
        """Get latest health metrics"""
        return self.last_health_metrics
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts"""
        return self.alert_manager.get_active_alerts()

# Global service instance
_monitoring_service: Optional[ErrorMonitoringService] = None

def get_monitoring_service() -> ErrorMonitoringService:
    """Get global error monitoring service instance"""
    global _monitoring_service
    if _monitoring_service is None:
        _monitoring_service = ErrorMonitoringService()
    return _monitoring_service