# ABOUTME: Enhanced structured logging framework for Betty Memory System  
# ABOUTME: Provides high-performance logging with real-time analysis and pattern detection

import asyncio
import json
import time
import os
import gzip
import re
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field, asdict
from collections import defaultdict, deque
import threading
from concurrent.futures import ThreadPoolExecutor
import structlog
from structlog.stdlib import LoggerFactory
import logging
from logging.handlers import RotatingFileHandler
import psutil

# API call logging decorator for compatibility
def log_api_call(func):
    """Decorator to log API calls for tracking and analysis"""
    def wrapper(*args, **kwargs):
        logger = structlog.get_logger(__name__)
        logger.info("API call", 
                    endpoint=func.__name__, 
                    method="POST",  # Default for most endpoints
                    args_count=len(args),
                    kwargs_keys=list(kwargs.keys()))
        return func(*args, **kwargs)
    return wrapper
import hashlib

logger = structlog.get_logger(__name__)

class LogLevel(Enum):
    """Enhanced log levels"""
    DEBUG = "debug"
    INFO = "info" 
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    SECURITY = "security"      # Security events
    PERFORMANCE = "performance" # Performance metrics
    AUDIT = "audit"            # Audit trail events

class ComponentType(Enum):
    """System components for logging context"""
    API_GATEWAY = "api_gateway"
    DATABASE = "database"
    MEMORY_ENGINE = "memory_engine"
    AUTH_SERVICE = "auth_service"
    VECTOR_STORE = "vector_store"
    GRAPH_DATABASE = "graph_database"
    CACHE_LAYER = "cache_layer"
    AGENT_SYSTEM = "agent_system"
    INGESTION_PIPELINE = "ingestion_pipeline"
    SEARCH_SERVICE = "search_service"
    ANALYTICS_ENGINE = "analytics_engine"
    HEALTH_MONITOR = "health_monitor"

class DatabaseOperation(Enum):
    """Database operation types"""
    SELECT = "select"
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    TRANSACTION_BEGIN = "transaction_begin"
    TRANSACTION_COMMIT = "transaction_commit"
    TRANSACTION_ROLLBACK = "transaction_rollback"
    SCHEMA_MIGRATION = "schema_migration"
    INDEX_CREATION = "index_creation"
    VACUUM = "vacuum"
    BACKUP = "backup"
    RESTORE = "restore"

@dataclass
class LogEntry:
    """Structured log entry with comprehensive metadata"""
    timestamp: datetime
    level: LogLevel
    component: ComponentType
    message: str
    logger_name: str
    
    # Context information
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    project_id: Optional[str] = None
    
    # Performance metrics
    duration_ms: Optional[float] = None
    memory_usage_mb: Optional[float] = None
    cpu_usage_percent: Optional[float] = None
    
    # Database information
    database_type: Optional[str] = None
    operation_type: Optional[DatabaseOperation] = None
    affected_rows: Optional[int] = None
    query_hash: Optional[str] = None
    
    # API information
    endpoint: Optional[str] = None
    method: Optional[str] = None
    status_code: Optional[int] = None
    response_size_bytes: Optional[int] = None
    
    # Error information
    error_type: Optional[str] = None
    error_id: Optional[str] = None
    stack_trace: Optional[str] = None
    
    # Security information
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    auth_method: Optional[str] = None
    permission_check: Optional[str] = None
    
    # Custom fields
    extra_fields: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)

@dataclass
class RequestInfo:
    """Information about HTTP requests for logging"""
    request_id: str
    method: str
    endpoint: str
    user_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)
    query_params: Dict[str, str] = field(default_factory=dict)
    body_size_bytes: Optional[int] = None
    started_at: Optional[datetime] = None

@dataclass
class DatabaseOperationInfo:
    """Information about database operations for logging"""
    operation_id: str
    database_type: str
    operation: DatabaseOperation
    table_name: Optional[str] = None
    query: Optional[str] = None
    query_hash: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    affected_rows: Optional[int] = None
    duration_ms: Optional[float] = None
    connection_id: Optional[str] = None
    transaction_id: Optional[str] = None

