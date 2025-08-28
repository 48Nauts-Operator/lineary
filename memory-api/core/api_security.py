# ABOUTME: Advanced API and network security for Betty with threat detection and DDoS protection
# ABOUTME: Enterprise-grade API security with input validation, rate limiting, and attack prevention

from typing import Dict, List, Optional, Any, Set, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import re
import time
import hashlib
import ipaddress
import structlog
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import user_agents

from core.security_framework import SecurityIncidentType, IncidentSeverity
from models.auth import CurrentUser

logger = structlog.get_logger(__name__)

class ThreatType(Enum):
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    COMMAND_INJECTION = "command_injection"
    PATH_TRAVERSAL = "path_traversal"
    BRUTE_FORCE = "brute_force"
    DDoS = "ddos"
    BOT_ATTACK = "bot_attack"
    CREDENTIAL_STUFFING = "credential_stuffing"
    API_ABUSE = "api_abuse"
    RATE_LIMIT_VIOLATION = "rate_limit_violation"
    MALICIOUS_PAYLOAD = "malicious_payload"

class SecurityAction(Enum):
    ALLOW = "allow"
    BLOCK = "block"
    CHALLENGE = "challenge"
    RATE_LIMIT = "rate_limit"
    QUARANTINE = "quarantine"
    LOG_ONLY = "log_only"

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class IPReputation:
    """IP reputation information"""
    ip_address: str
    reputation_score: float = 0.5  # 0.0 = bad, 1.0 = good
    threat_types: List[ThreatType] = field(default_factory=list)
    first_seen: datetime = field(default_factory=datetime.utcnow)
    last_seen: datetime = field(default_factory=datetime.utcnow)
    request_count: int = 0
    blocked_count: int = 0
    country: Optional[str] = None
    isp: Optional[str] = None
    is_vpn: bool = False
    is_tor: bool = False
    
    def update_reputation(self, threat_detected: bool):
        """Update reputation based on threat detection"""
        self.last_seen = datetime.utcnow()
        self.request_count += 1
        
        if threat_detected:
            self.blocked_count += 1
            self.reputation_score = max(0.0, self.reputation_score - 0.1)
        else:
            # Slowly improve reputation for good behavior
            self.reputation_score = min(1.0, self.reputation_score + 0.01)

@dataclass
class ThreatDetection:
    """Threat detection result"""
    threat_detected: bool = False
    threat_types: List[ThreatType] = field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.LOW
    confidence: float = 0.0  # 0.0 to 1.0
    evidence: List[str] = field(default_factory=list)
    recommended_action: SecurityAction = SecurityAction.ALLOW
    detection_rules_triggered: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "threat_detected": self.threat_detected,
            "threat_types": [t.value for t in self.threat_types],
            "risk_level": self.risk_level.value,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "recommended_action": self.recommended_action.value,
            "detection_rules_triggered": self.detection_rules_triggered
        }

@dataclass
class RequestFingerprint:
    """Request fingerprint for bot detection"""
    user_agent_hash: str
    header_signature: str
    timing_patterns: List[float] = field(default_factory=list)
    request_patterns: List[str] = field(default_factory=list)
    entropy_score: float = 0.0  # Measure of request randomness
    
    def calculate_bot_probability(self) -> float:
        """Calculate probability that request is from a bot"""
        bot_indicators = 0
        total_indicators = 5
        
        # Check user agent patterns
        if len(self.user_agent_hash) < 10:  # Suspiciously short
            bot_indicators += 1
        
        # Check timing patterns
        if len(self.timing_patterns) > 1:
            avg_interval = sum(self.timing_patterns) / len(self.timing_patterns)
            if avg_interval < 0.1:  # Suspiciously fast
                bot_indicators += 1
        
        # Check request patterns
        unique_patterns = len(set(self.request_patterns))
        if unique_patterns < len(self.request_patterns) * 0.5:  # Repetitive patterns
            bot_indicators += 1
        
        # Check entropy (randomness)
        if self.entropy_score < 0.3:  # Low entropy suggests automation
            bot_indicators += 1
        
        # Check header signature
        if "bot" in self.header_signature.lower():
            bot_indicators += 1
        
        return bot_indicators / total_indicators

