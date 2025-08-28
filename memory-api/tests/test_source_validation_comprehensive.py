# ABOUTME: Comprehensive test suite for Source Validation & Verification System
# ABOUTME: Security-focused testing with penetration testing scenarios, compliance validation, and performance benchmarks

import pytest
import asyncio
import json
import hashlib
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any, List
import structlog

from services.source_validation_framework import (
    SourceValidationFramework, ValidationResult, SourceCredibility,
    ValidationStatus, ValidationSeverity, ThreatType
)
from core.database import DatabaseManager
from services.vector_service import VectorService

logger = structlog.get_logger(__name__)

# Test fixtures and setup

@pytest.fixture
async def db_manager():
    """Mock database manager for testing"""
    mock_db = Mock(spec=DatabaseManager)
    
    # Mock PostgreSQL pool
    mock_pool = Mock()
    mock_conn = Mock()
    mock_conn.fetchrow = AsyncMock()
    mock_conn.fetchval = AsyncMock()
    mock_conn.fetch = AsyncMock()
    mock_conn.execute = AsyncMock()
    mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
    mock_pool.acquire.return_value.__aexit__ = AsyncMock()
    mock_db.get_postgres_pool.return_value = mock_pool
    
    # Mock Neo4j session
    mock_session = Mock()
    mock_session.run = AsyncMock()
    mock_db.get_neo4j_session.return_value.__aenter__.return_value = mock_session
    mock_db.get_neo4j_session.return_value.__aexit__ = AsyncMock()
    
    # Mock Qdrant client
    mock_qdrant = Mock()
    mock_qdrant.get_collections = AsyncMock(return_value=[])
    mock_db.qdrant_client = mock_qdrant
    
    # Mock Redis client
    mock_redis = Mock()
    mock_redis.ping = AsyncMock()
    mock_db.redis = mock_redis
    
    return mock_db

@pytest.fixture
async def vector_service():
    """Mock vector service for testing"""
    mock_vector = Mock(spec=VectorService)
    mock_vector.initialize = AsyncMock()
    mock_vector.close = AsyncMock()
    return mock_vector

@pytest.fixture
async def validation_framework(db_manager, vector_service):
    """Create validation framework instance for testing"""
    framework = SourceValidationFramework(db_manager, vector_service)
    yield framework

@pytest.fixture
def sample_content():
    """Sample content for validation testing"""
    return {
        "title": "Sample Security Pattern",
        "content": "This is a legitimate security configuration example.",
        "code": "#!/bin/bash\necho 'Hello, World!'",
        "tags": ["security", "configuration"],
        "metadata": {
            "author": "security_team",
            "created_at": "2025-08-10T12:00:00Z"
        }
    }

@pytest.fixture
def sample_source_info():
    """Sample source information for testing"""
    return {
        "source_id": "test_source_001",
        "url": "https://example.com/security-docs",
        "type": "documentation",
        "metadata": {
            "category": "security",
            "reputation": "high"
        }
    }

@pytest.fixture
def malicious_content():
    """Malicious content samples for threat detection testing"""
    return {
        "sql_injection": {
            "title": "Database Query",
            "content": "SELECT * FROM users WHERE id = 1; DROP TABLE users; --",
            "code": "SELECT * FROM users WHERE id = 1 UNION SELECT password FROM admin_users"
        },
        "xss_attack": {
            "title": "Web Form",
            "content": "User input processing",
            "code": "<script>alert('XSS');</script><img src=x onerror=alert('XSS')>"
        },
        "malware_signature": {
            "title": "System Command",
            "content": "File processing utility",
            "code": "eval(base64_decode($_POST['payload'])); system('rm -rf /');"
        },
        "phishing_content": {
            "title": "URGENT ACTION REQUIRED - Verify Your Account Immediately",
            "content": "Your account will be suspended. Click here now to verify immediately. Limited time offer expires soon!",
            "url": "http://suspicious-domain.com/verify-account"
        }
    }

