# ABOUTME: Comprehensive test suite for Betty's Enhanced Error Handling & Logging Architecture
# ABOUTME: Tests error classification, recovery, monitoring, and alerting functionality

import pytest
import asyncio
import time
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, AsyncMock
from fastapi import HTTPException
from fastapi.testclient import TestClient

from core.error_classification import (
    ErrorClassificationEngine, ErrorContext, ErrorSeverity, 
    ErrorCategory, ErrorSubcategory, get_error_classification_engine
)
from core.enhanced_logging import (
    EnhancedStructuredLogger, ComponentType, LogLevel,
    get_enhanced_logger, configure_enhanced_logging
)
from services.error_monitoring_service import (
    ErrorMonitoringService, AlertSeverity, AlertManager,
    ErrorTrendAnalyzer, get_monitoring_service
)
from middleware.error_handling import BettyErrorHandlingMiddleware

# Configure logging for tests
configure_enhanced_logging("DEBUG")

class TestErrorClassificationEngine:
    """Test suite for the ErrorClassificationEngine"""
    
    @pytest.fixture
    def engine(self):
        """Create a fresh error classification engine for each test"""
        return ErrorClassificationEngine()
    
    @pytest.fixture
    def sample_error_context(self):
        """Create a sample error context for testing"""
        return ErrorContext(
            timestamp=datetime.now(timezone.utc),
            user_id="test-user-123",
            session_id="session-456",
            project_id="project-789",
            endpoint="/api/test",
            method="POST",
            request_id="req-123",
            database_operations=["SELECT * FROM patterns"],
            performance_metrics={"response_time_ms": 1500.0},
            system_state={"memory_usage_percent": 75.0, "cpu_usage_percent": 60.0}
        )
    
    @pytest.mark.asyncio
    async def test_classify_database_timeout_error(self, engine, sample_error_context):
        """Test classification of database timeout errors"""
        error = TimeoutError("Database connection timeout occurred")
        
        classification = await engine.classify_error(error, sample_error_context)
        
        assert classification.category == ErrorCategory.DATABASE_ERROR
        assert classification.subcategory == ErrorSubcategory.CONNECTION_TIMEOUT
        assert classification.severity == ErrorSeverity.HIGH
        assert classification.auto_recoverable is True
        assert classification.confidence_score >= 0.8
        assert "Connection timeout pattern matched" in classification.classification_reasons
        assert classification.classification_time_ms > 0
    
    @pytest.mark.asyncio
    async def test_classify_memory_corruption_error(self, engine, sample_error_context):
        """Test classification of memory corruption errors"""
        error = ValueError("Pattern inconsistent across databases")
        
        classification = await engine.classify_error(error, sample_error_context)
        
        assert classification.category == ErrorCategory.MEMORY_CORRUPTION
        assert classification.subcategory == ErrorSubcategory.PATTERN_INCONSISTENCY
        assert classification.severity == ErrorSeverity.HIGH
        assert classification.auto_recoverable is True
        assert classification.confidence_score >= 0.8
    
    @pytest.mark.asyncio
    async def test_classify_validation_error(self, engine, sample_error_context):
        """Test classification of API validation errors"""
        error = ValueError("Invalid request format: missing required field")
        
        classification = await engine.classify_error(error, sample_error_context)
        
        assert classification.category == ErrorCategory.API_VALIDATION
        assert classification.auto_recoverable is False
        assert classification.severity == ErrorSeverity.LOW
    
    @pytest.mark.asyncio
    async def test_context_enhancement(self, engine, sample_error_context):
        """Test that error classification is enhanced by context"""
        # Error in database endpoint should be classified as database error
        sample_error_context.endpoint = "/api/database/query"
        error = Exception("Generic error message")
        
        classification = await engine.classify_error(error, sample_error_context)
        
        # Should be enhanced to database category due to endpoint context
        assert "Database endpoint context" in classification.classification_reasons
    
    @pytest.mark.asyncio
    async def test_get_remediation_strategy(self, engine, sample_error_context):
        """Test remediation strategy generation"""
        error = TimeoutError("Database connection timeout")
        classification = await engine.classify_error(error, sample_error_context)
        
        remediation_plan = await engine.get_remediation_strategy(classification)
        
        assert remediation_plan.plan_id is not None
        assert len(remediation_plan.steps) > 0
        assert remediation_plan.total_estimated_time_minutes > 0
        assert 0 <= remediation_plan.success_probability <= 1
        assert remediation_plan.error_classification.error_id == classification.error_id
    
    @pytest.mark.asyncio
    async def test_automated_recovery_database_error(self, engine, sample_error_context):
        """Test automated recovery for database errors"""
        error = TimeoutError("Database connection timeout")
        classification = await engine.classify_error(error, sample_error_context)
        
        # Attempt recovery
        recovery_result = await engine.execute_auto_recovery(classification.error_id)
        
        assert recovery_result.error_id == classification.error_id
        assert recovery_result.success is True  # Should succeed for recoverable errors
        assert len(recovery_result.steps_executed) > 0
        assert recovery_result.final_status is not None
        assert recovery_result.error_resolution_time_minutes >= 0
    
    @pytest.mark.asyncio
    async def test_automated_recovery_non_recoverable(self, engine, sample_error_context):
        """Test automated recovery for non-recoverable errors"""
        error = ValueError("Invalid request format")
        classification = await engine.classify_error(error, sample_error_context)
        
        # Attempt recovery (should fail for non-recoverable errors)
        recovery_result = await engine.execute_auto_recovery(classification.error_id)
        
        assert recovery_result.success is False
        assert recovery_result.manual_intervention_needed is True
    
    @pytest.mark.asyncio
    async def test_similar_error_detection(self, engine, sample_error_context):
        """Test detection of similar errors"""
        # Create multiple similar errors
        error1 = TimeoutError("Database connection timeout")
        error2 = TimeoutError("Connection timeout to database")
        
        classification1 = await engine.classify_error(error1, sample_error_context)
        classification2 = await engine.classify_error(error2, sample_error_context)
        
        # Second error should have similar errors listed
        assert len(classification2.similar_errors) >= 0

