# ABOUTME: Agent operation security for Betty's multi-agent orchestration platform
# ABOUTME: Enterprise-grade agent authentication, authorization, and behavior monitoring

from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import hashlib
import time
import structlog
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from core.execution_safety import SecurityContext, ExecutionResult
from core.security_framework import SecurityIncidentType, IncidentSeverity
from models.auth import CurrentUser, UserRole

logger = structlog.get_logger(__name__)

class AgentType(Enum):
    SECURITY_AUDITOR = "security-auditor"
    LLM_SYSTEMS_ARCHITECT = "llm-systems-architect"
    PROMPT_OPTIMIZER = "prompt-optimizer"
    GENERAL_PURPOSE = "general-purpose"
    CODE_REVIEWER = "code-reviewer"
    TEST_AUTOMATION_ARCHITECT = "test-automation-architect"
    DEBUG_SPECIALIST = "debug-specialist"
    VULNERABILITY_SCANNER = "vulnerability-scanner"

class AgentStatus(Enum):
    INACTIVE = "inactive"
    INITIALIZING = "initializing"
    ACTIVE = "active"
    BUSY = "busy"
    COMPROMISED = "compromised"
    QUARANTINED = "quarantined"
    TERMINATED = "terminated"

class AgentTrustLevel(Enum):
    UNTRUSTED = "untrusted"
    BASIC = "basic"
    TRUSTED = "trusted"
    VERIFIED = "verified"
    CRITICAL = "critical"

class SecurityBoundaryViolation(Enum):
    UNAUTHORIZED_OPERATION = "unauthorized_operation"
    RESOURCE_LIMIT_EXCEEDED = "resource_limit_exceeded"
    PRIVILEGE_ESCALATION_ATTEMPT = "privilege_escalation_attempt"
    SUSPICIOUS_COMMUNICATION = "suspicious_communication"
    DATA_ACCESS_VIOLATION = "data_access_violation"
    CAPABILITY_ABUSE = "capability_abuse"

@dataclass
class AgentCapabilities:
    """Defines agent capabilities and security boundaries"""
    allowed_operations: Set[str] = field(default_factory=set)
    data_access_scopes: Set[str] = field(default_factory=set)
    api_endpoints: Set[str] = field(default_factory=set)
    resource_limits: Dict[str, Any] = field(default_factory=dict)
    communication_permissions: Set[str] = field(default_factory=set)
    execution_timeout_seconds: int = 3600  # 1 hour default
    
    def can_perform_operation(self, operation: str) -> bool:
        """Check if agent can perform specific operation"""
        return operation in self.allowed_operations
    
    def can_access_data(self, data_scope: str) -> bool:
        """Check if agent can access specific data scope"""
        return data_scope in self.data_access_scopes
    
    def can_communicate_with(self, target_agent: str) -> bool:
        """Check if agent can communicate with target agent"""
        return target_agent in self.communication_permissions or "all" in self.communication_permissions

@dataclass
class AgentCredential:
    """Agent authentication credential"""
    agent_id: UUID
    certificate: Optional[str] = None
    private_key: Optional[str] = None
    public_key: Optional[str] = None
    issued_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    issuer: str = "betty-security-engine"
    revoked: bool = False
    
    def is_valid(self) -> bool:
        """Check if credential is valid and not expired"""
        if self.revoked:
            return False
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        return True

@dataclass
class AgentProfile:
    """Complete agent security profile"""
    id: UUID = field(default_factory=uuid4)
    agent_type: AgentType = AgentType.GENERAL_PURPOSE
    name: str = ""
    version: str = "1.0.0"
    status: AgentStatus = AgentStatus.INACTIVE
    trust_level: AgentTrustLevel = AgentTrustLevel.BASIC
    
    # Security attributes
    capabilities: AgentCapabilities = field(default_factory=AgentCapabilities)
    credential: Optional[AgentCredential] = None
    created_by: Optional[UUID] = None  # User who created/registered agent
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: Optional[datetime] = None
    
    # Monitoring and compliance
    security_violations: List[str] = field(default_factory=list)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    compliance_status: Dict[str, bool] = field(default_factory=dict)
    
    def update_last_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.utcnow()
    
    def add_security_violation(self, violation: str):
        """Add security violation to agent record"""
        self.security_violations.append(f"{datetime.utcnow().isoformat()}: {violation}")
        if len(self.security_violations) > 10:
            self.security_violations = self.security_violations[-10:]  # Keep last 10

