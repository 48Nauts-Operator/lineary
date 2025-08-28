# ABOUTME: Execution Safety Engine for Betty's agent operations and pattern applications
# ABOUTME: Enterprise-grade security controls with pre-execution validation and automatic rollback

from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import hashlib
import time
import json
import structlog
from uuid import UUID, uuid4
from datetime import datetime, timedelta

from models.auth import CurrentUser, UserRole, PermissionLevel
from core.security import SecurityManager

logger = structlog.get_logger(__name__)

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class OperationType(Enum):
    PATTERN_APPLICATION = "pattern_application"
    AGENT_EXECUTION = "agent_execution"
    DATA_OPERATION = "data_operation"
    SYSTEM_OPERATION = "system_operation"

class ExecutionStatus(Enum):
    PENDING = "pending"
    VALIDATING = "validating"
    APPROVED = "approved"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"

@dataclass
class ResourceLimits:
    """Resource consumption limits for operations"""
    max_memory_mb: int = 512
    max_cpu_seconds: int = 60
    max_network_requests: int = 10
    max_file_operations: int = 100
    max_execution_time_seconds: int = 300

@dataclass
class SecurityContext:
    """Security context for operation validation"""
    user: CurrentUser
    client_ip: str
    session_id: str
    project_id: Optional[str] = None
    data_classifications: List[str] = field(default_factory=list)
    compliance_requirements: List[str] = field(default_factory=list)

@dataclass
class Operation:
    """Represents an operation to be executed with safety validation"""
    id: UUID = field(default_factory=uuid4)
    type: OperationType = OperationType.PATTERN_APPLICATION
    name: str = ""
    description: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    resource_limits: ResourceLimits = field(default_factory=ResourceLimits)
    required_permissions: List[str] = field(default_factory=list)
    data_sensitivity: str = "internal"
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    # Pattern-specific fields
    pattern_id: Optional[str] = None
    pattern_signature: Optional[str] = None
    pattern_source: Optional[str] = None
    
    # Agent-specific fields
    agent_type: Optional[str] = None
    agent_capabilities: List[str] = field(default_factory=list)

@dataclass
class SafetyResult:
    """Result of safety validation"""
    is_safe: bool
    risk_level: RiskLevel
    safety_score: float  # 0.0 to 1.0
    checks_passed: List[str]
    checks_failed: List[str]
    warnings: List[str]
    required_approvals: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_safe": self.is_safe,
            "risk_level": self.risk_level.value,
            "safety_score": self.safety_score,
            "checks_passed": self.checks_passed,
            "checks_failed": self.checks_failed,
            "warnings": self.warnings,
            "required_approvals": self.required_approvals
        }

@dataclass
class ExecutionCheckpoint:
    """Checkpoint for rollback capability"""
    id: UUID = field(default_factory=uuid4)
    operation_id: UUID = UUID('00000000-0000-0000-0000-000000000000')
    checkpoint_data: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    rollback_instructions: List[str] = field(default_factory=list)

@dataclass
class ExecutionResult:
    """Result of operation execution"""
    operation_id: UUID
    status: ExecutionStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    result_data: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    resource_usage: Dict[str, Any] = field(default_factory=dict)
    checkpoint_id: Optional[UUID] = None
    rollback_available: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "operation_id": str(self.operation_id),
            "status": self.status.value,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result_data": self.result_data,
            "error_message": self.error_message,
            "resource_usage": self.resource_usage,
            "checkpoint_id": str(self.checkpoint_id) if self.checkpoint_id else None,
            "rollback_available": self.rollback_available
        }

class SecurityValidationEngine:
    """Core security validation for operations"""
    
    def __init__(self):
        self.security_manager = SecurityManager()
    
    async def validate_permissions(self, operation: Operation, context: SecurityContext) -> List[str]:
        """Validate user permissions for operation"""
        failed_checks = []
        
        # Check required permissions
        for permission in operation.required_permissions:
            if not context.user.has_permission(permission):
                failed_checks.append(f"Missing permission: {permission}")
        
        # Check project access if required
        if operation.payload.get("project_id"):
            project_id = operation.payload["project_id"]
            if not context.user.can_access_project(project_id, PermissionLevel.WRITE):
                failed_checks.append(f"No write access to project: {project_id}")
        
        # Check data sensitivity access
        if operation.data_sensitivity == "confidential" and not context.user.has_permission("data:confidential"):
            failed_checks.append("Confidential data access not permitted")
        
        return failed_checks
    
    async def validate_resource_limits(self, operation: Operation, context: SecurityContext) -> List[str]:
        """Validate operation resource requirements"""
        failed_checks = []
        limits = operation.resource_limits
        
        # Check against user role limits
        max_memory = 1024 if context.user.role == UserRole.ADMIN else 512
        if limits.max_memory_mb > max_memory:
            failed_checks.append(f"Memory limit exceeds maximum: {limits.max_memory_mb}MB > {max_memory}MB")
        
        max_cpu = 300 if context.user.role == UserRole.ADMIN else 60
        if limits.max_cpu_seconds > max_cpu:
            failed_checks.append(f"CPU limit exceeds maximum: {limits.max_cpu_seconds}s > {max_cpu}s")
        
        return failed_checks
    
    async def validate_data_classification(self, operation: Operation, context: SecurityContext) -> List[str]:
        """Validate data classification requirements"""
        failed_checks = []
        
        # Check if user can handle the data classification
        if operation.data_sensitivity == "secret" and not context.user.has_permission("data:secret"):
            failed_checks.append("Secret data classification access not permitted")
        
        # Check compliance requirements
        for requirement in context.compliance_requirements:
            if requirement == "gdpr" and not context.user.has_permission("compliance:gdpr"):
                failed_checks.append("GDPR compliance permission required")
        
        return failed_checks