class TestEnhancedStructuredLogger:
    """Test suite for the EnhancedStructuredLogger"""
    
    @pytest.fixture
    def logger(self):
        """Create a test logger"""
        return get_enhanced_logger("test_logger", ComponentType.API_GATEWAY)
    
    @pytest.mark.asyncio
    async def test_basic_logging(self, logger):
        """Test basic logging functionality"""
        await logger.info("Test message", test_field="test_value")
        await logger.error("Test error", error_code=500)
        await logger.warning("Test warning", component="test")
        
        # Logger should track metrics
        assert logger._request_count >= 3
        assert logger._error_count >= 1
    
    @pytest.mark.asyncio
    async def test_api_request_logging(self, logger):
        """Test API request logging"""
        from core.enhanced_logging import RequestInfo
        
        request_info = RequestInfo(
            request_id="test-123",
            method="POST",
            endpoint="/api/test",
            user_id="user-456",
            ip_address="127.0.0.1"
        )
        
        await logger.log_api_request(
            request_info=request_info,
            status_code=200,
            duration_ms=150.0,
            response_size_bytes=1024
        )
        
        # Should complete without errors
        assert True
    
    @pytest.mark.asyncio
    async def test_database_operation_logging(self, logger):
        """Test database operation logging"""
        from core.enhanced_logging import DatabaseOperationInfo, DatabaseOperation
        
        db_info = DatabaseOperationInfo(
            operation_id="op-123",
            database_type="postgresql",
            operation=DatabaseOperation.SELECT,
            table_name="patterns",
            query="SELECT * FROM patterns WHERE id = $1",
            duration_ms=25.5,
            affected_rows=1
        )
        
        await logger.log_database_operation(db_info)
        
        # Should complete without errors
        assert True
    
    @pytest.mark.asyncio
    async def test_performance_metrics_logging(self, logger):
        """Test performance metrics logging"""
        from core.enhanced_logging import PerformanceMetrics
        
        metrics = PerformanceMetrics(
            metric_name="response_time",
            value=150.0,
            unit="ms",
            timestamp=datetime.now(timezone.utc),
            component=ComponentType.API_GATEWAY,
            threshold_warning=1000.0,
            threshold_critical=5000.0
        )
        
        await logger.log_performance_metrics(metrics)
        
        # Should complete without errors
        assert True
    
    @pytest.mark.asyncio
    async def test_security_event_logging(self, logger):
        """Test security event logging"""
        from core.enhanced_logging import SecurityEvent
        
        event = SecurityEvent(
            event_type="authentication_failure",
            severity="high",
            user_id="user-123",
            ip_address="192.168.1.100",
            resource_accessed="/api/sensitive",
            action_attempted="POST",
            success=False,
            threat_indicators=["multiple_failed_attempts", "suspicious_ip"]
        )
        
        await logger.log_security_event(event)
        
        # Should complete without errors
        assert True
    
    def test_performance_summary(self, logger):
        """Test performance summary generation"""
        summary = logger.get_performance_summary()
        
        assert "logger_name" in summary
        assert "component" in summary
        assert "uptime_hours" in summary
        assert "total_requests" in summary
        assert "error_count" in summary
        assert "error_rate_percent" in summary

