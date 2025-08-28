# ABOUTME: Pipeline Manager for initializing and coordinating Multi-Source Knowledge Extraction components
# ABOUTME: Manages lifecycle of extractor, processor, and real-time updater services

import asyncio
import structlog
from typing import Dict, Any, Optional
from datetime import datetime

from core.database import DatabaseManager
from services.vector_service import VectorService
from services.pattern_quality_service import AdvancedQualityScorer
from services.pattern_intelligence_service import PatternIntelligenceEngine
from services.multi_source_knowledge_extractor import MultiSourceKnowledgeExtractor
from services.knowledge_processing_pipeline import KnowledgeProcessingPipeline
from services.realtime_knowledge_updater import RealtimeKnowledgeUpdater

logger = structlog.get_logger(__name__)

class ExtractionPipelineManager:
    """
    Manages the complete Multi-Source Knowledge Extraction Pipeline
    Coordinates initialization, startup, and shutdown of all components
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        
        # Core services
        self.vector_service = None
        self.quality_scorer = None
        self.pattern_intelligence = None
        
        # Pipeline components
        self.extractor = None
        self.processor = None
        self.updater = None
        
        # State tracking
        self.initialized = False
        self.running = False
        self.startup_time = None
        
    async def initialize(self) -> Dict[str, Any]:
        """Initialize all pipeline components"""
        if self.initialized:
            return self.get_pipeline_components()
        
        try:
            logger.info("Initializing Multi-Source Knowledge Extraction Pipeline")
            start_time = datetime.utcnow()
            
            # Initialize core services
            logger.info("Initializing core services")
            
            # Vector service for embeddings and semantic search
            self.vector_service = VectorService(self.db_manager)
            await self.vector_service.initialize()
            
            # Quality scorer for pattern assessment
            self.quality_scorer = AdvancedQualityScorer(self.db_manager, self.vector_service)
            
            # Pattern intelligence engine for relationships
            self.pattern_intelligence = PatternIntelligenceEngine(
                self.db_manager, self.vector_service, self.quality_scorer
            )
            
            # Initialize pipeline components
            logger.info("Initializing extraction pipeline components")
            
            # Multi-source extractor
            self.extractor = MultiSourceKnowledgeExtractor(
                self.db_manager, self.vector_service, self.quality_scorer, self.pattern_intelligence
            )
            
            # Knowledge processing pipeline
            self.processor = KnowledgeProcessingPipeline(
                self.db_manager, self.vector_service, self.quality_scorer, self.pattern_intelligence
            )
            
            # Real-time updater
            self.updater = RealtimeKnowledgeUpdater(
                self.db_manager, self.extractor, self.processor, self.vector_service
            )
            
            self.initialized = True
            self.startup_time = start_time
            
            initialization_time = (datetime.utcnow() - start_time).total_seconds()
            
            logger.info("Multi-Source Knowledge Extraction Pipeline initialized successfully",
                       initialization_time=f"{initialization_time:.2f}s")
            
            return self.get_pipeline_components()
            
        except Exception as e:
            logger.error("Failed to initialize extraction pipeline", error=str(e))
            raise RuntimeError(f"Pipeline initialization failed: {str(e)}")
    
    async def start_pipeline(self) -> Dict[str, Any]:
        """Start the processing pipeline and monitoring"""
        if not self.initialized:
            await self.initialize()
        
        if self.running:
            return {"status": "already_running", "message": "Pipeline is already running"}
        
        try:
            logger.info("Starting Multi-Source Knowledge Extraction Pipeline")
            
            # Start processing pipeline workers
            await self.processor.start_processing()
            logger.info("Processing pipeline started")
            
            # Start real-time monitoring (optional - can be started separately)
            try:
                await self.updater.start_monitoring()
                logger.info("Real-time monitoring started")
            except Exception as e:
                logger.warning("Real-time monitoring failed to start", error=str(e))
                # Don't fail the entire startup for monitoring issues
            
            self.running = True
            
            return {
                "status": "started",
                "message": "Multi-Source Knowledge Extraction Pipeline started successfully",
                "started_at": datetime.utcnow().isoformat(),
                "components": {
                    "extractor": "ready",
                    "processor": "running",
                    "updater": "monitoring" if self.updater else "ready"
                }
            }
            
        except Exception as e:
            logger.error("Failed to start extraction pipeline", error=str(e))
            raise RuntimeError(f"Pipeline startup failed: {str(e)}")
    
    async def stop_pipeline(self) -> Dict[str, Any]:
        """Stop the processing pipeline and monitoring"""
        if not self.running:
            return {"status": "not_running", "message": "Pipeline is not currently running"}
        
        try:
            logger.info("Stopping Multi-Source Knowledge Extraction Pipeline")
            
            # Stop real-time monitoring
            if self.updater:
                try:
                    await self.updater.stop_monitoring()
                    logger.info("Real-time monitoring stopped")
                except Exception as e:
                    logger.warning("Error stopping monitoring", error=str(e))
            
            # Stop processing pipeline
            if self.processor:
                await self.processor.stop_processing()
                logger.info("Processing pipeline stopped")
            
            self.running = False
            
            return {
                "status": "stopped",
                "message": "Multi-Source Knowledge Extraction Pipeline stopped successfully",
                "stopped_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("Failed to stop extraction pipeline", error=str(e))
            raise RuntimeError(f"Pipeline shutdown failed: {str(e)}")
    
    def get_pipeline_components(self) -> Dict[str, Any]:
        """Get pipeline components for dependency injection"""
        if not self.initialized:
            raise RuntimeError("Pipeline not initialized. Call initialize() first.")
        
        return {
            'extractor': self.extractor,
            'processor': self.processor,
            'updater': self.updater,
            'db_manager': self.db_manager,
            'vector_service': self.vector_service,
            'quality_scorer': self.quality_scorer,
            'pattern_intelligence': self.pattern_intelligence
        }
    
    async def get_pipeline_status(self) -> Dict[str, Any]:
        """Get comprehensive pipeline status"""
        status = {
            'initialized': self.initialized,
            'running': self.running,
            'startup_time': self.startup_time.isoformat() if self.startup_time else None,
            'components': {
                'extractor': 'ready' if self.extractor else 'not_initialized',
                'processor': 'running' if (self.processor and self.running) else 'stopped',
                'updater': 'monitoring' if (self.updater and self.running) else 'inactive',
                'vector_service': 'ready' if self.vector_service else 'not_initialized',
                'quality_scorer': 'ready' if self.quality_scorer else 'not_initialized',
                'pattern_intelligence': 'ready' if self.pattern_intelligence else 'not_initialized'
            }
        }
        
        if self.initialized and self.running:
            # Get detailed statistics from components
            try:
                extraction_stats = await self.extractor.get_extraction_statistics()
                processing_stats = await self.processor.get_processing_statistics()
                monitoring_status = await self.updater.get_monitoring_status()
                
                status['statistics'] = {
                    'extraction': extraction_stats,
                    'processing': processing_stats,
                    'monitoring': monitoring_status
                }
            except Exception as e:
                logger.warning("Failed to get component statistics", error=str(e))
                status['statistics_error'] = str(e)
        
        return status
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all pipeline components"""
        health = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'component_health': {}
        }
        
        issues = []
        
        # Check initialization
        if not self.initialized:
            issues.append("Pipeline not initialized")
            health['component_health']['initialization'] = 'failed'
        else:
            health['component_health']['initialization'] = 'healthy'
        
        # Check database connections
        try:
            # Test PostgreSQL
            async with self.db_manager.get_postgres_pool().acquire() as conn:
                await conn.fetchval("SELECT 1")
            health['component_health']['postgresql'] = 'healthy'
        except Exception as e:
            issues.append(f"PostgreSQL connection failed: {str(e)}")
            health['component_health']['postgresql'] = 'unhealthy'
        
        try:
            # Test Neo4j
            async with self.db_manager.get_neo4j_session() as session:
                await session.run("RETURN 1")
            health['component_health']['neo4j'] = 'healthy'
        except Exception as e:
            issues.append(f"Neo4j connection failed: {str(e)}")
            health['component_health']['neo4j'] = 'unhealthy'
        
        try:
            # Test Qdrant
            if hasattr(self.db_manager, 'qdrant_client') and self.db_manager.qdrant_client:
                collections = await self.db_manager.qdrant_client.get_collections()
                health['component_health']['qdrant'] = 'healthy'
        except Exception as e:
            issues.append(f"Qdrant connection failed: {str(e)}")
            health['component_health']['qdrant'] = 'unhealthy'
        
        try:
            # Test Redis
            if hasattr(self.db_manager, 'redis') and self.db_manager.redis:
                await self.db_manager.redis.ping()
                health['component_health']['redis'] = 'healthy'
        except Exception as e:
            issues.append(f"Redis connection failed: {str(e)}")
            health['component_health']['redis'] = 'unhealthy'
        
        # Check component health
        if self.initialized:
            if self.processor and self.running:
                try:
                    proc_stats = await self.processor.get_processing_statistics()
                    if proc_stats.get('active_workers', 0) > 0:
                        health['component_health']['processor'] = 'healthy'
                    else:
                        health['component_health']['processor'] = 'no_workers'
                except Exception as e:
                    issues.append(f"Processor health check failed: {str(e)}")
                    health['component_health']['processor'] = 'unhealthy'
            else:
                health['component_health']['processor'] = 'inactive'
            
            if self.updater:
                try:
                    monitor_status = await self.updater.get_monitoring_status()
                    if monitor_status.get('monitoring_active', False):
                        health['component_health']['updater'] = 'healthy'
                    else:
                        health['component_health']['updater'] = 'inactive'
                except Exception as e:
                    issues.append(f"Updater health check failed: {str(e)}")
                    health['component_health']['updater'] = 'unhealthy'
            else:
                health['component_health']['updater'] = 'not_initialized'
        
        # Determine overall health
        if issues:
            health['status'] = 'degraded' if len(issues) < 3 else 'unhealthy'
            health['issues'] = issues
        
        return health
    
    async def shutdown(self):
        """Clean shutdown of the pipeline"""
        logger.info("Shutting down Multi-Source Knowledge Extraction Pipeline")
        
        try:
            if self.running:
                await self.stop_pipeline()
            
            # Clean up resources
            if self.vector_service:
                await self.vector_service.close()
            
            logger.info("Pipeline shutdown completed")
            
        except Exception as e:
            logger.error("Error during pipeline shutdown", error=str(e))

# Global pipeline manager instance
_pipeline_manager: Optional[ExtractionPipelineManager] = None

async def get_pipeline_manager(db_manager: DatabaseManager) -> ExtractionPipelineManager:
    """Get or create the global pipeline manager instance"""
    global _pipeline_manager
    
    if _pipeline_manager is None:
        _pipeline_manager = ExtractionPipelineManager(db_manager)
        await _pipeline_manager.initialize()
    
    return _pipeline_manager

async def shutdown_pipeline_manager():
    """Shutdown the global pipeline manager"""
    global _pipeline_manager
    
    if _pipeline_manager:
        await _pipeline_manager.shutdown()
        _pipeline_manager = None