@dataclass
class RateLimitRule:
    """Rate limiting rule configuration"""
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    endpoint_pattern: str = "*"  # Glob pattern for endpoints
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    burst_limit: int = 10  # Allow burst requests
    window_size_seconds: int = 60
    
    # Advanced features
    user_based: bool = True  # Rate limit per user
    ip_based: bool = True   # Rate limit per IP
    key_based: bool = False  # Rate limit per API key
    
    # Exemptions
    whitelist_ips: Set[str] = field(default_factory=set)
    whitelist_users: Set[UUID] = field(default_factory=set)
    
    # Actions when limit exceeded
    action_on_violation: SecurityAction = SecurityAction.RATE_LIMIT
    escalation_threshold: int = 5  # Escalate action after N violations

class InputValidator:
    """Advanced input validation and sanitization"""
    
    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        re.compile(r"'(\s*|\s*or\s*|\s*and\s*|\s*union\s*|\s*select\s*|\s*insert\s*|\s*update\s*|\s*delete\s*|\s*drop\s*|\s*create\s*)", re.IGNORECASE),
        re.compile(r"(\s*|\s*or\s*|\s*and\s*)\s*\w*\s*=\s*\w*", re.IGNORECASE),
        re.compile(r"union\s+select", re.IGNORECASE),
        re.compile(r"drop\s+table", re.IGNORECASE),
        re.compile(r"insert\s+into", re.IGNORECASE)
    ]
    
    # XSS patterns
    XSS_PATTERNS = [
        re.compile(r"<script[^>]*>.*?</script>", re.IGNORECASE | re.DOTALL),
        re.compile(r"javascript:", re.IGNORECASE),
        re.compile(r"on\w+\s*=", re.IGNORECASE),
        re.compile(r"<iframe[^>]*>", re.IGNORECASE),
        re.compile(r"<object[^>]*>", re.IGNORECASE)
    ]
    
    # Command injection patterns
    COMMAND_INJECTION_PATTERNS = [
        re.compile(r"[;&|`$(){}<>]"),
        re.compile(r"(wget|curl|nc|netcat|bash|sh|cmd|powershell)", re.IGNORECASE)
    ]
    
    # Path traversal patterns
    PATH_TRAVERSAL_PATTERNS = [
        re.compile(r"\.\./"),
        re.compile(r"\.\.\\"),
        re.compile(r"/etc/passwd"),
        re.compile(r"/windows/system32", re.IGNORECASE)
    ]
    
    async def validate_input(
        self,
        data: Any,
        context: Dict[str, Any]
    ) -> ThreatDetection:
        """Comprehensive input validation"""
        
        detection = ThreatDetection()
        
        # Convert data to string for analysis
        if isinstance(data, dict):
            data_str = json.dumps(data, default=str)
        else:
            data_str = str(data)
        
        # Check for SQL injection
        sql_threats = await self._check_sql_injection(data_str)
        if sql_threats:
            detection.threat_detected = True
            detection.threat_types.append(ThreatType.SQL_INJECTION)
            detection.evidence.extend(sql_threats)
            detection.confidence = max(detection.confidence, 0.8)
        
        # Check for XSS
        xss_threats = await self._check_xss(data_str)
        if xss_threats:
            detection.threat_detected = True
            detection.threat_types.append(ThreatType.XSS)
            detection.evidence.extend(xss_threats)
            detection.confidence = max(detection.confidence, 0.7)
        
        # Check for command injection
        cmd_threats = await self._check_command_injection(data_str)
        if cmd_threats:
            detection.threat_detected = True
            detection.threat_types.append(ThreatType.COMMAND_INJECTION)
            detection.evidence.extend(cmd_threats)
            detection.confidence = max(detection.confidence, 0.9)
        
        # Check for path traversal
        path_threats = await self._check_path_traversal(data_str)
        if path_threats:
            detection.threat_detected = True
            detection.threat_types.append(ThreatType.PATH_TRAVERSAL)
            detection.evidence.extend(path_threats)
            detection.confidence = max(detection.confidence, 0.8)
        
        # Determine risk level and action
        if detection.threat_detected:
            if detection.confidence >= 0.9 or ThreatType.COMMAND_INJECTION in detection.threat_types:
                detection.risk_level = RiskLevel.CRITICAL
                detection.recommended_action = SecurityAction.BLOCK
            elif detection.confidence >= 0.7:
                detection.risk_level = RiskLevel.HIGH
                detection.recommended_action = SecurityAction.CHALLENGE
            else:
                detection.risk_level = RiskLevel.MEDIUM
                detection.recommended_action = SecurityAction.LOG_ONLY
        
        return detection
    
    async def _check_sql_injection(self, data: str) -> List[str]:
        """Check for SQL injection patterns"""
        threats = []
        for pattern in self.SQL_INJECTION_PATTERNS:
            matches = pattern.findall(data)
            if matches:
                threats.append(f"SQL injection pattern: {pattern.pattern}")
        return threats
    
    async def _check_xss(self, data: str) -> List[str]:
        """Check for XSS patterns"""
        threats = []
        for pattern in self.XSS_PATTERNS:
            if pattern.search(data):
                threats.append(f"XSS pattern: {pattern.pattern}")
        return threats
    
    async def _check_command_injection(self, data: str) -> List[str]:
        """Check for command injection patterns"""
        threats = []
        for pattern in self.COMMAND_INJECTION_PATTERNS:
            if pattern.search(data):
                threats.append(f"Command injection pattern: {pattern.pattern}")
        return threats
    
    async def _check_path_traversal(self, data: str) -> List[str]:
        """Check for path traversal patterns"""
        threats = []
        for pattern in self.PATH_TRAVERSAL_PATTERNS:
            if pattern.search(data):
                threats.append(f"Path traversal pattern: {pattern.pattern}")
        return threats