# Core Validation Tests

class TestSourceCredibilityAssessment:
    """Test suite for source credibility assessment functionality"""

    @pytest.mark.asyncio
    async def test_valid_source_credibility_assessment(self, validation_framework, sample_source_info):
        """Test credibility assessment for a valid source"""
        
        with patch.object(validation_framework, '_check_source_uptime', return_value=99.5):
            with patch.object(validation_framework, '_assess_historical_reliability', return_value=95.0):
                with patch.object(validation_framework, '_get_community_rating', return_value=90.0):
                    with patch.object(validation_framework, '_validate_ssl_certificate', return_value=True):
                        with patch.object(validation_framework, '_check_threat_intelligence', return_value=0.95):
                            with patch.object(validation_framework, '_assess_domain_reputation', return_value=5):
                                
                                credibility = await validation_framework.validate_source_credibility(sample_source_info)
                                
                                assert isinstance(credibility, SourceCredibility)
                                assert credibility.source_id == sample_source_info['source_id']
                                assert 0.8 <= credibility.reputation_score <= 1.0
                                assert credibility.uptime_percentage >= 99.0
                                assert credibility.ssl_validity is True
                                assert credibility.threat_intelligence_score >= 0.9

    @pytest.mark.asyncio
    async def test_low_credibility_source_assessment(self, validation_framework):
        """Test credibility assessment for a low-credibility source"""
        
        suspicious_source = {
            "source_id": "suspicious_source_001",
            "url": "http://untrusted-domain.com",
            "type": "unknown"
        }
        
        with patch.object(validation_framework, '_check_source_uptime', return_value=20.0):
            with patch.object(validation_framework, '_assess_historical_reliability', return_value=30.0):
                with patch.object(validation_framework, '_get_community_rating', return_value=25.0):
                    with patch.object(validation_framework, '_validate_ssl_certificate', return_value=False):
                        with patch.object(validation_framework, '_check_threat_intelligence', return_value=0.2):
                            with patch.object(validation_framework, '_assess_domain_reputation', return_value=1):
                                
                                credibility = await validation_framework.validate_source_credibility(suspicious_source)
                                
                                assert credibility.reputation_score <= 0.5
                                assert credibility.ssl_validity is False
                                assert credibility.threat_intelligence_score <= 0.3

    @pytest.mark.asyncio
    async def test_credibility_caching(self, validation_framework, sample_source_info):
        """Test that credibility assessments are properly cached"""
        
        with patch.object(validation_framework, '_check_source_uptime', return_value=99.5) as mock_uptime:
            
            # First call
            credibility1 = await validation_framework.validate_source_credibility(sample_source_info)
            
            # Second call (should use cache)
            credibility2 = await validation_framework.validate_source_credibility(sample_source_info)
            
            assert credibility1.source_id == credibility2.source_id
            assert credibility1.reputation_score == credibility2.reputation_score
            
            # Uptime check should only be called once (first time)
            mock_uptime.assert_called_once()

    @pytest.mark.asyncio
    async def test_credibility_performance_requirements(self, validation_framework, sample_source_info):
        """Test that credibility assessment meets performance requirements"""
        
        start_time = time.time()
        
        with patch.object(validation_framework, '_check_source_uptime', return_value=99.5):
            with patch.object(validation_framework, '_assess_historical_reliability', return_value=95.0):
                with patch.object(validation_framework, '_get_community_rating', return_value=90.0):
                    with patch.object(validation_framework, '_validate_ssl_certificate', return_value=True):
                        with patch.object(validation_framework, '_check_threat_intelligence', return_value=0.95):
                            with patch.object(validation_framework, '_assess_domain_reputation', return_value=5):
                                
                                await validation_framework.validate_source_credibility(sample_source_info)
        
        assessment_time = time.time() - start_time
        
        # Should complete within 2 seconds for performance requirements
        assert assessment_time < 2.0


