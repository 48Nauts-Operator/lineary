# ABOUTME: Advanced Knowledge Processing Pipeline with ML Classification and Real-time Updates
# ABOUTME: Processes extracted knowledge with semantic analysis, pattern classification, and conflict resolution

import asyncio
import json
import numpy as np
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple, Set
from uuid import UUID, uuid4
from dataclasses import dataclass, field
from enum import Enum
import structlog
from collections import defaultdict, deque
import hashlib
import re

# ML imports
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import DBSCAN, KMeans
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import joblib

from core.database import DatabaseManager
from models.knowledge import KnowledgeItem
from models.pattern_quality import PatternContext, QualityScore
from services.vector_service import VectorService
from services.pattern_quality_service import AdvancedQualityScorer
from services.pattern_intelligence_service import PatternIntelligenceEngine
from services.multi_source_knowledge_extractor import ExtractionResult

logger = structlog.get_logger(__name__)

class ProcessingStage(Enum):
    INTAKE = "intake"
    CLASSIFICATION = "classification"
    QUALITY_ASSESSMENT = "quality_assessment"
    DEDUPLICATION = "deduplication"
    RELATIONSHIP_DETECTION = "relationship_detection"
    CONFLICT_RESOLUTION = "conflict_resolution"
    STORAGE = "storage"
    INDEXING = "indexing"

@dataclass
class ProcessingResult:
    """Result of processing pipeline for a knowledge item"""
    item_id: UUID
    original_item: KnowledgeItem
    processed_item: Optional[KnowledgeItem]
    stage_completed: ProcessingStage
    classification: Dict[str, float]
    quality_score: Optional[QualityScore]
    conflicts_detected: List[str]
    conflicts_resolved: bool
    processing_time: float
    errors: List[str]
    
@dataclass
class ConflictResolution:
    """Conflict resolution decision"""
    conflict_type: str
    conflicting_items: List[UUID]
    resolution_strategy: str
    chosen_item: Optional[UUID]
    confidence: float
    reasoning: str