@dataclass
class AgentCommunication:
    """Agent-to-agent communication record"""
    id: UUID = field(default_factory=uuid4)
    source_agent: UUID = UUID('00000000-0000-0000-0000-000000000000')
    target_agent: UUID = UUID('00000000-0000-0000-0000-000000000000')
    message_type: str = "task_request"
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    encrypted: bool = False
    signature: Optional[str] = None
    
    def sign_message(self, private_key: str) -> str:
        """Sign message for integrity verification"""
        message_data = json.dumps(self.payload, sort_keys=True)
        signature = hashlib.sha256((message_data + private_key).encode()).hexdigest()
        self.signature = signature
        return signature
    
    def verify_signature(self, public_key: str) -> bool:
        """Verify message signature"""
        if not self.signature:
            return False
        message_data = json.dumps(self.payload, sort_keys=True)
        expected_signature = hashlib.sha256((message_data + public_key).encode()).hexdigest()
        return self.signature == expected_signature

@dataclass
class AgentAnomalyDetection:
    """Agent behavior anomaly detection result"""
    agent_id: UUID
    anomalies_detected: List[str] = field(default_factory=list)
    risk_score: float = 0.0  # 0.0 to 1.0
    behavioral_patterns: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    detection_timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": str(self.agent_id),
            "anomalies_detected": self.anomalies_detected,
            "risk_score": self.risk_score,
            "behavioral_patterns": self.behavioral_patterns,
            "recommendations": self.recommendations,
            "detection_timestamp": self.detection_timestamp.isoformat()
        }

class AgentAuthenticationService:
    """Service for agent authentication and credential management"""
    
    def __init__(self):
        self.agent_credentials: Dict[UUID, AgentCredential] = {}
        self.revoked_credentials: Set[str] = set()
    
    async def generate_agent_credential(
        self,
        agent_id: UUID,
        agent_type: AgentType,
        validity_days: int = 30
    ) -> AgentCredential:
        """Generate new agent authentication credential"""
        
        # Generate RSA key pair for agent
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        public_key = private_key.public_key()
        
        # Serialize keys
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode()
        
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()
        
        # Create credential
        expires_at = datetime.utcnow() + timedelta(days=validity_days)
        
        credential = AgentCredential(
            agent_id=agent_id,
            private_key=private_pem,
            public_key=public_pem,
            expires_at=expires_at
        )
        
        self.agent_credentials[agent_id] = credential
        
        logger.info("Agent credential generated",
                   agent_id=str(agent_id),
                   agent_type=agent_type.value,
                   expires_at=expires_at.isoformat())
        
        return credential
    
    async def authenticate_agent(
        self,
        agent_id: UUID,
        signature: str,
        challenge: str
    ) -> Optional[AgentCredential]:
        """Authenticate agent using signature verification"""
        
        if agent_id not in self.agent_credentials:
            logger.warning("Authentication failed: unknown agent", agent_id=str(agent_id))
            return None
        
        credential = self.agent_credentials[agent_id]
        
        if not credential.is_valid():
            logger.warning("Authentication failed: invalid credential", agent_id=str(agent_id))
            return None
        
        # Verify signature (simplified implementation)
        expected_signature = hashlib.sha256(
            (challenge + credential.public_key).encode()
        ).hexdigest()
        
        if signature != expected_signature:
            logger.warning("Authentication failed: invalid signature", agent_id=str(agent_id))
            return None
        
        logger.info("Agent authenticated successfully", agent_id=str(agent_id))
        return credential
    
    async def revoke_agent_credential(self, agent_id: UUID, reason: str = ""):
        """Revoke agent credential"""
        if agent_id in self.agent_credentials:
            credential = self.agent_credentials[agent_id]
            credential.revoked = True
            self.revoked_credentials.add(str(agent_id))
            
            logger.warning("Agent credential revoked",
                          agent_id=str(agent_id),
                          reason=reason)

