# ABOUTME: Data protection service with field-level encryption and retention policies
# ABOUTME: Enterprise-grade data protection with automatic PII detection and compliance

from typing import Dict, List, Optional, Any, Union, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import re
import hashlib
import base64
import secrets
import structlog
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from core.security_framework import DataSensitivity, SensitivityClassification, ComplianceFramework
from models.auth import CurrentUser

logger = structlog.get_logger(__name__)

class EncryptionMethod(Enum):
    NONE = "none"
    AES_256_GCM = "aes_256_gcm"
    FERNET = "fernet"
    FIELD_LEVEL = "field_level"

class RetentionStatus(Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    MARKED_FOR_DELETION = "marked_for_deletion"
    DELETED = "deleted"
    ARCHIVED = "archived"

class PIIType(Enum):
    EMAIL = "email"
    PHONE = "phone"
    SSN = "ssn"
    CREDIT_CARD = "credit_card"
    IP_ADDRESS = "ip_address"
    NAME = "name"
    ADDRESS = "address"
    DATE_OF_BIRTH = "date_of_birth"
    PASSPORT = "passport"
    DRIVER_LICENSE = "driver_license"

@dataclass
class EncryptionKey:
    """Encryption key metadata"""
    id: UUID = field(default_factory=uuid4)
    algorithm: EncryptionMethod = EncryptionMethod.FERNET
    key_data: str = ""  # Base64 encoded key
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    rotation_schedule_days: int = 90
    usage_count: int = 0
    max_usage: Optional[int] = None
    
    def is_expired(self) -> bool:
        """Check if key is expired"""
        if self.expires_at and self.expires_at < datetime.utcnow():
            return True
        if self.max_usage and self.usage_count >= self.max_usage:
            return True
        return False
    
    def should_rotate(self) -> bool:
        """Check if key should be rotated"""
        rotation_date = self.created_at + timedelta(days=self.rotation_schedule_days)
        return datetime.utcnow() >= rotation_date

@dataclass
class EncryptedData:
    """Encrypted data container"""
    id: UUID = field(default_factory=uuid4)
    encrypted_content: str = ""
    encryption_method: EncryptionMethod = EncryptionMethod.FERNET
    key_id: UUID = UUID('00000000-0000-0000-0000-000000000000')
    iv: Optional[str] = None  # Initialization vector for some algorithms
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "encrypted_content": self.encrypted_content,
            "encryption_method": self.encryption_method.value,
            "key_id": str(self.key_id),
            "iv": self.iv,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }

@dataclass
class PIIDetectionResult:
    """Result of PII detection scan"""
    pii_found: Dict[PIIType, List[str]] = field(default_factory=dict)
    confidence_scores: Dict[PIIType, float] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    requires_encryption: bool = False
    sensitivity_level: DataSensitivity = DataSensitivity.PUBLIC
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "pii_found": {k.value: v for k, v in self.pii_found.items()},
            "confidence_scores": {k.value: v for k, v in self.confidence_scores.items()},
            "recommendations": self.recommendations,
            "requires_encryption": self.requires_encryption,
            "sensitivity_level": self.sensitivity_level.value
        }

@dataclass
class RetentionPolicy:
    """Data retention policy definition"""
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: str = ""
    data_classification: DataSensitivity = DataSensitivity.INTERNAL
    retention_period_days: int = 2555  # 7 years default
    compliance_frameworks: List[ComplianceFramework] = field(default_factory=list)
    auto_delete: bool = True
    archive_before_delete: bool = True
    notify_before_deletion_days: int = 30
    
    # Conditions for policy application
    data_types: List[str] = field(default_factory=list)
    project_scope: Optional[str] = None
    user_scope: Optional[str] = None
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[UUID] = None
    active: bool = True

