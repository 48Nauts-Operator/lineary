# ABOUTME: Comprehensive error handling middleware for Betty Memory System
# ABOUTME: Integrates error classification, enhanced logging, and automated recovery

import asyncio
import time
import traceback
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Callable
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
import structlog
import psutil

from core.error_classification import (
    ErrorClassificationEngine, ErrorContext, ErrorSeverity, 
    get_error_classification_engine
)
from core.enhanced_logging import (
    EnhancedStructuredLogger, ComponentType, LogLevel,
    get_enhanced_logger, RequestInfo, SecurityEvent
)

logger = structlog.get_logger(__name__)

class BettyErrorHandlingMiddleware:
    """
    Comprehensive error handling middleware that provides:
    - Intelligent error classification and routing
    - Real-time error analysis and pattern detection
    - Automated recovery attempts for recoverable errors
    - Enhanced logging with structured data
    - Security event monitoring
    - Performance bottleneck detection
    """
    
    def __init__(self, 
                 app,
                 enable_auto_recovery: bool = True,
                 max_recovery_attempts: int = 3,
                 recovery_timeout_seconds: int = 30):
        self.app = app
        self.enable_auto_recovery = enable_auto_recovery
        self.max_recovery_attempts = max_recovery_attempts
        self.recovery_timeout_seconds = recovery_timeout_seconds
        
        # Initialize components
        self.error_engine = get_error_classification_engine()
        self.logger = get_enhanced_logger(__name__, ComponentType.API_GATEWAY)
        
        # Error tracking
        self.active_errors: Dict[str, Dict[str, Any]] = {}
        self.recovery_attempts: Dict[str, int] = {}
        
        # Performance monitoring
        self.request_start_times: Dict[str, float] = {}
        self.slow_request_threshold_ms = 5000
        self.error_rate_window_minutes = 15
        
        # Security monitoring
        self.suspicious_ips: Dict[str, Dict[str, Any]] = {}
        self.failed_auth_attempts: Dict[str, List[datetime]] = {}
        
        logger.info("Enhanced Error Handling Middleware initialized",
                   auto_recovery_enabled=enable_auto_recovery,
                   max_recovery_attempts=max_recovery_attempts)
    
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Process request through enhanced error handling pipeline"""
        
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Start timing
        start_time = time.time()
        self.request_start_times[request_id] = start_time
        
        # Create request context
        request_info = await self._create_request_info(request, request_id)
        
        # Security pre-checks
        security_issues = await self._perform_security_checks(request, request_info)
        if security_issues:
            return await self._handle_security_violation(request, request_info, security_issues)
        
        # Log request start
        await self.logger.log_api_request(request_info)
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate response time
            duration_ms = (time.time() - start_time) * 1000
            
            # Performance analysis
            if duration_ms > self.slow_request_threshold_ms:
                await self._handle_slow_request(request_info, duration_ms)
            
            # Log successful response
            await self.logger.log_api_request(
                request_info=request_info,
                status_code=response.status_code,
                duration_ms=duration_ms,
                response_size_bytes=self._get_response_size(response)
            )
            
            # Add performance headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
            response.headers["X-Component"] = "BETTY-Memory-System"
            
            return response
            
        except Exception as error:
            # Calculate error response time
            duration_ms = (time.time() - start_time) * 1000
            
            # Handle error through comprehensive pipeline
            return await self._handle_error_comprehensive(
                error=error,
                request=request,
                request_info=request_info,
                duration_ms=duration_ms
            )
        
        finally:
            # Cleanup request tracking
            self.request_start_times.pop(request_id, None)
    
    async def _create_request_info(self, request: Request, request_id: str) -> RequestInfo:
        """Create comprehensive request information"""
        
        # Extract request body size
        body_size = None
        if hasattr(request, 'headers') and 'content-length' in request.headers:
            try:
                body_size = int(request.headers['content-length'])
            except (ValueError, TypeError):
                pass
        
        return RequestInfo(
            request_id=request_id,
            method=request.method,
            endpoint=str(request.url.path),
            user_id=getattr(request.state, 'user_id', None),
            ip_address=self._get_client_ip(request),
            user_agent=request.headers.get('user-agent', 'unknown'),
            headers={k: v for k, v in request.headers.items() if not k.lower().startswith('authorization')},
            query_params=dict(request.query_params),
            body_size_bytes=body_size,
            started_at=datetime.now(timezone.utc)
        )
    
    async def _perform_security_checks(self, request: Request, request_info: RequestInfo) -> List[str]:
        """Perform security checks on incoming request"""
        security_issues = []
        
        # Check for suspicious IP patterns
        client_ip = request_info.ip_address
        if client_ip:
            if await self._is_suspicious_ip(client_ip):
                security_issues.append("suspicious_ip_detected")
        
        # Check for unusual request patterns
        if len(request_info.endpoint) > 1000:
            security_issues.append("unusually_long_endpoint")
        
        # Check for SQL injection patterns in query parameters
        for param, value in request_info.query_params.items():
            if self._contains_sql_injection_pattern(str(value)):
                security_issues.append("potential_sql_injection")
                break
        
        # Check for excessive header count
        if len(request_info.headers) > 50:
            security_issues.append("excessive_headers")
        
        # Check for authentication anomalies
        if request_info.endpoint.startswith('/auth') or 'login' in request_info.endpoint.lower():
            if await self._check_auth_anomalies(client_ip, request_info):
                security_issues.append("auth_anomaly_detected")
        
        return security_issues
    
    async def _handle_security_violation(self, request: Request, 
                                       request_info: RequestInfo, 
                                       security_issues: List[str]) -> JSONResponse:
        """Handle detected security violations"""
        
        # Log security event
        security_event = SecurityEvent(
            event_type="security_violation",
            severity="high",
            user_id=request_info.user_id,
            ip_address=request_info.ip_address,
            resource_accessed=request_info.endpoint,
            action_attempted=request_info.method,
            success=False,
            threat_indicators=security_issues,
            additional_context={
                "user_agent": request_info.user_agent,
                "headers_count": len(request_info.headers),
                "query_params": request_info.query_params
            }
        )
        
        await self.logger.log_security_event(security_event)
        
        # Add IP to suspicious list
        if request_info.ip_address:
            await self._mark_ip_suspicious(request_info.ip_address, security_issues)
        
        # Return security response
        return JSONResponse(
            status_code=403,
            content={
                "error": "Security Violation Detected",
                "message": "Request blocked due to security policy violation",
                "request_id": request_info.request_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "blocked_reasons": security_issues
            },
            headers={
                "X-Request-ID": request_info.request_id,
                "X-Security-Block": "true"
            }
        )
    
    async def _handle_error_comprehensive(self, error: Exception, request: Request,
                                        request_info: RequestInfo, duration_ms: float) -> JSONResponse:
        """Comprehensive error handling with classification and recovery"""
        
        # Create error context
        error_context = await self._create_error_context(error, request, request_info)
        
        # Classify the error
        classification = await self.error_engine.classify_error(error, error_context)
        
        # Log the error with classification
        await self.logger.log_api_request(
            request_info=request_info,
            status_code=self._determine_status_code(error, classification),
            duration_ms=duration_ms,
            error=error
        )
        
        # Additional structured error logging
        await self.logger.error(
            "Request error with classification",
            request_id=request_info.request_id,
            error_id=classification.error_id,
            error_category=classification.category.value,
            error_severity=classification.severity.value,
            confidence_score=classification.confidence_score,
            auto_recoverable=classification.auto_recoverable,
            classification_time_ms=classification.classification_time_ms
        )
        
        # Attempt automated recovery for recoverable errors
        recovery_attempted = False
        recovery_successful = False
        
        if (self.enable_auto_recovery and 
            classification.auto_recoverable and 
            classification.severity != ErrorSeverity.CRITICAL):
            
            recovery_attempted = True
            recovery_successful = await self._attempt_automated_recovery(
                classification, request_info
            )
        
        # Handle critical errors immediately
        if classification.severity == ErrorSeverity.CRITICAL:
            await self._handle_critical_error(classification, request_info, error)
        
        # Generate appropriate response
        response = await self._generate_error_response(
            error=error,
            classification=classification,
            request_info=request_info,
            recovery_attempted=recovery_attempted,
            recovery_successful=recovery_successful
        )
        
        return response
    
    async def _create_error_context(self, error: Exception, 
                                  request: Request, 
                                  request_info: RequestInfo) -> ErrorContext:
        """Create comprehensive error context"""
        
        # Get system metrics
        process = psutil.Process()
        memory_info = process.memory_info()
        
        # Extract database operations from request state if available
        database_operations = []
        if hasattr(request.state, 'database_operations'):
            database_operations = request.state.database_operations
        
        return ErrorContext(
            timestamp=datetime.now(timezone.utc),
            user_id=request_info.user_id,
            session_id=getattr(request.state, 'session_id', None),
            project_id=getattr(request.state, 'project_id', None),
            endpoint=request_info.endpoint,
            method=request_info.method,
            request_id=request_info.request_id,
            user_agent=request_info.user_agent,
            ip_address=request_info.ip_address,
            database_operations=database_operations,
            performance_metrics={
                "response_time_ms": (time.time() - self.request_start_times.get(request_info.request_id, time.time())) * 1000,
                "memory_usage_mb": memory_info.rss / 1024 / 1024,
                "cpu_usage_percent": process.cpu_percent()
            },
            system_state={
                "memory_usage_percent": psutil.virtual_memory().percent,
                "cpu_usage_percent": psutil.cpu_percent(),
                "disk_usage_percent": psutil.disk_usage('/').percent
            }
        )
    
    async def _attempt_automated_recovery(self, classification, request_info: RequestInfo) -> bool:
        """Attempt automated recovery for recoverable errors"""
        
        error_id = classification.error_id
        
        # Check if we've already attempted recovery for this error type
        attempts = self.recovery_attempts.get(error_id, 0)
        if attempts >= self.max_recovery_attempts:
            await self.logger.warning(
                "Recovery attempt limit reached",
                error_id=error_id,
                attempts=attempts,
                max_attempts=self.max_recovery_attempts
            )
            return False
        
        # Increment attempt counter
        self.recovery_attempts[error_id] = attempts + 1
        
        await self.logger.info(
            "Starting automated recovery",
            error_id=error_id,
            attempt_number=attempts + 1,
            max_attempts=self.max_recovery_attempts
        )
        
        try:
            # Execute recovery with timeout
            recovery_result = await asyncio.wait_for(
                self.error_engine.execute_auto_recovery(error_id),
                timeout=self.recovery_timeout_seconds
            )
            
            await self.logger.info(
                "Automated recovery completed",
                error_id=error_id,
                recovery_success=recovery_result.success,
                steps_executed=len(recovery_result.steps_executed),
                steps_failed=len(recovery_result.steps_failed),
                final_status=recovery_result.final_status
            )
            
            # Clean up successful recoveries from attempt tracking
            if recovery_result.success:
                self.recovery_attempts.pop(error_id, None)
            
            return recovery_result.success
            
        except asyncio.TimeoutError:
            await self.logger.error(
                "Recovery attempt timed out",
                error_id=error_id,
                timeout_seconds=self.recovery_timeout_seconds
            )
            return False
            
        except Exception as recovery_error:
            await self.logger.error(
                "Recovery attempt failed",
                error_id=error_id,
                recovery_error=str(recovery_error),
                recovery_error_type=type(recovery_error).__name__
            )
            return False
    
    async def _handle_critical_error(self, classification, request_info: RequestInfo, original_error: Exception):
        """Handle critical errors requiring immediate attention"""
        
        await self.logger.critical(
            "CRITICAL ERROR DETECTED",
            error_id=classification.error_id,
            error_category=classification.category.value,
            error_message=str(original_error),
            estimated_impact=classification.estimated_impact,
            request_id=request_info.request_id,
            endpoint=request_info.endpoint,
            user_id=request_info.user_id
        )
        
        # Send immediate notification for critical errors
        await self._send_critical_error_notification(classification, request_info, original_error)
    
    async def _send_critical_error_notification(self, classification, request_info: RequestInfo, error: Exception):
        """Send critical error notification to monitoring systems"""
        
        # This would integrate with NTFY or other notification systems
        notification_message = (
            f"🚨 BETTY CRITICAL ERROR 🚨\n"
            f"Error ID: {classification.error_id}\n"
            f"Category: {classification.category.value}\n"
            f"Endpoint: {request_info.endpoint}\n"
            f"Time: {datetime.now(timezone.utc).isoformat()}\n"
            f"Impact: {classification.estimated_impact}\n"
            f"User: {request_info.user_id or 'Anonymous'}"
        )
        
        # Log the notification attempt
        await self.logger.critical(
            "Critical error notification sent",
            error_id=classification.error_id,
            notification_message=notification_message
        )
    
    async def _generate_error_response(self, error: Exception, 
                                     classification,
                                     request_info: RequestInfo,
                                     recovery_attempted: bool,
                                     recovery_successful: bool) -> JSONResponse:
        """Generate appropriate error response based on classification"""
        
        status_code = self._determine_status_code(error, classification)
        
        # Base error response
        error_response = {
            "error": "BETTY Memory System Error",
            "message": self._get_user_friendly_message(error, classification),
            "error_id": classification.error_id,
            "request_id": request_info.request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "severity": classification.severity.value,
            "category": classification.category.value
        }
        
        # Add recovery information if applicable
        if recovery_attempted:
            error_response["recovery"] = {
                "attempted": True,
                "successful": recovery_successful,
                "message": "Automatic recovery was attempted" + (
                    " and succeeded" if recovery_successful else " but failed"
                )
            }
        
        # Add recommendations for user action
        if classification.category.value in ["api_validation", "authentication"]:
            error_response["user_action"] = self._get_user_action_recommendation(classification)
        
        # Add debug information in development mode
        if hasattr(self.app, 'debug') and self.app.debug:
            error_response["debug_info"] = {
                "error_type": type(error).__name__,
                "classification_confidence": classification.confidence_score,
                "auto_recoverable": classification.auto_recoverable,
                "similar_errors": classification.similar_errors[:3]  # Limit to 3
            }
        
        # Add retry information for recoverable errors
        if classification.auto_recoverable and not recovery_successful:
            error_response["retry_advice"] = {
                "can_retry": True,
                "recommended_delay_seconds": 5,
                "max_retries": 3
            }
        
        return JSONResponse(
            status_code=status_code,
            content=error_response,
            headers={
                "X-Request-ID": request_info.request_id,
                "X-Error-ID": classification.error_id,
                "X-Error-Category": classification.category.value,
                "X-Recovery-Attempted": str(recovery_attempted).lower()
            }
        )
    
    def _determine_status_code(self, error: Exception, classification) -> int:
        """Determine appropriate HTTP status code"""
        
        # Handle specific exception types
        if isinstance(error, HTTPException):
            return error.status_code
        elif isinstance(error, PermissionError):
            return 403
        elif isinstance(error, FileNotFoundError):
            return 404
        elif isinstance(error, TimeoutError):
            return 408
        elif isinstance(error, ValueError):
            return 400
        
        # Handle by error category
        category_status_map = {
            "database_error": 503,
            "memory_corruption": 503,
            "api_validation": 400,
            "authentication": 401,
            "authorization": 403,
            "network_error": 502,
            "performance_degradation": 503,
            "system_resource": 503,
            "configuration_error": 500
        }
        
        return category_status_map.get(classification.category.value, 500)
    
    def _get_user_friendly_message(self, error: Exception, classification) -> str:
        """Generate user-friendly error message"""
        
        # Category-specific messages
        category_messages = {
            "database_error": "Database service temporarily unavailable. Please try again in a few moments.",
            "memory_corruption": "Memory system is performing self-repair. Please try again shortly.",
            "api_validation": f"Request validation failed: {str(error)}",
            "authentication": "Authentication failed. Please check your credentials.",
            "authorization": "You don't have permission to access this resource.",
            "network_error": "Network connectivity issue. Please try again.",
            "performance_degradation": "Service is experiencing high load. Please try again.",
            "system_resource": "System resources are temporarily limited. Please try again later.",
            "configuration_error": "System configuration issue detected. Support has been notified."
        }
        
        base_message = category_messages.get(
            classification.category.value,
            "An unexpected error occurred. Our team has been notified."
        )
        
        # Add severity context
        if classification.severity == ErrorSeverity.CRITICAL:
            base_message = f"CRITICAL: {base_message} Priority support has been notified."
        elif classification.severity == ErrorSeverity.LOW:
            base_message = f"{base_message} This is a minor issue."
        
        return base_message
    
    def _get_user_action_recommendation(self, classification) -> str:
        """Get user action recommendation based on error classification"""
        
        recommendations = {
            "api_validation": "Please check your request format and required fields.",
            "authentication": "Please verify your authentication credentials and try again.",
            "authorization": "Contact your administrator for access permissions.",
            "rate_limit_exceeded": "Please reduce your request frequency and try again later.",
            "missing_required_field": "Please ensure all required fields are included in your request.",
            "invalid_request_format": "Please check your request format against the API documentation."
        }
        
        subcategory = classification.subcategory.value if classification.subcategory else None
        return recommendations.get(subcategory, recommendations.get(classification.category.value, 
                                                                   "Please contact support if the issue persists."))
    
    # Security helper methods
    
    def _get_client_ip(self, request: Request) -> Optional[str]:
        """Extract client IP address from request"""
        # Check X-Forwarded-For header first (for proxy setups)
        forwarded_for = request.headers.get('x-forwarded-for')
        if forwarded_for:
            # Get the first IP (original client)
            return forwarded_for.split(',')[0].strip()
        
        # Check X-Real-IP header
        real_ip = request.headers.get('x-real-ip')
        if real_ip:
            return real_ip
        
        # Fall back to direct connection
        if request.client:
            return request.client.host
        
        return None
    
    async def _is_suspicious_ip(self, ip_address: str) -> bool:
        """Check if IP address is marked as suspicious"""
        return ip_address in self.suspicious_ips
    
    async def _mark_ip_suspicious(self, ip_address: str, reasons: List[str]):
        """Mark IP address as suspicious"""
        self.suspicious_ips[ip_address] = {
            "reasons": reasons,
            "marked_at": datetime.now(timezone.utc),
            "incident_count": self.suspicious_ips.get(ip_address, {}).get("incident_count", 0) + 1
        }
    
    def _contains_sql_injection_pattern(self, value: str) -> bool:
        """Check for potential SQL injection patterns"""
        sql_patterns = [
            r"(\bunion\b.*\bselect\b)",
            r"(\bselect\b.*\bfrom\b)",
            r"(\bdrop\b.*\btable\b)",
            r"(\binsert\b.*\binto\b)",
            r"(\bdelete\b.*\bfrom\b)",
            r"(--\s*$)",
            r"(;\s*drop\b)",
            r"(\bor\b.*=.*\bor\b)"
        ]
        
        for pattern in sql_patterns:
            if re.search(pattern, value.lower()):
                return True
        
        return False
    
    async def _check_auth_anomalies(self, ip_address: str, request_info: RequestInfo) -> bool:
        """Check for authentication anomalies"""
        if not ip_address:
            return False
        
        # Track failed authentication attempts
        now = datetime.now(timezone.utc)
        if ip_address not in self.failed_auth_attempts:
            self.failed_auth_attempts[ip_address] = []
        
        # Clean old attempts (keep only last hour)
        cutoff_time = now - timedelta(hours=1)
        self.failed_auth_attempts[ip_address] = [
            attempt for attempt in self.failed_auth_attempts[ip_address] 
            if attempt > cutoff_time
        ]
        
        # Check if too many attempts from this IP
        recent_attempts = len(self.failed_auth_attempts[ip_address])
        if recent_attempts > 10:  # More than 10 failed attempts in last hour
            return True
        
        return False
    
    async def _handle_slow_request(self, request_info: RequestInfo, duration_ms: float):
        """Handle slow request analysis"""
        
        await self.logger.performance(
            "Slow request detected",
            request_id=request_info.request_id,
            endpoint=request_info.endpoint,
            method=request_info.method,
            duration_ms=duration_ms,
            threshold_ms=self.slow_request_threshold_ms,
            user_id=request_info.user_id
        )
        
        # Additional analysis could be added here
        # e.g., database query analysis, memory profiling, etc.
    
    def _get_response_size(self, response: Response) -> Optional[int]:
        """Get response size if available"""
        if hasattr(response, 'headers') and 'content-length' in response.headers:
            try:
                return int(response.headers['content-length'])
            except (ValueError, TypeError):
                pass
        return None
    
    def get_middleware_stats(self) -> Dict[str, Any]:
        """Get middleware performance statistics"""
        return {
            "active_errors": len(self.active_errors),
            "recovery_attempts": len(self.recovery_attempts),
            "suspicious_ips": len(self.suspicious_ips),
            "failed_auth_tracking": len(self.failed_auth_attempts),
            "auto_recovery_enabled": self.enable_auto_recovery,
            "max_recovery_attempts": self.max_recovery_attempts,
            "recovery_timeout_seconds": self.recovery_timeout_seconds
        }