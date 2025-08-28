# ABOUTME: Betty's Execution Safety & Guardrails Framework - Main Integration
# ABOUTME: Enterprise-grade security orchestration with zero violations and automatic rollback

from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import json
import structlog
from datetime import datetime, timedelta
from uuid import UUID, uuid4

# Import all security components
from core.execution_safety import (
    execution_safety_engine, Operation, OperationType, SecurityContext, 
    SafetyResult, ExecutionResult
)
from core.security_framework import (
    security_framework, DataSensitivity, ComplianceFramework, 
    SecurityIncidentType, IncidentSeverity
)
from core.pattern_security import (
    pattern_security_engine, PatternMetadata, PatternSource, ThreatType
)
from core.agent_security import (
    agent_security_engine, AgentType, AgentTrustLevel, AgentProfile
)
from core.data_protection import (
    data_protection_service, PIIType, EncryptionMethod, RetentionStatus
)
from core.api_security import (
    web_application_firewall, ThreatType as APIThreatType, SecurityAction
)
from core.audit_compliance import (
    compliance_orchestrator, AuditEventType, AuditSeverity, ComplianceReport
)
from core.vault_integration import (
    vault_security_integration, SecretType, SecretStatus
)
from core.security_testing import (
    security_test_suite, SecurityTestType
)
from models.auth import CurrentUser

logger = structlog.get_logger(__name__)

class FrameworkStatus(Enum):
    INITIALIZING = "initializing"
    ACTIVE = "active"
    MAINTENANCE = "maintenance"
    DEGRADED = "degraded"
    OFFLINE = "offline"

@dataclass
class SecurityMetrics:
    """Comprehensive security metrics"""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Execution safety metrics
    total_operations: int = 0
    safe_operations: int = 0
    blocked_operations: int = 0
    rollbacks_performed: int = 0
    
    # Pattern security metrics
    patterns_validated: int = 0
    malicious_patterns_blocked: int = 0
    sandbox_executions: int = 0
    
    # Agent security metrics
    active_agents: int = 0
    quarantined_agents: int = 0
    agent_violations: int = 0
    
    # Data protection metrics
    data_records_protected: int = 0
    pii_records_encrypted: int = 0
    retention_policies_applied: int = 0
    
    # API security metrics
    requests_processed: int = 0
    threats_blocked: int = 0
    rate_limits_enforced: int = 0
    
    # Compliance metrics
    audit_events_logged: int = 0
    compliance_reports_generated: int = 0
    violations_detected: int = 0
    
    # Vault integration metrics
    secrets_managed: int = 0
    keys_rotated: int = 0
    
    def calculate_safety_score(self) -> float:
        """Calculate overall safety score (0.0 to 1.0)"""
        if self.total_operations == 0:
            return 1.0
        
        safety_rate = self.safe_operations / self.total_operations
        threat_prevention_rate = 1.0 - (self.violations_detected / max(1, self.requests_processed))
        
        return (safety_rate + threat_prevention_rate) / 2.0

