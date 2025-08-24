# ABOUTME: Comprehensive security framework for Betty with data classification and compliance
# ABOUTME: Enterprise-grade security controls with GDPR, SOC2, and industry compliance support

from typing import Dict, List, Optional, Any, Union, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re
import json
import hashlib
import structlog
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from models.auth import CurrentUser, UserRole, PermissionLevel
from core.security import SecurityManager

logger = structlog.get_logger(__name__)

class DataSensitivity(Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    SECRET = "secret"
    REGULATED = "regulated"

class ComplianceFramework(Enum):
    GDPR = "gdpr"
    SOC2 = "soc2"
    HIPAA = "hipaa"
    PCI_DSS = "pci_dss"
    ISO27001 = "iso27001"
    NIST = "nist"

class IncidentSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class SecurityIncidentType(Enum):
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    DATA_BREACH = "data_breach"
    AUTHENTICATION_FAILURE = "authentication_failure"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    MALICIOUS_PATTERN = "malicious_pattern"
    RESOURCE_ABUSE = "resource_abuse"
    COMPLIANCE_VIOLATION = "compliance_violation"

@dataclass
class SensitivityClassification:
    """Data sensitivity classification with access controls"""
    level: DataSensitivity
    required_permissions: List[str] = field(default_factory=list)
    encryption_required: bool = False
    retention_days: Optional[int] = None
    audit_required: bool = False
    compliance_frameworks: List[ComplianceFramework] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "level": self.level.value,
            "required_permissions": self.required_permissions,
            "encryption_required": self.encryption_required,
            "retention_days": self.retention_days,
            "audit_required": self.audit_required,
            "compliance_frameworks": [f.value for f in self.compliance_frameworks]
        }

@dataclass
class SecurityIncident:
    """Security incident record"""
    id: UUID = field(default_factory=uuid4)
    incident_type: SecurityIncidentType = SecurityIncidentType.UNAUTHORIZED_ACCESS
    severity: IncidentSeverity = IncidentSeverity.MEDIUM
    description: str = ""
    affected_user_id: Optional[UUID] = None
    client_ip: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    resolved: bool = False
    resolution_notes: str = ""
    
    # Incident-specific data
    failed_operation: Optional[str] = None
    security_controls_bypassed: List[str] = field(default_factory=list)
    data_affected: List[str] = field(default_factory=list)
    compliance_impact: List[ComplianceFramework] = field(default_factory=list)

@dataclass
class PermissionResult:
    """Result of permission check"""
    granted: bool
    missing_permissions: List[str] = field(default_factory=list)
    additional_context: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ComplianceResult:
    """Result of compliance validation"""
    compliant: bool
    framework: ComplianceFramework
    violations: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    risk_level: str = "low"