class BotDetectionEngine:
    """Advanced bot detection and mitigation"""
    
    def __init__(self):
        self.request_fingerprints: Dict[str, RequestFingerprint] = {}
        self.known_bots = self._load_known_bot_signatures()
        self.suspicious_user_agents = self._load_suspicious_user_agents()
    
    def _load_known_bot_signatures(self) -> Set[str]:
        """Load known bot user agent signatures"""
        return {
            "python-requests",
            "curl",
            "wget",
            "postman",
            "insomnia",
            "scrapy",
            "httpx",
            "aiohttp"
        }
    
    def _load_suspicious_user_agents(self) -> List[re.Pattern]:
        """Load suspicious user agent patterns"""
        return [
            re.compile(r"bot", re.IGNORECASE),
            re.compile(r"crawler", re.IGNORECASE),
            re.compile(r"spider", re.IGNORECASE),
            re.compile(r"scraper", re.IGNORECASE),
            re.compile(r"^$"),  # Empty user agent
            re.compile(r"test", re.IGNORECASE)
        ]
    
    async def analyze_request(
        self,
        request: Request,
        client_ip: str
    ) -> ThreatDetection:
        """Analyze request for bot behavior"""
        
        detection = ThreatDetection()
        
        # Extract request characteristics
        user_agent = request.headers.get("user-agent", "")
        referer = request.headers.get("referer", "")
        
        # Create request fingerprint
        fingerprint = await self._create_fingerprint(request, client_ip)
        
        # Update fingerprint history
        if client_ip in self.request_fingerprints:
            existing = self.request_fingerprints[client_ip]
            existing.timing_patterns.append(time.time())
            existing.request_patterns.append(str(request.url))
            
            # Keep last 50 patterns
            if len(existing.timing_patterns) > 50:
                existing.timing_patterns = existing.timing_patterns[-50:]
            if len(existing.request_patterns) > 50:
                existing.request_patterns = existing.request_patterns[-50:]
        else:
            self.request_fingerprints[client_ip] = fingerprint
        
        # Check for known bots
        if any(bot_sig in user_agent.lower() for bot_sig in self.known_bots):
            detection.threat_detected = True
            detection.threat_types.append(ThreatType.BOT_ATTACK)
            detection.evidence.append(f"Known bot user agent: {user_agent}")
            detection.confidence = 0.9
        
        # Check suspicious user agent patterns
        for pattern in self.suspicious_user_agents:
            if pattern.search(user_agent):
                detection.threat_detected = True
                detection.threat_types.append(ThreatType.BOT_ATTACK)
                detection.evidence.append(f"Suspicious user agent pattern: {pattern.pattern}")
                detection.confidence = max(detection.confidence, 0.6)
        
        # Behavioral analysis
        current_fingerprint = self.request_fingerprints[client_ip]
        bot_probability = current_fingerprint.calculate_bot_probability()
        
        if bot_probability > 0.7:
            detection.threat_detected = True
            detection.threat_types.append(ThreatType.BOT_ATTACK)
            detection.evidence.append(f"Bot behavior probability: {bot_probability:.2f}")
            detection.confidence = max(detection.confidence, bot_probability)
        
        # Determine action
        if detection.confidence > 0.8:
            detection.recommended_action = SecurityAction.CHALLENGE
            detection.risk_level = RiskLevel.HIGH
        elif detection.confidence > 0.5:
            detection.recommended_action = SecurityAction.RATE_LIMIT
            detection.risk_level = RiskLevel.MEDIUM
        
        return detection
    
    async def _create_fingerprint(
        self,
        request: Request,
        client_ip: str
    ) -> RequestFingerprint:
        """Create request fingerprint for bot detection"""
        
        user_agent = request.headers.get("user-agent", "")
        
        # Create header signature
        important_headers = [
            "user-agent", "accept", "accept-language", 
            "accept-encoding", "connection"
        ]
        
        header_values = []
        for header in important_headers:
            value = request.headers.get(header, "")
            header_values.append(f"{header}:{value}")
        
        header_signature = hashlib.md5("|".join(header_values).encode()).hexdigest()
        
        # Calculate entropy of user agent
        entropy_score = await self._calculate_entropy(user_agent)
        
        return RequestFingerprint(
            user_agent_hash=hashlib.md5(user_agent.encode()).hexdigest(),
            header_signature=header_signature,
            entropy_score=entropy_score
        )
    
    async def _calculate_entropy(self, text: str) -> float:
        """Calculate entropy (randomness) of text"""
        if not text:
            return 0.0
        
        char_counts = {}
        for char in text:
            char_counts[char] = char_counts.get(char, 0) + 1
        
        text_length = len(text)
        entropy = 0.0
        
        for count in char_counts.values():
            probability = count / text_length
            if probability > 0:
                entropy -= probability * (probability).bit_length()
        
        # Normalize to 0-1 range
        return min(1.0, entropy / 8.0)  # Assuming max entropy of 8

