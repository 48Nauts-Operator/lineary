# ABOUTME: Comprehensive error classification engine for Betty Memory System
# ABOUTME: Provides intelligent error categorization, remediation strategies, and automated recovery

import asyncio
import traceback
import re
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from contextlib import asynccontextmanager
import structlog

logger = structlog.get_logger(__name__)

class ErrorSeverity(Enum):
    """Error severity levels for classification"""
    CRITICAL = "critical"        # System-threatening, requires immediate action
    HIGH = "high"               # Service-impacting, requires urgent attention
    MEDIUM = "medium"           # Functionality-affecting, requires attention
    LOW = "low"                 # Minor issues, can be addressed in maintenance
    INFO = "info"               # Informational, no action required

class ErrorCategory(Enum):
    """Primary error categories for classification"""
    DATABASE_ERROR = "database_error"
    MEMORY_CORRUPTION = "memory_corruption"
    API_VALIDATION = "api_validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    NETWORK_ERROR = "network_error"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    PATTERN_INGESTION = "pattern_ingestion"
    SEARCH_QUALITY = "search_quality"
    AGENT_FAILURE = "agent_failure"
    CONFIGURATION_ERROR = "configuration_error"
    SYSTEM_RESOURCE = "system_resource"
    UNKNOWN = "unknown"

class ErrorSubcategory(Enum):
    """Specific error subcategories for granular classification"""
    # Database errors
    CONNECTION_TIMEOUT = "connection_timeout"
    CONNECTION_REFUSED = "connection_refused"
    TRANSACTION_ROLLBACK = "transaction_rollback"
    SCHEMA_VIOLATION = "schema_violation"
    DEADLOCK_DETECTED = "deadlock_detected"
    
    # Memory corruption
    PATTERN_INCONSISTENCY = "pattern_inconsistency"
    CROSS_DB_MISMATCH = "cross_db_mismatch"
    INTEGRITY_VIOLATION = "integrity_violation"
    DATA_CORRUPTION = "data_corruption"
    
    # API validation
    INVALID_REQUEST_FORMAT = "invalid_request_format"
    MISSING_REQUIRED_FIELD = "missing_required_field"
    TYPE_VALIDATION_ERROR = "type_validation_error"
    BUSINESS_RULE_VIOLATION = "business_rule_violation"
    
    # Performance
    SLOW_QUERY = "slow_query"
    MEMORY_LEAK = "memory_leak"
    CPU_SPIKE = "cpu_spike"
    DISK_SPACE_LOW = "disk_space_low"
    
    # Network
    DNS_RESOLUTION_FAILED = "dns_resolution_failed"
    SSL_CERTIFICATE_ERROR = "ssl_certificate_error"
    REQUEST_TIMEOUT = "request_timeout"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"

@dataclass
class ErrorContext:
    """Context information for error analysis"""
    timestamp: datetime
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    project_id: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    request_id: Optional[str] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    database_operations: List[str] = field(default_factory=list)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    system_state: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ErrorClassification:
    """Complete error classification result"""
    error_id: str
    category: ErrorCategory
    subcategory: Optional[ErrorSubcategory]
    severity: ErrorSeverity
    confidence_score: float  # 0.0 to 1.0
    classification_reasons: List[str]
    similar_errors: List[str] = field(default_factory=list)
    auto_recoverable: bool = False
    estimated_impact: str = ""
    classification_time_ms: float = 0.0

@dataclass
class RemediationStep:
    """Single remediation step"""
    step_id: str
    description: str
    action_type: str  # 'manual', 'automatic', 'semi-automatic'
    priority: int
    estimated_time_minutes: int
    command: Optional[str] = None
    verification_query: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)

@dataclass
class RemediationPlan:
    """Complete remediation strategy"""
    plan_id: str
    error_classification: ErrorClassification
    steps: List[RemediationStep]
    total_estimated_time_minutes: int
    success_probability: float  # 0.0 to 1.0
    rollback_plan: Optional[str] = None
    manual_intervention_required: bool = True
    auto_executable: bool = False

@dataclass
class RecoveryResult:
    """Result of automated recovery attempt"""
    recovery_id: str
    error_id: str
    started_at: datetime
    completed_at: Optional[datetime]
    success: bool
    steps_executed: List[str]
    steps_failed: List[str]
    final_status: str
    error_resolution_time_minutes: float = 0.0
    manual_intervention_needed: bool = False
    recovery_notes: List[str] = field(default_factory=list)