class TestErrorTrendAnalyzer:
    """Test suite for the ErrorTrendAnalyzer"""
    
    @pytest.fixture
    def analyzer(self):
        """Create a fresh trend analyzer for each test"""
        return ErrorTrendAnalyzer(analysis_window_hours=1)
    
    @pytest.fixture
    def sample_classification(self):
        """Create a sample error classification"""
        from core.error_classification import ErrorClassification
        return ErrorClassification(
            error_id="test-error-123",
            category=ErrorCategory.DATABASE_ERROR,
            subcategory=ErrorSubcategory.CONNECTION_TIMEOUT,
            severity=ErrorSeverity.HIGH,
            confidence_score=0.9,
            classification_reasons=["Test classification"],
            auto_recoverable=True
        )
    
    def test_add_error(self, analyzer, sample_classification):
        """Test adding error to trend analysis"""
        context = {"component": "database", "endpoint": "/api/test"}
        
        analyzer.add_error(sample_classification, context)
        
        assert len(analyzer.error_history) == 1
        assert len(analyzer.pattern_cache) == 1
        
        pattern_key = f"{sample_classification.category.value}:{sample_classification.subcategory.value}"
        assert pattern_key in analyzer.pattern_cache
    
    def test_error_spike_detection(self, analyzer, sample_classification):
        """Test error spike detection"""
        context = {"component": "database"}
        
        # Add many errors to trigger spike detection
        for _ in range(25):
            analyzer.add_error(sample_classification, context)
        
        trends = analyzer.analyze_trends()
        
        # Should detect error spike
        spike_trends = [t for t in trends["trends"] if t.get("trend_type") == "error_spike"]
        assert len(spike_trends) > 0
        assert spike_trends[0]["error_rate_per_minute"] > analyzer.trend_thresholds["error_spike"]
    
    def test_pattern_tracking(self, analyzer, sample_classification):
        """Test error pattern tracking"""
        context = {"component": "database"}
        
        # Add same type of error multiple times
        for _ in range(5):
            analyzer.add_error(sample_classification, context)
        
        pattern_key = f"{sample_classification.category.value}:{sample_classification.subcategory.value}"
        pattern = analyzer.pattern_cache[pattern_key]
        
        assert pattern.occurrence_count == 5
        assert "database" in pattern.affected_components
        assert sample_classification.severity.value in pattern.severity_distribution