class TestContentSecurityValidation:
    """Test suite for content security validation functionality"""

    @pytest.mark.asyncio
    async def test_legitimate_content_validation(self, validation_framework, sample_content, sample_source_info):
        """Test validation of legitimate, safe content"""
        
        result = await validation_framework.validate_content_security(sample_content, sample_source_info)
        
        assert isinstance(result, ValidationResult)
        assert result.status == ValidationStatus.VALIDATED
        assert result.severity in [ValidationSeverity.LOW, ValidationSeverity.MEDIUM]
        assert len(result.threat_types) == 0
        assert 0.0 <= result.confidence_score <= 1.0
        assert result.content_hash is not None

    @pytest.mark.asyncio
    async def test_malware_detection(self, validation_framework, malicious_content, sample_source_info):
        """Test detection of malware signatures"""
        
        result = await validation_framework.validate_content_security(
            malicious_content['malware_signature'], sample_source_info
        )
        
        assert result.status in [ValidationStatus.REJECTED, ValidationStatus.QUARANTINED]
        assert result.severity in [ValidationSeverity.HIGH, ValidationSeverity.CRITICAL]
        assert ThreatType.MALWARE in result.threat_types
        assert result.confidence_score >= 0.8

    @pytest.mark.asyncio
    async def test_sql_injection_detection(self, validation_framework, malicious_content, sample_source_info):
        """Test detection of SQL injection attacks"""
        
        result = await validation_framework.validate_content_security(
            malicious_content['sql_injection'], sample_source_info
        )
        
        assert result.status in [ValidationStatus.REJECTED, ValidationStatus.QUARANTINED]
        assert ThreatType.INJECTION_ATTACK in result.threat_types
        assert result.confidence_score >= 0.9

    @pytest.mark.asyncio
    async def test_xss_attack_detection(self, validation_framework, malicious_content, sample_source_info):
        """Test detection of XSS attacks"""
        
        result = await validation_framework.validate_content_security(
            malicious_content['xss_attack'], sample_source_info
        )
        
        assert result.status in [ValidationStatus.REJECTED, ValidationStatus.MONITORING]
        assert ThreatType.INJECTION_ATTACK in result.threat_types

    @pytest.mark.asyncio
    async def test_phishing_detection(self, validation_framework, malicious_content, sample_source_info):
        """Test detection of phishing attempts"""
        
        result = await validation_framework.validate_content_security(
            malicious_content['phishing_content'], sample_source_info
        )
        
        assert result.status in [ValidationStatus.REJECTED, ValidationStatus.MONITORING]
        assert ThreatType.PHISHING in result.threat_types

    @pytest.mark.asyncio
    async def test_validation_performance_requirements(self, validation_framework, sample_content, sample_source_info):
        """Test that content validation meets <500ms latency requirement"""
        
        start_time = time.time()
        
        await validation_framework.validate_content_security(sample_content, sample_source_info)
        
        validation_time = time.time() - start_time
        
        # Should complete within 500ms per requirement
        assert validation_time < 0.5

    @pytest.mark.asyncio
    async def test_validation_accuracy_requirements(self, validation_framework, malicious_content, sample_source_info):
        """Test that malicious content detection meets 99.9% accuracy requirement"""
        
        # Test multiple malicious content types
        malicious_samples = list(malicious_content.values())
        detected_threats = 0
        
        for sample in malicious_samples:
            result = await validation_framework.validate_content_security(sample, sample_source_info)
            if len(result.threat_types) > 0:
                detected_threats += 1
        
        # Should detect threats in all malicious samples (100% in this test)
        detection_rate = detected_threats / len(malicious_samples)
        assert detection_rate >= 0.999  # 99.9% requirement

    @pytest.mark.asyncio
    async def test_content_hash_generation(self, validation_framework):
        """Test content hash generation for integrity verification"""
        
        content1 = {"test": "data", "number": 123}
        content2 = {"test": "data", "number": 123}
        content3 = {"test": "different", "number": 123}
        
        hash1 = validation_framework._generate_content_hash(content1)
        hash2 = validation_framework._generate_content_hash(content2)
        hash3 = validation_framework._generate_content_hash(content3)
        
        # Same content should generate same hash
        assert hash1 == hash2
        
        # Different content should generate different hash
        assert hash1 != hash3
        
        # Hashes should be proper SHA-256 format
        assert len(hash1) == 64  # SHA-256 hex string length
        assert all(c in '0123456789abcdef' for c in hash1)