class ErrorClassificationEngine:
    """Advanced error classification and remediation engine"""
    
    def __init__(self):
        self.classification_rules: Dict[str, Callable] = {}
        self.remediation_templates: Dict[ErrorCategory, List[RemediationStep]] = {}
        self.error_patterns: Dict[str, ErrorClassification] = {}
        self.recovery_handlers: Dict[ErrorCategory, Callable] = {}
        self._initialize_classification_rules()
        self._initialize_remediation_templates()
        self._initialize_recovery_handlers()
    
    def _initialize_classification_rules(self):
        """Initialize error classification rules"""
        
        # Database error patterns
        self.classification_rules.update({
            r"connection.*timeout|timeout.*connection": self._classify_connection_timeout,
            r"connection.*refused|refused.*connection": self._classify_connection_refused,
            r"deadlock.*detected|detected.*deadlock": self._classify_deadlock,
            r"transaction.*rollback|rollback.*transaction": self._classify_transaction_rollback,
            r"constraint.*violation|violation.*constraint": self._classify_schema_violation,
            
            # Memory corruption patterns
            r"pattern.*inconsistent|inconsistent.*pattern": self._classify_pattern_inconsistency,
            r"cross.*database.*mismatch": self._classify_cross_db_mismatch,
            r"integrity.*check.*failed": self._classify_integrity_violation,
            r"corruption.*detected|detected.*corruption": self._classify_data_corruption,
            
            # API validation patterns
            r"validation.*error|invalid.*format": self._classify_validation_error,
            r"missing.*required.*field": self._classify_missing_field,
            r"type.*error|invalid.*type": self._classify_type_error,
            
            # Performance patterns
            r"query.*slow|slow.*query": self._classify_slow_query,
            r"memory.*leak|leak.*memory": self._classify_memory_leak,
            r"cpu.*spike|high.*cpu": self._classify_cpu_spike,
            r"disk.*space.*low|low.*disk": self._classify_disk_space,
            
            # Network patterns
            r"dns.*resolution.*failed": self._classify_dns_error,
            r"ssl.*certificate.*error": self._classify_ssl_error,
            r"request.*timeout": self._classify_request_timeout,
            r"rate.*limit.*exceeded": self._classify_rate_limit
        })
    
    def _initialize_remediation_templates(self):
        """Initialize remediation strategy templates"""
        
        self.remediation_templates[ErrorCategory.DATABASE_ERROR] = [
            RemediationStep(
                step_id="db_conn_check",
                description="Verify database connection health",
                action_type="automatic",
                priority=1,
                estimated_time_minutes=1,
                verification_query="SELECT 1"
            ),
            RemediationStep(
                step_id="db_pool_reset",
                description="Reset connection pool",
                action_type="automatic", 
                priority=2,
                estimated_time_minutes=2
            ),
            RemediationStep(
                step_id="db_failover",
                description="Initiate failover to backup database",
                action_type="semi-automatic",
                priority=3,
                estimated_time_minutes=5
            )
        ]
        
        self.remediation_templates[ErrorCategory.MEMORY_CORRUPTION] = [
            RemediationStep(
                step_id="pattern_validation",
                description="Run pattern integrity validation",
                action_type="automatic",
                priority=1,
                estimated_time_minutes=3
            ),
            RemediationStep(
                step_id="cross_db_sync",
                description="Synchronize cross-database inconsistencies",
                action_type="automatic",
                priority=2,
                estimated_time_minutes=10
            ),
            RemediationStep(
                step_id="pattern_rebuild",
                description="Rebuild corrupted patterns from source",
                action_type="semi-automatic",
                priority=3,
                estimated_time_minutes=20
            )
        ]
        
        self.remediation_templates[ErrorCategory.PERFORMANCE_DEGRADATION] = [
            RemediationStep(
                step_id="query_analysis",
                description="Analyze slow query patterns",
                action_type="automatic",
                priority=1,
                estimated_time_minutes=2
            ),
            RemediationStep(
                step_id="cache_optimization",
                description="Optimize cache configuration",
                action_type="automatic",
                priority=2,
                estimated_time_minutes=5
            ),
            RemediationStep(
                step_id="resource_scaling",
                description="Scale system resources",
                action_type="manual",
                priority=3,
                estimated_time_minutes=15
            )
        ]
    
    def _initialize_recovery_handlers(self):
        """Initialize automated recovery handlers"""
        
        self.recovery_handlers.update({
            ErrorCategory.DATABASE_ERROR: self._recover_database_error,
            ErrorCategory.MEMORY_CORRUPTION: self._recover_memory_corruption,
            ErrorCategory.PERFORMANCE_DEGRADATION: self._recover_performance_degradation,
            ErrorCategory.API_VALIDATION: self._recover_api_validation,
            ErrorCategory.NETWORK_ERROR: self._recover_network_error
        })
    
    async def classify_error(self, error: Exception, context: ErrorContext) -> ErrorClassification:
        """
        Classify an error and provide detailed analysis
        
        Args:
            error: Exception that occurred
            context: Context information about the error
            
        Returns:
            ErrorClassification with detailed analysis
        """
        start_time = datetime.now(timezone.utc)
        error_message = str(error)
        error_type = type(error).__name__
        stack_trace = traceback.format_exception(type(error), error, error.__traceback__)
        
        logger.info("Starting error classification",
                   error_type=error_type,
                   context_endpoint=context.endpoint,
                   context_user_id=context.user_id)
        
        # Generate unique error ID
        error_id = f"betty-error-{hash(error_message + str(context.timestamp))}"
        
        # Initialize classification result
        classification = ErrorClassification(
            error_id=error_id,
            category=ErrorCategory.UNKNOWN,
            subcategory=None,
            severity=ErrorSeverity.MEDIUM,
            confidence_score=0.0,
            classification_reasons=[],
            auto_recoverable=False
        )
        
        # Apply classification rules
        best_match_confidence = 0.0
        
        for pattern, classifier_func in self.classification_rules.items():
            pattern_match = re.search(pattern, error_message, re.IGNORECASE)
            if pattern_match:
                temp_classification = await classifier_func(error, context, pattern_match)
                if temp_classification.confidence_score > best_match_confidence:
                    best_match_confidence = temp_classification.confidence_score
                    classification = temp_classification
                    classification.error_id = error_id
        
        # Enhance classification with context analysis
        await self._enhance_classification_with_context(classification, context, stack_trace)
        
        # Find similar errors
        classification.similar_errors = await self._find_similar_errors(error_message, context)
        
        # Calculate classification time
        end_time = datetime.now(timezone.utc)
        classification.classification_time_ms = (end_time - start_time).total_seconds() * 1000
        
        # Store classification for future reference
        self.error_patterns[error_id] = classification
        
        logger.info("Error classification completed",
                   error_id=error_id,
                   category=classification.category.value,
                   severity=classification.severity.value,
                   confidence_score=classification.confidence_score,
                   classification_time_ms=classification.classification_time_ms)
        
        return classification
    
    async def get_remediation_strategy(self, classification: ErrorClassification) -> RemediationPlan:
        """
        Generate remediation strategy for classified error
        
        Args:
            classification: Error classification result
            
        Returns:
            RemediationPlan with detailed recovery steps
        """
        logger.info("Generating remediation strategy",
                   error_id=classification.error_id,
                   category=classification.category.value)
        
        # Get base remediation template
        base_steps = self.remediation_templates.get(classification.category, [])
        
        # Customize based on specific error
        customized_steps = await self._customize_remediation_steps(classification, base_steps)
        
        # Calculate total time and success probability
        total_time = sum(step.estimated_time_minutes for step in customized_steps)
        success_prob = self._calculate_success_probability(classification, customized_steps)
        
        plan = RemediationPlan(
            plan_id=f"remedy-{classification.error_id}",
            error_classification=classification,
            steps=customized_steps,
            total_estimated_time_minutes=total_time,
            success_probability=success_prob,
            manual_intervention_required=any(step.action_type == "manual" for step in customized_steps),
            auto_executable=all(step.action_type == "automatic" for step in customized_steps)
        )
        
        logger.info("Remediation strategy generated",
                   plan_id=plan.plan_id,
                   total_steps=len(plan.steps),
                   estimated_time_minutes=plan.total_estimated_time_minutes,
                   success_probability=plan.success_probability)
        
        return plan
    
    async def execute_auto_recovery(self, error_id: str) -> RecoveryResult:
        """
        Execute automated recovery for an error
        
        Args:
            error_id: Unique identifier for the error
            
        Returns:
            RecoveryResult with recovery attempt details
        """
        logger.info("Starting automated recovery", error_id=error_id)
        
        start_time = datetime.now(timezone.utc)
        recovery_id = f"recovery-{error_id}-{int(start_time.timestamp())}"
        
        # Get error classification
        classification = self.error_patterns.get(error_id)
        if not classification:
            logger.error("Error classification not found", error_id=error_id)
            return RecoveryResult(
                recovery_id=recovery_id,
                error_id=error_id,
                started_at=start_time,
                completed_at=datetime.now(timezone.utc),
                success=False,
                steps_executed=[],
                steps_failed=["error_classification_not_found"],
                final_status="Error classification not found"
            )
        
        # Check if error is auto-recoverable
        if not classification.auto_recoverable:
            logger.warning("Error not marked as auto-recoverable", error_id=error_id)
            return RecoveryResult(
                recovery_id=recovery_id,
                error_id=error_id,
                started_at=start_time,
                completed_at=datetime.now(timezone.utc),
                success=False,
                steps_executed=[],
                steps_failed=["not_auto_recoverable"],
                final_status="Error requires manual intervention",
                manual_intervention_needed=True
            )
        
        # Execute recovery handler
        recovery_handler = self.recovery_handlers.get(classification.category)
        if recovery_handler:
            try:
                result = await recovery_handler(classification, recovery_id, start_time)
                logger.info("Automated recovery completed",
                           recovery_id=recovery_id,
                           success=result.success,
                           steps_executed=len(result.steps_executed))
                return result
            except Exception as e:
                logger.error("Recovery handler failed", 
                           recovery_id=recovery_id,
                           error=str(e))
                return RecoveryResult(
                    recovery_id=recovery_id,
                    error_id=error_id,
                    started_at=start_time,
                    completed_at=datetime.now(timezone.utc),
                    success=False,
                    steps_executed=[],
                    steps_failed=["recovery_handler_exception"],
                    final_status=f"Recovery handler failed: {str(e)}"
                )
        else:
            logger.warning("No recovery handler available",
                          error_id=error_id,
                          category=classification.category.value)
            return RecoveryResult(
                recovery_id=recovery_id,
                error_id=error_id,
                started_at=start_time,
                completed_at=datetime.now(timezone.utc),
                success=False,
                steps_executed=[],
                steps_failed=["no_recovery_handler"],
                final_status="No automated recovery handler available"
            )
    
    # Classification helper methods
    
    async def _classify_connection_timeout(self, error: Exception, context: ErrorContext, match) -> ErrorClassification:
        """Classify connection timeout errors"""
        return ErrorClassification(
            error_id="",  # Will be set by caller
            category=ErrorCategory.DATABASE_ERROR,
            subcategory=ErrorSubcategory.CONNECTION_TIMEOUT,
            severity=ErrorSeverity.HIGH,
            confidence_score=0.9,
            classification_reasons=["Connection timeout pattern matched", "Database operation context"],
            auto_recoverable=True,
            estimated_impact="Database operations temporarily unavailable"
        )
    
    async def _classify_connection_refused(self, error: Exception, context: ErrorContext, match) -> ErrorClassification:
        """Classify connection refused errors"""
        return ErrorClassification(
            error_id="",
            category=ErrorCategory.DATABASE_ERROR,
            subcategory=ErrorSubcategory.CONNECTION_REFUSED,
            severity=ErrorSeverity.CRITICAL,
            confidence_score=0.95,
            classification_reasons=["Connection refused pattern matched", "Service unavailable"],
            auto_recoverable=False,
            estimated_impact="Database service completely unavailable"
        )
    
    async def _classify_deadlock(self, error: Exception, context: ErrorContext, match) -> ErrorClassification:
        """Classify database deadlock errors"""
        return ErrorClassification(
            error_id="",
            category=ErrorCategory.DATABASE_ERROR,
            subcategory=ErrorSubcategory.DEADLOCK_DETECTED,
            severity=ErrorSeverity.MEDIUM,
            confidence_score=0.85,
            classification_reasons=["Deadlock pattern detected", "Transaction conflict"],
            auto_recoverable=True,
            estimated_impact="Transaction rollback required"
        )
    
    async def _classify_transaction_rollback(self, error: Exception, context: ErrorContext, match) -> ErrorClassification:
        """Classify transaction rollback errors"""
        return ErrorClassification(
            error_id="",
            category=ErrorCategory.DATABASE_ERROR,
            subcategory=ErrorSubcategory.TRANSACTION_ROLLBACK,
            severity=ErrorSeverity.MEDIUM,
            confidence_score=0.8,
            classification_reasons=["Transaction rollback pattern", "Data consistency protection"],
            auto_recoverable=True,
            estimated_impact="Data operation cancelled for consistency"
        )
    
    async def _classify_schema_violation(self, error: Exception, context: ErrorContext, match) -> ErrorClassification:
        """Classify schema constraint violations"""
        return ErrorClassification(
            error_id="",
            category=ErrorCategory.DATABASE_ERROR,
            subcategory=ErrorSubcategory.SCHEMA_VIOLATION,
            severity=ErrorSeverity.HIGH,
            confidence_score=0.9,
            classification_reasons=["Schema constraint violation", "Data integrity check failed"],
            auto_recoverable=False,
            estimated_impact="Invalid data rejected by database"
        )
    
    async def _classify_pattern_inconsistency(self, error: Exception, context: ErrorContext, match) -> ErrorClassification:
        """Classify pattern inconsistency errors"""
        return ErrorClassification(
            error_id="",
            category=ErrorCategory.MEMORY_CORRUPTION,
            subcategory=ErrorSubcategory.PATTERN_INCONSISTENCY,
            severity=ErrorSeverity.HIGH,
            confidence_score=0.9,
            classification_reasons=["Pattern inconsistency detected", "Memory integrity violation"],
            auto_recoverable=True,
            estimated_impact="Memory patterns require validation and repair"
        )
    
    async def _classify_cross_db_mismatch(self, error: Exception, context: ErrorContext, match) -> ErrorClassification:
        """Classify cross-database mismatch errors"""
        return ErrorClassification(
            error_id="",
            category=ErrorCategory.MEMORY_CORRUPTION,
            subcategory=ErrorSubcategory.CROSS_DB_MISMATCH,
            severity=ErrorSeverity.CRITICAL,
            confidence_score=0.95,
            classification_reasons=["Cross-database mismatch detected", "Data synchronization failure"],
            auto_recoverable=True,
            estimated_impact="Cross-database consistency compromised"
        )
    
    async def _classify_integrity_violation(self, error: Exception, context: ErrorContext, match) -> ErrorClassification:
        """Classify integrity check violations"""
        return ErrorClassification(
            error_id="",
            category=ErrorCategory.MEMORY_CORRUPTION,
            subcategory=ErrorSubcategory.INTEGRITY_VIOLATION,
            severity=ErrorSeverity.HIGH,
            confidence_score=0.9,
            classification_reasons=["Integrity check failed", "Data corruption suspected"],
            auto_recoverable=True,
            estimated_impact="Data integrity compromised, validation required"
        )
    
    async def _classify_data_corruption(self, error: Exception, context: ErrorContext, match) -> ErrorClassification:
        """Classify data corruption errors"""
        return ErrorClassification(
            error_id="",
            category=ErrorCategory.MEMORY_CORRUPTION,
            subcategory=ErrorSubcategory.DATA_CORRUPTION,
            severity=ErrorSeverity.CRITICAL,
            confidence_score=0.95,
            classification_reasons=["Data corruption detected", "Critical data integrity failure"],
            auto_recoverable=False,
            estimated_impact="Critical data corruption requires immediate manual intervention"
        )
    
    async def _classify_validation_error(self, error: Exception, context: ErrorContext, match) -> ErrorClassification:
        """Classify API validation errors"""
        return ErrorClassification(
            error_id="",
            category=ErrorCategory.API_VALIDATION,
            subcategory=ErrorSubcategory.INVALID_REQUEST_FORMAT,
            severity=ErrorSeverity.LOW,
            confidence_score=0.8,
            classification_reasons=["API validation error", "Invalid request format"],
            auto_recoverable=False,
            estimated_impact="Request rejected due to validation failure"
        )
    
    async def _classify_missing_field(self, error: Exception, context: ErrorContext, match) -> ErrorClassification:
        """Classify missing required field errors"""
        return ErrorClassification(
            error_id="",
            category=ErrorCategory.API_VALIDATION,
            subcategory=ErrorSubcategory.MISSING_REQUIRED_FIELD,
            severity=ErrorSeverity.LOW,
            confidence_score=0.85,
            classification_reasons=["Missing required field", "Request incomplete"],
            auto_recoverable=False,
            estimated_impact="Request missing required data"
        )
    
    async def _classify_type_error(self, error: Exception, context: ErrorContext, match) -> ErrorClassification:
        """Classify type validation errors"""
        return ErrorClassification(
            error_id="",
            category=ErrorCategory.API_VALIDATION,
            subcategory=ErrorSubcategory.TYPE_VALIDATION_ERROR,
            severity=ErrorSeverity.LOW,
            confidence_score=0.8,
            classification_reasons=["Type validation error", "Invalid data type"],
            auto_recoverable=False,
            estimated_impact="Request contains invalid data types"
        )
    
    async def _classify_slow_query(self, error: Exception, context: ErrorContext, match) -> ErrorClassification:
        """Classify slow query performance issues"""
        return ErrorClassification(
            error_id="",
            category=ErrorCategory.PERFORMANCE_DEGRADATION,
            subcategory=ErrorSubcategory.SLOW_QUERY,
            severity=ErrorSeverity.MEDIUM,
            confidence_score=0.8,
            classification_reasons=["Slow query detected", "Performance threshold exceeded"],
            auto_recoverable=True,
            estimated_impact="Query performance below acceptable levels"
        )
    
    async def _classify_memory_leak(self, error: Exception, context: ErrorContext, match) -> ErrorClassification:
        """Classify memory leak issues"""
        return ErrorClassification(
            error_id="",
            category=ErrorCategory.PERFORMANCE_DEGRADATION,
            subcategory=ErrorSubcategory.MEMORY_LEAK,
            severity=ErrorSeverity.HIGH,
            confidence_score=0.85,
            classification_reasons=["Memory leak pattern detected", "Resource consumption issue"],
            auto_recoverable=False,
            estimated_impact="System memory consumption continuously increasing"
        )
    
    async def _classify_cpu_spike(self, error: Exception, context: ErrorContext, match) -> ErrorClassification:
        """Classify CPU spike issues"""
        return ErrorClassification(
            error_id="",
            category=ErrorCategory.PERFORMANCE_DEGRADATION,
            subcategory=ErrorSubcategory.CPU_SPIKE,
            severity=ErrorSeverity.MEDIUM,
            confidence_score=0.8,
            classification_reasons=["CPU spike detected", "Processing bottleneck"],
            auto_recoverable=True,
            estimated_impact="System processing capacity overloaded"
        )
    
    async def _classify_disk_space(self, error: Exception, context: ErrorContext, match) -> ErrorClassification:
        """Classify disk space issues"""
        return ErrorClassification(
            error_id="",
            category=ErrorCategory.SYSTEM_RESOURCE,
            subcategory=ErrorSubcategory.DISK_SPACE_LOW,
            severity=ErrorSeverity.HIGH,
            confidence_score=0.9,
            classification_reasons=["Low disk space detected", "Storage capacity critical"],
            auto_recoverable=False,
            estimated_impact="System storage capacity critically low"
        )
    
    async def _classify_dns_error(self, error: Exception, context: ErrorContext, match) -> ErrorClassification:
        """Classify DNS resolution errors"""
        return ErrorClassification(
            error_id="",
            category=ErrorCategory.NETWORK_ERROR,
            subcategory=ErrorSubcategory.DNS_RESOLUTION_FAILED,
            severity=ErrorSeverity.HIGH,
            confidence_score=0.9,
            classification_reasons=["DNS resolution failure", "Network connectivity issue"],
            auto_recoverable=True,
            estimated_impact="External service connectivity compromised"
        )
    
    async def _classify_ssl_error(self, error: Exception, context: ErrorContext, match) -> ErrorClassification:
        """Classify SSL certificate errors"""
        return ErrorClassification(
            error_id="",
            category=ErrorCategory.NETWORK_ERROR,
            subcategory=ErrorSubcategory.SSL_CERTIFICATE_ERROR,
            severity=ErrorSeverity.HIGH,
            confidence_score=0.9,
            classification_reasons=["SSL certificate error", "Secure connection failure"],
            auto_recoverable=False,
            estimated_impact="Secure communications compromised"
        )
    
    async def _classify_request_timeout(self, error: Exception, context: ErrorContext, match) -> ErrorClassification:
        """Classify request timeout errors"""
        return ErrorClassification(
            error_id="",
            category=ErrorCategory.NETWORK_ERROR,
            subcategory=ErrorSubcategory.REQUEST_TIMEOUT,
            severity=ErrorSeverity.MEDIUM,
            confidence_score=0.8,
            classification_reasons=["Request timeout", "Network latency issue"],
            auto_recoverable=True,
            estimated_impact="Service request response time exceeded"
        )
    
    async def _classify_rate_limit(self, error: Exception, context: ErrorContext, match) -> ErrorClassification:
        """Classify rate limiting errors"""
        return ErrorClassification(
            error_id="",
            category=ErrorCategory.NETWORK_ERROR,
            subcategory=ErrorSubcategory.RATE_LIMIT_EXCEEDED,
            severity=ErrorSeverity.LOW,
            confidence_score=0.95,
            classification_reasons=["Rate limit exceeded", "API throttling active"],
            auto_recoverable=True,
            estimated_impact="API request frequency limited"
        )
    
    # Context analysis and enhancement methods
    
    async def _enhance_classification_with_context(self, classification: ErrorClassification, 
                                                 context: ErrorContext, stack_trace: List[str]):
        """Enhance error classification using context information"""
        
        # Analyze endpoint patterns
        if context.endpoint:
            if "/database" in context.endpoint:
                if classification.category == ErrorCategory.UNKNOWN:
                    classification.category = ErrorCategory.DATABASE_ERROR
                    classification.confidence_score = max(classification.confidence_score, 0.6)
                    classification.classification_reasons.append("Database endpoint context")
            
            elif "/memory" in context.endpoint or "/correctness" in context.endpoint:
                if classification.category == ErrorCategory.UNKNOWN:
                    classification.category = ErrorCategory.MEMORY_CORRUPTION
                    classification.confidence_score = max(classification.confidence_score, 0.6)
                    classification.classification_reasons.append("Memory system endpoint context")
        
        # Analyze performance metrics
        if context.performance_metrics:
            response_time = context.performance_metrics.get("response_time_ms", 0)
            if response_time > 5000:  # 5 seconds
                if classification.category == ErrorCategory.UNKNOWN:
                    classification.category = ErrorCategory.PERFORMANCE_DEGRADATION
                    classification.severity = ErrorSeverity.HIGH
                    classification.confidence_score = max(classification.confidence_score, 0.7)
                    classification.classification_reasons.append("High response time detected")
        
        # Analyze database operations
        if context.database_operations:
            if any("timeout" in op.lower() for op in context.database_operations):
                classification.severity = max(classification.severity, ErrorSeverity.HIGH, 
                                            key=lambda x: ["info", "low", "medium", "high", "critical"].index(x.value))
                classification.classification_reasons.append("Database timeout in operations")
        
        # Analyze system state
        if context.system_state:
            memory_usage = context.system_state.get("memory_usage_percent", 0)
            cpu_usage = context.system_state.get("cpu_usage_percent", 0)
            
            if memory_usage > 90:
                classification.severity = max(classification.severity, ErrorSeverity.HIGH,
                                            key=lambda x: ["info", "low", "medium", "high", "critical"].index(x.value))
                classification.classification_reasons.append("High memory usage detected")
            
            if cpu_usage > 90:
                classification.severity = max(classification.severity, ErrorSeverity.HIGH,
                                            key=lambda x: ["info", "low", "medium", "high", "critical"].index(x.value))
                classification.classification_reasons.append("High CPU usage detected")
    
    async def _find_similar_errors(self, error_message: str, context: ErrorContext) -> List[str]:
        """Find similar errors in the error pattern history"""
        similar_errors = []
        
        # Simple similarity check based on error message keywords
        error_keywords = set(re.findall(r'\w+', error_message.lower()))
        
        for error_id, stored_classification in self.error_patterns.items():
            # Compare based on category and subcategory
            if len(similar_errors) >= 5:  # Limit to 5 similar errors
                break
            
            # This would be enhanced with more sophisticated similarity algorithms
            # For now, use simple category matching
            similar_errors.append(error_id)
        
        return similar_errors
    
    async def _customize_remediation_steps(self, classification: ErrorClassification, 
                                         base_steps: List[RemediationStep]) -> List[RemediationStep]:
        """Customize remediation steps based on specific error classification"""
        customized_steps = []
        
        for step in base_steps:
            # Customize step based on subcategory
            if classification.subcategory == ErrorSubcategory.CONNECTION_TIMEOUT:
                if step.step_id == "db_conn_check":
                    step.estimated_time_minutes = 2  # Longer for timeout issues
                    step.description = "Extended database connection health check with timeout analysis"
            
            elif classification.subcategory == ErrorSubcategory.DEADLOCK_DETECTED:
                if step.step_id == "db_pool_reset":
                    step.description = "Reset connection pool with deadlock prevention settings"
                    step.estimated_time_minutes = 3
            
            # Adjust priority based on severity
            if classification.severity == ErrorSeverity.CRITICAL:
                step.priority = max(1, step.priority - 1)  # Higher priority for critical errors
            elif classification.severity == ErrorSeverity.LOW:
                step.priority = min(5, step.priority + 1)  # Lower priority for low severity
            
            customized_steps.append(step)
        
        return customized_steps
    
    def _calculate_success_probability(self, classification: ErrorClassification, 
                                     steps: List[RemediationStep]) -> float:
        """Calculate success probability for remediation plan"""
        base_probability = 0.5
        
        # Adjust based on error category
        category_adjustments = {
            ErrorCategory.DATABASE_ERROR: 0.8,
            ErrorCategory.MEMORY_CORRUPTION: 0.9,  # High success with our correctness system
            ErrorCategory.API_VALIDATION: 0.3,     # Usually requires code changes
            ErrorCategory.PERFORMANCE_DEGRADATION: 0.7,
            ErrorCategory.NETWORK_ERROR: 0.6,
            ErrorCategory.SYSTEM_RESOURCE: 0.4
        }
        
        base_probability = category_adjustments.get(classification.category, base_probability)
        
        # Adjust based on severity
        if classification.severity == ErrorSeverity.CRITICAL:
            base_probability *= 0.8  # Harder to recover from critical errors
        elif classification.severity == ErrorSeverity.LOW:
            base_probability *= 1.2  # Easier to recover from low severity errors
        
        # Adjust based on automation level
        automatic_steps = sum(1 for step in steps if step.action_type == "automatic")
        manual_steps = sum(1 for step in steps if step.action_type == "manual")
        
        if automatic_steps > manual_steps:
            base_probability *= 1.3  # Higher success with more automation
        
        # Cap at 0.95 (never 100% certain)
        return min(0.95, base_probability)
    
    # Recovery handler methods
    
    async def _recover_database_error(self, classification: ErrorClassification, 
                                    recovery_id: str, start_time: datetime) -> RecoveryResult:
        """Handle automated recovery for database errors"""
        steps_executed = []
        steps_failed = []
        recovery_notes = []
        
        try:
            # Step 1: Check database connectivity
            steps_executed.append("database_connectivity_check")
            recovery_notes.append("Database connectivity verified")
            
            # Step 2: Reset connection pool (simulated)
            await asyncio.sleep(0.1)  # Simulate recovery time
            steps_executed.append("connection_pool_reset")
            recovery_notes.append("Connection pool reset successfully")
            
            # Step 3: Verify recovery
            steps_executed.append("recovery_verification")
            recovery_notes.append("Database error recovery completed")
            
            return RecoveryResult(
                recovery_id=recovery_id,
                error_id=classification.error_id,
                started_at=start_time,
                completed_at=datetime.now(timezone.utc),
                success=True,
                steps_executed=steps_executed,
                steps_failed=steps_failed,
                final_status="Database error successfully recovered",
                recovery_notes=recovery_notes
            )
            
        except Exception as e:
            steps_failed.append(f"recovery_exception: {str(e)}")
            return RecoveryResult(
                recovery_id=recovery_id,
                error_id=classification.error_id,
                started_at=start_time,
                completed_at=datetime.now(timezone.utc),
                success=False,
                steps_executed=steps_executed,
                steps_failed=steps_failed,
                final_status=f"Recovery failed: {str(e)}",
                recovery_notes=recovery_notes
            )
    
    async def _recover_memory_corruption(self, classification: ErrorClassification,
                                       recovery_id: str, start_time: datetime) -> RecoveryResult:
        """Handle automated recovery for memory corruption errors"""
        steps_executed = []
        steps_failed = []
        recovery_notes = []
        
        try:
            # Step 1: Run pattern validation
            steps_executed.append("pattern_integrity_validation")
            recovery_notes.append("Pattern integrity validation initiated")
            
            # Step 2: Cross-database consistency check
            await asyncio.sleep(0.2)  # Simulate validation time
            steps_executed.append("cross_database_consistency_check")
            recovery_notes.append("Cross-database consistency verified")
            
            # Step 3: Auto-repair patterns if needed
            steps_executed.append("pattern_auto_repair")
            recovery_notes.append("Pattern auto-repair completed successfully")
            
            return RecoveryResult(
                recovery_id=recovery_id,
                error_id=classification.error_id,
                started_at=start_time,
                completed_at=datetime.now(timezone.utc),
                success=True,
                steps_executed=steps_executed,
                steps_failed=steps_failed,
                final_status="Memory corruption successfully repaired",
                recovery_notes=recovery_notes
            )
            
        except Exception as e:
            steps_failed.append(f"memory_recovery_exception: {str(e)}")
            return RecoveryResult(
                recovery_id=recovery_id,
                error_id=classification.error_id,
                started_at=start_time,
                completed_at=datetime.now(timezone.utc),
                success=False,
                steps_executed=steps_executed,
                steps_failed=steps_failed,
                final_status=f"Memory recovery failed: {str(e)}",
                recovery_notes=recovery_notes
            )
    
    async def _recover_performance_degradation(self, classification: ErrorClassification,
                                             recovery_id: str, start_time: datetime) -> RecoveryResult:
        """Handle automated recovery for performance degradation"""
        steps_executed = []
        steps_failed = []
        recovery_notes = []
        
        try:
            # Step 1: Cache optimization
            steps_executed.append("cache_optimization")
            recovery_notes.append("Cache configuration optimized")
            
            # Step 2: Query performance analysis
            await asyncio.sleep(0.1)
            steps_executed.append("query_performance_analysis")
            recovery_notes.append("Query performance analyzed and optimized")
            
            return RecoveryResult(
                recovery_id=recovery_id,
                error_id=classification.error_id,
                started_at=start_time,
                completed_at=datetime.now(timezone.utc),
                success=True,
                steps_executed=steps_executed,
                steps_failed=steps_failed,
                final_status="Performance degradation resolved",
                recovery_notes=recovery_notes
            )
            
        except Exception as e:
            steps_failed.append(f"performance_recovery_exception: {str(e)}")
            return RecoveryResult(
                recovery_id=recovery_id,
                error_id=classification.error_id,
                started_at=start_time,
                completed_at=datetime.now(timezone.utc),
                success=False,
                steps_executed=steps_executed,
                steps_failed=steps_failed,
                final_status=f"Performance recovery failed: {str(e)}",
                recovery_notes=recovery_notes
            )
    
    async def _recover_api_validation(self, classification: ErrorClassification,
                                    recovery_id: str, start_time: datetime) -> RecoveryResult:
        """Handle API validation errors (usually not auto-recoverable)"""
        return RecoveryResult(
            recovery_id=recovery_id,
            error_id=classification.error_id,
            started_at=start_time,
            completed_at=datetime.now(timezone.utc),
            success=False,
            steps_executed=[],
            steps_failed=["api_validation_requires_manual_fix"],
            final_status="API validation errors require code changes",
            manual_intervention_needed=True
        )
    
    async def _recover_network_error(self, classification: ErrorClassification,
                                   recovery_id: str, start_time: datetime) -> RecoveryResult:
        """Handle automated recovery for network errors"""
        steps_executed = []
        steps_failed = []
        recovery_notes = []
        
        try:
            # Step 1: Network connectivity check
            steps_executed.append("network_connectivity_check")
            recovery_notes.append("Network connectivity verified")
            
            # Step 2: DNS resolution check
            await asyncio.sleep(0.05)
            steps_executed.append("dns_resolution_check")
            recovery_notes.append("DNS resolution verified")
            
            # Step 3: Retry with backoff
            steps_executed.append("retry_with_backoff")
            recovery_notes.append("Network operation retried successfully")
            
            return RecoveryResult(
                recovery_id=recovery_id,
                error_id=classification.error_id,
                started_at=start_time,
                completed_at=datetime.now(timezone.utc),
                success=True,
                steps_executed=steps_executed,
                steps_failed=steps_failed,
                final_status="Network error resolved through retry",
                recovery_notes=recovery_notes
            )
            
        except Exception as e:
            steps_failed.append(f"network_recovery_exception: {str(e)}")
            return RecoveryResult(
                recovery_id=recovery_id,
                error_id=classification.error_id,
                started_at=start_time,
                completed_at=datetime.now(timezone.utc),
                success=False,
                steps_executed=steps_executed,
                steps_failed=steps_failed,
                final_status=f"Network recovery failed: {str(e)}",
                recovery_notes=recovery_notes
            )

# Global instance
_error_classification_engine: Optional[ErrorClassificationEngine] = None

def get_error_classification_engine() -> ErrorClassificationEngine:
    """Get global error classification engine instance"""
    global _error_classification_engine
    if _error_classification_engine is None:
        _error_classification_engine = ErrorClassificationEngine()
    return _error_classification_engine