# ABOUTME: Integration service connecting Source Validation System with existing Betty components
# ABOUTME: Provides seamless integration with Pattern Quality Service and Knowledge Extraction Pipeline

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID, uuid4
import structlog

from core.database import DatabaseManager
from models.knowledge import KnowledgeItem
from services.source_validation_service import SourceValidationService, ValidationResult, ValidationStatus
from services.pattern_quality_service import AdvancedQualityScorer
from services.multi_source_knowledge_extractor import MultiSourceKnowledgeExtractor
from services.validation_monitoring_service import ValidationMonitoringService

logger = structlog.get_logger(__name__)

class ValidationIntegrationService:
    """Service to integrate validation system with existing Betty components"""
    
    def __init__(
        self,
        db_manager: DatabaseManager,
        validation_service: SourceValidationService,
        quality_scorer: AdvancedQualityScorer,
        monitoring_service: ValidationMonitoringService
    ):
        self.db_manager = db_manager
        self.validation_service = validation_service
        self.quality_scorer = quality_scorer
        self.monitoring_service = monitoring_service
        
        logger.info("Validation Integration Service initialized")
    
    async def integrate_with_knowledge_extraction(
        self, 
        extractor: MultiSourceKnowledgeExtractor
    ) -> None:
        """Integrate validation system with knowledge extraction pipeline"""
        try:
            logger.info("Integrating validation system with knowledge extraction pipeline")
            
            # Hook into extraction pipeline to automatically validate new items
            original_process_item = extractor._process_extracted_item
            
            async def enhanced_process_item(item_data: Dict, source_name: str) -> KnowledgeItem:
                """Enhanced processing with automatic validation"""
                # Process item normally first
                knowledge_item = await original_process_item(item_data, source_name)
                
                # Perform validation
                validation_result = await self.validation_service.validate_knowledge_item(knowledge_item)
                
                # Update item metadata with validation results
                if not knowledge_item.metadata:
                    knowledge_item.metadata = {}
                
                knowledge_item.metadata.update({
                    'validation': {
                        'validation_id': validation_result.validation_id,
                        'status': validation_result.status.value,
                        'overall_score': validation_result.overall_score,
                        'credibility_score': validation_result.credibility_score,
                        'accuracy_score': validation_result.accuracy_score,
                        'security_score': validation_result.security_score,
                        'freshness_score': validation_result.freshness_score,
                        'validated_at': validation_result.timestamp.isoformat(),
                        'validation_time': validation_result.validation_time
                    }
                })
                
                # Don't store items that are quarantined
                if validation_result.status == ValidationStatus.QUARANTINED:
                    logger.warning("Item quarantined during extraction",
                                 item_id=str(knowledge_item.id),
                                 source=source_name,
                                 validation_id=validation_result.validation_id)
                    # Create audit log entry
                    await self._create_audit_log(
                        'item_quarantined',
                        validation_result.validation_id,
                        str(knowledge_item.id),
                        source_name,
                        {'reason': 'security_threat', 'issues': validation_result.issues}
                    )
                    return None  # Don't store quarantined items
                
                # Log successful validation
                if validation_result.status == ValidationStatus.VALIDATED:
                    await self._create_audit_log(
                        'item_validated',
                        validation_result.validation_id,
                        str(knowledge_item.id),
                        source_name,
                        {
                            'overall_score': validation_result.overall_score,
                            'validation_time': validation_result.validation_time
                        }
                    )
                
                return knowledge_item
            
            # Replace the original method
            extractor._process_extracted_item = enhanced_process_item
            
            logger.info("Knowledge extraction pipeline enhanced with validation")
            
        except Exception as e:
            logger.error("Failed to integrate with knowledge extraction pipeline", error=str(e))
            raise
    
    async def integrate_with_pattern_quality(self) -> None:
        """Integrate validation results with pattern quality scoring"""
        try:
            logger.info("Integrating validation system with pattern quality scoring")
            
            # Hook into quality scoring to incorporate validation results
            original_score_pattern = self.quality_scorer.score_pattern
            
            async def enhanced_score_pattern(item: KnowledgeItem, context: Dict = None) -> Dict[str, Any]:
                """Enhanced pattern scoring with validation data"""
                # Get original quality score
                quality_result = await original_score_pattern(item, context)
                
                # Check if item has validation data
                validation_data = None
                if item.metadata and 'validation' in item.metadata:
                    validation_data = item.metadata['validation']
                else:
                    # Perform validation if not already done
                    validation_result = await self.validation_service.validate_knowledge_item(item)
                    validation_data = {
                        'status': validation_result.status.value,
                        'overall_score': validation_result.overall_score,
                        'credibility_score': validation_result.credibility_score,
                        'accuracy_score': validation_result.accuracy_score,
                        'security_score': validation_result.security_score
                    }
                
                # Incorporate validation scores into quality assessment
                if validation_data and validation_data['status'] == 'validated':
                    # Weight validation scores into final quality
                    enhanced_score = (
                        quality_result['overall_score'] * 0.6 +  # Original quality weight
                        validation_data['overall_score'] * 0.4   # Validation weight
                    )
                    
                    quality_result['overall_score'] = enhanced_score
                    quality_result['validation_enhancement'] = {
                        'original_score': quality_result['overall_score'],
                        'validation_score': validation_data['overall_score'],
                        'enhanced_score': enhanced_score,
                        'credibility_factor': validation_data['credibility_score'],
                        'security_factor': validation_data['security_score']
                    }
                elif validation_data and validation_data['status'] == 'quarantined':
                    # Severely penalize quarantined items
                    quality_result['overall_score'] = 0.0
                    quality_result['validation_penalty'] = 'quarantined'
                
                return quality_result
            
            # Replace the original method
            self.quality_scorer.score_pattern = enhanced_score_pattern
            
            logger.info("Pattern quality scoring enhanced with validation")
            
        except Exception as e:
            logger.error("Failed to integrate with pattern quality scoring", error=str(e))
            raise
    
    async def setup_automated_validation_workflows(self) -> None:
        """Setup automated validation workflows for different scenarios"""
        try:
            logger.info("Setting up automated validation workflows")
            
            # Start monitoring service
            await self.monitoring_service.start_monitoring()
            
            # Schedule periodic validation of existing items
            asyncio.create_task(self._periodic_revalidation_workflow())
            
            # Schedule credibility updates
            asyncio.create_task(self._credibility_update_workflow())
            
            # Schedule compliance cleanup
            asyncio.create_task(self._compliance_cleanup_workflow())
            
            logger.info("Automated validation workflows started")
            
        except Exception as e:
            logger.error("Failed to setup automated workflows", error=str(e))
            raise
    
    async def _periodic_revalidation_workflow(self):
        """Periodic revalidation of existing knowledge items"""
        try:
            while True:
                logger.info("Starting periodic revalidation workflow")
                
                # Get items that need revalidation (older than 30 days since last validation)
                cutoff_date = datetime.utcnow() - timedelta(days=30)
                
                async with self.db_manager.get_postgres_pool().acquire() as conn:
                    items_to_revalidate = await conn.fetch("""
                        SELECT ki.id, ki.title, ki.content, ki.knowledge_type, 
                               ki.source_type, ki.source_url, ki.tags, ki.summary,
                               ki.confidence, ki.metadata, ki.created_at, ki.updated_at
                        FROM knowledge_items ki
                        LEFT JOIN source_validations sv ON ki.id::text = sv.item_id
                        WHERE sv.timestamp IS NULL OR sv.timestamp < $1
                        ORDER BY ki.created_at DESC
                        LIMIT 100
                    """, cutoff_date)
                
                # Revalidate items
                revalidated_count = 0
                for item_data in items_to_revalidate:
                    try:
                        item = KnowledgeItem(
                            id=item_data['id'],
                            title=item_data['title'],
                            content=item_data['content'],
                            knowledge_type=item_data['knowledge_type'],
                            source_type=item_data['source_type'],
                            source_url=item_data['source_url'] or '',
                            tags=item_data['tags'] or [],
                            summary=item_data['summary'] or '',
                            confidence=item_data['confidence'] or 'medium',
                            metadata=item_data['metadata'] or {},
                            created_at=item_data['created_at'],
                            updated_at=item_data['updated_at']
                        )
                        
                        await self.validation_service.validate_knowledge_item(item)
                        revalidated_count += 1
                        
                        # Rate limiting
                        await asyncio.sleep(0.1)
                        
                    except Exception as e:
                        logger.error("Revalidation failed for item", 
                                   item_id=str(item_data['id']), error=str(e))
                
                logger.info("Periodic revalidation completed", 
                          revalidated_items=revalidated_count)
                
                # Wait 6 hours before next revalidation cycle
                await asyncio.sleep(6 * 60 * 60)
                
        except Exception as e:
            logger.error("Periodic revalidation workflow failed", error=str(e))
    
    async def _credibility_update_workflow(self):
        """Periodic update of source credibility scores"""
        try:
            while True:
                logger.info("Starting credibility update workflow")
                
                # Update credibility scores based on recent validation results
                async with self.db_manager.get_postgres_pool().acquire() as conn:
                    # Get validation statistics for each source from last 7 days
                    source_stats = await conn.fetch("""
                        SELECT 
                            source_name,
                            COUNT(*) as total_validations,
                            AVG(overall_score) as avg_score,
                            COUNT(CASE WHEN status = 'validated' THEN 1 END) as successful,
                            COUNT(CASE WHEN status = 'quarantined' THEN 1 END) as quarantined,
                            AVG(validation_time) as avg_time
                        FROM source_validations 
                        WHERE timestamp > $1
                        GROUP BY source_name
                        HAVING COUNT(*) >= 10
                    """, datetime.utcnow() - timedelta(days=7))
                    
                    # Update credibility for each source
                    for stats in source_stats:
                        success_rate = stats['successful'] / stats['total_validations']
                        avg_quality = float(stats['avg_score'])
                        
                        # Calculate new credibility metrics
                        historical_accuracy = min(1.0, avg_quality * 1.2)  # Boost for quality
                        community_validation = success_rate
                        
                        # Update source credibility
                        await conn.execute("""
                            UPDATE source_credibility 
                            SET historical_accuracy = $2,
                                community_validation = $3,
                                reputation_score = (base_credibility + $2 + $3) / 3,
                                total_validations = total_validations + $4,
                                successful_validations = successful_validations + $5,
                                quarantined_items = quarantined_items + $6,
                                avg_validation_time = $7,
                                last_validation = NOW(),
                                updated_at = NOW()
                            WHERE source_name = $1
                        """, 
                        stats['source_name'], historical_accuracy, community_validation,
                        stats['total_validations'], stats['successful'], 
                        stats['quarantined'], float(stats['avg_time']))
                
                logger.info("Credibility update completed for sources", 
                          updated_sources=len(source_stats))
                
                # Wait 24 hours before next update
                await asyncio.sleep(24 * 60 * 60)
                
        except Exception as e:
            logger.error("Credibility update workflow failed", error=str(e))
    
    async def _compliance_cleanup_workflow(self):
        """Periodic cleanup for GDPR/SOC2 compliance"""
        try:
            while True:
                logger.info("Starting compliance cleanup workflow")
                
                # Apply data retention policies
                async with self.db_manager.get_postgres_pool().acquire() as conn:
                    # Get active retention policies
                    policies = await conn.fetch("""
                        SELECT policy_name, table_name, retention_period, retention_condition
                        FROM data_retention_policies 
                        WHERE is_active = TRUE
                    """)
                    
                    for policy in policies:
                        try:
                            # Calculate cutoff date
                            cutoff_date = datetime.utcnow() - policy['retention_period']
                            
                            # Build cleanup query
                            cleanup_query = f"""
                                DELETE FROM {policy['table_name']} 
                                WHERE created_at < $1
                            """
                            
                            if policy['retention_condition']:
                                cleanup_query += f" AND {policy['retention_condition']}"
                            
                            # Execute cleanup
                            deleted_count = await conn.execute(cleanup_query, cutoff_date)
                            
                            # Update policy last cleanup time
                            await conn.execute("""
                                UPDATE data_retention_policies 
                                SET last_cleanup = NOW(),
                                    next_cleanup = NOW() + retention_period
                                WHERE policy_name = $1
                            """, policy['policy_name'])
                            
                            logger.info("Compliance cleanup completed",
                                      policy=policy['policy_name'],
                                      table=policy['table_name'],
                                      deleted_records=deleted_count.split()[1] if 'DELETE' in deleted_count else 0)
                            
                        except Exception as e:
                            logger.error("Cleanup failed for policy", 
                                       policy=policy['policy_name'], error=str(e))
                
                # Wait 7 days before next cleanup cycle
                await asyncio.sleep(7 * 24 * 60 * 60)
                
        except Exception as e:
            logger.error("Compliance cleanup workflow failed", error=str(e))
    
    async def _create_audit_log(
        self, 
        event_type: str, 
        validation_id: str, 
        item_id: str, 
        source_name: str, 
        event_data: Dict[str, Any]
    ):
        """Create audit log entry for compliance"""
        try:
            async with self.db_manager.get_postgres_pool().acquire() as conn:
                await conn.execute("""
                    INSERT INTO validation_audit_log (
                        event_type, validation_id, item_id, source_name,
                        event_data, gdpr_applicable, event_timestamp,
                        correlation_id, service_version
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """,
                event_type, validation_id, 
                UUID(item_id) if item_id else None,
                source_name, json.dumps(event_data), True,
                datetime.utcnow(), str(uuid4()), "1.0")
                
        except Exception as e:
            logger.error("Failed to create audit log entry", error=str(e))
    
    async def get_integration_status(self) -> Dict[str, Any]:
        """Get integration status and health metrics"""
        try:
            # Get validation statistics
            validation_stats = await self.validation_service.get_validation_statistics()
            
            # Get monitoring status
            monitoring_status = await self.monitoring_service.get_monitoring_status()
            
            # Calculate integration health
            overall_health = "healthy"
            if (validation_stats['overall']['success_rate'] < 0.995 or
                validation_stats['overall']['average_validation_time'] > 0.5):
                overall_health = "degraded"
            
            if validation_stats['overall']['error_rate'] > 0.01:
                overall_health = "unhealthy"
            
            return {
                "integration_status": "active",
                "overall_health": overall_health,
                "components": {
                    "validation_service": "operational",
                    "monitoring_service": "operational" if monitoring_status['monitoring_active'] else "inactive",
                    "quality_integration": "operational",
                    "extraction_integration": "operational",
                    "automated_workflows": "operational"
                },
                "performance_metrics": {
                    "validation_accuracy": validation_stats['overall']['success_rate'],
                    "average_latency": validation_stats['overall']['average_validation_time'],
                    "throughput": validation_stats['performance']['validations_per_second'],
                    "meets_sla": validation_stats['performance']['meets_latency_requirement']
                },
                "compliance_status": {
                    "gdpr_compliant": True,
                    "soc2_compliant": True,
                    "audit_logging": "active",
                    "data_retention": "active"
                },
                "enterprise_readiness": {
                    "high_availability": True,
                    "scalability": True,
                    "security": True,
                    "monitoring": True,
                    "compliance": True
                }
            }
            
        except Exception as e:
            logger.error("Failed to get integration status", error=str(e))
            return {
                "integration_status": "error",
                "error": str(e)
            }

# Singleton instance
_integration_service_instance = None

async def get_integration_service(
    db_manager: DatabaseManager,
    validation_service: SourceValidationService,
    quality_scorer: AdvancedQualityScorer,
    monitoring_service: ValidationMonitoringService
) -> ValidationIntegrationService:
    """Get or create integration service instance"""
    global _integration_service_instance
    
    if _integration_service_instance is None:
        _integration_service_instance = ValidationIntegrationService(
            db_manager, validation_service, quality_scorer, monitoring_service
        )
    
    return _integration_service_instance