class TestDataIntegrityVerification:
    """Test suite for data integrity verification functionality"""

    @pytest.mark.asyncio
    async def test_data_integrity_verification_success(self, validation_framework):
        """Test successful data integrity verification"""
        
        content = {"test": "data", "integrity": "check"}
        expected_hash = validation_framework._generate_content_hash(content)
        
        result = await validation_framework.verify_data_integrity(content, expected_hash)
        
        assert result['integrity_verified'] is True
        assert result['tamper_detected'] is False
        assert result['current_hash'] == expected_hash
        assert 'integrity_proof' in result

    @pytest.mark.asyncio
    async def test_data_integrity_verification_tamper_detection(self, validation_framework):
        """Test tamper detection in data integrity verification"""
        
        content = {"test": "data", "integrity": "check"}
        wrong_hash = "1234567890abcdef" * 4  # Wrong hash
        
        result = await validation_framework.verify_data_integrity(content, wrong_hash)
        
        assert result['integrity_verified'] is False
        assert result['tamper_detected'] is True
        assert result['current_hash'] != wrong_hash

    @pytest.mark.asyncio
    async def test_digital_signature_generation(self, validation_framework):
        """Test digital signature generation for content"""
        
        content = {"test": "signature", "data": "verification"}
        
        signature = validation_framework._generate_digital_signature(content)
        
        assert isinstance(signature, bytes)
        assert len(signature) > 0

    @pytest.mark.asyncio
    async def test_integrity_verification_without_expected_hash(self, validation_framework):
        """Test integrity verification when no expected hash is provided"""
        
        content = {"test": "data", "no": "expected_hash"}
        
        result = await validation_framework.verify_data_integrity(content, None)
        
        assert result['integrity_verified'] is True  # Should pass without comparison
        assert result['current_hash'] is not None
        assert result['expected_hash'] is None


class TestSourceHealthMonitoring:
    """Test suite for source health monitoring functionality"""

    @pytest.mark.asyncio
    async def test_source_health_monitoring(self, validation_framework):
        """Test source health monitoring for multiple sources"""
        
        sources = [
            {"source_id": "source1", "url": "https://example1.com", "type": "api"},
            {"source_id": "source2", "url": "https://example2.com", "type": "docs"},
            {"source_id": "source3", "url": "https://example3.com", "type": "feed"}
        ]
        
        with patch.object(validation_framework, '_check_source_health') as mock_health:
            mock_health.side_effect = [
                {"status": "healthy", "response_time": 0.1},
                {"status": "degraded", "response_time": 2.0},
                {"status": "failed", "error": "Connection timeout"}
            ]
            
            results = await validation_framework.monitor_source_health(sources)
            
            assert results['sources_monitored'] == 3
            assert results['healthy_sources'] == 1
            assert results['degraded_sources'] == 1
            assert results['failed_sources'] == 1
            assert len(results['source_details']) == 3

    @pytest.mark.asyncio
    async def test_source_health_check_individual(self, validation_framework):
        """Test individual source health check"""
        
        source = {"source_id": "test_source", "url": "https://example.com"}
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = Mock()
            mock_response.status = 200
            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
            
            result = await validation_framework._check_source_health(source)
            
            assert result['status'] in ['healthy', 'degraded']
            assert 'response_time' in result
            assert 'http_status' in result

    @pytest.mark.asyncio
    async def test_source_health_check_failure(self, validation_framework):
        """Test source health check failure handling"""
        
        source = {"source_id": "failing_source", "url": "https://nonexistent.invalid"}
        
        result = await validation_framework._check_source_health(source)
        
        assert result['status'] == 'failed'
        assert 'error' in result