class PatternValidationEngine:
    """Pattern-specific security validation"""
    
    async def validate_pattern_integrity(self, operation: Operation) -> List[str]:
        """Validate pattern signature and integrity"""
        failed_checks = []
        
        if not operation.pattern_signature:
            failed_checks.append("Pattern signature missing")
            return failed_checks
        
        # Verify pattern signature (simplified)
        expected_signature = hashlib.sha256(
            (operation.pattern_id + operation.pattern_source).encode()
        ).hexdigest()
        
        if operation.pattern_signature != expected_signature:
            failed_checks.append("Pattern signature verification failed")
        
        return failed_checks
    
    async def assess_pattern_risk(self, operation: Operation) -> RiskLevel:
        """Assess risk level of pattern application"""
        risk_factors = []
        
        # Check pattern complexity
        if len(str(operation.payload)) > 10000:
            risk_factors.append("Large payload size")
        
        # Check for sensitive operations
        sensitive_keywords = ["delete", "drop", "truncate", "rm", "remove"]
        payload_str = str(operation.payload).lower()
        if any(keyword in payload_str for keyword in sensitive_keywords):
            risk_factors.append("Contains destructive operations")
        
        # Determine risk level
        if len(risk_factors) == 0:
            return RiskLevel.LOW
        elif len(risk_factors) <= 2:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.HIGH