class RateLimitingEngine:
    """Advanced rate limiting with multiple strategies"""
    
    def __init__(self):
        self.rate_limit_rules: List[RateLimitRule] = []
        self.violation_tracking: Dict[str, Dict[str, Any]] = {}
        self.sliding_windows: Dict[str, List[float]] = {}
        self.default_rules = self._create_default_rules()
    
    def _create_default_rules(self) -> List[RateLimitRule]:
        """Create default rate limiting rules"""
        return [
            RateLimitRule(
                name="Authentication Endpoints",
                endpoint_pattern="/auth/*",
                requests_per_minute=10,
                requests_per_hour=100,
                burst_limit=3,
                action_on_violation=SecurityAction.BLOCK
            ),
            RateLimitRule(
                name="API Endpoints",
                endpoint_pattern="/api/*",
                requests_per_minute=100,
                requests_per_hour=2000,
                burst_limit=20
            ),
            RateLimitRule(
                name="Public Endpoints",
                endpoint_pattern="/public/*",
                requests_per_minute=200,
                requests_per_hour=5000,
                burst_limit=50
            )
        ]
    
    async def check_rate_limit(
        self,
        request: Request,
        client_ip: str,
        user: Optional[CurrentUser] = None
    ) -> ThreatDetection:
        """Check request against rate limiting rules"""
        
        detection = ThreatDetection()
        endpoint = str(request.url.path)
        
        # Find applicable rules
        applicable_rules = []
        for rule in self.default_rules + self.rate_limit_rules:
            if self._matches_pattern(endpoint, rule.endpoint_pattern):
                applicable_rules.append(rule)
        
        # Check each applicable rule
        for rule in applicable_rules:
            violation = await self._check_rule_violation(
                rule, client_ip, user, endpoint
            )
            
            if violation:
                detection.threat_detected = True
                detection.threat_types.append(ThreatType.RATE_LIMIT_VIOLATION)
                detection.evidence.append(
                    f"Rate limit exceeded for rule '{rule.name}': {violation}"
                )
                detection.confidence = 1.0
                detection.recommended_action = rule.action_on_violation
                detection.risk_level = RiskLevel.MEDIUM
                
                # Track violations for escalation
                violation_key = f"{client_ip}:{rule.id}"
                if violation_key not in self.violation_tracking:
                    self.violation_tracking[violation_key] = {
                        "count": 0,
                        "first_violation": datetime.utcnow(),
                        "last_violation": datetime.utcnow()
                    }
                
                self.violation_tracking[violation_key]["count"] += 1
                self.violation_tracking[violation_key]["last_violation"] = datetime.utcnow()
                
                # Escalate action if repeated violations
                if self.violation_tracking[violation_key]["count"] >= rule.escalation_threshold:
                    detection.recommended_action = SecurityAction.BLOCK
                    detection.risk_level = RiskLevel.HIGH
        
        return detection
    
    def _matches_pattern(self, endpoint: str, pattern: str) -> bool:
        """Check if endpoint matches pattern (simple glob matching)"""
        if pattern == "*":
            return True
        if pattern.endswith("/*"):
            return endpoint.startswith(pattern[:-2])
        return endpoint == pattern
    
    async def _check_rule_violation(
        self,
        rule: RateLimitRule,
        client_ip: str,
        user: Optional[CurrentUser],
        endpoint: str
    ) -> Optional[str]:
        """Check if request violates specific rule"""
        
        # Check exemptions
        if client_ip in rule.whitelist_ips:
            return None
        if user and user.user_id in rule.whitelist_users:
            return None
        
        current_time = time.time()
        
        # Create tracking keys
        keys = []
        if rule.ip_based:
            keys.append(f"ip:{client_ip}:{rule.id}")
        if rule.user_based and user:
            keys.append(f"user:{user.user_id}:{rule.id}")
        
        for key in keys:
            # Initialize sliding window if needed
            if key not in self.sliding_windows:
                self.sliding_windows[key] = []
            
            # Clean old entries
            cutoff_time = current_time - rule.window_size_seconds
            self.sliding_windows[key] = [
                t for t in self.sliding_windows[key] if t > cutoff_time
            ]
            
            # Add current request
            self.sliding_windows[key].append(current_time)
            
            # Check limits
            current_count = len(self.sliding_windows[key])
            
            # Check burst limit (requests in last 10 seconds)
            recent_cutoff = current_time - 10
            recent_count = len([t for t in self.sliding_windows[key] if t > recent_cutoff])
            
            if recent_count > rule.burst_limit:
                return f"Burst limit exceeded: {recent_count}/{rule.burst_limit}"
            
            # Check per-minute limit
            minute_cutoff = current_time - 60
            minute_count = len([t for t in self.sliding_windows[key] if t > minute_cutoff])
            
            if minute_count > rule.requests_per_minute:
                return f"Per-minute limit exceeded: {minute_count}/{rule.requests_per_minute}"
            
            # Check per-hour limit
            hour_cutoff = current_time - 3600
            hour_count = len([t for t in self.sliding_windows[key] if t > hour_cutoff])
            
            if hour_count > rule.requests_per_hour:
                return f"Per-hour limit exceeded: {hour_count}/{rule.requests_per_hour}"
        
        return None