class TestAlertManager:
    """Test suite for the AlertManager"""
    
    @pytest.fixture
    def alert_manager(self):
        """Create a fresh alert manager for each test"""
        return AlertManager()
    
    @pytest.mark.asyncio
    async def test_create_alert(self, alert_manager):
        """Test alert creation"""
        alert = await alert_manager.create_alert(
            severity=AlertSeverity.HIGH,
            title="Test Alert",
            description="This is a test alert",
            component="test_component",
            recommended_actions=["Action 1", "Action 2"]
        )
        
        assert alert.alert_id is not None
        assert alert.severity == AlertSeverity.HIGH
        assert alert.title == "Test Alert"
        assert alert.component == "test_component"
        assert len(alert.recommended_actions) == 2
        assert alert.alert_id in alert_manager.active_alerts
    
    @pytest.mark.asyncio
    async def test_alert_rate_limiting(self, alert_manager):
        """Test alert rate limiting"""
        # Create multiple alerts in quick succession
        alerts_created = 0
        for i in range(10):
            alert = await alert_manager.create_alert(
                severity=AlertSeverity.CRITICAL,
                title=f"Test Alert {i}",
                description="Rate limit test",
                component="test_component"
            )
            if alert.alert_id in alert_manager.active_alerts:
                alerts_created += 1
        
        # Should be rate limited (not all alerts created)
        assert alerts_created < 10
    
    @pytest.mark.asyncio 
    async def test_resolve_alert(self, alert_manager):
        """Test alert resolution"""
        # Create alert
        alert = await alert_manager.create_alert(
            severity=AlertSeverity.MEDIUM,
            title="Test Alert",
            description="Test description",
            component="test_component"
        )
        
        alert_id = alert.alert_id
        assert alert_id in alert_manager.active_alerts
        
        # Resolve alert
        success = await alert_manager.resolve_alert(alert_id, "Test resolution")
        
        assert success is True
        assert alert_id not in alert_manager.active_alerts
    
    def test_alert_summary(self, alert_manager):
        """Test alert summary generation"""
        summary = alert_manager.get_alert_summary()
        
        assert "active_alerts_count" in summary
        assert "alerts_by_severity" in summary
        assert "alerts_by_component" in summary

class TestErrorMonitoringService:
    """Test suite for the ErrorMonitoringService"""
    
    @pytest.fixture
    def monitoring_service(self):
        """Create a fresh monitoring service for each test"""
        return ErrorMonitoringService()
    
    @pytest.mark.asyncio
    async def test_service_startup_shutdown(self, monitoring_service):
        """Test service startup and shutdown"""
        # Start monitoring
        await monitoring_service.start_monitoring()
        
        status = monitoring_service.get_service_status()
        assert status["monitoring_enabled"] is True
        assert status["background_tasks"]["trend_analysis_running"] is True
        assert status["background_tasks"]["health_check_running"] is True
        
        # Stop monitoring
        await monitoring_service.stop_monitoring()
        
        # Allow time for tasks to stop
        await asyncio.sleep(0.1)
        
        status = monitoring_service.get_service_status()
        assert status["background_tasks"]["trend_analysis_running"] is False
        assert status["background_tasks"]["health_check_running"] is False
    
    @pytest.mark.asyncio
    async def test_error_reporting(self, monitoring_service):
        """Test error reporting to monitoring service"""
        from core.error_classification import ErrorClassification
        
        classification = ErrorClassification(
            error_id="test-error-456",
            category=ErrorCategory.DATABASE_ERROR,
            subcategory=ErrorSubcategory.CONNECTION_TIMEOUT,
            severity=ErrorSeverity.HIGH,
            confidence_score=0.9,
            classification_reasons=["Test classification"],
            auto_recoverable=True
        )
        
        context = {"component": "database", "endpoint": "/api/test"}
        
        await monitoring_service.report_error(classification, context)
        
        # Error should be added to trend analyzer
        assert len(monitoring_service.trend_analyzer.error_history) == 1
    
    @pytest.mark.asyncio
    async def test_critical_error_alerting(self, monitoring_service):
        """Test that critical errors trigger immediate alerts"""
        from core.error_classification import ErrorClassification
        
        classification = ErrorClassification(
            error_id="critical-error-789",
            category=ErrorCategory.MEMORY_CORRUPTION,
            subcategory=ErrorSubcategory.DATA_CORRUPTION,
            severity=ErrorSeverity.CRITICAL,
            confidence_score=0.95,
            classification_reasons=["Critical data corruption detected"],
            auto_recoverable=False,
            estimated_impact="Critical system failure"
        )
        
        context = {"component": "memory_engine"}
        
        await monitoring_service.report_error(classification, context)
        
        # Should have created a critical alert
        active_alerts = monitoring_service.get_active_alerts()
        critical_alerts = [a for a in active_alerts if a.severity == AlertSeverity.CRITICAL]
        assert len(critical_alerts) > 0
    
    def test_service_status(self, monitoring_service):
        """Test service status reporting"""
        status = monitoring_service.get_service_status()
        
        assert "monitoring_enabled" in status
        assert "analysis_interval_seconds" in status
        assert "health_check_interval_seconds" in status
        assert "trend_analyzer" in status
        assert "alert_manager" in status
        assert "background_tasks" in status