@dataclass
class AgentActivity:
    """Information about agent activities for logging"""
    agent_id: str
    agent_type: str
    activity_type: str
    task_description: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str = "running"
    result: Optional[str] = None
    error_message: Optional[str] = None
    resources_used: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PerformanceMetrics:
    """Performance metrics for logging"""
    metric_name: str
    value: float
    unit: str
    timestamp: datetime
    component: ComponentType
    context: Dict[str, Any] = field(default_factory=dict)
    threshold_warning: Optional[float] = None
    threshold_critical: Optional[float] = None

@dataclass 
class SecurityEvent:
    """Security event information for logging"""
    event_type: str
    severity: str
    user_id: Optional[str] = None
    ip_address: Optional[str] = None
    resource_accessed: Optional[str] = None
    action_attempted: Optional[str] = None
    success: bool = False
    threat_indicators: List[str] = field(default_factory=list)
    additional_context: Dict[str, Any] = field(default_factory=dict)

class LogAnalyzer:
    """Real-time log analysis and pattern detection"""
    
    def __init__(self):
        self.pattern_detectors: Dict[str, Callable] = {}
        self.alert_rules: List[Dict[str, Any]] = []
        self.metrics_cache = defaultdict(deque)
        self.pattern_cache = defaultdict(int)
        self.analysis_window_minutes = 15
        self._initialize_pattern_detectors()
        self._initialize_alert_rules()
    
    def _initialize_pattern_detectors(self):
        """Initialize pattern detection rules"""
        self.pattern_detectors.update({
            "error_spike": self._detect_error_spike,
            "performance_degradation": self._detect_performance_degradation,
            "security_anomaly": self._detect_security_anomaly,
            "database_issues": self._detect_database_issues,
            "memory_leaks": self._detect_memory_leaks,
            "auth_failures": self._detect_auth_failures
        })
    
    def _initialize_alert_rules(self):
        """Initialize alerting rules"""
        self.alert_rules = [
            {
                "name": "high_error_rate",
                "condition": lambda metrics: metrics.get("error_rate_per_minute", 0) > 10,
                "severity": "high",
                "description": "Error rate exceeds 10 errors per minute"
            },
            {
                "name": "slow_response_time",
                "condition": lambda metrics: metrics.get("avg_response_time_ms", 0) > 5000,
                "severity": "medium", 
                "description": "Average response time exceeds 5 seconds"
            },
            {
                "name": "memory_usage_high",
                "condition": lambda metrics: metrics.get("memory_usage_percent", 0) > 90,
                "severity": "high",
                "description": "Memory usage exceeds 90%"
            },
            {
                "name": "database_connection_failures",
                "condition": lambda metrics: metrics.get("db_connection_failures", 0) > 5,
                "severity": "critical",
                "description": "Database connection failures exceed threshold"
            },
            {
                "name": "security_violations",
                "condition": lambda metrics: metrics.get("security_violations", 0) > 0,
                "severity": "critical",
                "description": "Security violations detected"
            }
        ]
    
    async def analyze_log_entry(self, log_entry: LogEntry) -> Dict[str, Any]:
        """Analyze individual log entry for patterns"""
        analysis_results = {
            "patterns_detected": [],
            "anomalies": [],
            "performance_issues": [],
            "security_concerns": [],
            "recommendations": []
        }
        
        # Update metrics cache
        self._update_metrics_cache(log_entry)
        
        # Run pattern detectors
        for pattern_name, detector_func in self.pattern_detectors.items():
            try:
                pattern_result = await detector_func(log_entry)
                if pattern_result:
                    analysis_results["patterns_detected"].append({
                        "pattern": pattern_name,
                        "result": pattern_result,
                        "timestamp": log_entry.timestamp
                    })
            except Exception as e:
                logger.error("Pattern detector failed", 
                           pattern=pattern_name, error=str(e))
        
        # Check alert rules
        current_metrics = self._get_current_metrics()
        for rule in self.alert_rules:
            try:
                if rule["condition"](current_metrics):
                    analysis_results["anomalies"].append({
                        "rule": rule["name"],
                        "severity": rule["severity"],
                        "description": rule["description"],
                        "metrics": current_metrics,
                        "timestamp": log_entry.timestamp
                    })
            except Exception as e:
                logger.error("Alert rule evaluation failed",
                           rule=rule["name"], error=str(e))
        
        return analysis_results
    
    def _update_metrics_cache(self, log_entry: LogEntry):
        """Update metrics cache with new log entry"""
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(minutes=self.analysis_window_minutes)
        
        # Clean old entries
        for metric_type in self.metrics_cache:
            while (self.metrics_cache[metric_type] and 
                   self.metrics_cache[metric_type][0][0] < window_start):
                self.metrics_cache[metric_type].popleft()
        
        # Add new metrics
        if log_entry.level == LogLevel.ERROR:
            self.metrics_cache["errors"].append((now, log_entry))
        
        if log_entry.duration_ms is not None:
            self.metrics_cache["response_times"].append((now, log_entry.duration_ms))
        
        if log_entry.memory_usage_mb is not None:
            self.metrics_cache["memory_usage"].append((now, log_entry.memory_usage_mb))
        
        if log_entry.database_type:
            self.metrics_cache["database_operations"].append((now, log_entry))
        
        if log_entry.level == LogLevel.SECURITY:
            self.metrics_cache["security_events"].append((now, log_entry))
    
    def _get_current_metrics(self) -> Dict[str, float]:
        """Get current aggregated metrics"""
        metrics = {}
        
        # Error rate per minute
        error_count = len(self.metrics_cache["errors"])
        metrics["error_rate_per_minute"] = error_count / self.analysis_window_minutes
        
        # Average response time
        if self.metrics_cache["response_times"]:
            response_times = [rt[1] for rt in self.metrics_cache["response_times"]]
            metrics["avg_response_time_ms"] = sum(response_times) / len(response_times)
        else:
            metrics["avg_response_time_ms"] = 0
        
        # Memory usage
        if self.metrics_cache["memory_usage"]:
            latest_memory = self.metrics_cache["memory_usage"][-1][1]
            metrics["memory_usage_percent"] = (latest_memory / 1024) * 100  # Rough estimate
        else:
            metrics["memory_usage_percent"] = 0
        
        # Database connection failures
        db_failures = sum(1 for _, entry in self.metrics_cache["database_operations"]
                         if entry.error_type and "connection" in entry.error_type.lower())
        metrics["db_connection_failures"] = db_failures
        
        # Security violations
        security_violations = len(self.metrics_cache["security_events"])
        metrics["security_violations"] = security_violations
        
        return metrics
    
    async def _detect_error_spike(self, log_entry: LogEntry) -> Optional[Dict[str, Any]]:
        """Detect error spikes"""
        if log_entry.level != LogLevel.ERROR:
            return None
        
        error_count = len(self.metrics_cache["errors"])
        if error_count > 20:  # More than 20 errors in 15 minutes
            return {
                "type": "error_spike",
                "error_count": error_count,
                "window_minutes": self.analysis_window_minutes,
                "severity": "high"
            }
        return None
    
    async def _detect_performance_degradation(self, log_entry: LogEntry) -> Optional[Dict[str, Any]]:
        """Detect performance degradation"""
        if log_entry.duration_ms is None or log_entry.duration_ms < 1000:
            return None
        
        # Check if this is part of a pattern of slow requests
        recent_slow = sum(1 for _, rt in self.metrics_cache["response_times"]
                         if rt > 2000)
        
        if recent_slow > 10:  # More than 10 slow requests
            return {
                "type": "performance_degradation",
                "slow_request_count": recent_slow,
                "current_duration_ms": log_entry.duration_ms,
                "severity": "medium"
            }
        return None
    
    async def _detect_security_anomaly(self, log_entry: LogEntry) -> Optional[Dict[str, Any]]:
        """Detect security anomalies"""
        if log_entry.level != LogLevel.SECURITY:
            return None
        
        # Always flag security events as potential anomalies
        return {
            "type": "security_anomaly",
            "event_type": log_entry.error_type or "unknown",
            "ip_address": log_entry.ip_address,
            "user_id": log_entry.user_id,
            "severity": "high"
        }
    
    async def _detect_database_issues(self, log_entry: LogEntry) -> Optional[Dict[str, Any]]:
        """Detect database issues"""
        if not log_entry.database_type:
            return None
        
        db_errors = sum(1 for _, entry in self.metrics_cache["database_operations"]
                       if entry.error_type)
        
        if db_errors > 5:
            return {
                "type": "database_issues",
                "database_type": log_entry.database_type,
                "error_count": db_errors,
                "severity": "high"
            }
        return None
    
    async def _detect_memory_leaks(self, log_entry: LogEntry) -> Optional[Dict[str, Any]]:
        """Detect potential memory leaks"""
        if log_entry.memory_usage_mb is None:
            return None
        
        # Check for continuously increasing memory usage
        if len(self.metrics_cache["memory_usage"]) > 5:
            recent_memory = [mem[1] for mem in list(self.metrics_cache["memory_usage"])[-5:]]
            if all(recent_memory[i] < recent_memory[i+1] for i in range(len(recent_memory)-1)):
                return {
                    "type": "memory_leak",
                    "current_usage_mb": log_entry.memory_usage_mb,
                    "trend": "increasing",
                    "severity": "medium"
                }
        return None
    
    async def _detect_auth_failures(self, log_entry: LogEntry) -> Optional[Dict[str, Any]]:
        """Detect authentication failure patterns"""
        if log_entry.status_code != 401 and log_entry.error_type != "AuthenticationError":
            return None
        
        # Count auth failures from same IP
        ip_failures = sum(1 for _, entry in self.metrics_cache["errors"]
                         if (entry.ip_address == log_entry.ip_address and 
                             (entry.status_code == 401 or entry.error_type == "AuthenticationError")))
        
        if ip_failures > 5:
            return {
                "type": "auth_failure_spike",
                "ip_address": log_entry.ip_address,
                "failure_count": ip_failures,
                "severity": "high"
            }
        return None

