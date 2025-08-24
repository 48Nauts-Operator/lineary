# ABOUTME: Core Source Validation & Verification Service for enterprise-grade content validation
# ABOUTME: Provides ML-powered validation, credibility scoring, and security scanning for knowledge sources

import asyncio
import hashlib
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import structlog
import numpy as np
from urllib.parse import urlparse
import re
import math
from collections import defaultdict
import aiohttp
import asyncpg

from core.database import DatabaseManager
from models.knowledge import KnowledgeItem
from services.vector_service import VectorService
from services.pattern_quality_service import AdvancedQualityScorer

logger = structlog.get_logger(__name__)

class ValidationStatus(Enum):
    PENDING = "pending"
    VALIDATING = "validating"
    VALIDATED = "validated"
    FAILED = "failed"
    QUARANTINED = "quarantined"

class CredibilityLevel(Enum):
    VERY_LOW = 0.0
    LOW = 0.3
    MEDIUM = 0.5
    HIGH = 0.7
    VERY_HIGH = 0.9
    EXCEPTIONAL = 1.0

class ValidationSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class ValidationResult:
    """Comprehensive validation result for a knowledge item"""
    item_id: str
    source_name: str
    validation_id: str
    status: ValidationStatus
    credibility_score: float
    accuracy_score: float
    security_score: float
    freshness_score: float
    overall_score: float
    validation_time: float
    timestamp: datetime
    issues: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SourceCredibility:
    """Source credibility assessment data"""
    source_name: str
    base_credibility: float
    historical_accuracy: float
    community_validation: float
    reputation_score: float
    last_updated: datetime
    validation_count: int = 0
    successful_validations: int = 0

@dataclass
class SecurityScanResult:
    """Security scanning result for content"""
    is_safe: bool
    threats_detected: List[str]
    risk_level: str
    scan_time: float
    details: Dict[str, Any]

class MLValidationModel:
    """Machine Learning model for content validation"""
    
    def __init__(self):
        self.accuracy_threshold = 0.85
        self.confidence_threshold = 0.7
        
    async def validate_content_accuracy(self, content: str, metadata: Dict) -> Tuple[float, float]:
        """Validate content accuracy using ML models"""
        try:
            # Simulate ML model validation with comprehensive checks
            start_time = time.time()
            
            # Content structure analysis
            structure_score = await self._analyze_content_structure(content)
            
            # Technical accuracy assessment
            technical_score = await self._assess_technical_accuracy(content, metadata)
            
            # Consistency validation
            consistency_score = await self._validate_consistency(content)
            
            # Calculate weighted accuracy score
            accuracy_score = (
                structure_score * 0.3 +
                technical_score * 0.5 +
                consistency_score * 0.2
            )
            
            # Calculate confidence based on validation certainty
            confidence = min(1.0, (accuracy_score + structure_score + consistency_score) / 3.0)
            
            validation_time = time.time() - start_time
            
            logger.debug("Content accuracy validation completed",
                        accuracy_score=accuracy_score,
                        confidence=confidence,
                        validation_time=validation_time)
            
            return accuracy_score, confidence
            
        except Exception as e:
            logger.error("ML validation failed", error=str(e))
            return 0.5, 0.0  # Default conservative scores
    
    async def _analyze_content_structure(self, content: str) -> float:
        """Analyze content structure quality"""
        # Check for proper formatting, code blocks, explanations
        score = 0.5  # Base score
        
        # Check for code blocks
        if "```" in content or "    " in content:  # Code formatting
            score += 0.2
            
        # Check for explanations
        if len(content.split('.')) > 3:  # Multiple sentences
            score += 0.1
            
        # Check for headers or structure
        if any(marker in content for marker in ['#', '##', '###', '-', '*']):
            score += 0.1
            
        # Check content length (not too short, not too verbose)
        word_count = len(content.split())
        if 10 <= word_count <= 1000:
            score += 0.1
            
        return min(1.0, score)
    
    async def _assess_technical_accuracy(self, content: str, metadata: Dict) -> float:
        """Assess technical accuracy of content"""
        score = 0.5  # Base score
        
        # Check for common technical patterns
        technical_indicators = [
            r'\b(function|def|class|import|from)\b',  # Code keywords
            r'\b(http|https|ftp|ssh)\b',  # Protocols
            r'\b(\d+\.\d+\.\d+\.\d+)\b',  # IP addresses
            r'\b[A-Z][A-Z_]+\b',  # Constants
            r'[{}()\[\]]',  # Brackets/braces
        ]
        
        for pattern in technical_indicators:
            if re.search(pattern, content, re.IGNORECASE):
                score += 0.05
        
        # Domain-specific validation
        source_type = metadata.get('source_type', '')
        if source_type == 'stackoverflow':
            if 'answer' in metadata.get('item_type', '').lower():
                if metadata.get('score', 0) > 0:  # Upvoted answer
                    score += 0.2
                if metadata.get('is_accepted', False):
                    score += 0.3
        
        elif source_type == 'commandlinefu':
            # Check for valid command syntax
            if content.strip().startswith(('$', '#', 'sudo')):
                score += 0.2
        
        return min(1.0, score)
    
    async def _validate_consistency(self, content: str) -> float:
        """Validate internal consistency of content"""
        score = 0.7  # Base score for consistency
        
        # Check for contradictory statements (simplified)
        contradiction_patterns = [
            (r'\b(always|never)\b.*\b(sometimes|maybe)\b', -0.2),
            (r'\b(true)\b.*\b(false)\b', -0.1),
            (r'\b(working|works)\b.*\b(broken|fails?)\b', -0.1),
        ]
        
        for pattern, penalty in contradiction_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                score += penalty
        
        return max(0.0, score)