class WebApplicationFirewall:
    """Web Application Firewall with threat detection and blocking"""
    
    def __init__(self):
        self.input_validator = InputValidator()
        self.bot_detector = BotDetectionEngine()
        self.rate_limiter = RateLimitingEngine()
        self.ip_reputation: Dict[str, IPReputation] = {}
        self.blocked_ips: Set[str] = set()
        self.threat_patterns = self._load_threat_patterns()
    
    def _load_threat_patterns(self) -> Dict[ThreatType, List[re.Pattern]]:
        """Load additional threat detection patterns"""
        return {
            ThreatType.MALICIOUS_PAYLOAD: [
                re.compile(r"<script", re.IGNORECASE),
                re.compile(r"javascript:", re.IGNORECASE),
                re.compile(r"eval\s*\(", re.IGNORECASE)
            ],
            ThreatType.API_ABUSE: [
                re.compile(r"bulk", re.IGNORECASE),
                re.compile(r"mass", re.IGNORECASE),
                re.compile(r"automated", re.IGNORECASE)
            ]
        }
    
    async def analyze_request(
        self,
        request: Request,
        client_ip: str,
        user: Optional[CurrentUser] = None
    ) -> ThreatDetection:
        """Comprehensive request analysis"""
        
        logger.debug("WAF analyzing request",
                    client_ip=client_ip,
                    endpoint=str(request.url.path),
                    method=request.method)
        
        # Initialize combined detection result
        combined_detection = ThreatDetection()
        
        # Check if IP is blocked
        if client_ip in self.blocked_ips:
            combined_detection.threat_detected = True
            combined_detection.threat_types.append(ThreatType.API_ABUSE)
            combined_detection.evidence.append("IP address is blocked")
            combined_detection.confidence = 1.0
            combined_detection.recommended_action = SecurityAction.BLOCK
            combined_detection.risk_level = RiskLevel.CRITICAL
            return combined_detection
        
        # Get/create IP reputation
        if client_ip not in self.ip_reputation:
            self.ip_reputation[client_ip] = IPReputation(ip_address=client_ip)
        
        ip_rep = self.ip_reputation[client_ip]
        
        # Rate limiting check
        rate_detection = await self.rate_limiter.check_rate_limit(request, client_ip, user)
        if rate_detection.threat_detected:
            self._merge_detection_results(combined_detection, rate_detection)
        
        # Bot detection
        bot_detection = await self.bot_detector.analyze_request(request, client_ip)
        if bot_detection.threat_detected:
            self._merge_detection_results(combined_detection, bot_detection)
        
        # Input validation on request body and parameters
        if hasattr(request, '_body'):
            body_data = await request.body()
            if body_data:
                try:
                    json_data = json.loads(body_data)
                    input_detection = await self.input_validator.validate_input(
                        json_data, {"source": "request_body"}
                    )
                    if input_detection.threat_detected:
                        self._merge_detection_results(combined_detection, input_detection)
                except json.JSONDecodeError:
                    # Not JSON, validate as string
                    input_detection = await self.input_validator.validate_input(
                        body_data.decode('utf-8', errors='ignore'),
                        {"source": "request_body"}
                    )
                    if input_detection.threat_detected:
                        self._merge_detection_results(combined_detection, input_detection)
        
        # Validate query parameters
        if request.query_params:
            for key, value in request.query_params.items():
                param_detection = await self.input_validator.validate_input(
                    value, {"source": "query_param", "param_name": key}
                )
                if param_detection.threat_detected:
                    self._merge_detection_results(combined_detection, param_detection)
        
        # Update IP reputation
        ip_rep.update_reputation(combined_detection.threat_detected)
        
        # Adjust confidence based on IP reputation
        if ip_rep.reputation_score < 0.3:
            combined_detection.confidence = min(1.0, combined_detection.confidence + 0.2)
            combined_detection.evidence.append(f"Low IP reputation: {ip_rep.reputation_score:.2f}")
        
        # Final risk assessment
        if combined_detection.threat_detected:
            await self._assess_final_risk(combined_detection, ip_rep, user)
        
        logger.debug("WAF analysis completed",
                    client_ip=client_ip,
                    threat_detected=combined_detection.threat_detected,
                    confidence=combined_detection.confidence,
                    recommended_action=combined_detection.recommended_action.value)
        
        return combined_detection
    
    def _merge_detection_results(
        self,
        combined: ThreatDetection,
        new_detection: ThreatDetection
    ):
        """Merge detection results into combined result"""
        if new_detection.threat_detected:
            combined.threat_detected = True
            combined.threat_types.extend(new_detection.threat_types)
            combined.evidence.extend(new_detection.evidence)
            combined.detection_rules_triggered.extend(new_detection.detection_rules_triggered)
            combined.confidence = max(combined.confidence, new_detection.confidence)
            
            # Use most restrictive action
            action_severity = {
                SecurityAction.ALLOW: 0,
                SecurityAction.LOG_ONLY: 1,
                SecurityAction.RATE_LIMIT: 2,
                SecurityAction.CHALLENGE: 3,
                SecurityAction.QUARANTINE: 4,
                SecurityAction.BLOCK: 5
            }
            
            if action_severity[new_detection.recommended_action] > action_severity[combined.recommended_action]:
                combined.recommended_action = new_detection.recommended_action
    
    async def _assess_final_risk(
        self,
        detection: ThreatDetection,
        ip_rep: IPReputation,
        user: Optional[CurrentUser]
    ):
        """Assess final risk level and action"""
        
        # Critical threats always block
        if ThreatType.COMMAND_INJECTION in detection.threat_types:
            detection.risk_level = RiskLevel.CRITICAL
            detection.recommended_action = SecurityAction.BLOCK
        
        # High confidence threats
        elif detection.confidence >= 0.8:
            detection.risk_level = RiskLevel.HIGH
            if ip_rep.reputation_score < 0.3:
                detection.recommended_action = SecurityAction.BLOCK
            else:
                detection.recommended_action = SecurityAction.CHALLENGE
        
        # Medium confidence threats
        elif detection.confidence >= 0.5:
            detection.risk_level = RiskLevel.MEDIUM
            detection.recommended_action = SecurityAction.RATE_LIMIT
        
        # Low confidence - log only
        else:
            detection.risk_level = RiskLevel.LOW
            detection.recommended_action = SecurityAction.LOG_ONLY
        
        # Adjust for authenticated users (slightly more permissive)
        if user and user.role.value in ["admin", "developer"]:
            if detection.recommended_action == SecurityAction.BLOCK:
                detection.recommended_action = SecurityAction.CHALLENGE
            elif detection.recommended_action == SecurityAction.CHALLENGE:
                detection.recommended_action = SecurityAction.RATE_LIMIT
    
    async def block_ip(self, ip_address: str, reason: str):
        """Block IP address"""
        self.blocked_ips.add(ip_address)
        
        if ip_address in self.ip_reputation:
            self.ip_reputation[ip_address].reputation_score = 0.0
        
        logger.warning("IP address blocked",
                      ip_address=ip_address,
                      reason=reason)
    
    async def unblock_ip(self, ip_address: str):
        """Unblock IP address"""
        self.blocked_ips.discard(ip_address)
        logger.info("IP address unblocked", ip_address=ip_address)
    
    async def get_security_metrics(self) -> Dict[str, Any]:
        """Get WAF security metrics"""
        
        total_ips = len(self.ip_reputation)
        blocked_ips = len(self.blocked_ips)
        low_reputation_ips = len([
            ip for ip in self.ip_reputation.values()
            if ip.reputation_score < 0.3
        ])
        
        threat_type_counts = {}
        for ip_rep in self.ip_reputation.values():
            for threat_type in ip_rep.threat_types:
                threat_type_counts[threat_type.value] = threat_type_counts.get(threat_type.value, 0) + 1
        
        return {
            "total_tracked_ips": total_ips,
            "blocked_ips": blocked_ips,
            "low_reputation_ips": low_reputation_ips,
            "threat_type_distribution": threat_type_counts,
            "rate_limit_rules": len(self.rate_limiter.rate_limit_rules),
            "active_violations": len(self.rate_limiter.violation_tracking),
            "last_updated": datetime.utcnow().isoformat()
        }

# Global WAF instance
web_application_firewall = WebApplicationFirewall()