class TestComplianceAndAuditing:
    """Test suite for compliance and auditing functionality"""

    @pytest.mark.asyncio
    async def test_compliance_report_generation(self, validation_framework):
        """Test SOC2/GDPR compliance report generation"""
        
        start_date = datetime.utcnow() - timedelta(days=30)
        end_date = datetime.utcnow()
        
        # Mock database responses
        validation_framework.db_manager.get_postgres_pool().acquire.return_value.__aenter__.return_value.fetchrow.side_effect = [
            {
                'total_validations': 1000,
                'validated_count': 950,
                'rejected_count': 45,
                'quarantined_count': 5,
                'avg_confidence': 0.92,
                'unique_sources': 8
            },
            {
                'avg_validation_time': 0.35,
                'max_validation_time': 0.48,
                'min_validation_time': 0.15
            }
        ]
        
        validation_framework.db_manager.get_postgres_pool().acquire.return_value.__aenter__.return_value.fetch.return_value = [
            {'threat_types': ['malware'], 'occurrence_count': 10, 'avg_confidence': 0.95},
            {'threat_types': ['phishing'], 'occurrence_count': 5, 'avg_confidence': 0.88}
        ]
        
        report = await validation_framework.generate_compliance_report(start_date, end_date)
        
        assert 'report_metadata' in report
        assert 'validation_statistics' in report
        assert 'threat_detection_summary' in report
        assert 'performance_metrics' in report
        assert 'compliance_status' in report
        assert report['compliance_status']['soc2_controls'] is not None
        assert report['compliance_status']['gdpr_compliance'] is not None

    @pytest.mark.asyncio
    async def test_soc2_compliance_assessment(self, validation_framework):
        """Test SOC2 compliance assessment"""
        
        compliance = validation_framework._assess_soc2_compliance()
        
        required_controls = [
            'CC6.1_logical_access',
            'CC6.2_authentication',
            'CC6.3_authorization',
            'CC7.1_threat_detection',
            'CC7.2_monitoring'
        ]
        
        for control in required_controls:
            assert control in compliance
            assert compliance[control] in ['compliant', 'non_compliant', 'not_applicable']

    @pytest.mark.asyncio
    async def test_gdpr_compliance_assessment(self, validation_framework):
        """Test GDPR compliance assessment"""
        
        compliance = validation_framework._assess_gdpr_compliance()
        
        required_articles = [
            'article_5_principles',
            'article_25_data_protection',
            'article_32_security',
            'article_33_breach_notification'
        ]
        
        for article in required_articles:
            assert article in compliance
            assert compliance[article] in ['compliant', 'non_compliant']

    @pytest.mark.asyncio
    async def test_audit_trail_completeness(self, validation_framework, sample_content, sample_source_info):
        """Test that all validation operations generate proper audit trails"""
        
        result = await validation_framework.validate_content_security(sample_content, sample_source_info)
        
        assert len(result.audit_trail) > 0
        
        audit_entry = result.audit_trail[0]
        required_fields = ['timestamp', 'action', 'content_hash', 'validation_time', 'source']
        
        for field in required_fields:
            assert field in audit_entry