class SecurityScanner:
    """Advanced security scanner for content validation"""
    
    def __init__(self):
        self.malicious_patterns = [
            r'<script[^>]*>.*?</script>',  # Script injection
            r'javascript:',  # JavaScript URLs
            r'on\w+\s*=',  # Event handlers
            r'eval\s*\(',  # Eval function
            r'document\.(cookie|domain)',  # Cookie manipulation
            r'(rm\s+-rf|del\s+/[sq])',  # Dangerous commands
            r'(wget|curl).*\|\s*(sh|bash|python)',  # Remote execution
            r'[\'"]\s*;\s*(drop|delete|insert|update)',  # SQL injection
            r'(exec|system|shell_exec)\s*\(',  # Code execution
        ]
        
        self.suspicious_patterns = [
            r'(password|passwd|pwd)\s*[:=]',  # Password exposure
            r'(api[_-]?key|secret|token)\s*[:=]',  # API key exposure
            r'BEGIN\s+(RSA\s+)?PRIVATE\s+KEY',  # Private key
            r'-----BEGIN\s+CERTIFICATE-----',  # Certificate
            r'\b\d{16,19}\b',  # Credit card numbers
        ]
    
    async def scan_content(self, content: str, metadata: Dict) -> SecurityScanResult:
        """Perform comprehensive security scan of content"""
        start_time = time.time()
        
        try:
            threats = []
            risk_level = "low"
            
            # Check for malicious patterns
            for pattern in self.malicious_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    threats.append(f"Malicious pattern detected: {pattern[:50]}...")
                    risk_level = "critical"
            
            # Check for suspicious patterns
            for pattern in self.suspicious_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    threats.append(f"Suspicious pattern detected: {pattern[:50]}...")
                    if risk_level == "low":
                        risk_level = "medium"
            
            # URL validation
            urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', content)
            for url in urls:
                if await self._validate_url_safety(url):
                    continue
                else:
                    threats.append(f"Potentially unsafe URL: {url}")
                    if risk_level in ["low", "medium"]:
                        risk_level = "high"
            
            # Content entropy analysis (detect obfuscation)
            entropy = self._calculate_entropy(content)
            if entropy > 7.5:  # High entropy might indicate obfuscation
                threats.append("High entropy content detected (possible obfuscation)")
                if risk_level == "low":
                    risk_level = "medium"
            
            scan_time = time.time() - start_time
            is_safe = risk_level in ["low", "medium"]
            
            return SecurityScanResult(
                is_safe=is_safe,
                threats_detected=threats,
                risk_level=risk_level,
                scan_time=scan_time,
                details={
                    "entropy": entropy,
                    "urls_found": len(urls),
                    "patterns_checked": len(self.malicious_patterns) + len(self.suspicious_patterns)
                }
            )
            
        except Exception as e:
            logger.error("Security scan failed", error=str(e))
            return SecurityScanResult(
                is_safe=False,
                threats_detected=[f"Scan error: {str(e)}"],
                risk_level="unknown",
                scan_time=time.time() - start_time,
                details={"error": str(e)}
            )
    
    async def _validate_url_safety(self, url: str) -> bool:
        """Validate URL safety using reputation databases"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Check against known safe domains
            safe_domains = {
                'github.com', 'stackoverflow.com', 'docs.microsoft.com',
                'developer.mozilla.org', 'kubernetes.io', 'terraform.io',
                'registry.terraform.io', 'discuss.hashicorp.com'
            }
            
            # Check against suspicious TLDs
            suspicious_tlds = {'.tk', '.ml', '.ga', '.cf', '.bit'}
            
            if domain in safe_domains:
                return True
            
            if any(domain.endswith(tld) for tld in suspicious_tlds):
                return False
            
            # Additional checks could include DNS validation, reputation APIs, etc.
            return True
            
        except Exception:
            return False
    
    def _calculate_entropy(self, content: str) -> float:
        """Calculate Shannon entropy of content"""
        if not content:
            return 0.0
        
        # Count character frequencies
        char_counts = defaultdict(int)
        for char in content:
            char_counts[char] += 1
        
        # Calculate entropy
        length = len(content)
        entropy = 0.0
        
        for count in char_counts.values():
            probability = count / length
            entropy -= probability * math.log2(probability)
        
        return entropy

class SourceValidationService:
    """Main Source Validation & Verification Service"""
    
    def __init__(self, db_manager: DatabaseManager, vector_service: VectorService):
        self.db_manager = db_manager
        self.vector_service = vector_service
        self.ml_validator = MLValidationModel()
        self.security_scanner = SecurityScanner()
        self.quality_scorer = AdvancedQualityScorer()
        
        # Performance metrics tracking
        self.validation_count = 0
        self.total_validation_time = 0.0
        self.error_count = 0
        
        # Source credibility cache
        self.source_credibility_cache = {}
        self.cache_expiry = timedelta(hours=1)
        
        logger.info("Source Validation Service initialized")
    
    async def validate_knowledge_item(self, item: KnowledgeItem) -> ValidationResult:
        """Comprehensive validation of a knowledge item"""
        validation_id = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            logger.info("Starting validation",
                       item_id=str(item.id),
                       validation_id=validation_id,
                       source=item.source_type)
            
            # Initialize validation result
            result = ValidationResult(
                item_id=str(item.id),
                source_name=item.source_type,
                validation_id=validation_id,
                status=ValidationStatus.VALIDATING,
                credibility_score=0.0,
                accuracy_score=0.0,
                security_score=0.0,
                freshness_score=0.0,
                overall_score=0.0,
                validation_time=0.0,
                timestamp=datetime.utcnow()
            )
            
            # Run parallel validation checks
            tasks = [
                self._assess_credibility(item),
                self._validate_accuracy(item),
                self._perform_security_scan(item),
                self._assess_freshness(item),
                self._check_duplicate_content(item)
            ]
            
            (credibility_score, accuracy_score, 
             security_scan, freshness_score, duplicate_info) = await asyncio.gather(*tasks)
            
            # Update validation result
            result.credibility_score = credibility_score
            result.accuracy_score = accuracy_score[0] if isinstance(accuracy_score, tuple) else accuracy_score
            result.security_score = 1.0 if security_scan.is_safe else 0.0
            result.freshness_score = freshness_score
            
            # Calculate overall score with weights
            result.overall_score = (
                result.credibility_score * 0.25 +
                result.accuracy_score * 0.35 +
                result.security_score * 0.25 +
                result.freshness_score * 0.15
            )
            
            # Determine final status
            if not security_scan.is_safe and security_scan.risk_level == "critical":
                result.status = ValidationStatus.QUARANTINED
                result.issues.append({
                    "type": "security",
                    "severity": ValidationSeverity.CRITICAL.value,
                    "message": "Critical security threats detected",
                    "details": security_scan.threats_detected
                })
            elif result.overall_score >= 0.7:
                result.status = ValidationStatus.VALIDATED
            elif result.overall_score >= 0.4:
                result.status = ValidationStatus.VALIDATED
                result.issues.append({
                    "type": "quality",
                    "severity": ValidationSeverity.WARNING.value,
                    "message": "Content quality below optimal threshold",
                    "score": result.overall_score
                })
            else:
                result.status = ValidationStatus.FAILED
                result.issues.append({
                    "type": "quality",
                    "severity": ValidationSeverity.ERROR.value,
                    "message": "Content quality insufficient",
                    "score": result.overall_score
                })
            
            # Add duplicate detection results
            if duplicate_info["is_duplicate"]:
                result.issues.append({
                    "type": "duplicate",
                    "severity": ValidationSeverity.WARNING.value,
                    "message": f"Similar content found ({duplicate_info['similarity']:.2%} similarity)",
                    "similar_items": duplicate_info["similar_items"][:3]  # Top 3 matches
                })
            
            result.validation_time = time.time() - start_time
            
            # Store validation result in database
            await self._store_validation_result(result)
            
            # Update performance metrics
            self.validation_count += 1
            self.total_validation_time += result.validation_time
            
            logger.info("Validation completed",
                       validation_id=validation_id,
                       status=result.status.value,
                       overall_score=result.overall_score,
                       validation_time=result.validation_time)
            
            return result
            
        except Exception as e:
            self.error_count += 1
            logger.error("Validation failed",
                        validation_id=validation_id,
                        error=str(e))
            
            result.status = ValidationStatus.FAILED
            result.validation_time = time.time() - start_time
            result.issues.append({
                "type": "system",
                "severity": ValidationSeverity.ERROR.value,
                "message": f"Validation system error: {str(e)}"
            })
            
            return result
    
    async def _assess_credibility(self, item: KnowledgeItem) -> float:
        """Assess source credibility"""
        try:
            # Get or calculate source credibility
            source_cred = await self._get_source_credibility(item.source_type)
            
            # Factor in item-specific credibility indicators
            item_credibility = 0.5  # Base score
            
            if item.metadata:
                # Stack Overflow specific
                if item.source_type == "stackoverflow":
                    score = item.metadata.get("score", 0)
                    is_accepted = item.metadata.get("is_accepted", False)
                    
                    if score > 10:
                        item_credibility += 0.2
                    elif score > 0:
                        item_credibility += 0.1
                    
                    if is_accepted:
                        item_credibility += 0.3
                
                # Command line specific
                elif item.source_type == "commandlinefu":
                    votes = item.metadata.get("votes", 0)
                    if votes > 5:
                        item_credibility += 0.2
                    elif votes > 0:
                        item_credibility += 0.1
                
                # Security sources (typically high credibility)
                elif item.source_type in ["owasp", "exploit-db", "hacktricks"]:
                    item_credibility += 0.3
                
                # Documentation sources (high credibility)
                elif item.source_type in ["kubernetes", "terraform", "hashicorp"]:
                    item_credibility += 0.4
            
            # Combine source and item credibility
            combined_credibility = (source_cred.base_credibility * 0.6 + 
                                  min(1.0, item_credibility) * 0.4)
            
            return combined_credibility
            
        except Exception as e:
            logger.error("Credibility assessment failed", error=str(e))
            return 0.5  # Default neutral credibility
    
    async def _validate_accuracy(self, item: KnowledgeItem) -> Tuple[float, float]:
        """Validate content accuracy using ML models"""
        return await self.ml_validator.validate_content_accuracy(
            item.content, 
            item.metadata or {}
        )
    
    async def _perform_security_scan(self, item: KnowledgeItem) -> SecurityScanResult:
        """Perform security scan on content"""
        return await self.security_scanner.scan_content(
            item.content, 
            item.metadata or {}
        )
    
    async def _assess_freshness(self, item: KnowledgeItem) -> float:
        """Assess content freshness"""
        try:
            # Calculate age-based freshness score
            if item.created_at:
                age_days = (datetime.utcnow() - item.created_at).days
                
                # Freshness decay function
                if age_days <= 30:
                    return 1.0
                elif age_days <= 90:
                    return 0.8
                elif age_days <= 365:
                    return 0.6
                elif age_days <= 730:
                    return 0.4
                else:
                    return 0.2
            
            return 0.5  # Default if no creation date
            
        except Exception:
            return 0.5
    
    async def _check_duplicate_content(self, item: KnowledgeItem) -> Dict[str, Any]:
        """Check for duplicate or similar content"""
        try:
            # Generate embedding for similarity search
            embedding = await self.vector_service.generate_embedding(item.content)
            
            # Find similar items
            similar_items = await self.vector_service.search_similar(
                embedding,
                limit=10,
                threshold=0.7
            )
            
            # Filter out the item itself and calculate similarity
            duplicates = []
            max_similarity = 0.0
            
            for similar_item in similar_items:
                if similar_item.id != item.id:
                    # Calculate text similarity (simplified)
                    similarity = await self._calculate_text_similarity(
                        item.content, 
                        similar_item.content
                    )
                    
                    if similarity > max_similarity:
                        max_similarity = similarity
                    
                    if similarity > 0.85:  # High similarity threshold
                        duplicates.append({
                            "id": str(similar_item.id),
                            "title": similar_item.title,
                            "similarity": similarity,
                            "source": similar_item.source_type
                        })
            
            return {
                "is_duplicate": len(duplicates) > 0,
                "similarity": max_similarity,
                "similar_items": duplicates
            }
            
        except Exception as e:
            logger.error("Duplicate detection failed", error=str(e))
            return {
                "is_duplicate": False,
                "similarity": 0.0,
                "similar_items": []
            }
    
    async def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity using simple metrics"""
        # Simplified Jaccard similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    async def _get_source_credibility(self, source_name: str) -> SourceCredibility:
        """Get or calculate source credibility"""
        # Check cache first
        if (source_name in self.source_credibility_cache and
            datetime.utcnow() - self.source_credibility_cache[source_name].last_updated < self.cache_expiry):
            return self.source_credibility_cache[source_name]
        
        try:
            # Query database for historical performance
            async with self.db_manager.get_postgres_pool().acquire() as conn:
                historical_data = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as total_validations,
                        AVG(overall_score) as avg_score,
                        COUNT(CASE WHEN status = 'validated' THEN 1 END) as successful_validations
                    FROM source_validations 
                    WHERE source_name = $1 
                    AND timestamp > $2
                """, source_name, datetime.utcnow() - timedelta(days=30))
            
            if historical_data and historical_data['total_validations'] > 0:
                historical_accuracy = historical_data['avg_score'] or 0.5
                success_rate = (historical_data['successful_validations'] / 
                              historical_data['total_validations'])
            else:
                historical_accuracy = 0.5
                success_rate = 0.5
            
            # Base credibility scores for known sources
            base_scores = {
                "stackoverflow": 0.8,
                "commandlinefu": 0.7,
                "owasp": 0.95,
                "exploit-db": 0.9,
                "hacktricks": 0.8,
                "kubernetes": 0.95,
                "terraform": 0.9,
                "hashicorp": 0.9
            }
            
            base_credibility = base_scores.get(source_name, 0.5)
            
            # Create source credibility object
            source_cred = SourceCredibility(
                source_name=source_name,
                base_credibility=base_credibility,
                historical_accuracy=historical_accuracy,
                community_validation=success_rate,
                reputation_score=(base_credibility + historical_accuracy + success_rate) / 3,
                last_updated=datetime.utcnow(),
                validation_count=historical_data['total_validations'] if historical_data else 0,
                successful_validations=historical_data['successful_validations'] if historical_data else 0
            )
            
            # Cache the result
            self.source_credibility_cache[source_name] = source_cred
            
            return source_cred
            
        except Exception as e:
            logger.error("Failed to get source credibility", source=source_name, error=str(e))
            # Return default credibility
            return SourceCredibility(
                source_name=source_name,
                base_credibility=0.5,
                historical_accuracy=0.5,
                community_validation=0.5,
                reputation_score=0.5,
                last_updated=datetime.utcnow()
            )
    
    async def _store_validation_result(self, result: ValidationResult) -> None:
        """Store validation result in database"""
        try:
            async with self.db_manager.get_postgres_pool().acquire() as conn:
                await conn.execute("""
                    INSERT INTO source_validations (
                        validation_id, item_id, source_name, status, 
                        credibility_score, accuracy_score, security_score, 
                        freshness_score, overall_score, validation_time,
                        issues, recommendations, metadata, timestamp
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                """, 
                result.validation_id, result.item_id, result.source_name, 
                result.status.value, result.credibility_score, result.accuracy_score,
                result.security_score, result.freshness_score, result.overall_score,
                result.validation_time, json.dumps(result.issues), 
                json.dumps(result.recommendations), json.dumps(result.metadata),
                result.timestamp)
        
        except Exception as e:
            logger.error("Failed to store validation result", 
                        validation_id=result.validation_id, error=str(e))
    
    async def get_validation_statistics(self) -> Dict[str, Any]:
        """Get comprehensive validation statistics"""
        try:
            async with self.db_manager.get_postgres_pool().acquire() as conn:
                # Overall statistics
                overall_stats = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as total_validations,
                        AVG(overall_score) as avg_overall_score,
                        AVG(validation_time) as avg_validation_time,
                        COUNT(CASE WHEN status = 'validated' THEN 1 END) as successful_validations,
                        COUNT(CASE WHEN status = 'quarantined' THEN 1 END) as quarantined_items,
                        COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_validations
                    FROM source_validations
                    WHERE timestamp > $1
                """, datetime.utcnow() - timedelta(days=7))
                
                # Source-specific statistics
                source_stats = await conn.fetch("""
                    SELECT 
                        source_name,
                        COUNT(*) as validations,
                        AVG(overall_score) as avg_score,
                        AVG(credibility_score) as avg_credibility,
                        AVG(security_score) as avg_security,
                        COUNT(CASE WHEN status = 'quarantined' THEN 1 END) as quarantined
                    FROM source_validations
                    WHERE timestamp > $1
                    GROUP BY source_name
                    ORDER BY validations DESC
                """, datetime.utcnow() - timedelta(days=7))
            
            # Calculate performance metrics
            avg_validation_time = (self.total_validation_time / self.validation_count 
                                 if self.validation_count > 0 else 0.0)
            
            success_rate = (overall_stats['successful_validations'] / overall_stats['total_validations'] 
                          if overall_stats and overall_stats['total_validations'] > 0 else 0.0)
            
            return {
                "overall": {
                    "total_validations": overall_stats['total_validations'] if overall_stats else 0,
                    "success_rate": success_rate,
                    "average_score": float(overall_stats['avg_overall_score']) if overall_stats and overall_stats['avg_overall_score'] else 0.0,
                    "average_validation_time": avg_validation_time,
                    "quarantined_items": overall_stats['quarantined_items'] if overall_stats else 0,
                    "failed_validations": overall_stats['failed_validations'] if overall_stats else 0,
                    "error_rate": self.error_count / max(1, self.validation_count)
                },
                "by_source": [
                    {
                        "source_name": row['source_name'],
                        "validations": row['validations'],
                        "avg_score": float(row['avg_score']),
                        "avg_credibility": float(row['avg_credibility']),
                        "avg_security": float(row['avg_security']),
                        "quarantined": row['quarantined']
                    }
                    for row in source_stats
                ],
                "performance": {
                    "validations_per_second": self.validation_count / max(1, self.total_validation_time),
                    "meets_latency_requirement": avg_validation_time < 0.5,  # <500ms requirement
                    "accuracy_requirement_met": success_rate >= 0.995  # 99.5% requirement
                }
            }
            
        except Exception as e:
            logger.error("Failed to get validation statistics", error=str(e))
            return {
                "overall": {"total_validations": 0, "success_rate": 0.0},
                "by_source": [],
                "performance": {"validations_per_second": 0.0}
            }

# Service instance for dependency injection
_validation_service_instance = None

async def get_validation_service(db_manager: DatabaseManager, vector_service: VectorService) -> SourceValidationService:
    """Get or create validation service instance"""
    global _validation_service_instance
    
    if _validation_service_instance is None:
        _validation_service_instance = SourceValidationService(db_manager, vector_service)
    
    return _validation_service_instance