# ABOUTME: Advanced Pattern Intelligence Engine for BETTY's Pattern Intelligence System
# ABOUTME: Semantic relationship detection, pattern generalization, and intelligent recommendations

import asyncio
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple, Set
from uuid import UUID, uuid4
import structlog
from collections import defaultdict, Counter
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import PCA
import networkx as nx

from core.database import DatabaseManager
from models.pattern_quality import (
    SemanticRelationship, PatternRecommendation, SuccessPrediction,
    PatternContext, QualityScore, SuccessProbability
)
from models.knowledge import KnowledgeItem
from services.vector_service import VectorService
from services.pattern_quality_service import AdvancedQualityScorer

logger = structlog.get_logger(__name__)

class PatternIntelligenceEngine:
    """
    Advanced Pattern Intelligence Engine with semantic analysis,
    relationship detection, and intelligent recommendations
    """
    
    def __init__(
        self, 
        db_manager: DatabaseManager, 
        vector_service: VectorService,
        quality_scorer: AdvancedQualityScorer
    ):
        self.db_manager = db_manager
        self.vector_service = vector_service
        self.quality_scorer = quality_scorer
        
        # Intelligence caches
        self._relationship_cache = {}
        self._pattern_clusters = {}
        self._recommendation_cache = {}
        
        # Graph for pattern relationships
        self._pattern_graph = nx.Graph()
        self._graph_last_updated = None
        
        # ML models for intelligence
        self._clustering_model = None
        self._similarity_threshold = 0.75
        self._last_model_training = None
        
    async def detect_semantic_relationships(
        self, 
        patterns: List[KnowledgeItem],
        min_similarity: float = 0.7
    ) -> List[SemanticRelationship]:
        """
        Detect semantic relationships between patterns using advanced NLP and vector analysis
        
        Args:
            patterns: List of patterns to analyze
            min_similarity: Minimum similarity threshold for relationships
            
        Returns:
            List of discovered semantic relationships
        """
        logger.info("Detecting semantic relationships", 
                   pattern_count=len(patterns), 
                   min_similarity=min_similarity)
        
        relationships = []
        
        try:
            # Generate embeddings for all patterns
            embeddings_map = {}
            for pattern in patterns:
                embedding = await self.vector_service.generate_embedding(
                    f"{pattern.title} {pattern.content}"
                )
                embeddings_map[pattern.id] = embedding
            
            # Calculate pairwise similarities
            pattern_ids = list(embeddings_map.keys())
            embeddings_matrix = np.array([embeddings_map[pid] for pid in pattern_ids])
            
            # Compute cosine similarity matrix
            similarity_matrix = cosine_similarity(embeddings_matrix)
            
            # Detect relationships based on similarity scores
            for i, pattern_1 in enumerate(patterns):
                for j, pattern_2 in enumerate(patterns):
                    if i >= j:  # Avoid duplicate pairs and self-comparison
                        continue
                    
                    similarity_score = similarity_matrix[i][j]
                    
                    if similarity_score >= min_similarity:
                        # Determine relationship type
                        relationship_type = await self._classify_relationship_type(
                            pattern_1, pattern_2, similarity_score
                        )
                        
                        # Generate evidence for the relationship
                        evidence = await self._generate_relationship_evidence(
                            pattern_1, pattern_2, relationship_type, similarity_score
                        )
                        
                        relationship = SemanticRelationship(
                            from_pattern_id=pattern_1.id,
                            to_pattern_id=pattern_2.id,
                            relationship_type=relationship_type,
                            strength=similarity_score,
                            evidence=evidence,
                            discovered_at=datetime.utcnow()
                        )
                        
                        relationships.append(relationship)
            
            # Store relationships in database
            await self._store_semantic_relationships(relationships)
            
            # Update pattern graph
            await self._update_pattern_graph(relationships)
            
            logger.info("Semantic relationship detection completed", 
                       relationships_found=len(relationships))
            
            return relationships
            
        except Exception as e:
            logger.error("Failed to detect semantic relationships", error=str(e))
            raise
    
    async def generalize_patterns(
        self, 
        similar_patterns: List[KnowledgeItem],
        context: PatternContext
    ) -> KnowledgeItem:
        """
        Generalize similar patterns into a higher-level pattern
        
        Args:
            similar_patterns: List of similar patterns to generalize
            context: Context for the generalization
            
        Returns:
            Generalized pattern
        """
        logger.info("Generalizing patterns", 
                   pattern_count=len(similar_patterns),
                   context_domain=context.domain)
        
        try:
            # Extract common elements
            common_concepts = await self._extract_common_concepts(similar_patterns)
            common_code_patterns = await self._extract_common_code_patterns(similar_patterns)
            common_tags = self._extract_common_tags(similar_patterns)
            
            # Generate generalized title and content
            generalized_title = await self._generate_generalized_title(
                similar_patterns, common_concepts
            )
            
            generalized_content = await self._generate_generalized_content(
                similar_patterns, common_concepts, common_code_patterns
            )
            
            # Create generalized pattern
            generalized_pattern = KnowledgeItem(
                id=uuid4(),
                title=generalized_title,
                content=generalized_content,
                knowledge_type="pattern",  # Assuming this is a pattern type
                source_type="generated",
                tags=common_tags,
                summary=f"Generalized pattern from {len(similar_patterns)} similar patterns",
                confidence="high",
                metadata={
                    "generalization_source_count": len(similar_patterns),
                    "source_patterns": [str(p.id) for p in similar_patterns],
                    "generalization_context": context.dict(),
                    "common_concepts": common_concepts,
                    "generalization_timestamp": datetime.utcnow().isoformat()
                }
            )
            
            # Score the generalized pattern
            quality_score = await self.quality_scorer.score_pattern_quality(
                generalized_pattern, context
            )
            
            logger.info("Pattern generalization completed",
                       generalized_pattern_id=str(generalized_pattern.id),
                       quality_score=quality_score.overall_score)
            
            return generalized_pattern
            
        except Exception as e:
            logger.error("Failed to generalize patterns", error=str(e))
            raise
    
    async def predict_pattern_success(
        self, 
        pattern: KnowledgeItem, 
        context: PatternContext
    ) -> SuccessPrediction:
        """
        Predict pattern success probability using ML models and historical data
        
        Args:
            pattern: Pattern to analyze
            context: Application context
            
        Returns:
            Success prediction with confidence scores
        """
        logger.info("Predicting pattern success", 
                   pattern_id=str(pattern.id),
                   context_domain=context.domain)
        
        try:
            # Get quality score first
            quality_score = await self.quality_scorer.score_pattern_quality(pattern, context)
            
            # Analyze similar historical patterns
            similar_outcomes = await self._analyze_similar_pattern_outcomes(pattern, context)
            
            # Generate feature vector for prediction
            features = await self._generate_prediction_features(pattern, context, quality_score)
            
            # Calculate success probability using multiple approaches
            ml_prediction = await self._ml_success_prediction(features)
            similarity_prediction = await self._similarity_based_prediction(similar_outcomes)
            rule_based_prediction = await self._rule_based_prediction(pattern, context, quality_score)
            
            # Ensemble prediction (weighted average)
            final_probability = (
                ml_prediction * 0.4 + 
                similarity_prediction * 0.4 + 
                rule_based_prediction * 0.2
            )
            
            # Map probability to enum
            success_prob = self._probability_to_enum(final_probability)
            
            # Identify success and risk factors
            positive_factors = await self._identify_positive_factors(pattern, context, quality_score)
            negative_factors = await self._identify_negative_factors(pattern, context, quality_score)
            risk_mitigations = await self._suggest_risk_mitigations(negative_factors, context)
            
            # Calculate confidence score
            confidence = await self._calculate_prediction_confidence(
                ml_prediction, similarity_prediction, rule_based_prediction, similar_outcomes
            )
            
            prediction = SuccessPrediction(
                pattern_id=pattern.id,
                context=context,
                success_probability=success_prob,
                success_percentage=final_probability * 100,
                confidence_score=confidence,
                positive_factors=positive_factors,
                negative_factors=negative_factors,
                risk_mitigation_suggestions=risk_mitigations,
                similar_patterns_outcomes=similar_outcomes,
                success_rate_trend=await self._calculate_success_trend(pattern, context),
                model_version="1.0.0",
                prediction_timestamp=datetime.utcnow()
            )
            
            logger.info("Pattern success prediction completed",
                       pattern_id=str(pattern.id),
                       success_probability=success_prob.value,
                       confidence=confidence)
            
            return prediction
            
        except Exception as e:
            logger.error("Failed to predict pattern success", 
                        pattern_id=str(pattern.id), 
                        error=str(e))
            raise
    
    async def recommend_patterns(
        self, 
        query: str, 
        context: PatternContext,
        limit: int = 10
    ) -> List[PatternRecommendation]:
        """
        Recommend patterns based on query and context using intelligent ranking
        
        Args:
            query: Search query or problem description
            context: Application context
            limit: Maximum number of recommendations
            
        Returns:
            List of pattern recommendations ranked by relevance and quality
        """
        logger.info("Generating pattern recommendations", 
                   query_length=len(query),
                   context_domain=context.domain,
                   limit=limit)
        
        try:
            # Search for relevant patterns
            search_results = await self._semantic_pattern_search(query, context)
            
            # Generate recommendations with comprehensive scoring
            recommendations = []
            
            for pattern in search_results[:limit * 2]:  # Get more candidates for better ranking
                # Calculate relevance score
                relevance_score = await self._calculate_relevance_score(
                    pattern, query, context
                )
                
                # Get quality score
                quality_score = await self.quality_scorer.score_pattern_quality(pattern, context)
                
                # Get success prediction
                success_prediction = await self.predict_pattern_success(pattern, context)
                
                # Generate recommendation reason
                recommendation_reason = await self._generate_recommendation_reason(
                    pattern, query, context, relevance_score, quality_score
                )
                
                # Generate implementation notes
                implementation_notes = await self._generate_implementation_notes(
                    pattern, context
                )
                
                # Find alternative patterns
                alternatives = await self._find_alternative_patterns(pattern, context)
                
                recommendation = PatternRecommendation(
                    pattern_id=pattern.id,
                    pattern_title=pattern.title,
                    pattern_summary=pattern.summary or pattern.content[:200] + "...",
                    quality_score=quality_score,
                    relevance_score=relevance_score,
                    recommendation_reason=recommendation_reason,
                    implementation_notes=implementation_notes,
                    alternative_patterns=[alt.id for alt in alternatives]
                )
                
                recommendations.append(recommendation)
            
            # Rank recommendations by composite score
            recommendations = await self._rank_recommendations(recommendations, context)
            
            # Return top recommendations
            final_recommendations = recommendations[:limit]
            
            logger.info("Pattern recommendations generated", 
                       recommendations_count=len(final_recommendations))
            
            return final_recommendations
            
        except Exception as e:
            logger.error("Failed to generate pattern recommendations", error=str(e))
            raise
    
    # Helper methods for relationship detection
    async def _classify_relationship_type(
        self, 
        pattern_1: KnowledgeItem, 
        pattern_2: KnowledgeItem, 
        similarity_score: float
    ) -> str:
        """Classify the type of relationship between two patterns"""
        
        # Analyze content overlap and differences
        title_similarity = await self._calculate_text_similarity(pattern_1.title, pattern_2.title)
        content_similarity = await self._calculate_text_similarity(pattern_1.content, pattern_2.content)
        
        # Check for code similarity
        code_similarity = await self._calculate_code_similarity(pattern_1.content, pattern_2.content)
        
        # Determine relationship type based on various factors
        if similarity_score > 0.9 and title_similarity > 0.8:
            return "duplicate"
        elif code_similarity > 0.8:
            return "implementation_variant"
        elif similarity_score > 0.8:
            return "very_similar"
        elif self._are_complementary_patterns(pattern_1, pattern_2):
            return "complementary"
        elif self._are_alternative_patterns(pattern_1, pattern_2):
            return "alternative"
        elif content_similarity > 0.6:
            return "related"
        else:
            return "similar"
    
    async def _generate_relationship_evidence(
        self, 
        pattern_1: KnowledgeItem, 
        pattern_2: KnowledgeItem, 
        relationship_type: str, 
        similarity_score: float
    ) -> List[str]:
        """Generate evidence supporting the relationship"""
        evidence = []
        
        evidence.append(f"Semantic similarity score: {similarity_score:.3f}")
        
        # Check for shared concepts
        shared_concepts = await self._find_shared_concepts(pattern_1, pattern_2)
        if shared_concepts:
            evidence.append(f"Shared concepts: {', '.join(shared_concepts[:3])}")
        
        # Check for shared tags
        shared_tags = set(pattern_1.tags) & set(pattern_2.tags)
        if shared_tags:
            evidence.append(f"Shared tags: {', '.join(list(shared_tags)[:3])}")
        
        # Check for similar code patterns
        if relationship_type == "implementation_variant":
            evidence.append("Similar code implementation patterns detected")
        
        return evidence
    
    # Helper methods for pattern generalization
    async def _extract_common_concepts(self, patterns: List[KnowledgeItem]) -> List[str]:
        """Extract common concepts across patterns"""
        # This would use NLP to extract key concepts
        # For now, simplified implementation
        all_words = []
        for pattern in patterns:
            words = pattern.content.lower().split()
            all_words.extend(words)
        
        # Get most common words (excluding stop words)
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were'}
        word_counts = Counter(word for word in all_words if len(word) > 3 and word not in stop_words)
        
        return [word for word, count in word_counts.most_common(10)]
    
    async def _extract_common_code_patterns(self, patterns: List[KnowledgeItem]) -> List[str]:
        """Extract common code patterns"""
        # Extract code blocks and find common patterns
        import re
        
        all_code_blocks = []
        for pattern in patterns:
            code_blocks = re.findall(r'```[\w]*\n(.*?)```', pattern.content, re.DOTALL)
            all_code_blocks.extend(code_blocks)
        
        # Simplified: return common lines
        if not all_code_blocks:
            return []
        
        # Find lines that appear in multiple code blocks
        line_counts = Counter()
        for code_block in all_code_blocks:
            lines = [line.strip() for line in code_block.split('\n') if line.strip()]
            for line in lines:
                line_counts[line] += 1
        
        common_patterns = [line for line, count in line_counts.most_common(5) if count > 1]
        return common_patterns
    
    def _extract_common_tags(self, patterns: List[KnowledgeItem]) -> List[str]:
        """Extract common tags across patterns"""
        tag_counts = Counter()
        for pattern in patterns:
            for tag in pattern.tags:
                tag_counts[tag] += 1
        
        # Return tags that appear in at least half the patterns
        min_count = len(patterns) // 2
        return [tag for tag, count in tag_counts.items() if count >= min_count]
    
    # Helper methods for success prediction
    async def _generate_prediction_features(
        self, 
        pattern: KnowledgeItem, 
        context: PatternContext, 
        quality_score: QualityScore
    ) -> List[float]:
        """Generate feature vector for ML prediction"""
        features = []
        
        # Quality score features
        features.append(quality_score.overall_score)
        features.append(quality_score.technical_accuracy.score)
        features.append(quality_score.source_credibility.score)
        features.append(quality_score.practical_utility.score)
        features.append(quality_score.completeness.score)
        
        # Context features
        features.append(self._encode_team_experience(context.team_experience))
        features.append(self._encode_business_criticality(context.business_criticality))
        features.append(len(context.technology_stack))
        features.append(len(context.compliance_requirements))
        
        # Pattern features
        features.append(len(pattern.content))
        features.append(len(pattern.tags))
        features.append(pattern.access_count or 0)
        features.append(self._days_since_creation(pattern.created_at))
        
        return features
    
    def _encode_team_experience(self, experience: str) -> float:
        """Encode team experience as numeric value"""
        mapping = {"low": 0.2, "medium": 0.5, "high": 0.8}
        return mapping.get(experience, 0.5)
    
    def _encode_business_criticality(self, criticality: str) -> float:
        """Encode business criticality as numeric value"""
        mapping = {"low": 0.2, "medium": 0.5, "high": 0.8}
        return mapping.get(criticality, 0.5)
    
    def _days_since_creation(self, created_at: datetime) -> float:
        """Calculate days since pattern creation"""
        return (datetime.utcnow() - created_at).days
    
    def _probability_to_enum(self, probability: float) -> SuccessProbability:
        """Convert probability float to enum"""
        if probability >= 0.8:
            return SuccessProbability.VERY_HIGH
        elif probability >= 0.6:
            return SuccessProbability.HIGH
        elif probability >= 0.4:
            return SuccessProbability.MEDIUM
        elif probability >= 0.2:
            return SuccessProbability.LOW
        else:
            return SuccessProbability.VERY_LOW
    
    # Database integration methods
    async def _store_semantic_relationships(self, relationships: List[SemanticRelationship]) -> None:
        """Store semantic relationships in Neo4j"""
        async with self.db_manager.get_neo4j_session() as session:
            for rel in relationships:
                query = """
                MATCH (a:Pattern {id: $from_id}), (b:Pattern {id: $to_id})
                MERGE (a)-[r:SEMANTIC_RELATIONSHIP {type: $rel_type}]->(b)
                SET r.strength = $strength,
                    r.evidence = $evidence,
                    r.discovered_at = $discovered_at
                """
                await session.run(query, {
                    'from_id': str(rel.from_pattern_id),
                    'to_id': str(rel.to_pattern_id),
                    'rel_type': rel.relationship_type,
                    'strength': rel.strength,
                    'evidence': rel.evidence,
                    'discovered_at': rel.discovered_at.isoformat()
                })
    
    async def _update_pattern_graph(self, relationships: List[SemanticRelationship]) -> None:
        """Update in-memory pattern graph"""
        for rel in relationships:
            self._pattern_graph.add_edge(
                str(rel.from_pattern_id),
                str(rel.to_pattern_id),
                weight=rel.strength,
                relationship_type=rel.relationship_type
            )
        
        self._graph_last_updated = datetime.utcnow()
    
    # Placeholder implementations for complex methods
    async def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between texts"""
        # Would use advanced NLP models like BERT
        return 0.5  # Placeholder
    
    async def _calculate_code_similarity(self, content1: str, content2: str) -> float:
        """Calculate code similarity using AST analysis"""
        # Would use AST comparison and code structure analysis
        return 0.5  # Placeholder
    
    def _are_complementary_patterns(self, p1: KnowledgeItem, p2: KnowledgeItem) -> bool:
        """Check if patterns are complementary"""
        # Would analyze if patterns work together
        return False  # Placeholder
    
    def _are_alternative_patterns(self, p1: KnowledgeItem, p2: KnowledgeItem) -> bool:
        """Check if patterns are alternatives to each other"""
        # Would analyze if patterns solve the same problem differently
        return False  # Placeholder
    
    async def _find_shared_concepts(self, p1: KnowledgeItem, p2: KnowledgeItem) -> List[str]:
        """Find shared concepts between patterns"""
        # Would use NLP concept extraction
        return []  # Placeholder
    
    # Additional placeholder methods for full implementation...
    async def _semantic_pattern_search(self, query: str, context: PatternContext) -> List[KnowledgeItem]:
        """Perform semantic search for patterns"""
        # Would use vector search
        return []  # Placeholder
    
    async def _calculate_relevance_score(self, pattern: KnowledgeItem, query: str, context: PatternContext) -> float:
        """Calculate pattern relevance to query and context"""
        return 0.7  # Placeholder
    
    async def _ml_success_prediction(self, features: List[float]) -> float:
        """ML-based success prediction"""
        return 0.6  # Placeholder
    
    async def _similarity_based_prediction(self, similar_outcomes: List[Dict[str, Any]]) -> float:
        """Similarity-based success prediction"""
        return 0.7  # Placeholder
    
    async def _rule_based_prediction(self, pattern: KnowledgeItem, context: PatternContext, quality_score: QualityScore) -> float:
        """Rule-based success prediction"""
        return quality_score.overall_score  # Use quality score as base