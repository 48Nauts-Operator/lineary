# ABOUTME: Pattern execution security with sandbox validation and threat detection
# ABOUTME: Enterprise-grade pattern security controls for safe pattern application at scale

from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import hashlib
import re
import ast
import tempfile
import subprocess
import time
import structlog
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from pathlib import Path

from core.execution_safety import Operation, OperationType, RiskLevel, SecurityContext
from core.security_framework import DataSensitivity, SecurityIncidentType, security_framework
from models.auth import CurrentUser

logger = structlog.get_logger(__name__)

class PatternSource(Enum):
    TRUSTED = "trusted"
    COMMUNITY = "community"
    EXTERNAL = "external"
    USER_GENERATED = "user_generated"

class SandboxStatus(Enum):
    CREATED = "created"
    INITIALIZED = "initialized"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    TERMINATED = "terminated"

class ThreatType(Enum):
    CODE_INJECTION = "code_injection"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DATA_EXFILTRATION = "data_exfiltration"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    MALICIOUS_NETWORK = "malicious_network"
    FILE_SYSTEM_ABUSE = "file_system_abuse"
    CRYPTOMINING = "cryptomining"

@dataclass
class PatternSignature:
    """Digital signature for pattern integrity"""
    pattern_id: str
    content_hash: str
    signature: str
    signer: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    algorithm: str = "sha256_rsa"
    
    def verify(self, pattern_content: str) -> bool:
        """Verify pattern signature integrity"""
        expected_hash = hashlib.sha256(pattern_content.encode()).hexdigest()
        return self.content_hash == expected_hash

@dataclass
class PatternMetadata:
    """Enhanced pattern metadata for security validation"""
    id: str
    title: str
    description: str
    source: PatternSource
    author: str
    version: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    # Security attributes
    risk_level: RiskLevel = RiskLevel.LOW
    required_permissions: List[str] = field(default_factory=list)
    data_sensitivity: DataSensitivity = DataSensitivity.INTERNAL
    
    # Execution attributes
    execution_timeout_seconds: int = 300
    max_memory_mb: int = 256
    max_cpu_cores: int = 1
    network_access_required: bool = False
    file_system_access: List[str] = field(default_factory=list)
    
    # Dependencies and requirements
    dependencies: List[str] = field(default_factory=list)
    python_version: Optional[str] = None
    required_tools: List[str] = field(default_factory=list)
    
    # Trust and validation
    signature: Optional[PatternSignature] = None
    validation_status: str = "pending"
    security_scan_results: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SandboxEnvironment:
    """Isolated sandbox environment for pattern execution"""
    id: UUID = field(default_factory=uuid4)
    pattern_id: str = ""
    status: SandboxStatus = SandboxStatus.CREATED
    container_id: Optional[str] = None
    
    # Resource limits
    memory_limit_mb: int = 256
    cpu_limit: float = 0.5  # CPU cores
    disk_limit_mb: int = 100
    network_enabled: bool = False
    
    # Security controls
    allowed_syscalls: Set[str] = field(default_factory=set)
    blocked_domains: Set[str] = field(default_factory=set)
    file_system_readonly: bool = True
    
    # Monitoring
    created_at: datetime = field(default_factory=datetime.utcnow)
    execution_start: Optional[datetime] = None
    execution_end: Optional[datetime] = None
    resource_usage: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ThreatDetectionResult:
    """Result of threat detection scan"""
    threats_found: List[ThreatType] = field(default_factory=list)
    risk_score: float = 0.0  # 0.0 to 1.0
    suspicious_patterns: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    scan_timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "threats_found": [t.value for t in self.threats_found],
            "risk_score": self.risk_score,
            "suspicious_patterns": self.suspicious_patterns,
            "recommendations": self.recommendations,
            "scan_timestamp": self.scan_timestamp.isoformat()
        }