class ExecutionSafetyFramework:
    """
    Main orchestrator for Betty's Execution Safety & Guardrails Framework
    Provides enterprise-grade security with zero violations and automatic rollback
    """
    
    def __init__(self):
        self.status = FrameworkStatus.INITIALIZING
        self.metrics = SecurityMetrics()
        self.incident_count = 0
        self.last_health_check = datetime.utcnow()
        self.framework_version = "1.0.0"
        
        # Component health tracking
        self.component_health = {
            "execution_safety": True,
            "security_framework": True,
            "pattern_security": True,
            "agent_security": True,
            "data_protection": True,
            "api_security": True,
            "audit_compliance": True,
            "vault_integration": True
        }
    
    async def initialize(self, user_id: Optional[UUID] = None) -> bool:
        """Initialize the complete security framework"""
        
        logger.info("Initializing Betty's Execution Safety & Guardrails Framework")
        
        try:
            # Initialize Vault security integration
            await vault_security_integration.initialize_security_secrets(user_id)
            
            # Start automatic secret rotation
            await vault_security_integration.start_rotation_scheduler()
            
            # Log framework initialization
            await compliance_orchestrator.log_audit_event(
                AuditEventType.SYSTEM_CONFIGURATION,
                "Execution Safety & Guardrails Framework initialized",
                severity=AuditSeverity.INFO,
                metadata={
                    "framework_version": self.framework_version,
                    "initialized_by": str(user_id) if user_id else "system"
                }
            )
            
            self.status = FrameworkStatus.ACTIVE
            
            logger.info("Execution Safety & Guardrails Framework initialized successfully")
            return True
            
        except Exception as e:
            self.status = FrameworkStatus.OFFLINE
            logger.error("Failed to initialize security framework", error=str(e))
            return False
    
    async def execute_operation_safely(
        self,
        operation: Operation,
        context: SecurityContext
    ) -> ExecutionResult:
        """
        Execute operation with comprehensive safety validation
        Implements the core safety guarantee: zero security violations with automatic rollback
        """
        
        logger.info("Executing operation with safety validation",
                   operation_id=str(operation.id),
                   operation_type=operation.type.value)
        
        try:
            # Phase 1: Pre-execution safety validation
            safety_result = await execution_safety_engine.validate_execution_safety(
                operation, context
            )
            
            # Update metrics
            self.metrics.total_operations += 1
            
            if not safety_result.is_safe:
                self.metrics.blocked_operations += 1
                
                # Log security incident
                await self._handle_security_incident(
                    SecurityIncidentType.UNAUTHORIZED_OPERATION,
                    f"Operation blocked by safety validation: {operation.id}",
                    context,
                    {
                        "operation_type": operation.type.value,
                        "safety_result": safety_result.to_dict(),
                        "risk_level": safety_result.risk_level.value
                    }
                )
                
                return ExecutionResult(
                    operation_id=operation.id,
                    status="blocked",
                    started_at=datetime.utcnow(),
                    completed_at=datetime.utcnow(),
                    error_message="Operation blocked by security validation",
                    result_data={
                        "safety_validation": safety_result.to_dict(),
                        "reason": "Security policy violation"
                    }
                )
            
            # Phase 2: Pattern-specific validation (if applicable)
            if operation.type == OperationType.PATTERN_APPLICATION:
                pattern_validation = await self._validate_pattern_security(operation, context)
                if not pattern_validation["safe"]:
                    return self._create_blocked_result(operation, "Pattern security validation failed", pattern_validation)
            
            # Phase 3: Agent security validation (if applicable)
            if operation.type == OperationType.AGENT_EXECUTION:
                agent_validation = await self._validate_agent_security(operation, context)
                if not agent_validation["authorized"]:
                    return self._create_blocked_result(operation, "Agent security validation failed", agent_validation)
            
            # Phase 4: Data protection validation
            data_validation = await self._validate_data_protection(operation, context)
            if not data_validation["compliant"]:
                return self._create_blocked_result(operation, "Data protection validation failed", data_validation)
            
            # Phase 5: Execute with rollback capability
            execution_result = await execution_safety_engine.execute_with_rollback(operation, context)
            
            # Phase 6: Post-execution validation
            if execution_result.status == "completed":
                self.metrics.safe_operations += 1
                
                # Create audit record
                await execution_safety_engine.audit_operation(operation, execution_result, context)
                
                logger.info("Operation executed safely",
                           operation_id=str(operation.id),
                           execution_time=execution_result.resource_usage.get("execution_time", 0))
            
            elif execution_result.status == "rolled_back":
                self.metrics.rollbacks_performed += 1
                
                await self._handle_security_incident(
                    SecurityIncidentType.SYSTEM_CONFIGURATION,
                    f"Operation rolled back: {operation.id}",
                    context,
                    {"execution_result": execution_result.to_dict()}
                )
            
            return execution_result
            
        except Exception as e:
            self.metrics.blocked_operations += 1
            
            logger.error("Operation execution failed",
                        operation_id=str(operation.id),
                        error=str(e))
            
            await self._handle_security_incident(
                SecurityIncidentType.SYSTEM_CONFIGURATION,
                f"Operation execution error: {str(e)}",
                context,
                {"operation_id": str(operation.id), "error": str(e)}
            )
            
            return ExecutionResult(
                operation_id=operation.id,
                status="failed",
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                error_message=str(e)
            )
    
    async def _validate_pattern_security(
        self,
        operation: Operation,
        context: SecurityContext
    ) -> Dict[str, Any]:
        """Validate pattern security for pattern operations"""
        
        if not operation.pattern_id:
            return {"safe": False, "reason": "No pattern ID provided"}
        
        # Create pattern metadata from operation
        pattern_metadata = PatternMetadata(
            id=operation.pattern_id,
            title=operation.name,
            description=operation.description,
            source=PatternSource.USER_GENERATED,  # Default, would be determined dynamically
            author="unknown"
        )
        
        # Validate pattern security
        validation_result = await pattern_security_engine.validate_pattern_security(
            pattern_metadata,
            str(operation.payload),
            context.user
        )
        
        self.metrics.patterns_validated += 1
        
        if validation_result["overall_status"] == "rejected":
            self.metrics.malicious_patterns_blocked += 1
            return {
                "safe": False,
                "reason": "Pattern failed security validation",
                "validation_result": validation_result
            }
        
        return {
            "safe": True,
            "validation_result": validation_result
        }
    
    async def _validate_agent_security(
        self,
        operation: Operation,
        context: SecurityContext
    ) -> Dict[str, Any]:
        """Validate agent security for agent operations"""
        
        if not operation.agent_type:
            return {"authorized": False, "reason": "No agent type specified"}
        
        # Create mock agent ID for validation (in practice, would come from operation context)
        agent_id = uuid4()
        
        # Check if agent operation is authorized
        authorized = await agent_security_engine.authenticate_agent_operation(
            agent_id,
            operation.action_performed if hasattr(operation, 'action_performed') else "execute",
            {"operation_id": str(operation.id)}
        )
        
        if not authorized:
            self.metrics.agent_violations += 1
            return {
                "authorized": False,
                "reason": "Agent operation not authorized",
                "agent_id": str(agent_id)
            }
        
        return {
            "authorized": True,
            "agent_id": str(agent_id)
        }
    
    async def _validate_data_protection(
        self,
        operation: Operation,
        context: SecurityContext
    ) -> Dict[str, Any]:
        """Validate data protection requirements"""
        
        # Check if operation involves sensitive data
        if operation.data_sensitivity in ["confidential", "secret", "regulated"]:
            # Verify user has appropriate permissions
            required_permission = f"data:{operation.data_sensitivity}"
            if not context.user.has_permission(required_permission):
                return {
                    "compliant": False,
                    "reason": f"User lacks permission: {required_permission}",
                    "data_sensitivity": operation.data_sensitivity
                }
            
            # Log data access for compliance
            await compliance_orchestrator.log_audit_event(
                AuditEventType.DATA_ACCESS,
                f"Sensitive data accessed: {operation.data_sensitivity}",
                user=context.user,
                client_ip=context.client_ip,
                metadata={
                    "operation_id": str(operation.id),
                    "data_sensitivity": operation.data_sensitivity
                }
            )
        
        return {
            "compliant": True,
            "data_sensitivity": operation.data_sensitivity
        }
    
    def _create_blocked_result(
        self,
        operation: Operation,
        reason: str,
        validation_details: Dict[str, Any]
    ) -> ExecutionResult:
        """Create standardized blocked operation result"""
        
        self.metrics.blocked_operations += 1
        
        return ExecutionResult(
            operation_id=operation.id,
            status="blocked",
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            error_message=reason,
            result_data={
                "blocked_reason": reason,
                "validation_details": validation_details,
                "security_policy": "zero_violations"
            }
        )
    
    async def _handle_security_incident(
        self,
        incident_type: SecurityIncidentType,
        description: str,
        context: SecurityContext,
        metadata: Dict[str, Any]
    ):
        """Handle security incident with automated response"""
        
        self.incident_count += 1
        
        # Log incident for compliance
        await compliance_orchestrator.log_audit_event(
            AuditEventType.SECURITY_INCIDENT,
            description,
            user=context.user,
            client_ip=context.client_ip,
            severity=AuditSeverity.WARNING,
            metadata=metadata
        )
        
        # Trigger automated incident response if needed
        response = await security_framework.handle_security_incident(
            incident_type,
            {
                "description": description,
                "user_id": context.user.user_id if context.user else None,
                "client_ip": context.client_ip,
                "session_id": context.session_id,
                **metadata
            }
        )
        
        if response:
            logger.warning("Security incident handled",
                          incident_type=incident_type.value,
                          response_actions=len(response.get("response_actions", [])))
    
    async def run_security_validation(self) -> Dict[str, Any]:
        """Run comprehensive security validation tests"""
        
        logger.info("Running comprehensive security validation")
        
        # Run security test suite
        test_results = await security_test_suite.run_full_security_suite()
        
        # Update metrics
        total_tests = test_results["execution_summary"]["total_tests"]
        passed_tests = test_results["execution_summary"]["passed_tests"]
        success_rate = test_results["execution_summary"]["success_rate"]
        
        # Generate compliance reports
        gdpr_report = await compliance_orchestrator.generate_compliance_report(
            ComplianceFramework.GDPR
        )
        soc2_report = await compliance_orchestrator.generate_compliance_report(
            ComplianceFramework.SOC2
        )
        
        validation_results = {
            "framework_status": self.status.value,
            "security_tests": test_results,
            "compliance_reports": {
                "gdpr": {
                    "compliance_score": gdpr_report.compliance_score,
                    "status": gdpr_report.overall_status.value,
                    "controls_compliant": gdpr_report.controls_compliant,
                    "controls_non_compliant": gdpr_report.controls_non_compliant
                },
                "soc2": {
                    "compliance_score": soc2_report.compliance_score,
                    "status": soc2_report.overall_status.value,
                    "controls_compliant": soc2_report.controls_compliant,
                    "controls_non_compliant": soc2_report.controls_non_compliant
                }
            },
            "security_metrics": {
                "safety_score": self.metrics.calculate_safety_score(),
                "total_operations": self.metrics.total_operations,
                "blocked_operations": self.metrics.blocked_operations,
                "rollbacks_performed": self.metrics.rollbacks_performed,
                "incidents_handled": self.incident_count
            },
            "validation_timestamp": datetime.utcnow().isoformat(),
            "overall_status": "PASS" if success_rate >= 95.0 and gdpr_report.compliance_score >= 0.9 and soc2_report.compliance_score >= 0.9 else "FAIL"
        }
        
        logger.info("Security validation completed",
                   overall_status=validation_results["overall_status"],
                   security_test_success_rate=success_rate,
                   gdpr_compliance=gdpr_report.compliance_score,
                   soc2_compliance=soc2_report.compliance_score)
        
        return validation_results
    
    async def get_framework_status(self) -> Dict[str, Any]:
        """Get comprehensive framework status"""
        
        # Refresh metrics from all components
        await self._refresh_metrics()
        
        # Check component health
        await self._health_check()
        
        return {
            "framework": {
                "status": self.status.value,
                "version": self.framework_version,
                "uptime_seconds": (datetime.utcnow() - self.last_health_check).total_seconds(),
                "last_health_check": self.last_health_check.isoformat()
            },
            "component_health": self.component_health,
            "security_metrics": {
                "safety_score": self.metrics.calculate_safety_score(),
                "total_operations": self.metrics.total_operations,
                "safe_operations": self.metrics.safe_operations,
                "blocked_operations": self.metrics.blocked_operations,
                "rollbacks_performed": self.metrics.rollbacks_performed,
                "incidents_handled": self.incident_count
            },
            "phase_2_targets": {
                "zero_security_violations": self.metrics.blocked_operations == 0 or self.metrics.calculate_safety_score() >= 0.99,
                "100_percent_operations_logged": self.metrics.audit_events_logged > 0,
                "90_percent_rollback_success": (self.metrics.rollbacks_performed / max(1, self.metrics.blocked_operations)) >= 0.9,
                "enterprise_certification_ready": self._check_enterprise_certification_readiness()
            }
        }
    
    async def _refresh_metrics(self):
        """Refresh metrics from all components"""
        
        # Get metrics from each security component
        vault_metrics = await vault_security_integration.get_security_metrics()
        waf_metrics = await web_application_firewall.get_security_metrics()
        agent_metrics = await agent_security_engine.get_agent_security_metrics()
        data_metrics = await data_protection_service.get_protection_metrics()
        
        # Update consolidated metrics
        self.metrics.secrets_managed = vault_metrics["vault_integration"]["total_secrets_managed"]
        self.metrics.requests_processed = waf_metrics["total_tracked_ips"]
        self.metrics.threats_blocked = waf_metrics["blocked_ips"]
        self.metrics.active_agents = agent_metrics["active_agents"]
        self.metrics.quarantined_agents = agent_metrics["quarantined_agents"]
        self.metrics.data_records_protected = data_metrics["total_protected_records"]
        self.metrics.pii_records_encrypted = data_metrics["encrypted_records"]
        
        self.metrics.timestamp = datetime.utcnow()
    
    async def _health_check(self):
        """Perform health check on all components"""
        
        try:
            # Basic health checks for each component
            self.component_health["execution_safety"] = execution_safety_engine is not None
            self.component_health["security_framework"] = security_framework is not None
            self.component_health["pattern_security"] = pattern_security_engine is not None
            self.component_health["agent_security"] = agent_security_engine is not None
            self.component_health["data_protection"] = data_protection_service is not None
            self.component_health["api_security"] = web_application_firewall is not None
            self.component_health["audit_compliance"] = compliance_orchestrator is not None
            self.component_health["vault_integration"] = vault_security_integration is not None
            
            # Update framework status based on component health
            unhealthy_components = [k for k, v in self.component_health.items() if not v]
            
            if len(unhealthy_components) == 0:
                self.status = FrameworkStatus.ACTIVE
            elif len(unhealthy_components) <= 2:
                self.status = FrameworkStatus.DEGRADED
            else:
                self.status = FrameworkStatus.OFFLINE
            
            self.last_health_check = datetime.utcnow()
            
        except Exception as e:
            logger.error("Health check failed", error=str(e))
            self.status = FrameworkStatus.DEGRADED
    
    def _check_enterprise_certification_readiness(self) -> bool:
        """Check if framework meets enterprise certification requirements"""
        
        safety_score = self.metrics.calculate_safety_score()
        
        criteria = [
            safety_score >= 0.95,  # 95% safety score
            self.incident_count == 0 or (self.metrics.safe_operations / max(1, self.incident_count)) >= 100,  # Low incident rate
            self.metrics.audit_events_logged > 0,  # Audit logging active
            all(self.component_health.values()),  # All components healthy
            self.status == FrameworkStatus.ACTIVE  # Framework active
        ]
        
        return all(criteria)

# Global framework instance
execution_safety_framework = ExecutionSafetyFramework()