class DataClassificationEngine:
    """Engine for automatic data sensitivity classification"""
    
    # PII patterns for automatic detection
    PII_PATTERNS = {
        'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
        'ssn': re.compile(r'\b\d{3}-?\d{2}-?\d{4}\b'),
        'phone': re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'),
        'credit_card': re.compile(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'),
        'ip_address': re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b')
    }
    
    # Sensitive keywords that trigger higher classification
    SENSITIVE_KEYWORDS = {
        'secret', 'password', 'private', 'confidential', 'classified',
        'medical', 'health', 'diagnosis', 'treatment', 'patient',
        'financial', 'account', 'balance', 'transaction', 'payment'
    }
    
    def __init__(self):
        self.classification_rules = self._initialize_classification_rules()
    
    def _initialize_classification_rules(self) -> Dict[DataSensitivity, SensitivityClassification]:
        """Initialize data classification rules"""
        return {
            DataSensitivity.PUBLIC: SensitivityClassification(
                level=DataSensitivity.PUBLIC,
                required_permissions=[],
                encryption_required=False,
                retention_days=None,
                audit_required=False
            ),
            DataSensitivity.INTERNAL: SensitivityClassification(
                level=DataSensitivity.INTERNAL,
                required_permissions=["data:internal"],
                encryption_required=False,
                retention_days=2555,  # 7 years
                audit_required=False
            ),
            DataSensitivity.CONFIDENTIAL: SensitivityClassification(
                level=DataSensitivity.CONFIDENTIAL,
                required_permissions=["data:confidential"],
                encryption_required=True,
                retention_days=2555,
                audit_required=True,
                compliance_frameworks=[ComplianceFramework.SOC2]
            ),
            DataSensitivity.SECRET: SensitivityClassification(
                level=DataSensitivity.SECRET,
                required_permissions=["data:secret"],
                encryption_required=True,
                retention_days=1825,  # 5 years
                audit_required=True,
                compliance_frameworks=[ComplianceFramework.SOC2, ComplianceFramework.ISO27001]
            ),
            DataSensitivity.REGULATED: SensitivityClassification(
                level=DataSensitivity.REGULATED,
                required_permissions=["data:regulated"],
                encryption_required=True,
                retention_days=1095,  # 3 years
                audit_required=True,
                compliance_frameworks=[ComplianceFramework.GDPR, ComplianceFramework.HIPAA, ComplianceFramework.PCI_DSS]
            )
        }
    
    async def classify_data(self, data: Any, context: Optional[Dict[str, Any]] = None) -> SensitivityClassification:
        """
        Automatically classify data sensitivity based on content analysis
        """
        if not data:
            return self.classification_rules[DataSensitivity.PUBLIC]
        
        # Convert data to string for analysis
        data_str = str(data).lower()
        
        # Check for PII patterns
        pii_detected = []
        for pii_type, pattern in self.PII_PATTERNS.items():
            if pattern.search(data_str):
                pii_detected.append(pii_type)
        
        # Check for sensitive keywords
        sensitive_keywords_found = [
            keyword for keyword in self.SENSITIVE_KEYWORDS
            if keyword in data_str
        ]
        
        # Classify based on findings
        if any(pii in ['ssn', 'credit_card'] for pii in pii_detected):
            classification = DataSensitivity.REGULATED
        elif 'medical' in sensitive_keywords_found or 'health' in sensitive_keywords_found:
            classification = DataSensitivity.REGULATED
        elif pii_detected or sensitive_keywords_found:
            classification = DataSensitivity.CONFIDENTIAL
        elif context and context.get('internal_project', False):
            classification = DataSensitivity.INTERNAL
        else:
            classification = DataSensitivity.PUBLIC
        
        result = self.classification_rules[classification].to_dict()
        
        logger.debug("Data classification completed",
                    classification=classification.value,
                    pii_detected=pii_detected,
                    sensitive_keywords=len(sensitive_keywords_found))
        
        return SensitivityClassification(**result)

class ComplianceEngine:
    """Engine for compliance validation and monitoring"""
    
    def __init__(self):
        self.compliance_rules = self._initialize_compliance_rules()
    
    def _initialize_compliance_rules(self) -> Dict[ComplianceFramework, Dict[str, Any]]:
        """Initialize compliance validation rules"""
        return {
            ComplianceFramework.GDPR: {
                "data_subject_rights": ["access", "rectification", "erasure", "portability"],
                "lawful_basis_required": True,
                "consent_tracking": True,
                "data_retention_limits": True,
                "breach_notification_required": True,
                "dpo_required": False  # Depends on organization size
            },
            ComplianceFramework.SOC2: {
                "controls": ["security", "availability", "processing_integrity", "confidentiality"],
                "audit_logging": True,
                "access_controls": True,
                "encryption_required": True,
                "incident_response": True,
                "vendor_management": True
            },
            ComplianceFramework.HIPAA: {
                "minimum_necessary": True,
                "encryption_required": True,
                "access_logging": True,
                "breach_notification": True,
                "business_associate_agreements": True,
                "administrative_safeguards": True,
                "physical_safeguards": True,
                "technical_safeguards": True
            },
            ComplianceFramework.PCI_DSS: {
                "cardholder_data_protection": True,
                "encryption_in_transit": True,
                "encryption_at_rest": True,
                "access_controls": True,
                "regular_security_testing": True,
                "vulnerability_management": True
            }
        }
    
    async def validate_compliance(
        self, 
        operation: Dict[str, Any], 
        data_classification: SensitivityClassification
    ) -> List[ComplianceResult]:
        """Validate operation against applicable compliance frameworks"""
        results = []
        
        for framework in data_classification.compliance_frameworks:
            result = await self._validate_framework_compliance(operation, framework, data_classification)
            results.append(result)
        
        return results
    
    async def _validate_framework_compliance(
        self,
        operation: Dict[str, Any],
        framework: ComplianceFramework,
        data_classification: SensitivityClassification
    ) -> ComplianceResult:
        """Validate against specific compliance framework"""
        rules = self.compliance_rules.get(framework, {})
        violations = []
        recommendations = []
        
        if framework == ComplianceFramework.GDPR:
            violations, recommendations = await self._validate_gdpr(operation, data_classification, rules)
        elif framework == ComplianceFramework.SOC2:
            violations, recommendations = await self._validate_soc2(operation, data_classification, rules)
        elif framework == ComplianceFramework.HIPAA:
            violations, recommendations = await self._validate_hipaa(operation, data_classification, rules)
        elif framework == ComplianceFramework.PCI_DSS:
            violations, recommendations = await self._validate_pci_dss(operation, data_classification, rules)
        
        # Determine risk level
        risk_level = "high" if violations else "low"
        if len(violations) > 3:
            risk_level = "critical"
        elif len(violations) > 1:
            risk_level = "medium"
        
        return ComplianceResult(
            compliant=len(violations) == 0,
            framework=framework,
            violations=violations,
            recommendations=recommendations,
            risk_level=risk_level
        )
    
    async def _validate_gdpr(
        self, 
        operation: Dict[str, Any], 
        classification: SensitivityClassification,
        rules: Dict[str, Any]
    ) -> Tuple[List[str], List[str]]:
        """GDPR-specific compliance validation"""
        violations = []
        recommendations = []
        
        # Check for lawful basis
        if not operation.get("lawful_basis"):
            violations.append("No lawful basis specified for personal data processing")
        
        # Check data retention
        if not classification.retention_days:
            violations.append("No data retention period specified")
        
        # Check encryption for personal data
        if not classification.encryption_required and classification.level != DataSensitivity.PUBLIC:
            recommendations.append("Consider encryption for personal data protection")
        
        return violations, recommendations
    
    async def _validate_soc2(
        self,
        operation: Dict[str, Any],
        classification: SensitivityClassification,
        rules: Dict[str, Any]
    ) -> Tuple[List[str], List[str]]:
        """SOC 2 compliance validation"""
        violations = []
        recommendations = []
        
        # Check audit logging
        if not classification.audit_required:
            violations.append("Audit logging required for SOC 2 compliance")
        
        # Check encryption
        if not classification.encryption_required and classification.level in [DataSensitivity.CONFIDENTIAL, DataSensitivity.SECRET]:
            violations.append("Encryption required for confidential data")
        
        return violations, recommendations
    
    async def _validate_hipaa(
        self,
        operation: Dict[str, Any],
        classification: SensitivityClassification,
        rules: Dict[str, Any]
    ) -> Tuple[List[str], List[str]]:
        """HIPAA compliance validation"""
        violations = []
        recommendations = []
        
        # Check minimum necessary standard
        if not operation.get("minimum_necessary_justification"):
            violations.append("Minimum necessary standard requires justification for PHI access")
        
        # Check encryption
        if not classification.encryption_required:
            violations.append("PHI must be encrypted at rest and in transit")
        
        return violations, recommendations
    
    async def _validate_pci_dss(
        self,
        operation: Dict[str, Any],
        classification: SensitivityClassification,
        rules: Dict[str, Any]
    ) -> Tuple[List[str], List[str]]:
        """PCI DSS compliance validation"""
        violations = []
        recommendations = []
        
        # Check cardholder data protection
        if "cardholder_data" in str(operation).lower():
            if not classification.encryption_required:
                violations.append("Cardholder data must be encrypted")
            if not classification.audit_required:
                violations.append("Cardholder data access must be logged")
        
        return violations, recommendations

class SecurityIncidentEngine:
    """Engine for security incident detection and response"""
    
    def __init__(self):
        self.incidents: Dict[UUID, SecurityIncident] = {}
        self.incident_thresholds = self._initialize_thresholds()
    
    def _initialize_thresholds(self) -> Dict[str, int]:
        """Initialize incident detection thresholds"""
        return {
            "failed_logins_per_minute": 5,
            "failed_logins_per_hour": 20,
            "api_requests_per_minute": 100,
            "data_access_anomaly_threshold": 10,
            "privilege_escalation_attempts": 3
        }
    
    async def detect_incident(
        self,
        incident_type: SecurityIncidentType,
        context: Dict[str, Any]
    ) -> Optional[SecurityIncident]:
        """Detect and classify security incidents"""
        
        # Analyze incident severity
        severity = await self._assess_incident_severity(incident_type, context)
        
        if severity == IncidentSeverity.LOW and not context.get("force_incident"):
            return None  # Don't create incident for low-severity events
        
        incident = SecurityIncident(
            incident_type=incident_type,
            severity=severity,
            description=context.get("description", "Security incident detected"),
            affected_user_id=context.get("user_id"),
            client_ip=context.get("client_ip", ""),
            failed_operation=context.get("operation"),
            security_controls_bypassed=context.get("controls_bypassed", []),
            data_affected=context.get("data_affected", [])
        )
        
        self.incidents[incident.id] = incident
        
        logger.warning("Security incident detected",
                      incident_id=str(incident.id),
                      incident_type=incident_type.value,
                      severity=severity.value)
        
        return incident
    
    async def _assess_incident_severity(
        self,
        incident_type: SecurityIncidentType,
        context: Dict[str, Any]
    ) -> IncidentSeverity:
        """Assess incident severity based on type and context"""
        
        # Critical incidents
        if incident_type == SecurityIncidentType.DATA_BREACH:
            return IncidentSeverity.CRITICAL
        if incident_type == SecurityIncidentType.PRIVILEGE_ESCALATION:
            return IncidentSeverity.HIGH
        
        # High-severity incidents
        if incident_type == SecurityIncidentType.MALICIOUS_PATTERN:
            return IncidentSeverity.HIGH
        if incident_type == SecurityIncidentType.UNAUTHORIZED_ACCESS and context.get("admin_account"):
            return IncidentSeverity.HIGH
        
        # Medium-severity incidents
        if incident_type == SecurityIncidentType.AUTHENTICATION_FAILURE:
            failed_attempts = context.get("failed_attempts", 1)
            if failed_attempts > 10:
                return IncidentSeverity.HIGH
            elif failed_attempts > 5:
                return IncidentSeverity.MEDIUM
        
        return IncidentSeverity.LOW
    
    async def handle_security_incident(self, incident: SecurityIncident) -> Dict[str, Any]:
        """Automated security incident response"""
        response_actions = []
        
        # Immediate response based on severity
        if incident.severity == IncidentSeverity.CRITICAL:
            response_actions.extend([
                "Alert security team immediately",
                "Consider system lockdown",
                "Initiate breach notification process"
            ])
        elif incident.severity == IncidentSeverity.HIGH:
            response_actions.extend([
                "Alert security team",
                "Review affected systems",
                "Implement additional monitoring"
            ])
        
        # Incident-type specific responses
        if incident.incident_type == SecurityIncidentType.AUTHENTICATION_FAILURE:
            response_actions.append("Increase login monitoring for affected IP")
        elif incident.incident_type == SecurityIncidentType.PRIVILEGE_ESCALATION:
            response_actions.extend([
                "Review user permissions",
                "Audit recent access changes"
            ])
        
        response_result = {
            "incident_id": str(incident.id),
            "response_actions": response_actions,
            "automated_actions_taken": [],
            "manual_actions_required": response_actions,
            "response_timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info("Security incident response initiated",
                   incident_id=str(incident.id),
                   actions_count=len(response_actions))
        
        return response_result

class SecurityFramework:
    """Main security framework orchestrating all security engines"""
    
    def __init__(self):
        self.data_classifier = DataClassificationEngine()
        self.compliance_engine = ComplianceEngine()
        self.incident_engine = SecurityIncidentEngine()
        self.security_manager = SecurityManager()
    
    async def check_rbac_permissions(
        self,
        user: CurrentUser,
        resource: str,
        action: str,
        context: Optional[Dict[str, Any]] = None
    ) -> PermissionResult:
        """Enhanced RBAC permission checking"""
        
        # Basic permission check
        required_permission = f"{resource}:{action}"
        if user.has_permission(required_permission):
            return PermissionResult(granted=True)
        
        # Check for elevated permissions based on context
        missing_permissions = [required_permission]
        additional_context = {}
        
        # Check data sensitivity permissions
        if context and "data_sensitivity" in context:
            data_permission = f"data:{context['data_sensitivity']}"
            if not user.has_permission(data_permission):
                missing_permissions.append(data_permission)
        
        # Check project-specific permissions
        if context and "project_id" in context:
            project_access = user.can_access_project(
                context["project_id"], 
                PermissionLevel.WRITE if action in ["create", "update", "delete"] else PermissionLevel.READ
            )
            if not project_access:
                additional_context["project_access_denied"] = context["project_id"]
        
        return PermissionResult(
            granted=False,
            missing_permissions=missing_permissions,
            additional_context=additional_context
        )
    
    async def classify_data_sensitivity(self, data: Any, context: Optional[Dict[str, Any]] = None) -> SensitivityClassification:
        """Classify data sensitivity with compliance mapping"""
        return await self.data_classifier.classify_data(data, context)
    
    async def validate_compliance(
        self,
        operation: Dict[str, Any],
        data_classification: SensitivityClassification
    ) -> List[ComplianceResult]:
        """Validate operation compliance across all applicable frameworks"""
        return await self.compliance_engine.validate_compliance(operation, data_classification)
    
    async def handle_security_incident(
        self,
        incident_type: SecurityIncidentType,
        context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Handle security incident with automated response"""
        
        incident = await self.incident_engine.detect_incident(incident_type, context)
        if not incident:
            return None
        
        response = await self.incident_engine.handle_security_incident(incident)
        
        # Log security incident for audit
        self.security_manager.log_security_event(
            incident_type.value,
            {
                "incident_id": str(incident.id),
                "severity": incident.severity.value,
                "description": incident.description
            },
            context.get("client_ip"),
            str(context.get("user_id")) if context.get("user_id") else None
        )
        
        return response
    
    async def get_security_metrics(self) -> Dict[str, Any]:
        """Get comprehensive security metrics"""
        return {
            "active_incidents": len([i for i in self.incident_engine.incidents.values() if not i.resolved]),
            "total_incidents": len(self.incident_engine.incidents),
            "incident_severity_breakdown": self._get_incident_severity_breakdown(),
            "classification_rules": len(self.data_classifier.classification_rules),
            "compliance_frameworks_supported": len(self.compliance_engine.compliance_rules),
            "last_updated": datetime.utcnow().isoformat()
        }
    
    def _get_incident_severity_breakdown(self) -> Dict[str, int]:
        """Get breakdown of incidents by severity"""
        breakdown = {severity.value: 0 for severity in IncidentSeverity}
        for incident in self.incident_engine.incidents.values():
            breakdown[incident.severity.value] += 1
        return breakdown

# Global security framework instance
security_framework = SecurityFramework()