class TestBettyErrorHandlingMiddleware:
    """Test suite for the BettyErrorHandlingMiddleware"""
    
    @pytest.fixture
    def mock_app(self):
        """Create a mock FastAPI app"""
        from fastapi import FastAPI
        app = FastAPI()
        return app
    
    @pytest.fixture
    def middleware(self, mock_app):
        """Create error handling middleware"""
        return BettyErrorHandlingMiddleware(
            app=mock_app,
            enable_auto_recovery=True,
            max_recovery_attempts=2,
            recovery_timeout_seconds=5
        )
    
    @pytest.mark.asyncio
    async def test_security_checks(self, middleware):
        """Test security check functionality"""
        from fastapi import Request
        
        # Mock request with suspicious patterns
        mock_request = Mock(spec=Request)
        mock_request.method = "POST"
        mock_request.url.path = "/api/test"
        mock_request.client.host = "192.168.1.100"
        mock_request.headers = {"user-agent": "test-agent"}
        mock_request.query_params = {"param": "SELECT * FROM users; DROP TABLE users;"}  # SQL injection pattern
        
        request_info = await middleware._create_request_info(mock_request, "test-123")
        security_issues = await middleware._perform_security_checks(mock_request, request_info)
        
        assert "potential_sql_injection" in security_issues
    
    @pytest.mark.asyncio
    async def test_error_context_creation(self, middleware):
        """Test error context creation"""
        from fastapi import Request
        
        mock_request = Mock(spec=Request)
        mock_request.method = "GET"
        mock_request.url.path = "/api/database/query"
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "test"}
        
        request_info = await middleware._create_request_info(mock_request, "test-456")
        
        error = Exception("Test error")
        context = await middleware._create_error_context(error, mock_request, request_info)
        
        assert context.endpoint == "/api/database/query"
        assert context.method == "GET"
        assert context.request_id == "test-456"
        assert context.performance_metrics is not None
        assert context.system_state is not None
    
    def test_middleware_stats(self, middleware):
        """Test middleware statistics"""
        stats = middleware.get_middleware_stats()
        
        assert "active_errors" in stats
        assert "recovery_attempts" in stats
        assert "suspicious_ips" in stats
        assert "auto_recovery_enabled" in stats