class TestPerformanceAndScalability:
    """Test suite for performance and scalability requirements"""

    @pytest.mark.asyncio
    async def test_concurrent_validation_performance(self, validation_framework, sample_content, sample_source_info):
        """Test concurrent validation performance"""
        
        # Prepare multiple validation tasks
        tasks = []
        for i in range(10):
            content = {**sample_content, "id": i}
            task = validation_framework.validate_content_security(content, sample_source_info)
            tasks.append(task)
        
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        # All validations should complete successfully
        assert len(results) == 10
        assert all(isinstance(r, ValidationResult) for r in results)
        
        # Concurrent processing should be faster than sequential
        # (Allow some overhead, should be < 3 seconds for 10 concurrent validations)
        assert total_time < 3.0

    @pytest.mark.asyncio
    async def test_cache_performance_optimization(self, validation_framework, sample_content, sample_source_info):
        """Test that caching provides performance optimization"""
        
        # First validation (cache miss)
        start_time = time.time()
        result1 = await validation_framework.validate_content_security(sample_content, sample_source_info)
        first_validation_time = time.time() - start_time
        
        # Second validation (cache hit)
        start_time = time.time()
        result2 = await validation_framework.validate_content_security(sample_content, sample_source_info)
        second_validation_time = time.time() - start_time
        
        # Results should be identical
        assert result1.content_hash == result2.content_hash
        assert result1.status == result2.status
        
        # Second validation should be faster due to caching
        assert second_validation_time < first_validation_time

    @pytest.mark.asyncio
    async def test_memory_usage_limits(self, validation_framework):
        """Test memory usage remains within acceptable limits"""
        
        # Get initial cache sizes
        initial_source_cache = len(validation_framework.source_cache)
        initial_validation_cache = len(validation_framework.validation_cache)
        
        # Simulate processing many items
        for i in range(100):
            content = {"test_item": i, "data": f"test_data_{i}"}
            source_info = {"source_id": f"test_source_{i % 10}", "type": "test"}
            
            await validation_framework.validate_content_security(content, source_info)
        
        # Cache sizes should not grow excessively
        final_source_cache = len(validation_framework.source_cache)
        final_validation_cache = len(validation_framework.validation_cache)
        
        # Reasonable cache growth (not linear with processed items due to source reuse)
        assert final_source_cache - initial_source_cache <= 10
        assert final_validation_cache - initial_validation_cache <= 100

    @pytest.mark.asyncio
    async def test_statistics_collection_performance(self, validation_framework):
        """Test that statistics collection doesn't impact performance"""
        
        start_time = time.time()
        statistics = await validation_framework.get_validation_statistics()
        stats_time = time.time() - start_time
        
        # Statistics collection should be fast
        assert stats_time < 0.1
        
        # Should contain expected metrics
        assert 'performance_metrics' in statistics
        assert 'cache_statistics' in statistics
        assert 'configuration' in statistics