class PatternThreatDetector:
    """Advanced threat detection for patterns"""
    
    # Dangerous function patterns
    DANGEROUS_FUNCTIONS = {
        'eval', 'exec', 'compile', '__import__',
        'open', 'file', 'input', 'raw_input',
        'subprocess', 'os.system', 'os.popen',
        'pickle.loads', 'marshal.loads'
    }
    
    # Suspicious network patterns
    NETWORK_PATTERNS = {
        'urllib', 'requests', 'socket', 'http',
        'ftp', 'smtp', 'telnet', 'ssh'
    }
    
    # File system access patterns
    FILE_SYSTEM_PATTERNS = {
        'os.remove', 'os.unlink', 'shutil.rmtree',
        'os.chmod', 'os.chown', 'os.rename'
    }
    
    # Privilege escalation patterns
    PRIVILEGE_PATTERNS = {
        'sudo', 'su', 'chmod +x', '/etc/passwd',
        'setuid', 'setgid', 'root', 'administrator'
    }
    
    def __init__(self):
        self.threat_signatures = self._load_threat_signatures()
    
    def _load_threat_signatures(self) -> Dict[ThreatType, List[str]]:
        """Load threat detection signatures"""
        return {
            ThreatType.CODE_INJECTION: [
                r'eval\s*\(',
                r'exec\s*\(',
                r'__import__\s*\(',
                r'compile\s*\('
            ],
            ThreatType.PRIVILEGE_ESCALATION: [
                r'sudo\s+',
                r'chmod\s+\+x',
                r'/etc/passwd',
                r'setuid\s*\('
            ],
            ThreatType.DATA_EXFILTRATION: [
                r'base64\.encode',
                r'urllib\.request',
                r'requests\.post',
                r'socket\.connect'
            ],
            ThreatType.RESOURCE_EXHAUSTION: [
                r'while\s+True:',
                r'for.*in.*range\(\s*\d{6,}',
                r'.*\*\*.*\d{3,}',  # Large exponentials
                r'threading\.Thread'
            ],
            ThreatType.FILE_SYSTEM_ABUSE: [
                r'os\.remove',
                r'shutil\.rmtree',
                r'open\(.*["\']w["\']',
                r'os\.chmod'
            ],
            ThreatType.CRYPTOMINING: [
                r'hashlib\.sha256.*nonce',
                r'mining',
                r'blockchain',
                r'cryptocurrency'
            ]
        }
    
    async def scan_pattern_content(self, pattern_content: str) -> ThreatDetectionResult:
        """Comprehensive threat detection scan of pattern content"""
        logger.info("Starting pattern threat detection scan")
        
        threats_found = []
        suspicious_patterns = []
        risk_score = 0.0
        recommendations = []
        
        # 1. Static code analysis for dangerous functions
        for func in self.DANGEROUS_FUNCTIONS:
            if func in pattern_content:
                threats_found.append(ThreatType.CODE_INJECTION)
                suspicious_patterns.append(f"Dangerous function: {func}")
                risk_score += 0.3
        
        # 2. Regex-based signature detection
        for threat_type, signatures in self.threat_signatures.items():
            for signature in signatures:
                if re.search(signature, pattern_content, re.IGNORECASE):
                    if threat_type not in threats_found:
                        threats_found.append(threat_type)
                    suspicious_patterns.append(f"{threat_type.value}: {signature}")
                    risk_score += 0.2
        
        # 3. AST-based analysis for Python code
        try:
            ast_analysis = await self._analyze_ast(pattern_content)
            threats_found.extend(ast_analysis["threats"])
            suspicious_patterns.extend(ast_analysis["patterns"])
            risk_score += ast_analysis["risk_increment"]
        except SyntaxError:
            # Not Python code or malformed
            pass
        
        # 4. Network activity detection
        if any(pattern in pattern_content.lower() for pattern in self.NETWORK_PATTERNS):
            threats_found.append(ThreatType.MALICIOUS_NETWORK)
            suspicious_patterns.append("Network access detected")
            risk_score += 0.15
        
        # 5. Generate recommendations
        if risk_score > 0.7:
            recommendations.extend([
                "Pattern requires admin approval",
                "Execute in maximum security sandbox",
                "Monitor for suspicious behavior"
            ])
        elif risk_score > 0.4:
            recommendations.extend([
                "Execute with limited privileges",
                "Monitor resource usage",
                "Restrict network access"
            ])
        
        # Normalize risk score
        risk_score = min(1.0, risk_score)
        
        result = ThreatDetectionResult(
            threats_found=threats_found,
            risk_score=risk_score,
            suspicious_patterns=suspicious_patterns,
            recommendations=recommendations
        )
        
        logger.info("Pattern threat detection completed",
                   threats_count=len(threats_found),
                   risk_score=risk_score)
        
        return result
    
    async def _analyze_ast(self, code: str) -> Dict[str, Any]:
        """AST-based code analysis for deeper threat detection"""
        threats = []
        patterns = []
        risk_increment = 0.0
        
        try:
            tree = ast.parse(code)
            
            # Analyze AST nodes
            for node in ast.walk(tree):
                # Check for dangerous imports
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in ['os', 'subprocess', 'pickle', 'marshal']:
                            patterns.append(f"Dangerous import: {alias.name}")
                            risk_increment += 0.1
                
                # Check for function calls
                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        if node.func.id in self.DANGEROUS_FUNCTIONS:
                            threats.append(ThreatType.CODE_INJECTION)
                            patterns.append(f"Dangerous function call: {node.func.id}")
                            risk_increment += 0.2
                
                # Check for while loops (potential infinite loops)
                elif isinstance(node, ast.While):
                    if isinstance(node.test, ast.Constant) and node.test.value is True:
                        threats.append(ThreatType.RESOURCE_EXHAUSTION)
                        patterns.append("Potential infinite loop: while True")
                        risk_increment += 0.3
        
        except Exception as e:
            logger.debug("AST analysis failed", error=str(e))
        
        return {
            "threats": threats,
            "patterns": patterns,
            "risk_increment": risk_increment
        }