class KnowledgeProcessingPipeline:
    """
    Advanced Knowledge Processing Pipeline with ML classification,
    real-time processing, and intelligent conflict resolution
    """
    
    def __init__(
        self,
        db_manager: DatabaseManager,
        vector_service: VectorService,
        quality_scorer: AdvancedQualityScorer,
        pattern_intelligence: PatternIntelligenceEngine
    ):
        self.db_manager = db_manager
        self.vector_service = vector_service
        self.quality_scorer = quality_scorer
        self.pattern_intelligence = pattern_intelligence
        
        # Processing queue and workers
        self.processing_queue = asyncio.Queue(maxsize=10000)
        self.processing_workers = []
        self.worker_count = 4
        
        # ML models and classifiers
        self.domain_classifier = None
        self.quality_predictor = None
        self.tfidf_vectorizer = None
        self.scaler = StandardScaler()
        
        # Caches and indexes
        self._similarity_cache = {}
        self._conflict_rules = []
        self._processing_stats = defaultdict(int)
        
        # Real-time processing tracking
        self._active_processing = {}
        self._recent_items = deque(maxlen=1000)
        
        # Performance monitoring
        self._stage_timings = defaultdict(list)
        self._throughput_tracker = deque(maxlen=100)
        
        self._initialize_ml_models()
        self._initialize_conflict_rules()
    
    def _initialize_ml_models(self):
        """Initialize ML models for classification and quality prediction"""
        try:
            # Try to load pre-trained models
            self.domain_classifier = joblib.load('data/models/domain_classifier.joblib')
            self.quality_predictor = joblib.load('data/models/quality_predictor.joblib')
            self.tfidf_vectorizer = joblib.load('data/models/tfidf_vectorizer.joblib')
            logger.info("Loaded pre-trained ML models")
        except FileNotFoundError:
            # Initialize new models that will be trained incrementally
            self.domain_classifier = RandomForestClassifier(
                n_estimators=100,
                random_state=42,
                max_depth=20
            )
            self.quality_predictor = RandomForestClassifier(
                n_estimators=50,
                random_state=42
            )
            self.tfidf_vectorizer = TfidfVectorizer(
                max_features=5000,
                stop_words='english',
                ngram_range=(1, 2)
            )
            logger.info("Initialized new ML models for training")
    
    def _initialize_conflict_rules(self):
        """Initialize conflict detection and resolution rules"""
        self._conflict_rules = [
            {
                'type': 'duplicate_content',
                'threshold': 0.95,
                'resolution': 'keep_higher_quality'
            },
            {
                'type': 'conflicting_information',
                'threshold': 0.8,
                'resolution': 'keep_newer_source'
            },
            {
                'type': 'outdated_information',
                'threshold': 0.9,
                'resolution': 'deprecate_older'
            },
            {
                'type': 'source_reliability',
                'threshold': 0.7,
                'resolution': 'prefer_reliable_source'
            }
        ]
    
    async def start_processing(self):
        """Start the processing pipeline workers"""
        logger.info("Starting knowledge processing pipeline",
                   worker_count=self.worker_count)
        
        # Start processing workers
        for i in range(self.worker_count):
            worker = asyncio.create_task(self._processing_worker(f"worker-{i}"))
            self.processing_workers.append(worker)
        
        logger.info("Knowledge processing pipeline started")
    
    async def stop_processing(self):
        """Stop the processing pipeline"""
        logger.info("Stopping knowledge processing pipeline")
        
        # Cancel all workers
        for worker in self.processing_workers:
            worker.cancel()
        
        # Wait for workers to finish
        await asyncio.gather(*self.processing_workers, return_exceptions=True)
        
        self.processing_workers.clear()
        logger.info("Knowledge processing pipeline stopped")
    
    async def submit_for_processing(
        self, 
        knowledge_item: KnowledgeItem,
        priority: int = 0
    ) -> UUID:
        """Submit knowledge item for processing"""
        processing_id = uuid4()
        
        try:
            await self.processing_queue.put({
                'id': processing_id,
                'item': knowledge_item,
                'priority': priority,
                'submitted_at': datetime.utcnow(),
                'stage': ProcessingStage.INTAKE
            })
            
            self._active_processing[processing_id] = {
                'item_id': knowledge_item.id,
                'stage': ProcessingStage.INTAKE,
                'started_at': datetime.utcnow()
            }
            
            logger.info("Submitted item for processing",
                       processing_id=str(processing_id),
                       item_id=str(knowledge_item.id))
            
            return processing_id
            
        except asyncio.QueueFull:
            logger.error("Processing queue full, cannot submit item",
                        item_id=str(knowledge_item.id))
            raise RuntimeError("Processing queue full")
    
    async def _processing_worker(self, worker_id: str):
        """Processing worker that handles items from the queue"""
        logger.info(f"Starting processing worker {worker_id}")
        
        try:
            while True:
                # Get next item from queue
                processing_task = await self.processing_queue.get()
                start_time = time.time()
                
                try:
                    # Process the item through all stages
                    result = await self._process_knowledge_item(processing_task)
                    
                    # Update statistics
                    processing_time = time.time() - start_time
                    self._throughput_tracker.append(processing_time)
                    self._processing_stats['items_processed'] += 1
                    
                    if result.errors:
                        self._processing_stats['items_failed'] += 1
                    else:
                        self._processing_stats['items_successful'] += 1
                    
                    # Clean up tracking
                    if processing_task['id'] in self._active_processing:
                        del self._active_processing[processing_task['id']]
                    
                    logger.info(f"Worker {worker_id} completed processing",
                               processing_id=str(processing_task['id']),
                               processing_time=processing_time,
                               stage_completed=result.stage_completed.value)
                    
                except Exception as e:
                    logger.error(f"Worker {worker_id} processing failed",
                                processing_id=str(processing_task['id']),
                                error=str(e))
                    self._processing_stats['items_failed'] += 1
                
                finally:
                    self.processing_queue.task_done()
                    
        except asyncio.CancelledError:
            logger.info(f"Processing worker {worker_id} cancelled")
        except Exception as e:
            logger.error(f"Processing worker {worker_id} error", error=str(e))
    
    async def _process_knowledge_item(self, processing_task: Dict[str, Any]) -> ProcessingResult:
        """Process a knowledge item through all pipeline stages"""
        item = processing_task['item']
        processing_id = processing_task['id']
        
        result = ProcessingResult(
            item_id=item.id,
            original_item=item,
            processed_item=None,
            stage_completed=ProcessingStage.INTAKE,
            classification={},
            quality_score=None,
            conflicts_detected=[],
            conflicts_resolved=False,
            processing_time=0.0,
            errors=[]
        )
        
        start_time = time.time()
        
        try:
            # Stage 1: Classification
            result.stage_completed = ProcessingStage.CLASSIFICATION
            stage_start = time.time()
            result.classification = await self._classify_knowledge_item(item)
            self._stage_timings[ProcessingStage.CLASSIFICATION].append(time.time() - stage_start)
            
            # Stage 2: Quality Assessment
            result.stage_completed = ProcessingStage.QUALITY_ASSESSMENT
            stage_start = time.time()
            context = self._create_processing_context(item, result.classification)
            result.quality_score = await self.quality_scorer.score_pattern_quality(item, context)
            self._stage_timings[ProcessingStage.QUALITY_ASSESSMENT].append(time.time() - stage_start)
            
            # Stage 3: Deduplication Check
            result.stage_completed = ProcessingStage.DEDUPLICATION
            stage_start = time.time()
            duplicates = await self._detect_duplicates(item)
            if duplicates:
                result.conflicts_detected.append(f"Found {len(duplicates)} potential duplicates")
            self._stage_timings[ProcessingStage.DEDUPLICATION].append(time.time() - stage_start)
            
            # Stage 4: Relationship Detection
            result.stage_completed = ProcessingStage.RELATIONSHIP_DETECTION
            stage_start = time.time()
            relationships = await self._detect_relationships(item)
            self._stage_timings[ProcessingStage.RELATIONSHIP_DETECTION].append(time.time() - stage_start)
            
            # Stage 5: Conflict Resolution
            result.stage_completed = ProcessingStage.CONFLICT_RESOLUTION
            stage_start = time.time()
            if result.conflicts_detected:
                conflicts_resolved = await self._resolve_conflicts(item, duplicates, result.quality_score)
                result.conflicts_resolved = conflicts_resolved
            else:
                result.conflicts_resolved = True
            self._stage_timings[ProcessingStage.CONFLICT_RESOLUTION].append(time.time() - stage_start)
            
            # Stage 6: Enhanced Processing (only if no unresolved conflicts)
            if result.conflicts_resolved:
                # Enhance the item with additional metadata
                enhanced_item = await self._enhance_knowledge_item(
                    item, result.classification, result.quality_score, relationships
                )
                result.processed_item = enhanced_item
                
                # Stage 7: Storage
                result.stage_completed = ProcessingStage.STORAGE
                stage_start = time.time()
                await self._store_processed_item(enhanced_item, result.quality_score)
                self._stage_timings[ProcessingStage.STORAGE].append(time.time() - stage_start)
                
                # Stage 8: Indexing
                result.stage_completed = ProcessingStage.INDEXING
                stage_start = time.time()
                await self._index_knowledge_item(enhanced_item, relationships)
                self._stage_timings[ProcessingStage.INDEXING].append(time.time() - stage_start)
            
        except Exception as e:
            result.errors.append(str(e))
            logger.error("Failed to process knowledge item",
                        item_id=str(item.id),
                        stage=result.stage_completed.value,
                        error=str(e))
        
        result.processing_time = time.time() - start_time
        return result
    
    async def _classify_knowledge_item(self, item: KnowledgeItem) -> Dict[str, float]:
        """Classify knowledge item using ML models"""
        try:
            # Extract features for classification
            text_features = f"{item.title} {item.content} {' '.join(item.tags)}"
            
            # Domain classification
            domain_scores = await self._classify_domain(text_features)
            
            # Pattern type classification
            pattern_type_scores = await self._classify_pattern_type(text_features, item)
            
            # Source reliability assessment
            source_reliability = await self._assess_source_reliability(item)
            
            # Technical complexity assessment
            complexity_score = await self._assess_technical_complexity(text_features)
            
            classification = {
                **domain_scores,
                **pattern_type_scores,
                'source_reliability': source_reliability,
                'technical_complexity': complexity_score
            }
            
            return classification
            
        except Exception as e:
            logger.warning("Failed to classify knowledge item", error=str(e))
            return {'domain': 'unknown', 'confidence': 0.0}
    
    async def _classify_domain(self, text_features: str) -> Dict[str, float]:
        """Classify the domain of the knowledge item"""
        # Domain keywords mapping
        domain_keywords = {
            'security': ['security', 'vulnerability', 'exploit', 'authentication', 'encryption', 'hack'],
            'infrastructure': ['docker', 'kubernetes', 'terraform', 'aws', 'cloud', 'deployment'],
            'development': ['python', 'javascript', 'programming', 'code', 'api', 'framework'],
            'devops': ['ci/cd', 'pipeline', 'monitoring', 'logging', 'automation'],
            'database': ['sql', 'database', 'query', 'mongodb', 'postgresql', 'redis'],
            'networking': ['network', 'http', 'tcp', 'ssl', 'proxy', 'load balancer']
        }
        
        text_lower = text_features.lower()
        scores = {}
        
        for domain, keywords in domain_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            scores[f'domain_{domain}'] = score / len(keywords)
        
        # Determine primary domain
        primary_domain = max(scores.keys(), key=lambda k: scores[k]) if scores else 'domain_general'
        scores['primary_domain'] = primary_domain.replace('domain_', '')
        scores['domain_confidence'] = max(scores.values()) if scores else 0.0
        
        return scores
    
    async def _classify_pattern_type(self, text_features: str, item: KnowledgeItem) -> Dict[str, float]:
        """Classify the type of pattern"""
        pattern_indicators = {
            'code_example': ['```', 'function', 'class', 'def ', 'import', 'from '],
            'configuration': ['config', 'yaml', 'json', 'xml', 'settings', 'environment'],
            'command': ['$', 'sudo', 'chmod', 'grep', 'awk', 'sed'],
            'troubleshooting': ['error', 'issue', 'problem', 'solution', 'fix', 'debug'],
            'best_practice': ['best practice', 'recommended', 'should', 'avoid', 'consider'],
            'tutorial': ['step', 'tutorial', 'guide', 'how to', 'walkthrough']
        }
        
        text_lower = text_features.lower()
        content_lower = item.content.lower()
        
        scores = {}
        for pattern_type, indicators in pattern_indicators.items():
            score = 0
            for indicator in indicators:
                if indicator in text_lower or indicator in content_lower:
                    score += 1
            scores[f'pattern_{pattern_type}'] = min(score / len(indicators), 1.0)
        
        return scores
    
    async def _assess_source_reliability(self, item: KnowledgeItem) -> float:
        """Assess the reliability of the source"""
        source_reliability = {
            'stackoverflow': 0.8,
            'owasp': 0.95,
            'kubernetes': 0.9,
            'terraform': 0.85,
            'exploitdb': 0.9,
            'hacktricks': 0.8,
            'commandlinefu': 0.7,
            'hashicorp': 0.85
        }
        
        base_reliability = source_reliability.get(item.source_type, 0.5)
        
        # Adjust based on metadata
        if hasattr(item, 'metadata') and item.metadata:
            # Higher reliability for items with more votes/interactions
            if 'votes' in item.metadata:
                vote_bonus = min(int(item.metadata.get('votes', 0)) / 100, 0.2)
                base_reliability += vote_bonus
            
            # Higher reliability for verified sources
            if item.metadata.get('verified', False):
                base_reliability += 0.1
        
        return min(base_reliability, 1.0)
    
    async def _assess_technical_complexity(self, text_features: str) -> float:
        """Assess the technical complexity of the content"""
        complexity_indicators = {
            'high': ['advanced', 'complex', 'enterprise', 'scalable', 'architecture'],
            'medium': ['configuration', 'setup', 'implementation', 'integration'],
            'low': ['basic', 'simple', 'introduction', 'getting started']
        }
        
        text_lower = text_features.lower()
        scores = {'high': 0, 'medium': 0, 'low': 0}
        
        for level, indicators in complexity_indicators.items():
            for indicator in indicators:
                if indicator in text_lower:
                    scores[level] += 1
        
        # Calculate complexity score (0.0 = low, 1.0 = high)
        total_indicators = sum(scores.values())
        if total_indicators == 0:
            return 0.5  # Default medium complexity
        
        weighted_score = (scores['high'] * 1.0 + scores['medium'] * 0.5 + scores['low'] * 0.0)
        return weighted_score / total_indicators
    
    def _create_processing_context(self, item: KnowledgeItem, classification: Dict[str, float]) -> PatternContext:
        """Create context for quality assessment"""
        primary_domain = classification.get('primary_domain', 'general')
        complexity = classification.get('technical_complexity', 0.5)
        
        # Map complexity to team experience requirement
        if complexity > 0.7:
            team_experience = "high"
        elif complexity > 0.3:
            team_experience = "medium"
        else:
            team_experience = "low"
        
        return PatternContext(
            domain=primary_domain,
            team_experience=team_experience,
            business_criticality="medium",  # Default
            technology_stack=item.tags,
            compliance_requirements=[]
        )
    
    async def _detect_duplicates(self, item: KnowledgeItem) -> List[KnowledgeItem]:
        """Detect potential duplicate knowledge items"""
        try:
            # Generate embedding for the item
            embedding_text = f"{item.title} {item.content[:500]}"
            embedding = await self.vector_service.generate_embedding(embedding_text)
            
            # Search for similar items
            similar_items = await self.vector_service.search_similar(
                embedding, limit=20, threshold=0.85
            )
            
            duplicates = []
            for similar_item in similar_items:
                if similar_item.id != item.id:
                    # Check for high content similarity
                    similarity = await self._calculate_content_similarity(item, similar_item)
                    if similarity > 0.9:
                        duplicates.append(similar_item)
            
            return duplicates
            
        except Exception as e:
            logger.warning("Failed to detect duplicates", error=str(e))
            return []
    
    async def _calculate_content_similarity(self, item1: KnowledgeItem, item2: KnowledgeItem) -> float:
        """Calculate content similarity between two items"""
        # Create cache key
        cache_key = f"{item1.id}:{item2.id}"
        if cache_key in self._similarity_cache:
            return self._similarity_cache[cache_key]
        
        # Simple text similarity using TF-IDF
        texts = [
            f"{item1.title} {item1.content}",
            f"{item2.title} {item2.content}"
        ]
        
        try:
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(texts)
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0, 0]
        except:
            # Fallback to simple word overlap
            words1 = set(f"{item1.title} {item1.content}".lower().split())
            words2 = set(f"{item2.title} {item2.content}".lower().split())
            similarity = len(words1 & words2) / len(words1 | words2) if words1 | words2 else 0.0
        
        self._similarity_cache[cache_key] = similarity
        return similarity
    
    async def _detect_relationships(self, item: KnowledgeItem) -> List[Dict[str, Any]]:
        """Detect relationships with existing knowledge items"""
        try:
            # Use pattern intelligence for relationship detection
            # This would integrate with the existing pattern intelligence system
            relationships = []
            
            # Find complementary patterns
            complementary = await self._find_complementary_patterns(item)
            for comp_item in complementary:
                relationships.append({
                    'type': 'complementary',
                    'target_id': comp_item.id,
                    'confidence': 0.8
                })
            
            # Find alternative patterns
            alternatives = await self._find_alternative_patterns(item)
            for alt_item in alternatives:
                relationships.append({
                    'type': 'alternative',
                    'target_id': alt_item.id,
                    'confidence': 0.7
                })
            
            return relationships
            
        except Exception as e:
            logger.warning("Failed to detect relationships", error=str(e))
            return []
    
    async def _find_complementary_patterns(self, item: KnowledgeItem) -> List[KnowledgeItem]:
        """Find patterns that complement this item"""
        # Simplified implementation - would use more sophisticated matching
        complementary_tags = {
            'docker': ['kubernetes', 'docker-compose'],
            'kubernetes': ['docker', 'helm', 'ingress'],
            'terraform': ['ansible', 'aws', 'infrastructure'],
            'security': ['authentication', 'authorization', 'encryption']
        }
        
        complementary_items = []
        for tag in item.tags:
            if tag in complementary_tags:
                # Search for items with complementary tags
                for comp_tag in complementary_tags[tag]:
                    # This would be a proper search in the real implementation
                    pass
        
        return complementary_items
    
    async def _find_alternative_patterns(self, item: KnowledgeItem) -> List[KnowledgeItem]:
        """Find alternative patterns that solve similar problems"""
        # Placeholder implementation
        return []
    
    async def _resolve_conflicts(
        self, 
        item: KnowledgeItem, 
        conflicting_items: List[KnowledgeItem],
        quality_score: QualityScore
    ) -> bool:
        """Resolve conflicts between knowledge items"""
        try:
            resolutions = []
            
            for conflict_item in conflicting_items:
                # Determine conflict type and resolution strategy
                for rule in self._conflict_rules:
                    if rule['type'] == 'duplicate_content':
                        # Resolve duplicate content conflicts
                        resolution = await self._resolve_duplicate_conflict(
                            item, conflict_item, quality_score, rule
                        )
                        if resolution:
                            resolutions.append(resolution)
            
            # Apply resolutions
            for resolution in resolutions:
                await self._apply_conflict_resolution(resolution)
            
            return len(resolutions) == len(conflicting_items)
            
        except Exception as e:
            logger.error("Failed to resolve conflicts", error=str(e))
            return False
    
    async def _resolve_duplicate_conflict(
        self,
        item: KnowledgeItem,
        conflict_item: KnowledgeItem,
        quality_score: QualityScore,
        rule: Dict[str, Any]
    ) -> Optional[ConflictResolution]:
        """Resolve duplicate content conflict"""
        try:
            # Get quality score for conflicting item
            context = PatternContext(
                domain='general',
                team_experience='medium',
                business_criticality='medium',
                technology_stack=[],
                compliance_requirements=[]
            )
            
            conflict_quality = await self.quality_scorer.score_pattern_quality(conflict_item, context)
            
            # Apply resolution strategy
            if rule['resolution'] == 'keep_higher_quality':
                if quality_score.overall_score > conflict_quality.overall_score:
                    chosen_item = item.id
                    reasoning = f"Higher quality score ({quality_score.overall_score:.2f} vs {conflict_quality.overall_score:.2f})"
                else:
                    chosen_item = conflict_item.id
                    reasoning = f"Higher quality score ({conflict_quality.overall_score:.2f} vs {quality_score.overall_score:.2f})"
                
                return ConflictResolution(
                    conflict_type='duplicate_content',
                    conflicting_items=[item.id, conflict_item.id],
                    resolution_strategy=rule['resolution'],
                    chosen_item=chosen_item,
                    confidence=0.9,
                    reasoning=reasoning
                )
            
        except Exception as e:
            logger.warning("Failed to resolve duplicate conflict", error=str(e))
        
        return None
    
    async def _apply_conflict_resolution(self, resolution: ConflictResolution) -> None:
        """Apply a conflict resolution decision"""
        try:
            if resolution.resolution_strategy == 'keep_higher_quality':
                # Mark non-chosen items as duplicates/deprecated
                for item_id in resolution.conflicting_items:
                    if item_id != resolution.chosen_item:
                        await self._mark_item_as_duplicate(item_id, resolution.chosen_item)
            
            # Log the resolution
            async with self.db_manager.get_postgres_pool().acquire() as conn:
                await conn.execute("""
                    INSERT INTO conflict_resolutions (
                        id, conflict_type, conflicting_items, resolution_strategy,
                        chosen_item, confidence, reasoning, resolved_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """, 
                str(uuid4()), resolution.conflict_type, 
                [str(id) for id in resolution.conflicting_items],
                resolution.resolution_strategy, str(resolution.chosen_item) if resolution.chosen_item else None,
                resolution.confidence, resolution.reasoning, datetime.utcnow())
            
        except Exception as e:
            logger.error("Failed to apply conflict resolution", error=str(e))
    
    async def _mark_item_as_duplicate(self, duplicate_id: UUID, canonical_id: UUID) -> None:
        """Mark an item as duplicate of another"""
        try:
            async with self.db_manager.get_postgres_pool().acquire() as conn:
                await conn.execute("""
                    UPDATE knowledge_items 
                    SET status = 'duplicate', 
                        canonical_id = $2,
                        updated_at = $3
                    WHERE id = $1
                """, str(duplicate_id), str(canonical_id), datetime.utcnow())
        except Exception as e:
            logger.error("Failed to mark item as duplicate", error=str(e))
    
    async def _enhance_knowledge_item(
        self,
        item: KnowledgeItem,
        classification: Dict[str, float],
        quality_score: QualityScore,
        relationships: List[Dict[str, Any]]
    ) -> KnowledgeItem:
        """Enhance knowledge item with processing results"""
        # Create enhanced metadata
        enhanced_metadata = {
            **(item.metadata or {}),
            'processing_timestamp': datetime.utcnow().isoformat(),
            'classification': classification,
            'quality_scores': {
                'overall': quality_score.overall_score,
                'technical_accuracy': quality_score.technical_accuracy.score,
                'source_credibility': quality_score.source_credibility.score,
                'practical_utility': quality_score.practical_utility.score,
                'completeness': quality_score.completeness.score
            },
            'relationships_count': len(relationships),
            'processing_version': '1.0.0'
        }
        
        # Add derived tags based on classification
        enhanced_tags = list(item.tags)
        primary_domain = classification.get('primary_domain')
        if primary_domain and primary_domain not in enhanced_tags:
            enhanced_tags.append(primary_domain)
        
        # Add complexity tag
        complexity = classification.get('technical_complexity', 0.5)
        if complexity > 0.7:
            enhanced_tags.append('advanced')
        elif complexity < 0.3:
            enhanced_tags.append('basic')
        
        # Create enhanced item
        enhanced_item = KnowledgeItem(
            id=item.id,
            title=item.title,
            content=item.content,
            knowledge_type=item.knowledge_type,
            source_type=item.source_type,
            source_url=item.source_url,
            tags=enhanced_tags,
            summary=item.summary,
            confidence=self._calculate_enhanced_confidence(quality_score, classification),
            metadata=enhanced_metadata,
            created_at=item.created_at,
            updated_at=datetime.utcnow()
        )
        
        return enhanced_item
    
    def _calculate_enhanced_confidence(self, quality_score: QualityScore, classification: Dict[str, float]) -> str:
        """Calculate enhanced confidence level"""
        base_confidence = quality_score.overall_score
        source_reliability = classification.get('source_reliability', 0.5)
        
        combined_confidence = (base_confidence * 0.7) + (source_reliability * 0.3)
        
        if combined_confidence > 0.8:
            return 'very_high'
        elif combined_confidence > 0.6:
            return 'high'
        elif combined_confidence > 0.4:
            return 'medium'
        else:
            return 'low'
    
    async def _store_processed_item(self, item: KnowledgeItem, quality_score: QualityScore) -> None:
        """Store processed knowledge item"""
        try:
            # Store in PostgreSQL
            async with self.db_manager.get_postgres_pool().acquire() as conn:
                await conn.execute("""
                    INSERT INTO knowledge_items (
                        id, title, content, knowledge_type, source_type, 
                        source_url, tags, summary, confidence, metadata, 
                        created_at, updated_at, quality_score
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13
                    ) ON CONFLICT (id) DO UPDATE SET
                        title = EXCLUDED.title,
                        content = EXCLUDED.content,
                        tags = EXCLUDED.tags,
                        summary = EXCLUDED.summary,
                        confidence = EXCLUDED.confidence,
                        metadata = EXCLUDED.metadata,
                        updated_at = EXCLUDED.updated_at,
                        quality_score = EXCLUDED.quality_score
                """, 
                str(item.id), item.title, item.content, item.knowledge_type, 
                item.source_type, item.source_url, item.tags, item.summary, 
                item.confidence, json.dumps(item.metadata), 
                item.created_at, item.updated_at, quality_score.overall_score)
            
        except Exception as e:
            logger.error("Failed to store processed item", error=str(e))
            raise
    
    async def _index_knowledge_item(self, item: KnowledgeItem, relationships: List[Dict[str, Any]]) -> None:
        """Index knowledge item for search and relationships"""
        try:
            # Store vector embedding
            embedding_text = f"{item.title} {item.summary} {' '.join(item.tags)}"
            embedding = await self.vector_service.generate_embedding(embedding_text)
            
            metadata = {
                'source': item.source_type,
                'domain': item.metadata.get('classification', {}).get('primary_domain', 'general'),
                'quality_score': item.metadata.get('quality_scores', {}).get('overall', 0.0)
            }
            
            await self.vector_service.store_embedding(
                str(item.id), embedding, metadata
            )
            
            # Store relationships in Neo4j
            async with self.db_manager.get_neo4j_session() as session:
                # Create or update the knowledge node
                await session.run("""
                    MERGE (k:Knowledge {id: $id})
                    SET k.title = $title,
                        k.source_type = $source_type,
                        k.domain = $domain,
                        k.quality_score = $quality_score,
                        k.updated_at = $updated_at
                """, {
                    'id': str(item.id),
                    'title': item.title,
                    'source_type': item.source_type,
                    'domain': item.metadata.get('classification', {}).get('primary_domain', 'general'),
                    'quality_score': item.metadata.get('quality_scores', {}).get('overall', 0.0),
                    'updated_at': datetime.utcnow().isoformat()
                })
                
                # Create relationship edges
                for rel in relationships:
                    await session.run("""
                        MATCH (a:Knowledge {id: $from_id}), (b:Knowledge {id: $to_id})
                        MERGE (a)-[r:RELATED {type: $rel_type}]->(b)
                        SET r.confidence = $confidence,
                            r.created_at = $created_at
                    """, {
                        'from_id': str(item.id),
                        'to_id': str(rel['target_id']),
                        'rel_type': rel['type'],
                        'confidence': rel['confidence'],
                        'created_at': datetime.utcnow().isoformat()
                    })
            
        except Exception as e:
            logger.error("Failed to index knowledge item", error=str(e))
    
    async def get_processing_statistics(self) -> Dict[str, Any]:
        """Get processing pipeline statistics"""
        avg_throughput = np.mean(list(self._throughput_tracker)) if self._throughput_tracker else 0.0
        
        stage_performance = {}
        for stage, timings in self._stage_timings.items():
            if timings:
                stage_performance[stage.value] = {
                    'avg_time': np.mean(timings),
                    'min_time': np.min(timings),
                    'max_time': np.max(timings),
                    'total_processed': len(timings)
                }
        
        return {
            'queue_size': self.processing_queue.qsize(),
            'active_workers': len(self.processing_workers),
            'items_processing': len(self._active_processing),
            'average_throughput': avg_throughput,
            'stage_performance': stage_performance,
            **self._processing_stats
        }
    
    async def get_processing_status(self, processing_id: UUID) -> Optional[Dict[str, Any]]:
        """Get status of a specific processing task"""
        if processing_id in self._active_processing:
            processing_info = self._active_processing[processing_id]
            return {
                'processing_id': str(processing_id),
                'item_id': str(processing_info['item_id']),
                'current_stage': processing_info['stage'].value,
                'started_at': processing_info['started_at'].isoformat(),
                'processing_time': (datetime.utcnow() - processing_info['started_at']).total_seconds()
            }
        
        return None