class TestSecurityPenetrationTests:
    """Penetration testing scenarios for security validation"""

    @pytest.mark.asyncio
    async def test_bypass_attempt_with_encoded_payload(self, validation_framework, sample_source_info):
        """Test detection of encoded malicious payloads"""
        
        # Base64 encoded malicious payload
        import base64
        malicious_payload = "system('rm -rf /');"
        encoded_payload = base64.b64encode(malicious_payload.encode()).decode()
        
        content = {
            "title": "Utility Script",
            "content": "Data processing utility",
            "code": f"eval(base64_decode('{encoded_payload}'));"
        }
        
        result = await validation_framework.validate_content_security(content, sample_source_info)
        
        # Should detect the threat despite encoding
        assert result.status in [ValidationStatus.REJECTED, ValidationStatus.QUARANTINED]
        assert len(result.threat_types) > 0

    @pytest.mark.asyncio
    async def test_polyglot_attack_detection(self, validation_framework, sample_source_info):
        """Test detection of polyglot attacks (multiple attack vectors)"""
        
        polyglot_content = {
            "title": "Mixed Content Attack",
            "content": "URGENT: Verify your account immediately or it will be suspended!",
            "code": "SELECT * FROM users; DROP TABLE users; <script>alert('XSS')</script>",
            "url": "javascript:alert('XSS')"
        }
        
        result = await validation_framework.validate_content_security(polyglot_content, sample_source_info)
        
        # Should detect multiple threat types
        assert len(result.threat_types) >= 2
        assert result.severity in [ValidationSeverity.HIGH, ValidationSeverity.CRITICAL]

    @pytest.mark.asyncio
    async def test_time_based_attack_resistance(self, validation_framework, sample_source_info):
        """Test resistance to time-based attacks"""
        
        # Simulate time-based SQL injection
        time_attack_content = {
            "title": "Database Query",
            "code": "SELECT * FROM users WHERE id = 1 AND (SELECT COUNT(*) FROM information_schema.tables) > 0"
        }
        
        result = await validation_framework.validate_content_security(time_attack_content, sample_source_info)
        
        # Should detect injection attempt
        assert ThreatType.INJECTION_ATTACK in result.threat_types

    @pytest.mark.asyncio
    async def test_social_engineering_detection(self, validation_framework, sample_source_info):
        """Test detection of social engineering attacks"""
        
        social_engineering_content = {
            "title": "Important Security Update Required",
            "content": """
            Dear valued user,
            
            We have detected suspicious activity on your account. To protect your data,
            you must verify your credentials immediately by clicking the link below.
            
            This is urgent and your account will be permanently suspended if you don't
            act within the next 24 hours.
            
            Click here to verify: http://account-verification.suspicious-domain.com
            
            Best regards,
            Security Team
            """,
            "metadata": {
                "urgency": "high",
                "action_required": True
            }
        }
        
        result = await validation_framework.validate_content_security(social_engineering_content, sample_source_info)
        
        # Should detect phishing/social engineering
        assert ThreatType.PHISHING in result.threat_types or ThreatType.SOCIAL_ENGINEERING in result.threat_types

    @pytest.mark.asyncio
    async def test_obfuscation_bypass_attempt(self, validation_framework, sample_source_info):
        """Test detection of obfuscated malicious code"""
        
        obfuscated_content = {
            "title": "Data Processing",
            "code": """
            var a = 'sys'; var b = 'tem'; var c = '('; var d = "'"; var e = 'rm'; 
            var f = ' -rf'; var g = ' /'; var h = "'"; var i = ')'; var j = ';';
            eval(a+b+c+d+e+f+g+h+i+j);
            """,
            "metadata": {"type": "javascript"}
        }
        
        result = await validation_framework.validate_content_security(obfuscated_content, sample_source_info)
        
        # Should detect the obfuscated malicious code
        assert result.status in [ValidationStatus.REJECTED, ValidationStatus.QUARANTINED]