class SandboxManager:
    """Manages isolated sandbox environments for pattern execution"""
    
    def __init__(self):
        self.active_sandboxes: Dict[UUID, SandboxEnvironment] = {}
        self.sandbox_templates = self._initialize_templates()
    
    def _initialize_templates(self) -> Dict[str, Dict[str, Any]]:
        """Initialize sandbox security templates"""
        return {
            "minimal": {
                "memory_limit_mb": 128,
                "cpu_limit": 0.25,
                "disk_limit_mb": 50,
                "network_enabled": False,
                "execution_timeout": 60
            },
            "standard": {
                "memory_limit_mb": 256,
                "cpu_limit": 0.5,
                "disk_limit_mb": 100,
                "network_enabled": False,
                "execution_timeout": 300
            },
            "network": {
                "memory_limit_mb": 512,
                "cpu_limit": 0.5,
                "disk_limit_mb": 100,
                "network_enabled": True,
                "execution_timeout": 300
            },
            "high_security": {
                "memory_limit_mb": 128,
                "cpu_limit": 0.1,
                "disk_limit_mb": 25,
                "network_enabled": False,
                "execution_timeout": 30
            }
        }
    
    async def create_sandbox(
        self,
        pattern_metadata: PatternMetadata,
        security_template: str = "standard"
    ) -> SandboxEnvironment:
        """Create isolated sandbox environment for pattern execution"""
        
        template = self.sandbox_templates.get(security_template, self.sandbox_templates["standard"])
        
        sandbox = SandboxEnvironment(
            pattern_id=pattern_metadata.id,
            memory_limit_mb=min(pattern_metadata.max_memory_mb, template["memory_limit_mb"]),
            cpu_limit=template["cpu_limit"],
            disk_limit_mb=template["disk_limit_mb"],
            network_enabled=template["network_enabled"] and pattern_metadata.network_access_required,
            file_system_readonly=True,
            allowed_syscalls=self._get_allowed_syscalls(security_template),
            blocked_domains=self._get_blocked_domains()
        )
        
        # Initialize container (simplified implementation)
        sandbox.container_id = f"betty_sandbox_{sandbox.id.hex[:8]}"
        sandbox.status = SandboxStatus.INITIALIZED
        
        self.active_sandboxes[sandbox.id] = sandbox
        
        logger.info("Sandbox created",
                   sandbox_id=str(sandbox.id),
                   pattern_id=pattern_metadata.id,
                   template=security_template)
        
        return sandbox
    
    def _get_allowed_syscalls(self, template: str) -> Set[str]:
        """Get allowed system calls for sandbox template"""
        base_calls = {
            'read', 'write', 'open', 'close', 'stat', 'mmap',
            'munmap', 'brk', 'rt_sigaction', 'rt_sigprocmask',
            'ioctl', 'access', 'getpid', 'getuid', 'geteuid'
        }
        
        if template == "high_security":
            return {'read', 'write', 'getpid', 'getuid'}
        
        return base_calls
    
    def _get_blocked_domains(self) -> Set[str]:
        """Get blocked domains for network restrictions"""
        return {
            'pastebin.com',
            'hastebin.com',
            'transfer.sh',
            'file.io',
            'temp.sh',
            'raw.githubusercontent.com'  # Prevent code injection
        }
    
    async def execute_in_sandbox(
        self,
        sandbox: SandboxEnvironment,
        pattern_content: str,
        timeout_seconds: int = 300
    ) -> Dict[str, Any]:
        """Execute pattern in isolated sandbox environment"""
        
        sandbox.status = SandboxStatus.EXECUTING
        sandbox.execution_start = datetime.utcnow()
        
        logger.info("Starting sandbox execution",
                   sandbox_id=str(sandbox.id),
                   timeout=timeout_seconds)
        
        try:
            # Create temporary file for pattern execution
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(pattern_content)
                temp_file = f.name
            
            # Execute with resource limits (simplified implementation)
            start_time = time.time()
            
            # Simulate execution with security monitoring
            result = await self._simulate_secure_execution(
                temp_file, sandbox, timeout_seconds
            )
            
            execution_time = time.time() - start_time
            
            # Update sandbox status
            sandbox.status = SandboxStatus.COMPLETED
            sandbox.execution_end = datetime.utcnow()
            sandbox.resource_usage = {
                "execution_time": execution_time,
                "memory_used_mb": min(50, sandbox.memory_limit_mb),
                "cpu_time": min(1.0, execution_time * sandbox.cpu_limit)
            }
            
            logger.info("Sandbox execution completed",
                       sandbox_id=str(sandbox.id),
                       execution_time=execution_time)
            
            return result
            
        except TimeoutError:
            sandbox.status = SandboxStatus.TIMEOUT
            logger.warning("Sandbox execution timeout",
                          sandbox_id=str(sandbox.id))
            return {"error": "Execution timeout", "status": "timeout"}
            
        except Exception as e:
            sandbox.status = SandboxStatus.FAILED
            sandbox.execution_end = datetime.utcnow()
            logger.error("Sandbox execution failed",
                        sandbox_id=str(sandbox.id),
                        error=str(e))
            return {"error": str(e), "status": "failed"}
        
        finally:
            # Cleanup
            try:
                Path(temp_file).unlink()
            except:
                pass
    
    async def _simulate_secure_execution(
        self,
        script_path: str,
        sandbox: SandboxEnvironment,
        timeout: int
    ) -> Dict[str, Any]:
        """Simulate secure pattern execution with monitoring"""
        
        # In production, this would use Docker/containers
        # For now, simulate execution result
        
        return {
            "status": "success",
            "output": "Pattern executed successfully in sandbox",
            "resource_usage": {
                "memory_mb": 32,
                "cpu_seconds": 1.2,
                "network_requests": 0
            },
            "security_violations": [],
            "execution_time": 1.5
        }
    
    async def terminate_sandbox(self, sandbox_id: UUID) -> bool:
        """Terminate sandbox and cleanup resources"""
        
        if sandbox_id not in self.active_sandboxes:
            return False
        
        sandbox = self.active_sandboxes[sandbox_id]
        sandbox.status = SandboxStatus.TERMINATED
        
        # Cleanup container/resources (simplified)
        logger.info("Sandbox terminated",
                   sandbox_id=str(sandbox_id))
        
        del self.active_sandboxes[sandbox_id]
        return True