@dataclass
class DataRecord:
    """Data record with protection metadata"""
    id: UUID = field(default_factory=uuid4)
    data_type: str = ""
    content: Union[str, Dict[str, Any], EncryptedData] = ""
    classification: SensitivityClassification = field(default_factory=lambda: SensitivityClassification(DataSensitivity.PUBLIC))
    
    # Retention management
    retention_policy_id: Optional[UUID] = None
    retention_status: RetentionStatus = RetentionStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    deletion_scheduled_at: Optional[datetime] = None
    
    # Access control
    owner_id: Optional[UUID] = None
    access_log: List[Dict[str, Any]] = field(default_factory=list)
    
    # PII and encryption
    contains_pii: bool = False
    pii_types: List[PIIType] = field(default_factory=list)
    encrypted: bool = False
    encryption_key_id: Optional[UUID] = None
    
    def add_access_event(self, user_id: UUID, action: str, context: Dict[str, Any]):
        """Add access event to audit log"""
        self.access_log.append({
            "user_id": str(user_id),
            "action": action,
            "context": context,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Keep last 100 access events
        if len(self.access_log) > 100:
            self.access_log = self.access_log[-100:]

class PIIDetectionEngine:
    """Engine for automatic PII detection and classification"""
    
    # Enhanced PII patterns with higher accuracy
    PII_PATTERNS = {
        PIIType.EMAIL: re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        ),
        PIIType.PHONE: re.compile(
            r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b'
        ),
        PIIType.SSN: re.compile(
            r'\b\d{3}[-.]?\d{2}[-.]?\d{4}\b'
        ),
        PIIType.CREDIT_CARD: re.compile(
            r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3[0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b'
        ),
        PIIType.IP_ADDRESS: re.compile(
            r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
        ),
        PIIType.DATE_OF_BIRTH: re.compile(
            r'\b(?:0?[1-9]|1[0-2])[/-](?:0?[1-9]|[12][0-9]|3[01])[/-](?:19|20)\d{2}\b'
        ),
        PIIType.PASSPORT: re.compile(
            r'\b[A-Z]{1,2}[0-9]{6,9}\b'
        )
    }
    
    # Name detection patterns (simplified)
    NAME_PATTERNS = [
        re.compile(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b'),  # First Last
        re.compile(r'\b[A-Z][a-z]+, [A-Z][a-z]+\b'),  # Last, First
    ]
    
    # Address patterns (simplified)
    ADDRESS_PATTERNS = [
        re.compile(r'\b\d+\s+[A-Za-z\s]+(Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd)\b', re.IGNORECASE),
        re.compile(r'\b[A-Z]{2}\s+\d{5}(?:-\d{4})?\b'),  # State ZIP
    ]
    
    async def detect_pii(self, data: Any, context: Optional[Dict[str, Any]] = None) -> PIIDetectionResult:
        """Detect PII in data with confidence scoring"""
        
        result = PIIDetectionResult()
        
        # Convert data to string for analysis
        if isinstance(data, dict):
            data_str = json.dumps(data, default=str)
        else:
            data_str = str(data)
        
        # Scan for each PII type
        for pii_type, pattern in self.PII_PATTERNS.items():
            matches = pattern.findall(data_str)
            if matches:
                result.pii_found[pii_type] = matches
                # Calculate confidence based on pattern strength and context
                confidence = self._calculate_confidence(pii_type, matches, context)
                result.confidence_scores[pii_type] = confidence
        
        # Scan for names using multiple patterns
        name_matches = []
        for pattern in self.NAME_PATTERNS:
            name_matches.extend(pattern.findall(data_str))
        
        if name_matches:
            result.pii_found[PIIType.NAME] = name_matches
            result.confidence_scores[PIIType.NAME] = 0.7  # Names are harder to verify
        
        # Scan for addresses
        address_matches = []
        for pattern in self.ADDRESS_PATTERNS:
            address_matches.extend(pattern.findall(data_str))
        
        if address_matches:
            result.pii_found[PIIType.ADDRESS] = address_matches
            result.confidence_scores[PIIType.ADDRESS] = 0.8
        
        # Determine if encryption is required
        high_confidence_pii = [
            pii_type for pii_type, confidence in result.confidence_scores.items()
            if confidence >= 0.8
        ]
        
        if high_confidence_pii:
            result.requires_encryption = True
            
            # Determine sensitivity level based on PII types found
            if PIIType.SSN in high_confidence_pii or PIIType.CREDIT_CARD in high_confidence_pii:
                result.sensitivity_level = DataSensitivity.REGULATED
            elif PIIType.EMAIL in high_confidence_pii or PIIType.PHONE in high_confidence_pii:
                result.sensitivity_level = DataSensitivity.CONFIDENTIAL
            else:
                result.sensitivity_level = DataSensitivity.INTERNAL
        
        # Generate recommendations
        if result.requires_encryption:
            result.recommendations.extend([
                "Encrypt data due to PII content",
                "Apply appropriate retention policy",
                "Enable access logging"
            ])
        
        if PIIType.SSN in high_confidence_pii or PIIType.CREDIT_CARD in high_confidence_pii:
            result.recommendations.extend([
                "Apply highest security classification",
                "Implement field-level encryption",
                "Enable compliance monitoring"
            ])
        
        logger.debug("PII detection completed",
                    pii_types=len(result.pii_found),
                    requires_encryption=result.requires_encryption,
                    sensitivity_level=result.sensitivity_level.value)
        
        return result
    
    def _calculate_confidence(
        self,
        pii_type: PIIType,
        matches: List[str],
        context: Optional[Dict[str, Any]]
    ) -> float:
        """Calculate confidence score for PII detection"""
        
        base_confidence = {
            PIIType.EMAIL: 0.95,
            PIIType.SSN: 0.90,
            PIIType.CREDIT_CARD: 0.85,
            PIIType.PHONE: 0.80,
            PIIType.IP_ADDRESS: 0.70,  # Could be legitimate system data
            PIIType.DATE_OF_BIRTH: 0.75,
            PIIType.PASSPORT: 0.85
        }
        
        confidence = base_confidence.get(pii_type, 0.5)
        
        # Adjust based on context
        if context:
            # Higher confidence in user-provided data
            if context.get("source") == "user_input":
                confidence += 0.1
            
            # Lower confidence in system logs
            if context.get("source") == "system_log":
                confidence -= 0.2
        
        # Adjust based on number of matches
        if len(matches) > 1:
            confidence += 0.05  # Multiple matches increase confidence
        
        return min(1.0, max(0.0, confidence))

class EncryptionEngine:
    """Engine for data encryption and key management"""
    
    def __init__(self):
        self.encryption_keys: Dict[UUID, EncryptionKey] = {}
        self.master_key = self._generate_master_key()
    
    def _generate_master_key(self) -> bytes:
        """Generate master key for key encryption (would use Vault in production)"""
        return Fernet.generate_key()
    
    async def generate_encryption_key(
        self,
        algorithm: EncryptionMethod = EncryptionMethod.FERNET,
        rotation_days: int = 90
    ) -> EncryptionKey:
        """Generate new encryption key"""
        
        if algorithm == EncryptionMethod.FERNET:
            key_data = base64.urlsafe_b64encode(Fernet.generate_key()).decode()
        else:
            # For other algorithms, generate appropriate key
            key_data = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()
        
        encryption_key = EncryptionKey(
            algorithm=algorithm,
            key_data=key_data,
            rotation_schedule_days=rotation_days,
            expires_at=datetime.utcnow() + timedelta(days=rotation_days * 2)  # Grace period
        )
        
        self.encryption_keys[encryption_key.id] = encryption_key
        
        logger.info("Encryption key generated",
                   key_id=str(encryption_key.id),
                   algorithm=algorithm.value)
        
        return encryption_key
    
    async def encrypt_data(
        self,
        data: Any,
        classification: SensitivityClassification,
        key_id: Optional[UUID] = None
    ) -> EncryptedData:
        """Encrypt data based on classification requirements"""
        
        if not classification.encryption_required:
            # Return data as-is if encryption not required
            return EncryptedData(
                encrypted_content=json.dumps(data, default=str),
                encryption_method=EncryptionMethod.NONE
            )
        
        # Get or generate encryption key
        if key_id and key_id in self.encryption_keys:
            encryption_key = self.encryption_keys[key_id]
        else:
            encryption_key = await self.generate_encryption_key()
        
        # Convert data to JSON string
        data_str = json.dumps(data, default=str, sort_keys=True)
        
        # Encrypt based on classification level
        if classification.level in [DataSensitivity.SECRET, DataSensitivity.REGULATED]:
            encrypted_content = await self._encrypt_with_fernet(data_str, encryption_key)
        else:
            encrypted_content = await self._encrypt_with_fernet(data_str, encryption_key)
        
        encrypted_data = EncryptedData(
            encrypted_content=encrypted_content,
            encryption_method=EncryptionMethod.FERNET,
            key_id=encryption_key.id,
            metadata={
                "original_type": type(data).__name__,
                "classification": classification.level.value,
                "encryption_timestamp": datetime.utcnow().isoformat()
            }
        )
        
        # Update key usage
        encryption_key.usage_count += 1
        
        logger.debug("Data encrypted",
                    key_id=str(encryption_key.id),
                    data_size=len(data_str),
                    classification=classification.level.value)
        
        return encrypted_data
    
    async def decrypt_data(
        self,
        encrypted_data: EncryptedData,
        user: CurrentUser,
        audit_context: Dict[str, Any]
    ) -> Any:
        """Decrypt data with access control and auditing"""
        
        if encrypted_data.encryption_method == EncryptionMethod.NONE:
            return json.loads(encrypted_data.encrypted_content)
        
        # Check if user has permission to decrypt
        required_classification = encrypted_data.metadata.get("classification", "internal")
        required_permission = f"data:{required_classification}"
        
        if not user.has_permission(required_permission):
            raise PermissionError(f"Insufficient permissions to decrypt {required_classification} data")
        
        # Get encryption key
        key_id = encrypted_data.key_id
        if key_id not in self.encryption_keys:
            raise ValueError(f"Encryption key {key_id} not found")
        
        encryption_key = self.encryption_keys[key_id]
        if encryption_key.is_expired():
            raise ValueError(f"Encryption key {key_id} has expired")
        
        # Decrypt data
        if encrypted_data.encryption_method == EncryptionMethod.FERNET:
            decrypted_str = await self._decrypt_with_fernet(
                encrypted_data.encrypted_content, 
                encryption_key
            )
        else:
            raise ValueError(f"Unsupported encryption method: {encrypted_data.encryption_method}")
        
        # Parse decrypted data
        decrypted_data = json.loads(decrypted_str)
        
        logger.info("Data decrypted",
                   key_id=str(key_id),
                   user_id=str(user.user_id),
                   data_id=str(encrypted_data.id))
        
        return decrypted_data
    
    async def _encrypt_with_fernet(self, data: str, key: EncryptionKey) -> str:
        """Encrypt data using Fernet (AES 128 in CBC mode)"""
        key_bytes = base64.urlsafe_b64decode(key.key_data)
        fernet = Fernet(key_bytes)
        encrypted = fernet.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    async def _decrypt_with_fernet(self, encrypted_data: str, key: EncryptionKey) -> str:
        """Decrypt data using Fernet"""
        key_bytes = base64.urlsafe_b64decode(key.key_data)
        fernet = Fernet(key_bytes)
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
        decrypted = fernet.decrypt(encrypted_bytes)
        return decrypted.decode()
    
    async def rotate_encryption_keys(self) -> List[UUID]:
        """Rotate encryption keys that are due for rotation"""
        rotated_keys = []
        
        for key_id, key in list(self.encryption_keys.items()):
            if key.should_rotate():
                # Generate new key
                new_key = await self.generate_encryption_key(
                    key.algorithm,
                    key.rotation_schedule_days
                )
                
                # Mark old key for rotation (would re-encrypt data in production)
                key.expires_at = datetime.utcnow() + timedelta(days=30)  # Grace period
                
                rotated_keys.append(key_id)
                
                logger.info("Encryption key rotated",
                           old_key_id=str(key_id),
                           new_key_id=str(new_key.id))
        
        return rotated_keys

class RetentionEngine:
    """Engine for data retention policy management"""
    
    def __init__(self):
        self.retention_policies: Dict[UUID, RetentionPolicy] = {}
        self.default_policies = self._create_default_policies()
    
    def _create_default_policies(self) -> Dict[DataSensitivity, RetentionPolicy]:
        """Create default retention policies for each data sensitivity level"""
        return {
            DataSensitivity.PUBLIC: RetentionPolicy(
                name="Public Data Retention",
                data_classification=DataSensitivity.PUBLIC,
                retention_period_days=3650,  # 10 years
                auto_delete=False  # Manual review for public data
            ),
            DataSensitivity.INTERNAL: RetentionPolicy(
                name="Internal Data Retention", 
                data_classification=DataSensitivity.INTERNAL,
                retention_period_days=2555,  # 7 years
                auto_delete=True
            ),
            DataSensitivity.CONFIDENTIAL: RetentionPolicy(
                name="Confidential Data Retention",
                data_classification=DataSensitivity.CONFIDENTIAL,
                retention_period_days=1825,  # 5 years
                auto_delete=True,
                archive_before_delete=True
            ),
            DataSensitivity.SECRET: RetentionPolicy(
                name="Secret Data Retention",
                data_classification=DataSensitivity.SECRET,
                retention_period_days=1095,  # 3 years
                auto_delete=True,
                archive_before_delete=True,
                notify_before_deletion_days=60
            ),
            DataSensitivity.REGULATED: RetentionPolicy(
                name="Regulated Data Retention",
                data_classification=DataSensitivity.REGULATED,
                retention_period_days=2555,  # 7 years (common for financial/medical)
                auto_delete=False,  # Manual review required
                archive_before_delete=True,
                notify_before_deletion_days=90,
                compliance_frameworks=[
                    ComplianceFramework.GDPR,
                    ComplianceFramework.HIPAA,
                    ComplianceFramework.PCI_DSS
                ]
            )
        }
    
    async def apply_retention_policy(
        self,
        data_record: DataRecord,
        policy_id: Optional[UUID] = None
    ) -> RetentionPolicy:
        """Apply retention policy to data record"""
        
        if policy_id and policy_id in self.retention_policies:
            policy = self.retention_policies[policy_id]
        else:
            # Use default policy for data classification
            policy = self.default_policies.get(
                data_record.classification.level,
                self.default_policies[DataSensitivity.INTERNAL]
            )
        
        # Set retention metadata on data record
        data_record.retention_policy_id = policy.id
        data_record.expires_at = datetime.utcnow() + timedelta(days=policy.retention_period_days)
        
        if policy.auto_delete:
            notification_date = data_record.expires_at - timedelta(days=policy.notify_before_deletion_days)
            if notification_date > datetime.utcnow():
                data_record.deletion_scheduled_at = notification_date
        
        logger.info("Retention policy applied",
                   data_record_id=str(data_record.id),
                   policy_id=str(policy.id),
                   expires_at=data_record.expires_at.isoformat())
        
        return policy
    
    async def process_expired_data(self) -> Dict[str, List[UUID]]:
        """Process data that has reached retention expiry"""
        # This would scan database for expired records in production
        # For now, return structure showing what would be processed
        
        return {
            "marked_for_deletion": [],
            "archived": [],
            "deleted": [],
            "notifications_sent": []
        }

class DataProtectionService:
    """Main data protection service orchestrating all protection mechanisms"""
    
    def __init__(self):
        self.pii_detector = PIIDetectionEngine()
        self.encryption_engine = EncryptionEngine()
        self.retention_engine = RetentionEngine()
        self.protected_records: Dict[UUID, DataRecord] = {}
    
    async def classify_and_encrypt(
        self,
        data: Any,
        context: Optional[Dict[str, Any]] = None,
        user: Optional[CurrentUser] = None
    ) -> DataRecord:
        """Classify data sensitivity and encrypt if required"""
        
        # Detect PII in data
        pii_detection = await self.pii_detector.detect_pii(data, context)
        
        # Create sensitivity classification
        classification = SensitivityClassification(
            level=pii_detection.sensitivity_level,
            encryption_required=pii_detection.requires_encryption,
            audit_required=pii_detection.sensitivity_level in [DataSensitivity.SECRET, DataSensitivity.REGULATED],
            retention_days=self._get_retention_days(pii_detection.sensitivity_level)
        )
        
        # Encrypt data if required
        if classification.encryption_required:
            encrypted_data = await self.encryption_engine.encrypt_data(data, classification)
            content = encrypted_data
            encrypted = True
        else:
            content = data
            encrypted = False
        
        # Create data record
        data_record = DataRecord(
            content=content,
            classification=classification,
            contains_pii=bool(pii_detection.pii_found),
            pii_types=list(pii_detection.pii_found.keys()),
            encrypted=encrypted,
            encryption_key_id=content.key_id if encrypted else None,
            owner_id=user.user_id if user else None
        )
        
        # Apply retention policy
        await self.retention_engine.apply_retention_policy(data_record)
        
        # Store record
        self.protected_records[data_record.id] = data_record
        
        logger.info("Data classified and protected",
                   record_id=str(data_record.id),
                   classification=classification.level.value,
                   encrypted=encrypted,
                   contains_pii=data_record.contains_pii)
        
        return data_record
    
    async def decrypt_with_permissions(
        self,
        record_id: UUID,
        user: CurrentUser,
        access_reason: str = "data_access"
    ) -> Any:
        """Decrypt data with permission validation and audit logging"""
        
        if record_id not in self.protected_records:
            raise ValueError(f"Data record {record_id} not found")
        
        data_record = self.protected_records[record_id]
        
        # Check permissions based on data classification
        required_permission = f"data:{data_record.classification.level.value}"
        if not user.has_permission(required_permission):
            raise PermissionError(f"Insufficient permissions to access {data_record.classification.level.value} data")
        
        # Log access event
        audit_context = {
            "access_reason": access_reason,
            "client_info": "betty_system",
            "classification": data_record.classification.level.value
        }
        
        data_record.add_access_event(user.user_id, "decrypt", audit_context)
        
        # Decrypt if needed
        if data_record.encrypted and isinstance(data_record.content, EncryptedData):
            decrypted_data = await self.encryption_engine.decrypt_data(
                data_record.content,
                user,
                audit_context
            )
        else:
            decrypted_data = data_record.content
        
        logger.info("Data decrypted with permissions",
                   record_id=str(record_id),
                   user_id=str(user.user_id),
                   classification=data_record.classification.level.value)
        
        return decrypted_data
    
    async def apply_retention_policy(
        self,
        record_id: UUID,
        policy_id: Optional[UUID] = None
    ) -> bool:
        """Apply retention policy to specific data record"""
        
        if record_id not in self.protected_records:
            return False
        
        data_record = self.protected_records[record_id]
        await self.retention_engine.apply_retention_policy(data_record, policy_id)
        
        return True
    
    async def audit_data_access(
        self,
        record_id: UUID,
        user: CurrentUser,
        action: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create audit record for data access"""
        
        if record_id not in self.protected_records:
            return {"error": "Record not found"}
        
        data_record = self.protected_records[record_id]
        
        audit_record = {
            "audit_id": str(uuid4()),
            "record_id": str(record_id),
            "user_id": str(user.user_id),
            "action": action,
            "context": context,
            "data_classification": data_record.classification.level.value,
            "contains_pii": data_record.contains_pii,
            "pii_types": [pii_type.value for pii_type in data_record.pii_types],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        data_record.add_access_event(user.user_id, action, context)
        
        logger.info("Data access audited",
                   audit_id=audit_record["audit_id"],
                   record_id=str(record_id),
                   action=action)
        
        return audit_record
    
    async def get_protection_metrics(self) -> Dict[str, Any]:
        """Get data protection metrics"""
        
        total_records = len(self.protected_records)
        encrypted_records = len([r for r in self.protected_records.values() if r.encrypted])
        pii_records = len([r for r in self.protected_records.values() if r.contains_pii])
        
        classification_counts = {}
        for record in self.protected_records.values():
            level = record.classification.level.value
            classification_counts[level] = classification_counts.get(level, 0) + 1
        
        return {
            "total_protected_records": total_records,
            "encrypted_records": encrypted_records,
            "pii_records": pii_records,
            "classification_distribution": classification_counts,
            "encryption_keys": len(self.encryption_engine.encryption_keys),
            "retention_policies": len(self.retention_engine.retention_policies),
            "last_updated": datetime.utcnow().isoformat()
        }
    
    def _get_retention_days(self, sensitivity: DataSensitivity) -> int:
        """Get default retention days for sensitivity level"""
        retention_map = {
            DataSensitivity.PUBLIC: 3650,    # 10 years
            DataSensitivity.INTERNAL: 2555,  # 7 years  
            DataSensitivity.CONFIDENTIAL: 1825,  # 5 years
            DataSensitivity.SECRET: 1095,    # 3 years
            DataSensitivity.REGULATED: 2555  # 7 years
        }
        return retention_map.get(sensitivity, 2555)

# Global data protection service
data_protection_service = DataProtectionService()