class TestIntegration:
    """Integration tests for the complete error handling system"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_error_flow(self):
        """Test complete error handling flow from classification to recovery"""
        # Initialize components
        engine = ErrorClassificationEngine()
        monitoring_service = ErrorMonitoringService()
        
        # Create error context
        context = ErrorContext(
            timestamp=datetime.now(timezone.utc),
            user_id="integration-test-user",
            endpoint="/api/integration/test",
            method="POST",
            request_id="integration-test-123"
        )
        
        # Simulate database timeout error
        error = TimeoutError("Database connection timeout during integration test")
        
        # 1. Classify error
        classification = await engine.classify_error(error, context)
        assert classification.category == ErrorCategory.DATABASE_ERROR
        assert classification.auto_recoverable is True
        
        # 2. Report to monitoring service
        await monitoring_service.report_error(classification, {"component": "database"})
        
        # 3. Attempt automated recovery
        if classification.auto_recoverable:
            recovery_result = await engine.execute_auto_recovery(classification.error_id)
            assert recovery_result.success is True
        
        # 4. Verify monitoring service tracked the error
        trend_analysis = monitoring_service.get_trend_analysis()
        assert trend_analysis["total_errors_analyzed"] > 0
    
    @pytest.mark.asyncio
    async def test_alert_generation_flow(self):
        """Test alert generation and management flow"""
        monitoring_service = ErrorMonitoringService()
        
        # Create multiple high-severity errors to trigger alerts
        from core.error_classification import ErrorClassification
        
        for i in range(3):
            classification = ErrorClassification(
                error_id=f"alert-test-{i}",
                category=ErrorCategory.MEMORY_CORRUPTION,
                subcategory=ErrorSubcategory.INTEGRITY_VIOLATION,
                severity=ErrorSeverity.CRITICAL,
                confidence_score=0.9,
                classification_reasons=["Integration test alert"],
                auto_recoverable=False,
                estimated_impact="Critical system impact"
            )
            
            await monitoring_service.report_error(classification, {"component": "memory_system"})
        
        # Should have generated critical alerts
        active_alerts = monitoring_service.get_active_alerts()
        critical_alerts = [a for a in active_alerts if a.severity == AlertSeverity.CRITICAL]
        assert len(critical_alerts) >= 1
        
        # Test alert resolution
        if critical_alerts:
            alert_id = critical_alerts[0].alert_id
            success = await monitoring_service.alert_manager.resolve_alert(alert_id, "Integration test resolution")
            assert success is True

# Performance and load testing

class TestPerformance:
    """Performance tests for the error handling system"""
    
    @pytest.mark.asyncio
    async def test_error_classification_performance(self):
        """Test error classification performance under load"""
        engine = ErrorClassificationEngine()
        
        context = ErrorContext(
            timestamp=datetime.now(timezone.utc),
            user_id="perf-test",
            endpoint="/api/performance/test",
            method="POST"
        )
        
        start_time = time.time()
        
        # Classify 100 errors
        tasks = []
        for i in range(100):
            error = TimeoutError(f"Performance test error {i}")
            tasks.append(engine.classify_error(error, context))
        
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        total_time = (end_time - start_time) * 1000  # Convert to milliseconds
        avg_time_per_classification = total_time / 100
        
        # Performance target: <100ms per classification
        assert avg_time_per_classification < 100.0
        assert len(results) == 100
        assert all(r.classification_time_ms > 0 for r in results)
    
    @pytest.mark.asyncio
    async def test_logging_performance(self):
        """Test logging performance under load"""
        logger = get_enhanced_logger("performance_test", ComponentType.API_GATEWAY)
        
        start_time = time.time()
        
        # Log 1000 messages
        tasks = []
        for i in range(1000):
            tasks.append(logger.info(f"Performance test message {i}", test_id=i))
        
        await asyncio.gather(*tasks)
        
        end_time = time.time()
        total_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        # Performance target: <1ms per log entry
        avg_time_per_log = total_time / 1000
        assert avg_time_per_log < 1.0

# Utility functions for testing

def create_mock_request(method="GET", path="/api/test", ip="127.0.0.1", headers=None):
    """Create a mock request for testing"""
    from fastapi import Request
    
    mock_request = Mock(spec=Request)
    mock_request.method = method
    mock_request.url.path = path
    mock_request.client.host = ip
    mock_request.headers = headers or {"user-agent": "test-client"}
    mock_request.query_params = {}
    
    return mock_request

def create_sample_error_classification(error_id="test", category=ErrorCategory.UNKNOWN, severity=ErrorSeverity.MEDIUM):
    """Create a sample error classification for testing"""
    from core.error_classification import ErrorClassification
    
    return ErrorClassification(
        error_id=error_id,
        category=category,
        subcategory=None,
        severity=severity,
        confidence_score=0.8,
        classification_reasons=["Test classification"],
        auto_recoverable=True
    )

if __name__ == "__main__":
    # Run tests with: python -m pytest tests/test_enhanced_error_handling.py -v
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])