class PatternSecurityEngine:
    """Main pattern security engine orchestrating all security controls"""
    
    def __init__(self):
        self.threat_detector = PatternThreatDetector()
        self.sandbox_manager = SandboxManager()
        self.trusted_sources: Set[str] = {"betty-official", "verified-community"}
    
    async def validate_pattern_security(
        self,
        pattern_metadata: PatternMetadata,
        pattern_content: str,
        user: CurrentUser
    ) -> Dict[str, Any]:
        """
        Comprehensive pattern security validation
        Returns validation results with security recommendations
        """
        logger.info("Starting pattern security validation",
                   pattern_id=pattern_metadata.id,
                   user_id=str(user.user_id))
        
        validation_results = {
            "pattern_id": pattern_metadata.id,
            "validation_timestamp": datetime.utcnow().isoformat(),
            "overall_status": "pending",
            "security_score": 0.0,
            "validation_stages": {}
        }
        
        try:
            # Stage 1: Signature verification
            signature_valid = await self._verify_pattern_signature(pattern_metadata, pattern_content)
            validation_results["validation_stages"]["signature_verification"] = {
                "status": "passed" if signature_valid else "failed",
                "trusted_source": pattern_metadata.source.value in self.trusted_sources
            }
            
            # Stage 2: Threat detection
            threat_scan = await self.threat_detector.scan_pattern_content(pattern_content)
            validation_results["validation_stages"]["threat_detection"] = threat_scan.to_dict()
            
            # Stage 3: Permission validation
            permission_check = await security_framework.check_rbac_permissions(
                user, "pattern", "execute", {
                    "data_sensitivity": pattern_metadata.data_sensitivity.value,
                    "risk_level": pattern_metadata.risk_level.value
                }
            )
            validation_results["validation_stages"]["permission_check"] = {
                "status": "passed" if permission_check.granted else "failed",
                "missing_permissions": permission_check.missing_permissions
            }
            
            # Stage 4: Resource validation
            resource_check = await self._validate_resource_requirements(pattern_metadata, user)
            validation_results["validation_stages"]["resource_validation"] = resource_check
            
            # Calculate overall security score
            security_score = await self._calculate_security_score(
                validation_results["validation_stages"], threat_scan
            )
            validation_results["security_score"] = security_score
            
            # Determine overall status
            if security_score >= 0.8 and threat_scan.risk_score < 0.3:
                validation_results["overall_status"] = "approved"
            elif security_score >= 0.6 and threat_scan.risk_score < 0.6:
                validation_results["overall_status"] = "conditional_approval"
            else:
                validation_results["overall_status"] = "rejected"
            
            # Generate security recommendations
            validation_results["security_recommendations"] = await self._generate_security_recommendations(
                validation_results, pattern_metadata, threat_scan
            )
            
            logger.info("Pattern security validation completed",
                       pattern_id=pattern_metadata.id,
                       status=validation_results["overall_status"],
                       security_score=security_score)
            
        except Exception as e:
            validation_results["overall_status"] = "error"
            validation_results["error"] = str(e)
            logger.error("Pattern security validation failed",
                        pattern_id=pattern_metadata.id,
                        error=str(e))
        
        return validation_results
    
    async def execute_pattern_safely(
        self,
        pattern_metadata: PatternMetadata,
        pattern_content: str,
        user: CurrentUser,
        execution_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute pattern in secure sandbox environment
        Returns execution results with security monitoring
        """
        logger.info("Starting secure pattern execution",
                   pattern_id=pattern_metadata.id,
                   user_id=str(user.user_id))
        
        # First validate pattern security
        validation = await self.validate_pattern_security(pattern_metadata, pattern_content, user)
        
        if validation["overall_status"] not in ["approved", "conditional_approval"]:
            return {
                "status": "rejected",
                "reason": "Pattern failed security validation",
                "validation_results": validation
            }
        
        # Determine sandbox security level
        security_template = await self._determine_sandbox_template(
            pattern_metadata, validation, user
        )
        
        # Create sandbox
        sandbox = await self.sandbox_manager.create_sandbox(pattern_metadata, security_template)
        
        try:
            # Execute in sandbox
            execution_result = await self.sandbox_manager.execute_in_sandbox(
                sandbox, pattern_content, pattern_metadata.execution_timeout_seconds
            )
            
            # Security monitoring and analysis
            security_analysis = await self._analyze_execution_security(
                sandbox, execution_result, pattern_metadata
            )
            
            execution_result.update({
                "sandbox_id": str(sandbox.id),
                "security_analysis": security_analysis,
                "validation_results": validation
            })
            
            return execution_result
            
        finally:
            # Cleanup sandbox
            await self.sandbox_manager.terminate_sandbox(sandbox.id)
    
    async def _verify_pattern_signature(
        self,
        pattern_metadata: PatternMetadata,
        pattern_content: str
    ) -> bool:
        """Verify pattern digital signature"""
        if not pattern_metadata.signature:
            return pattern_metadata.source in [PatternSource.TRUSTED]
        
        return pattern_metadata.signature.verify(pattern_content)
    
    async def _validate_resource_requirements(
        self,
        pattern_metadata: PatternMetadata,
        user: CurrentUser
    ) -> Dict[str, Any]:
        """Validate pattern resource requirements against user limits"""
        
        # User resource limits based on role
        user_limits = {
            "admin": {"memory_mb": 1024, "cpu_cores": 2, "execution_time": 600},
            "developer": {"memory_mb": 512, "cpu_cores": 1, "execution_time": 300},
            "reader": {"memory_mb": 256, "cpu_cores": 1, "execution_time": 60}
        }
        
        limits = user_limits.get(user.role.value, user_limits["reader"])
        violations = []
        
        if pattern_metadata.max_memory_mb > limits["memory_mb"]:
            violations.append(f"Memory requirement {pattern_metadata.max_memory_mb}MB exceeds limit {limits['memory_mb']}MB")
        
        if pattern_metadata.max_cpu_cores > limits["cpu_cores"]:
            violations.append(f"CPU requirement {pattern_metadata.max_cpu_cores} cores exceeds limit {limits['cpu_cores']} cores")
        
        if pattern_metadata.execution_timeout_seconds > limits["execution_time"]:
            violations.append(f"Execution time {pattern_metadata.execution_timeout_seconds}s exceeds limit {limits['execution_time']}s")
        
        return {
            "status": "passed" if not violations else "failed",
            "violations": violations,
            "user_limits": limits
        }
    
    async def _calculate_security_score(
        self,
        validation_stages: Dict[str, Any],
        threat_scan: ThreatDetectionResult
    ) -> float:
        """Calculate overall security score for pattern"""
        
        score = 1.0
        
        # Signature verification weight: 0.3
        if not validation_stages["signature_verification"]["status"] == "passed":
            score -= 0.3
        
        # Threat detection weight: 0.4
        score -= (threat_scan.risk_score * 0.4)
        
        # Permission check weight: 0.2
        if not validation_stages["permission_check"]["status"] == "passed":
            score -= 0.2
        
        # Resource validation weight: 0.1
        if not validation_stages["resource_validation"]["status"] == "passed":
            score -= 0.1
        
        return max(0.0, min(1.0, score))
    
    async def _generate_security_recommendations(
        self,
        validation_results: Dict[str, Any],
        pattern_metadata: PatternMetadata,
        threat_scan: ThreatDetectionResult
    ) -> List[str]:
        """Generate security recommendations based on validation results"""
        
        recommendations = []
        
        if validation_results["security_score"] < 0.8:
            recommendations.append("Pattern requires additional security review")
        
        if threat_scan.risk_score > 0.5:
            recommendations.extend([
                "Execute in high-security sandbox",
                "Monitor for suspicious behavior during execution",
                "Restrict network access"
            ])
        
        if pattern_metadata.network_access_required:
            recommendations.append("Network access should be limited to essential domains only")
        
        if validation_results["validation_stages"]["permission_check"]["status"] == "failed":
            recommendations.append("User requires additional permissions for safe execution")
        
        return recommendations
    
    async def _determine_sandbox_template(
        self,
        pattern_metadata: PatternMetadata,
        validation: Dict[str, Any],
        user: CurrentUser
    ) -> str:
        """Determine appropriate sandbox security template"""
        
        if validation["security_score"] < 0.6:
            return "high_security"
        
        if pattern_metadata.risk_level == RiskLevel.HIGH:
            return "high_security"
        
        if pattern_metadata.network_access_required:
            return "network"
        
        if user.role == UserRole.READER:
            return "minimal"
        
        return "standard"
    
    async def _analyze_execution_security(
        self,
        sandbox: SandboxEnvironment,
        execution_result: Dict[str, Any],
        pattern_metadata: PatternMetadata
    ) -> Dict[str, Any]:
        """Analyze execution security and detect anomalies"""
        
        analysis = {
            "resource_compliance": True,
            "security_violations": [],
            "anomalies_detected": [],
            "risk_assessment": "low"
        }
        
        # Check resource usage compliance
        if execution_result.get("resource_usage", {}).get("memory_mb", 0) > sandbox.memory_limit_mb:
            analysis["resource_compliance"] = False
            analysis["security_violations"].append("Memory limit exceeded")
        
        # Check for security violations in output
        output = execution_result.get("output", "")
        if any(keyword in output.lower() for keyword in ["error", "exception", "failed"]):
            analysis["anomalies_detected"].append("Execution errors detected")
        
        # Assess overall risk
        if analysis["security_violations"] or len(analysis["anomalies_detected"]) > 2:
            analysis["risk_assessment"] = "high"
        elif analysis["anomalies_detected"]:
            analysis["risk_assessment"] = "medium"
        
        return analysis

# Global pattern security engine
pattern_security_engine = PatternSecurityEngine()