class TestErrorHandlingAndResilience:
    """Test suite for error handling and system resilience"""

    @pytest.mark.asyncio
    async def test_database_connection_failure_handling(self, validation_framework, sample_content, sample_source_info):
        """Test handling of database connection failures"""
        
        # Mock database connection failure
        validation_framework.db_manager.get_postgres_pool.side_effect = Exception("Database connection failed")
        
        # Validation should still work (degraded mode)
        result = await validation_framework.validate_content_security(sample_content, sample_source_info)
        
        assert isinstance(result, ValidationResult)
        # Should indicate some form of degraded operation

    @pytest.mark.asyncio
    async def test_invalid_content_handling(self, validation_framework, sample_source_info):
        """Test handling of invalid or corrupted content"""
        
        invalid_contents = [
            None,
            "",
            {"malformed": float('inf')},
            {"circular_ref": None}
        ]
        
        # Add circular reference
        invalid_contents[3]["circular_ref"] = invalid_contents[3]
        
        for invalid_content in invalid_contents[:3]:  # Skip circular ref test
            try:
                result = await validation_framework.validate_content_security(invalid_content, sample_source_info)
                # Should either succeed with appropriate status or handle gracefully
                assert isinstance(result, ValidationResult)
            except Exception as e:
                # If exception is raised, it should be a well-defined validation error
                assert "validation" in str(e).lower() or "content" in str(e).lower()

    @pytest.mark.asyncio
    async def test_source_unreachable_handling(self, validation_framework):
        """Test handling of unreachable sources during credibility assessment"""
        
        unreachable_source = {
            "source_id": "unreachable_source",
            "url": "https://nonexistent.invalid",
            "type": "unreachable"
        }
        
        credibility = await validation_framework.validate_source_credibility(unreachable_source)
        
        # Should return minimal credibility score for unreachable sources
        assert credibility.reputation_score <= 0.2
        assert credibility.uptime_percentage == 0.0

    @pytest.mark.asyncio
    async def test_threat_detection_model_failure(self, validation_framework, sample_content, sample_source_info):
        """Test handling of ML model failures in threat detection"""
        
        with patch.object(validation_framework, 'ml_analytics') as mock_ml:
            mock_ml.predict_malware_probability.side_effect = Exception("ML model unavailable")
            
            result = await validation_framework.validate_content_security(sample_content, sample_source_info)
            
            # Should still perform pattern-based detection
            assert isinstance(result, ValidationResult)

    @pytest.mark.asyncio
    async def test_system_overload_handling(self, validation_framework, sample_content, sample_source_info):
        """Test system behavior under high load"""
        
        # Simulate high concurrent load
        tasks = []
        for i in range(50):
            content = {**sample_content, "load_test": i}
            task = validation_framework.validate_content_security(content, sample_source_info)
            tasks.append(task)
        
        try:
            results = await asyncio.wait_for(asyncio.gather(*tasks), timeout=10.0)
            
            # All tasks should complete or fail gracefully
            assert len(results) == 50
            assert all(isinstance(r, ValidationResult) for r in results)
            
        except asyncio.TimeoutError:
            pytest.fail("System failed to handle load within acceptable time")


# Performance benchmark tests

@pytest.mark.benchmark
class TestPerformanceBenchmarks:
    """Performance benchmark tests for validation system"""

    @pytest.mark.asyncio
    async def test_validation_latency_benchmark(self, validation_framework, sample_content, sample_source_info):
        """Benchmark validation latency requirements"""
        
        latencies = []
        
        for _ in range(100):
            start_time = time.time()
            await validation_framework.validate_content_security(sample_content, sample_source_info)
            latency = time.time() - start_time
            latencies.append(latency)
        
        avg_latency = sum(latencies) / len(latencies)
        max_latency = max(latencies)
        p95_latency = sorted(latencies)[int(0.95 * len(latencies))]
        
        # Performance requirements
        assert avg_latency < 0.3  # Average under 300ms
        assert max_latency < 0.5  # Max under 500ms requirement
        assert p95_latency < 0.4  # 95th percentile under 400ms
        
        logger.info("Validation latency benchmark",
                   avg_latency=f"{avg_latency:.3f}s",
                   max_latency=f"{max_latency:.3f}s",
                   p95_latency=f"{p95_latency:.3f}s")

    @pytest.mark.asyncio
    async def test_throughput_benchmark(self, validation_framework, sample_source_info):
        """Benchmark validation throughput"""
        
        # Generate test content
        test_contents = []
        for i in range(200):
            content = {
                "id": i,
                "title": f"Test Content {i}",
                "content": f"This is test content number {i} for throughput testing.",
                "metadata": {"test_id": i}
            }
            test_contents.append(content)
        
        start_time = time.time()
        
        tasks = [
            validation_framework.validate_content_security(content, sample_source_info)
            for content in test_contents
        ]
        
        results = await asyncio.gather(*tasks)
        
        total_time = time.time() - start_time
        throughput = len(results) / total_time
        
        # Should achieve reasonable throughput
        assert throughput >= 20  # At least 20 validations per second
        
        logger.info("Validation throughput benchmark",
                   total_validations=len(results),
                   total_time=f"{total_time:.2f}s",
                   throughput=f"{throughput:.2f} validations/sec")


if __name__ == "__main__":
    # Run the test suite
    pytest.main([
        __file__,
        "-v",
        "--asyncio-mode=auto",
        "--tb=short",
        "-x"  # Stop on first failure
    ])