class AgentBehaviorMonitor:
    """Monitor agent behavior for anomaly detection"""
    
    def __init__(self):
        self.behavioral_baselines: Dict[UUID, Dict[str, Any]] = {}
        self.activity_logs: Dict[UUID, List[Dict[str, Any]]] = {}
        self.anomaly_thresholds = self._initialize_thresholds()
    
    def _initialize_thresholds(self) -> Dict[str, float]:
        """Initialize anomaly detection thresholds"""
        return {
            "requests_per_minute_max": 60.0,
            "error_rate_threshold": 0.1,  # 10% error rate
            "resource_usage_deviation": 2.0,  # Standard deviations
            "communication_frequency_max": 100.0,  # Messages per hour
            "execution_time_deviation": 3.0  # Standard deviations
        }
    
    async def record_agent_activity(
        self,
        agent_id: UUID,
        activity: Dict[str, Any]
    ):
        """Record agent activity for behavior analysis"""
        
        if agent_id not in self.activity_logs:
            self.activity_logs[agent_id] = []
        
        activity_record = {
            **activity,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.activity_logs[agent_id].append(activity_record)
        
        # Keep last 1000 activities per agent
        if len(self.activity_logs[agent_id]) > 1000:
            self.activity_logs[agent_id] = self.activity_logs[agent_id][-1000:]
    
    async def analyze_agent_behavior(self, agent_id: UUID) -> AgentAnomalyDetection:
        """Analyze agent behavior for anomalies"""
        
        if agent_id not in self.activity_logs:
            return AgentAnomalyDetection(agent_id=agent_id)
        
        activities = self.activity_logs[agent_id]
        recent_activities = [
            a for a in activities 
            if datetime.fromisoformat(a["timestamp"]) > datetime.utcnow() - timedelta(hours=1)
        ]
        
        anomalies = []
        risk_score = 0.0
        patterns = {}
        
        # Analyze request frequency
        requests_per_minute = len(recent_activities) / max(1, len(recent_activities) / 60)
        if requests_per_minute > self.anomaly_thresholds["requests_per_minute_max"]:
            anomalies.append(f"High request frequency: {requests_per_minute:.1f}/min")
            risk_score += 0.3
        
        # Analyze error rates
        error_activities = [a for a in recent_activities if a.get("status") == "error"]
        error_rate = len(error_activities) / max(1, len(recent_activities))
        if error_rate > self.anomaly_thresholds["error_rate_threshold"]:
            anomalies.append(f"High error rate: {error_rate:.2%}")
            risk_score += 0.4
        
        # Analyze resource usage patterns
        resource_usage = [a.get("resource_usage", {}) for a in recent_activities if a.get("resource_usage")]
        if resource_usage:
            avg_memory = sum(r.get("memory_mb", 0) for r in resource_usage) / len(resource_usage)
            patterns["average_memory_usage"] = avg_memory
            if avg_memory > 1000:  # High memory usage
                anomalies.append(f"High memory usage: {avg_memory:.1f}MB")
                risk_score += 0.2
        
        # Generate recommendations
        recommendations = []
        if risk_score > 0.7:
            recommendations.extend([
                "Consider quarantining agent for detailed investigation",
                "Review agent permissions and capabilities",
                "Increase monitoring frequency"
            ])
        elif risk_score > 0.4:
            recommendations.extend([
                "Increase monitoring for this agent",
                "Review recent activities for patterns"
            ])
        
        return AgentAnomalyDetection(
            agent_id=agent_id,
            anomalies_detected=anomalies,
            risk_score=min(1.0, risk_score),
            behavioral_patterns=patterns,
            recommendations=recommendations
        )

class AgentSecurityEngine:
    """Main agent security engine orchestrating all agent security controls"""
    
    def __init__(self):
        self.agent_profiles: Dict[UUID, AgentProfile] = {}
        self.auth_service = AgentAuthenticationService()
        self.behavior_monitor = AgentBehaviorMonitor()
        self.communication_log: List[AgentCommunication] = []
        self.security_policies = self._initialize_security_policies()
    
    def _initialize_security_policies(self) -> Dict[AgentType, AgentCapabilities]:
        """Initialize default security policies for each agent type"""
        return {
            AgentType.SECURITY_AUDITOR: AgentCapabilities(
                allowed_operations={
                    "security_scan", "vulnerability_assessment", "compliance_check",
                    "security_report_generation", "threat_analysis"
                },
                data_access_scopes={"security_logs", "audit_trails", "vulnerability_data"},
                api_endpoints={"/api/security/*", "/api/audit/*"},
                resource_limits={"memory_mb": 1024, "cpu_cores": 2},
                communication_permissions={"all"}
            ),
            AgentType.LLM_SYSTEMS_ARCHITECT: AgentCapabilities(
                allowed_operations={
                    "architecture_design", "system_analysis", "performance_optimization",
                    "ai_model_deployment", "vector_database_management"
                },
                data_access_scopes={"system_metrics", "performance_data", "architecture_specs"},
                api_endpoints={"/api/systems/*", "/api/architecture/*"},
                resource_limits={"memory_mb": 2048, "cpu_cores": 2},
                communication_permissions={"general-purpose", "test-automation-architect"}
            ),
            AgentType.GENERAL_PURPOSE: AgentCapabilities(
                allowed_operations={
                    "task_orchestration", "data_processing", "report_generation",
                    "file_operations", "api_calls"
                },
                data_access_scopes={"general_data", "public_resources"},
                api_endpoints={"/api/general/*", "/api/public/*"},
                resource_limits={"memory_mb": 512, "cpu_cores": 1},
                communication_permissions={"all"}
            ),
            AgentType.CODE_REVIEWER: AgentCapabilities(
                allowed_operations={
                    "code_analysis", "quality_assessment", "security_review",
                    "best_practices_validation", "documentation_review"
                },
                data_access_scopes={"source_code", "code_quality_metrics"},
                api_endpoints={"/api/code/*", "/api/review/*"},
                resource_limits={"memory_mb": 512, "cpu_cores": 1},
                communication_permissions={"security-auditor", "test-automation-architect"}
            ),
            AgentType.DEBUG_SPECIALIST: AgentCapabilities(
                allowed_operations={
                    "error_analysis", "log_analysis", "debugging", "troubleshooting",
                    "system_diagnosis"
                },
                data_access_scopes={"error_logs", "system_logs", "debug_info"},
                api_endpoints={"/api/debug/*", "/api/logs/*"},
                resource_limits={"memory_mb": 768, "cpu_cores": 1},
                communication_permissions={"all"}
            )
        }
    
    async def register_agent(
        self,
        agent_type: AgentType,
        name: str,
        version: str = "1.0.0",
        created_by: Optional[UUID] = None,
        trust_level: AgentTrustLevel = AgentTrustLevel.BASIC
    ) -> AgentProfile:
        """Register new agent with security profile"""
        
        agent_id = uuid4()
        
        # Get default capabilities for agent type
        default_capabilities = self.security_policies.get(
            agent_type, 
            self.security_policies[AgentType.GENERAL_PURPOSE]
        )
        
        # Generate authentication credential
        credential = await self.auth_service.generate_agent_credential(
            agent_id, agent_type
        )
        
        # Create agent profile
        profile = AgentProfile(
            id=agent_id,
            agent_type=agent_type,
            name=name,
            version=version,
            trust_level=trust_level,
            capabilities=default_capabilities,
            credential=credential,
            created_by=created_by
        )
        
        self.agent_profiles[agent_id] = profile
        
        logger.info("Agent registered",
                   agent_id=str(agent_id),
                   agent_type=agent_type.value,
                   name=name,
                   trust_level=trust_level.value)
        
        return profile
    
    async def authenticate_agent_operation(
        self,
        agent_id: UUID,
        operation: str,
        context: Dict[str, Any]
    ) -> bool:
        """Authenticate and authorize agent operation"""
        
        if agent_id not in self.agent_profiles:
            logger.warning("Operation denied: unknown agent", agent_id=str(agent_id))
            return False
        
        profile = self.agent_profiles[agent_id]
        
        # Check agent status
        if profile.status in [AgentStatus.COMPROMISED, AgentStatus.QUARANTINED, AgentStatus.TERMINATED]:
            logger.warning("Operation denied: agent status",
                          agent_id=str(agent_id),
                          status=profile.status.value)
            return False
        
        # Check operation permissions
        if not profile.capabilities.can_perform_operation(operation):
            logger.warning("Operation denied: insufficient permissions",
                          agent_id=str(agent_id),
                          operation=operation)
            
            await self._record_security_violation(
                agent_id, 
                SecurityBoundaryViolation.UNAUTHORIZED_OPERATION,
                {"operation": operation, "context": context}
            )
            return False
        
        # Check data access permissions
        data_scope = context.get("data_scope")
        if data_scope and not profile.capabilities.can_access_data(data_scope):
            logger.warning("Operation denied: data access violation",
                          agent_id=str(agent_id),
                          data_scope=data_scope)
            
            await self._record_security_violation(
                agent_id,
                SecurityBoundaryViolation.DATA_ACCESS_VIOLATION,
                {"data_scope": data_scope, "context": context}
            )
            return False
        
        # Record successful operation
        await self.behavior_monitor.record_agent_activity(agent_id, {
            "operation": operation,
            "context": context,
            "status": "authorized",
            "resource_usage": context.get("resource_usage", {})
        })
        
        profile.update_last_activity()
        
        return True
    
    async def monitor_agent_communication(
        self,
        source_agent: UUID,
        target_agent: UUID,
        message: Dict[str, Any]
    ) -> bool:
        """Monitor and validate agent-to-agent communication"""
        
        if source_agent not in self.agent_profiles or target_agent not in self.agent_profiles:
            logger.warning("Communication denied: unknown agent",
                          source=str(source_agent),
                          target=str(target_agent))
            return False
        
        source_profile = self.agent_profiles[source_agent]
        target_profile = self.agent_profiles[target_agent]
        
        # Check communication permissions
        if not source_profile.capabilities.can_communicate_with(target_profile.agent_type.value):
            logger.warning("Communication denied: permission violation",
                          source=str(source_agent),
                          target=str(target_agent))
            
            await self._record_security_violation(
                source_agent,
                SecurityBoundaryViolation.SUSPICIOUS_COMMUNICATION,
                {"target_agent": str(target_agent), "message_type": message.get("type")}
            )
            return False
        
        # Create communication record
        comm = AgentCommunication(
            source_agent=source_agent,
            target_agent=target_agent,
            message_type=message.get("type", "unknown"),
            payload=message
        )
        
        self.communication_log.append(comm)
        
        # Keep last 10000 communications
        if len(self.communication_log) > 10000:
            self.communication_log = self.communication_log[-10000:]
        
        return True
    
    async def detect_agent_anomalies(self, agent_id: Optional[UUID] = None) -> List[AgentAnomalyDetection]:
        """Detect behavioral anomalies across agents"""
        
        results = []
        
        if agent_id:
            # Analyze specific agent
            result = await self.behavior_monitor.analyze_agent_behavior(agent_id)
            if result.risk_score > 0.3:  # Only report significant anomalies
                results.append(result)
        else:
            # Analyze all active agents
            for agent_id in self.agent_profiles:
                if self.agent_profiles[agent_id].status == AgentStatus.ACTIVE:
                    result = await self.behavior_monitor.analyze_agent_behavior(agent_id)
                    if result.risk_score > 0.3:
                        results.append(result)
        
        return results
    
    async def quarantine_agent(self, agent_id: UUID, reason: str) -> bool:
        """Quarantine agent for security investigation"""
        
        if agent_id not in self.agent_profiles:
            return False
        
        profile = self.agent_profiles[agent_id]
        profile.status = AgentStatus.QUARANTINED
        profile.add_security_violation(f"Quarantined: {reason}")
        
        # Revoke credentials
        await self.auth_service.revoke_agent_credential(agent_id, reason)
        
        logger.warning("Agent quarantined",
                      agent_id=str(agent_id),
                      reason=reason)
        
        return True
    
    async def _record_security_violation(
        self,
        agent_id: UUID,
        violation_type: SecurityBoundaryViolation,
        context: Dict[str, Any]
    ):
        """Record security violation for agent"""
        
        if agent_id in self.agent_profiles:
            profile = self.agent_profiles[agent_id]
            profile.add_security_violation(f"{violation_type.value}: {json.dumps(context)}")
            
            # Check if agent should be quarantined
            if len(profile.security_violations) >= 5:
                await self.quarantine_agent(agent_id, "Multiple security violations")
    
    async def get_agent_security_metrics(self) -> Dict[str, Any]:
        """Get comprehensive agent security metrics"""
        
        total_agents = len(self.agent_profiles)
        active_agents = len([p for p in self.agent_profiles.values() if p.status == AgentStatus.ACTIVE])
        quarantined_agents = len([p for p in self.agent_profiles.values() if p.status == AgentStatus.QUARANTINED])
        
        # Calculate security violations by agent type
        violations_by_type = {}
        for profile in self.agent_profiles.values():
            agent_type = profile.agent_type.value
            if agent_type not in violations_by_type:
                violations_by_type[agent_type] = 0
            violations_by_type[agent_type] += len(profile.security_violations)
        
        return {
            "total_agents": total_agents,
            "active_agents": active_agents,
            "quarantined_agents": quarantined_agents,
            "security_violations_by_type": violations_by_type,
            "communication_messages_last_hour": len([
                c for c in self.communication_log 
                if c.timestamp > datetime.utcnow() - timedelta(hours=1)
            ]),
            "last_updated": datetime.utcnow().isoformat()
        }

# Global agent security engine
agent_security_engine = AgentSecurityEngine()