class EnhancedStructuredLogger:
    """Enhanced structured logger with real-time analysis"""
    
    def __init__(self, logger_name: str, component: ComponentType):
        self.logger_name = logger_name
        self.component = component
        self.base_logger = structlog.get_logger(logger_name)
        self.analyzer = LogAnalyzer()
        self.executor = ThreadPoolExecutor(max_workers=2)
        
        # Performance monitoring
        self._start_time = time.time()
        self._request_count = 0
        self._error_count = 0
        
        # Log file handling
        self.log_dir = "/var/log/betty/"
        self._ensure_log_directory()
        self._setup_file_handlers()
    
    def _ensure_log_directory(self):
        """Ensure log directory exists"""
        try:
            os.makedirs(self.log_dir, exist_ok=True)
        except Exception as e:
            logger.error("Failed to create log directory", error=str(e))
    
    def _setup_file_handlers(self):
        """Setup file handlers for different log types"""
        # Main application log
        self.app_handler = RotatingFileHandler(
            f"{self.log_dir}betty-app.log",
            maxBytes=100*1024*1024,  # 100MB
            backupCount=10
        )
        
        # Error log
        self.error_handler = RotatingFileHandler(
            f"{self.log_dir}betty-errors.log",
            maxBytes=50*1024*1024,   # 50MB
            backupCount=20
        )
        
        # Performance log
        self.performance_handler = RotatingFileHandler(
            f"{self.log_dir}betty-performance.log",
            maxBytes=50*1024*1024,   # 50MB
            backupCount=10
        )
        
        # Security log
        self.security_handler = RotatingFileHandler(
            f"{self.log_dir}betty-security.log",
            maxBytes=100*1024*1024,  # 100MB
            backupCount=50  # Keep more security logs
        )
    
    async def log(self, level: LogLevel, message: str, **kwargs) -> None:
        """Enhanced logging method with analysis"""
        timestamp = datetime.now(timezone.utc)
        
        # Create comprehensive log entry
        log_entry = LogEntry(
            timestamp=timestamp,
            level=level,
            component=self.component,
            message=message,
            logger_name=self.logger_name,
            **kwargs
        )
        
        # Log to appropriate handlers
        await self._write_to_handlers(log_entry)
        
        # Real-time analysis (async)
        if level in [LogLevel.ERROR, LogLevel.CRITICAL, LogLevel.SECURITY]:
            asyncio.create_task(self._analyze_log_entry(log_entry))
        
        # Update internal metrics
        self._update_internal_metrics(log_entry)
    
    async def _write_to_handlers(self, log_entry: LogEntry):
        """Write log entry to appropriate file handlers"""
        log_data = asdict(log_entry)
        
        # Convert datetime to ISO string
        if isinstance(log_data.get('timestamp'), datetime):
            log_data['timestamp'] = log_data['timestamp'].isoformat()
        
        # Convert enums to values
        log_data['level'] = log_entry.level.value
        log_data['component'] = log_entry.component.value
        
        json_log = json.dumps(log_data, default=str)
        
        # Write to main app log
        self.app_handler.emit(logging.LogRecord(
            name=self.logger_name,
            level=getattr(logging, log_entry.level.value.upper(), logging.INFO),
            pathname="",
            lineno=0,
            msg=json_log,
            args=(),
            exc_info=None
        ))
        
        # Write to specific logs based on level
        if log_entry.level in [LogLevel.ERROR, LogLevel.CRITICAL]:
            self.error_handler.emit(logging.LogRecord(
                name=self.logger_name,
                level=logging.ERROR,
                pathname="",
                lineno=0,
                msg=json_log,
                args=(),
                exc_info=None
            ))
        
        if log_entry.level == LogLevel.PERFORMANCE:
            self.performance_handler.emit(logging.LogRecord(
                name=self.logger_name,
                level=logging.INFO,
                pathname="",
                lineno=0,
                msg=json_log,
                args=(),
                exc_info=None
            ))
        
        if log_entry.level == LogLevel.SECURITY:
            self.security_handler.emit(logging.LogRecord(
                name=self.logger_name,
                level=logging.WARNING,
                pathname="",
                lineno=0,
                msg=json_log,
                args=(),
                exc_info=None
            ))
    
    async def _analyze_log_entry(self, log_entry: LogEntry):
        """Perform real-time analysis on log entry"""
        try:
            analysis_result = await self.analyzer.analyze_log_entry(log_entry)
            
            # Handle analysis results
            if analysis_result["anomalies"]:
                await self._handle_anomalies(analysis_result["anomalies"], log_entry)
            
            if analysis_result["patterns_detected"]:
                await self._handle_patterns(analysis_result["patterns_detected"], log_entry)
            
        except Exception as e:
            logger.error("Log analysis failed", error=str(e))
    
    async def _handle_anomalies(self, anomalies: List[Dict[str, Any]], log_entry: LogEntry):
        """Handle detected anomalies"""
        for anomaly in anomalies:
            severity = anomaly.get("severity", "medium")
            
            # Log the anomaly
            logger.warning("Anomaly detected",
                         anomaly_type=anomaly["rule"],
                         severity=severity,
                         description=anomaly["description"],
                         original_log_id=log_entry.request_id)
            
            # Send critical anomalies to notification system
            if severity == "critical":
                await self._send_critical_alert(anomaly, log_entry)
    
    async def _handle_patterns(self, patterns: List[Dict[str, Any]], log_entry: LogEntry):
        """Handle detected patterns"""
        for pattern in patterns:
            logger.info("Pattern detected",
                       pattern_type=pattern["pattern"],
                       details=pattern["result"],
                       original_log_id=log_entry.request_id)
    
    async def _send_critical_alert(self, anomaly: Dict[str, Any], log_entry: LogEntry):
        """Send critical alert to notification systems"""
        # This would integrate with NTFY or other notification systems
        alert_message = (f"BETTY CRITICAL ALERT: {anomaly['description']} - "
                        f"Component: {self.component.value} - "
                        f"Time: {log_entry.timestamp.isoformat()}")
        
        logger.critical("Critical alert generated",
                       alert=alert_message,
                       anomaly=anomaly,
                       log_entry_id=log_entry.request_id)
    
    def _update_internal_metrics(self, log_entry: LogEntry):
        """Update internal performance metrics"""
        self._request_count += 1
        
        if log_entry.level in [LogLevel.ERROR, LogLevel.CRITICAL]:
            self._error_count += 1
    
    # Convenience methods for different log types
    
    async def info(self, message: str, **kwargs) -> None:
        """Log info message"""
        await self.log(LogLevel.INFO, message, **kwargs)
    
    async def error(self, message: str, **kwargs) -> None:
        """Log error message"""
        await self.log(LogLevel.ERROR, message, **kwargs)
    
    async def warning(self, message: str, **kwargs) -> None:
        """Log warning message"""
        await self.log(LogLevel.WARNING, message, **kwargs)
    
    async def critical(self, message: str, **kwargs) -> None:
        """Log critical message"""
        await self.log(LogLevel.CRITICAL, message, **kwargs)
    
    async def security(self, message: str, **kwargs) -> None:
        """Log security event"""
        await self.log(LogLevel.SECURITY, message, **kwargs)
    
    async def performance(self, message: str, **kwargs) -> None:
        """Log performance metrics"""
        await self.log(LogLevel.PERFORMANCE, message, **kwargs)
    
    async def audit(self, message: str, **kwargs) -> None:
        """Log audit event"""
        await self.log(LogLevel.AUDIT, message, **kwargs)
    
    # Specialized logging methods
    
    async def log_api_request(self, request_info: RequestInfo, 
                            status_code: int = None, 
                            duration_ms: float = None,
                            response_size_bytes: int = None,
                            error: Exception = None) -> None:
        """Log API request with comprehensive information"""
        
        level = LogLevel.INFO
        message = f"API request: {request_info.method} {request_info.endpoint}"
        
        if error:
            level = LogLevel.ERROR
            message = f"API request failed: {request_info.method} {request_info.endpoint}"
        elif status_code and status_code >= 500:
            level = LogLevel.ERROR
        elif status_code and status_code >= 400:
            level = LogLevel.WARNING
        
        await self.log(
            level=level,
            message=message,
            request_id=request_info.request_id,
            method=request_info.method,
            endpoint=request_info.endpoint,
            status_code=status_code,
            duration_ms=duration_ms,
            response_size_bytes=response_size_bytes,
            user_id=request_info.user_id,
            ip_address=request_info.ip_address,
            user_agent=request_info.user_agent,
            error_type=type(error).__name__ if error else None,
            stack_trace=str(error) if error else None
        )
    
    async def log_database_operation(self, db_info: DatabaseOperationInfo,
                                   error: Exception = None) -> None:
        """Log database operation with performance metrics"""
        
        level = LogLevel.INFO
        message = f"Database operation: {db_info.operation.value}"
        
        if error:
            level = LogLevel.ERROR
            message = f"Database operation failed: {db_info.operation.value}"
        elif db_info.duration_ms and db_info.duration_ms > 1000:
            level = LogLevel.WARNING
            message = f"Slow database operation: {db_info.operation.value}"
        
        # Hash sensitive query for logging
        query_hash = None
        if db_info.query:
            query_hash = hashlib.sha256(db_info.query.encode()).hexdigest()[:16]
        
        await self.log(
            level=level,
            message=message,
            database_type=db_info.database_type,
            operation_type=db_info.operation,
            table_name=db_info.table_name,
            query_hash=query_hash,
            affected_rows=db_info.affected_rows,
            duration_ms=db_info.duration_ms,
            connection_id=db_info.connection_id,
            transaction_id=db_info.transaction_id,
            error_type=type(error).__name__ if error else None,
            stack_trace=str(error) if error else None
        )
    
    async def log_agent_activity(self, activity: AgentActivity) -> None:
        """Log agent activity with status tracking"""
        
        if activity.status == "completed":
            level = LogLevel.INFO
            message = f"Agent activity completed: {activity.activity_type}"
        elif activity.status == "failed":
            level = LogLevel.ERROR
            message = f"Agent activity failed: {activity.activity_type}"
        else:
            level = LogLevel.INFO
            message = f"Agent activity {activity.status}: {activity.activity_type}"
        
        duration_ms = None
        if activity.completed_at and activity.started_at:
            duration_ms = (activity.completed_at - activity.started_at).total_seconds() * 1000
        
        await self.log(
            level=level,
            message=message,
            request_id=activity.agent_id,
            duration_ms=duration_ms,
            extra_fields={
                "agent_id": activity.agent_id,
                "agent_type": activity.agent_type,
                "task_description": activity.task_description,
                "activity_status": activity.status,
                "result": activity.result,
                "resources_used": activity.resources_used
            },
            error_type="AgentError" if activity.status == "failed" else None,
            stack_trace=activity.error_message
        )
    
    async def log_performance_metrics(self, metrics: PerformanceMetrics) -> None:
        """Log performance metrics with threshold checking"""
        
        level = LogLevel.PERFORMANCE
        message = f"Performance metric: {metrics.metric_name} = {metrics.value} {metrics.unit}"
        
        # Check thresholds
        if metrics.threshold_critical and metrics.value >= metrics.threshold_critical:
            level = LogLevel.CRITICAL
            message = f"CRITICAL: {message} (threshold: {metrics.threshold_critical})"
        elif metrics.threshold_warning and metrics.value >= metrics.threshold_warning:
            level = LogLevel.WARNING
            message = f"WARNING: {message} (threshold: {metrics.threshold_warning})"
        
        await self.log(
            level=level,
            message=message,
            extra_fields={
                "metric_name": metrics.metric_name,
                "metric_value": metrics.value,
                "metric_unit": metrics.unit,
                "component": metrics.component.value,
                "context": metrics.context,
                "threshold_warning": metrics.threshold_warning,
                "threshold_critical": metrics.threshold_critical
            }
        )
    
    async def log_security_event(self, event: SecurityEvent) -> None:
        """Log security event with comprehensive context"""
        
        message = f"Security event: {event.event_type}"
        
        if not event.success and event.threat_indicators:
            message = f"SECURITY THREAT: {event.event_type} - {', '.join(event.threat_indicators)}"
        
        await self.log(
            level=LogLevel.SECURITY,
            message=message,
            user_id=event.user_id,
            ip_address=event.ip_address,
            extra_fields={
                "event_type": event.event_type,
                "severity": event.severity,
                "resource_accessed": event.resource_accessed,
                "action_attempted": event.action_attempted,
                "success": event.success,
                "threat_indicators": event.threat_indicators,
                "additional_context": event.additional_context
            }
        )
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary for this logger"""
        uptime_seconds = time.time() - self._start_time
        uptime_hours = uptime_seconds / 3600
        
        return {
            "logger_name": self.logger_name,
            "component": self.component.value,
            "uptime_hours": round(uptime_hours, 2),
            "total_requests": self._request_count,
            "error_count": self._error_count,
            "error_rate_percent": (self._error_count / max(1, self._request_count)) * 100,
            "requests_per_hour": self._request_count / max(0.1, uptime_hours),
            "system_metrics": {
                "memory_usage_mb": psutil.Process().memory_info().rss / 1024 / 1024,
                "cpu_percent": psutil.Process().cpu_percent()
            }
        }

# Global logger registry
_logger_registry: Dict[str, EnhancedStructuredLogger] = {}

def get_enhanced_logger(logger_name: str, component: ComponentType) -> EnhancedStructuredLogger:
    """Get or create an enhanced structured logger"""
    global _logger_registry
    
    key = f"{logger_name}:{component.value}"
    if key not in _logger_registry:
        _logger_registry[key] = EnhancedStructuredLogger(logger_name, component)
    
    return _logger_registry[key]

def configure_enhanced_logging(log_level: str = "INFO") -> None:
    """Configure enhanced structured logging system"""
    
    # Configure structlog with enhanced processors
    structlog.configure(
        processors=[
            # Add log level and timestamp
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            # Enhanced JSON formatter
            structlog.processors.JSONRenderer(sort_keys=True)
        ],
        context_class=dict,
        logger_factory=LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, log_level.upper()),
        handlers=[]  # We handle file output through our custom handlers
    )
    
    # Set specific logger levels
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)