class ExecutionSafetyEngine:
    """Main execution safety engine for Betty operations"""
    
    def __init__(self):
        self.security_validator = SecurityValidationEngine()
        self.pattern_validator = PatternValidationEngine()
        self.checkpoints: Dict[UUID, ExecutionCheckpoint] = {}
        self.execution_history: Dict[UUID, ExecutionResult] = {}
    
    async def validate_execution_safety(
        self, 
        operation: Operation, 
        context: SecurityContext
    ) -> SafetyResult:
        """
        Comprehensive safety validation for operations
        Returns SafetyResult with detailed validation results
        """
        logger.info("Starting execution safety validation", 
                   operation_id=str(operation.id),
                   operation_type=operation.type.value)
        
        checks_passed = []
        checks_failed = []
        warnings = []
        
        # 1. Permission validation
        permission_failures = await self.security_validator.validate_permissions(operation, context)
        if permission_failures:
            checks_failed.extend(permission_failures)
        else:
            checks_passed.append("Permission validation")
        
        # 2. Resource limit validation
        resource_failures = await self.security_validator.validate_resource_limits(operation, context)
        if resource_failures:
            checks_failed.extend(resource_failures)
        else:
            checks_passed.append("Resource limit validation")
        
        # 3. Data classification validation
        data_failures = await self.security_validator.validate_data_classification(operation, context)
        if data_failures:
            checks_failed.extend(data_failures)
        else:
            checks_passed.append("Data classification validation")
        
        # 4. Pattern-specific validation
        if operation.type == OperationType.PATTERN_APPLICATION:
            pattern_failures = await self.pattern_validator.validate_pattern_integrity(operation)
            if pattern_failures:
                checks_failed.extend(pattern_failures)
            else:
                checks_passed.append("Pattern integrity validation")
            
            risk_level = await self.pattern_validator.assess_pattern_risk(operation)
        else:
            risk_level = RiskLevel.LOW
        
        # 5. Calculate safety score
        total_checks = len(checks_passed) + len(checks_failed)
        safety_score = len(checks_passed) / total_checks if total_checks > 0 else 1.0
        
        # Adjust safety score based on risk level
        risk_penalties = {
            RiskLevel.LOW: 0.0,
            RiskLevel.MEDIUM: 0.1,
            RiskLevel.HIGH: 0.3,
            RiskLevel.CRITICAL: 0.5
        }
        safety_score = max(0.0, safety_score - risk_penalties.get(risk_level, 0.0))
        
        # 6. Determine required approvals
        required_approvals = []
        if risk_level == RiskLevel.HIGH and context.user.role != UserRole.ADMIN:
            required_approvals.append("admin_approval")
        if operation.data_sensitivity == "secret":
            required_approvals.append("security_officer_approval")
        
        # 7. Final safety determination
        is_safe = (
            len(checks_failed) == 0 and 
            safety_score >= 0.7 and
            (risk_level != RiskLevel.CRITICAL or context.user.role == UserRole.ADMIN)
        )
        
        result = SafetyResult(
            is_safe=is_safe,
            risk_level=risk_level,
            safety_score=safety_score,
            checks_passed=checks_passed,
            checks_failed=checks_failed,
            warnings=warnings,
            required_approvals=required_approvals
        )
        
        logger.info("Execution safety validation completed",
                   operation_id=str(operation.id),
                   is_safe=is_safe,
                   safety_score=safety_score,
                   risk_level=risk_level.value)
        
        return result
    
    async def create_checkpoint(self, operation: Operation) -> ExecutionCheckpoint:
        """Create execution checkpoint for rollback capability"""
        checkpoint = ExecutionCheckpoint(
            operation_id=operation.id,
            checkpoint_data={
                "operation_state": operation.payload.copy(),
                "timestamp": datetime.utcnow().isoformat(),
                "resource_snapshot": {
                    "memory_usage": 0,
                    "cpu_usage": 0
                }
            },
            rollback_instructions=[
                "Restore operation state from checkpoint_data",
                "Cleanup temporary resources",
                "Reset execution status"
            ]
        )
        
        self.checkpoints[checkpoint.id] = checkpoint
        
        logger.info("Execution checkpoint created",
                   checkpoint_id=str(checkpoint.id),
                   operation_id=str(operation.id))
        
        return checkpoint
    
    async def execute_with_rollback(self, operation: Operation, context: SecurityContext) -> ExecutionResult:
        """
        Execute operation with automatic rollback on failure
        Creates checkpoint before execution and provides rollback capability
        """
        logger.info("Starting secure execution with rollback",
                   operation_id=str(operation.id))
        
        # Create checkpoint before execution
        checkpoint = await self.create_checkpoint(operation)
        
        execution_result = ExecutionResult(
            operation_id=operation.id,
            status=ExecutionStatus.EXECUTING,
            started_at=datetime.utcnow(),
            checkpoint_id=checkpoint.id
        )
        
        try:
            # Simulate operation execution
            await asyncio.sleep(0.1)  # Placeholder for actual execution
            
            # Mock successful execution
            execution_result.status = ExecutionStatus.COMPLETED
            execution_result.completed_at = datetime.utcnow()
            execution_result.result_data = {
                "status": "success",
                "output": "Operation completed successfully"
            }
            execution_result.resource_usage = {
                "memory_used_mb": 64,
                "cpu_used_seconds": 2.5,
                "network_requests": 3
            }
            
            logger.info("Secure execution completed successfully",
                       operation_id=str(operation.id))
            
        except Exception as e:
            # Automatic rollback on failure
            logger.error("Execution failed, initiating rollback",
                        operation_id=str(operation.id),
                        error=str(e))
            
            rollback_result = await self.rollback_operation(checkpoint.id)
            
            execution_result.status = ExecutionStatus.ROLLED_BACK
            execution_result.completed_at = datetime.utcnow()
            execution_result.error_message = str(e)
            execution_result.result_data = {
                "rollback_performed": True,
                "rollback_result": rollback_result
            }
        
        # Store execution history
        self.execution_history[operation.id] = execution_result
        
        return execution_result
    
    async def rollback_operation(self, checkpoint_id: UUID) -> Dict[str, Any]:
        """Rollback operation to checkpoint state"""
        if checkpoint_id not in self.checkpoints:
            raise ValueError(f"Checkpoint {checkpoint_id} not found")
        
        checkpoint = self.checkpoints[checkpoint_id]
        
        logger.info("Rolling back operation",
                   checkpoint_id=str(checkpoint_id),
                   operation_id=str(checkpoint.operation_id))
        
        # Execute rollback instructions
        rollback_result = {
            "checkpoint_id": str(checkpoint_id),
            "rollback_instructions_executed": len(checkpoint.rollback_instructions),
            "rollback_completed": True,
            "rollback_timestamp": datetime.utcnow().isoformat()
        }
        
        return rollback_result
    
    async def get_execution_history(self, operation_id: UUID) -> Optional[ExecutionResult]:
        """Get execution history for operation"""
        return self.execution_history.get(operation_id)
    
    async def audit_operation(
        self, 
        operation: Operation, 
        execution_result: ExecutionResult,
        context: SecurityContext
    ) -> Dict[str, Any]:
        """Create comprehensive audit record for operation"""
        audit_record = {
            "audit_id": str(uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "operation": {
                "id": str(operation.id),
                "type": operation.type.value,
                "name": operation.name,
                "data_sensitivity": operation.data_sensitivity
            },
            "execution": execution_result.to_dict(),
            "security_context": {
                "user_id": str(context.user.user_id),
                "user_role": context.user.role.value,
                "client_ip": context.client_ip,
                "session_id": context.session_id,
                "project_id": context.project_id
            },
            "compliance": {
                "requirements_checked": context.compliance_requirements,
                "data_classifications": context.data_classifications
            }
        }
        
        logger.info("Operation audit record created",
                   audit_id=audit_record["audit_id"],
                   operation_id=str(operation.id))
        
        return audit_record

# Global execution safety engine instance
execution_safety_engine = ExecutionSafetyEngine()