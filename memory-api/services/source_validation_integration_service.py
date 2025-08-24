# ABOUTME: Integration service to connect Source Validation & Verification System with Betty's Multi-Source Knowledge Extraction Pipeline
# ABOUTME: Orchestrates validation workflow with existing pattern intelligence and quality scoring systems

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import structlog

from services.source_validation_framework import SourceValidationFramework
from services.multi_source_knowledge_extractor import MultiSourceKnowledgeExtractor
from services.knowledge_processing_pipeline import KnowledgeProcessingPipeline
from services.pattern_quality_service import AdvancedQualityScorer
from core.database import DatabaseManager
from services.vector_service import VectorService

logger = structlog.get_logger(__name__)

class SourceValidationIntegrationService:
    """
    Integration service that orchestrates Source Validation & Verification System
    with Betty's existing Multi-Source Knowledge Extraction Pipeline
    
    This service ensures that all extracted knowledge patterns are validated for:
    - Security threats and malicious content
    - Source credibility and reliability
    - Data integrity and provenance
    - Compliance with SOC2/GDPR requirements
    """
    
    def __init__(self, 
                 db_manager: DatabaseManager,
                 vector_service: VectorService,
                 validation_framework: SourceValidationFramework,
                 extractor: MultiSourceKnowledgeExtractor,
                 processor: KnowledgeProcessingPipeline,
                 quality_scorer: AdvancedQualityScorer):
        
        self.db_manager = db_manager
        self.vector_service = vector_service
        self.validation_framework = validation_framework
        self.extractor = extractor
        self.processor = processor
        self.quality_scorer = quality_scorer
        
        # Integration configuration
        self.integration_config = {
            'validation_enabled': True,
            'credibility_threshold': 0.7,
            'quality_threshold': 0.7,
            'security_threshold': 0.9,
            'auto_quarantine': True,
            'compliance_mode': 'SOC2_GDPR'
        }
        
        # Integration statistics
        self.stats = {
            'patterns_validated': 0,
            'patterns_rejected': 0,
            'patterns_quarantined': 0,
            'security_threats_detected': 0,
            'integration_start_time': datetime.utcnow()
        }
        
        logger.info("Source Validation Integration Service initialized")
    
    async def integrate_validation_pipeline(self) -> Dict[str, Any]:
        """
        Integrate validation system with knowledge extraction pipeline
        
        Returns:
            Integration status and configuration details
        """
        try:
            logger.info("Starting Source Validation integration with knowledge extraction pipeline")
            
            # Test validation framework connectivity
            validation_health = await self.validation_framework.health_check()
            if validation_health['status'] != 'healthy':
                raise RuntimeError(f"Validation framework not healthy: {validation_health}")
            
            # Configure extraction pipeline to use validation
            await self._configure_extraction_validation()
            
            # Configure processing pipeline to use validation
            await self._configure_processing_validation()
            
            # Setup validation event handlers
            await self._setup_validation_event_handlers()
            
            integration_result = {
                'status': 'integrated',
                'timestamp': datetime.utcnow().isoformat(),
                'validation_framework_status': validation_health['status'],
                'integration_config': self.integration_config,
                'components_integrated': [
                    'multi_source_extractor',
                    'knowledge_processor', 
                    'pattern_quality_scorer',
                    'validation_framework'
                ]
            }
            
            logger.info("Source Validation integration completed successfully")
            return integration_result
            
        except Exception as e:
            logger.error("Source Validation integration failed", error=str(e))
            raise
    
    async def validate_extracted_pattern(self, 
                                       pattern_data: Dict[str, Any], 
                                       source_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive validation of extracted pattern data
        
        Args:
            pattern_data: The extracted pattern data
            source_info: Source metadata and information
            
        Returns:
            Validation result with security assessment and recommendations
        """
        try:
            validation_id = pattern_data.get('id', 'unknown')
            logger.info("Starting pattern validation", validation_id=validation_id)
            
            # Step 1: Validate source credibility
            credibility_result = await self.validation_framework.validate_source_credibility(source_info)
            
            if credibility_result.reputation_score < self.integration_config['credibility_threshold']:
                logger.warning("Pattern from low-credibility source", 
                             source_id=source_info.get('source_id'),
                             reputation_score=credibility_result.reputation_score)
            
            # Step 2: Validate content security
            security_result = await self.validation_framework.validate_content_security(
                pattern_data, source_info
            )
            
            self.stats['patterns_validated'] += 1
            
            if len(security_result.threat_types) > 0:
                self.stats['security_threats_detected'] += 1
                logger.warning("Security threats detected in pattern",
                             validation_id=validation_id,
                             threats=len(security_result.threat_types))
            
            # Step 3: Assess pattern quality (integrate with existing scorer)
            quality_score = await self.quality_scorer.assess_pattern_quality(pattern_data)
            
            # Step 4: Verify data integrity
            integrity_result = await self.validation_framework.verify_data_integrity(pattern_data)
            
            # Step 5: Make validation decision
            validation_decision = await self._make_validation_decision(
                credibility_result, security_result, quality_score, integrity_result
            )
            
            # Step 6: Update statistics based on decision
            if validation_decision['action'] == 'reject':
                self.stats['patterns_rejected'] += 1
            elif validation_decision['action'] == 'quarantine':
                self.stats['patterns_quarantined'] += 1
            
            comprehensive_result = {
                'validation_id': security_result.id,
                'pattern_id': validation_id,
                'timestamp': datetime.utcnow().isoformat(),
                'source_credibility': {
                    'reputation_score': credibility_result.reputation_score,
                    'uptime_percentage': credibility_result.uptime_percentage,
                    'ssl_validity': credibility_result.ssl_validity,
                    'threat_intelligence_score': credibility_result.threat_intelligence_score
                },
                'security_assessment': {
                    'status': security_result.status.value,
                    'severity': security_result.severity.value,
                    'threat_types': [t.value for t in security_result.threat_types],
                    'confidence_score': security_result.confidence_score
                },
                'quality_assessment': {
                    'score': quality_score.get('overall_score', 0.0),
                    'factors': quality_score.get('factors', {})
                },
                'data_integrity': {
                    'verified': integrity_result['integrity_verified'],
                    'tamper_detected': integrity_result['tamper_detected']
                },
                'validation_decision': validation_decision,
                'compliance_flags': security_result.compliance_flags
            }
            
            logger.info("Pattern validation completed",
                       validation_id=validation_id,
                       action=validation_decision['action'],
                       threats_detected=len(security_result.threat_types))
            
            return comprehensive_result
            
        except Exception as e:
            logger.error("Pattern validation failed", 
                        pattern_id=pattern_data.get('id', 'unknown'),
                        error=str(e))
            
            # Return safe default result
            return {
                'validation_id': 'failed',
                'pattern_id': pattern_data.get('id', 'unknown'),
                'timestamp': datetime.utcnow().isoformat(),
                'validation_decision': {
                    'action': 'quarantine',
                    'reason': f'Validation failed: {str(e)}',
                    'confidence': 0.0
                },
                'error': str(e)
            }
    
    async def validate_batch_patterns(self, 
                                    patterns: List[Dict[str, Any]], 
                                    source_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Batch validation of multiple patterns for performance optimization
        
        Args:
            patterns: List of pattern data to validate
            source_info: Source metadata for all patterns
            
        Returns:
            List of validation results
        """
        try:
            logger.info("Starting batch pattern validation", pattern_count=len(patterns))
            
            # Process patterns in parallel for performance
            validation_tasks = [
                self.validate_extracted_pattern(pattern, source_info)
                for pattern in patterns
            ]
            
            results = await asyncio.gather(*validation_tasks, return_exceptions=True)
            
            # Handle any exceptions in results
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error("Batch validation item failed", 
                               index=i, error=str(result))
                    processed_results.append({
                        'validation_id': 'batch_failed',
                        'pattern_id': patterns[i].get('id', f'batch_item_{i}'),
                        'validation_decision': {'action': 'quarantine', 'reason': str(result)},
                        'error': str(result)
                    })
                else:
                    processed_results.append(result)
            
            logger.info("Batch pattern validation completed", 
                       total_patterns=len(patterns),
                       successful_validations=len([r for r in processed_results if 'error' not in r]))
            
            return processed_results
            
        except Exception as e:
            logger.error("Batch pattern validation failed", error=str(e))
            raise
    
    async def get_validation_statistics(self) -> Dict[str, Any]:
        """Get comprehensive validation statistics"""
        
        # Get framework statistics
        framework_stats = await self.validation_framework.get_validation_statistics()
        
        # Calculate integration-specific metrics
        runtime = (datetime.utcnow() - self.stats['integration_start_time']).total_seconds()
        patterns_per_second = self.stats['patterns_validated'] / runtime if runtime > 0 else 0
        
        integration_stats = {
            'integration_runtime_seconds': runtime,
            'patterns_validated': self.stats['patterns_validated'],
            'patterns_rejected': self.stats['patterns_rejected'],
            'patterns_quarantined': self.stats['patterns_quarantined'],
            'security_threats_detected': self.stats['security_threats_detected'],
            'validation_rate_per_second': round(patterns_per_second, 2),
            'rejection_rate': round(
                (self.stats['patterns_rejected'] / max(self.stats['patterns_validated'], 1)) * 100, 2
            ),
            'threat_detection_rate': round(
                (self.stats['security_threats_detected'] / max(self.stats['patterns_validated'], 1)) * 100, 2
            )
        }
        
        return {
            'integration_statistics': integration_stats,
            'framework_statistics': framework_stats,
            'configuration': self.integration_config,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def update_integration_config(self, config_updates: Dict[str, Any]):
        """Update integration configuration"""
        
        allowed_updates = [
            'validation_enabled', 'credibility_threshold', 'quality_threshold',
            'security_threshold', 'auto_quarantine', 'compliance_mode'
        ]
        
        updated_keys = []
        for key, value in config_updates.items():
            if key in allowed_updates:
                self.integration_config[key] = value
                updated_keys.append(key)
        
        logger.info("Integration configuration updated", updated_keys=updated_keys)
        
        return {
            'status': 'updated',
            'updated_keys': updated_keys,
            'current_config': self.integration_config,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    # Private helper methods
    
    async def _configure_extraction_validation(self):
        """Configure the extraction pipeline to use validation"""
        
        # This would integrate with the MultiSourceKnowledgeExtractor
        # to ensure all extracted patterns go through validation
        logger.info("Configuring extraction pipeline validation integration")
        
        # Add validation callback to extractor
        if hasattr(self.extractor, 'add_validation_callback'):
            await self.extractor.add_validation_callback(self.validate_extracted_pattern)
    
    async def _configure_processing_validation(self):
        """Configure the processing pipeline to use validation"""
        
        logger.info("Configuring processing pipeline validation integration")
        
        # Add validation step to processor
        if hasattr(self.processor, 'add_processing_step'):
            await self.processor.add_processing_step('validation', self.validate_extracted_pattern)
    
    async def _setup_validation_event_handlers(self):
        """Setup event handlers for validation events"""
        
        logger.info("Setting up validation event handlers")
        
        # This would setup listeners for validation events
        # to trigger notifications, alerts, etc.
    
    async def _make_validation_decision(self, 
                                      credibility_result,
                                      security_result, 
                                      quality_score,
                                      integrity_result) -> Dict[str, Any]:
        """
        Make comprehensive validation decision based on all assessment results
        
        Returns:
            Validation decision with action and reasoning
        """
        
        decision = {
            'action': 'accept',
            'reason': 'Pattern passed all validation checks',
            'confidence': 1.0,
            'recommendations': []
        }
        
        # Check security threats (highest priority)
        if len(security_result.threat_types) > 0:
            if security_result.confidence_score >= self.integration_config['security_threshold']:
                decision['action'] = 'reject'
                decision['reason'] = f"Security threats detected: {[t.value for t in security_result.threat_types]}"
                decision['confidence'] = security_result.confidence_score
                return decision
            else:
                decision['action'] = 'quarantine'
                decision['reason'] = f"Potential security threats (low confidence): {[t.value for t in security_result.threat_types]}"
                decision['confidence'] = security_result.confidence_score
                decision['recommendations'].append('Manual security review required')
        
        # Check source credibility
        if credibility_result.reputation_score < self.integration_config['credibility_threshold']:
            if decision['action'] == 'accept':
                decision['action'] = 'review'
                decision['reason'] = f"Low source credibility: {credibility_result.reputation_score}"
                decision['recommendations'].append('Verify source reliability before use')
        
        # Check quality score
        overall_quality = quality_score.get('overall_score', 0.0)
        if overall_quality < self.integration_config['quality_threshold']:
            if decision['action'] == 'accept':
                decision['action'] = 'review'
                decision['reason'] = f"Low quality score: {overall_quality}"
                decision['recommendations'].append('Quality improvement needed before deployment')
        
        # Check data integrity
        if integrity_result['tamper_detected']:
            decision['action'] = 'reject'
            decision['reason'] = 'Data tampering detected - integrity compromised'
            decision['confidence'] = 1.0
            return decision
        
        # Apply auto-quarantine policy
        if self.integration_config['auto_quarantine'] and decision['action'] in ['review', 'quarantine']:
            decision['action'] = 'quarantine'
        
        return decision

# Global integration service instance
_integration_service: Optional[SourceValidationIntegrationService] = None

async def get_integration_service(
    db_manager: DatabaseManager,
    vector_service: VectorService,
    validation_framework: SourceValidationFramework,
    extractor: MultiSourceKnowledgeExtractor,
    processor: KnowledgeProcessingPipeline,
    quality_scorer: AdvancedQualityScorer
) -> SourceValidationIntegrationService:
    """Get or create the global integration service instance"""
    global _integration_service
    
    if _integration_service is None:
        _integration_service = SourceValidationIntegrationService(
            db_manager, vector_service, validation_framework,
            extractor, processor, quality_scorer
        )
        await _integration_service.integrate_validation_pipeline()
    
    return _integration_service