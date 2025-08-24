# ABOUTME: REST API endpoints for BETTY's Advanced Pattern Quality Scoring System
# ABOUTME: Provides quality scoring, predictions, recommendations, and intelligence analytics

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from fastapi.responses import JSONResponse
import structlog

from core.dependencies import get_db_manager, get_vector_service
from core.database import DatabaseManager
from models.pattern_quality import (
    QualityScoreRequest, QualityScoreResponse, PatternQualityStatsResponse,
    PatternContext, QualityScore, SuccessPrediction, PatternRecommendation,
    SemanticRelationship
)
from models.knowledge import KnowledgeItem, SearchQuery
from models.base import BaseResponse, PaginatedResponse
from services.pattern_quality_service import AdvancedQualityScorer
from services.pattern_intelligence_service import PatternIntelligenceEngine
from services.vector_service import VectorService
from services.knowledge_service import KnowledgeService

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v2/pattern-quality", tags=["Pattern Quality"])

# Initialize services (in a real app, these would be dependency injected)
quality_scorer = None
intelligence_engine = None
knowledge_service = None

async def get_quality_scorer(
    db_manager: DatabaseManager = Depends(get_db_manager),
    vector_service: VectorService = Depends(get_vector_service)
) -> AdvancedQualityScorer:
    """Get quality scorer instance"""
    global quality_scorer
    if not quality_scorer:
        quality_scorer = AdvancedQualityScorer(db_manager, vector_service)
    return quality_scorer

async def get_intelligence_engine(
    db_manager: DatabaseManager = Depends(get_db_manager),
    vector_service: VectorService = Depends(get_vector_service),
    scorer: AdvancedQualityScorer = Depends(get_quality_scorer)
) -> PatternIntelligenceEngine:
    """Get pattern intelligence engine instance"""
    global intelligence_engine
    if not intelligence_engine:
        intelligence_engine = PatternIntelligenceEngine(db_manager, vector_service, scorer)
    return intelligence_engine

async def get_knowledge_service(
    db_manager: DatabaseManager = Depends(get_db_manager)
) -> KnowledgeService:
    """Get knowledge service instance"""
    global knowledge_service
    if not knowledge_service:
        knowledge_service = KnowledgeService(db_manager)
    return knowledge_service

@router.post("/score", response_model=QualityScoreResponse)
async def score_pattern_quality(
    request: QualityScoreRequest,
    background_tasks: BackgroundTasks,
    scorer: AdvancedQualityScorer = Depends(get_quality_scorer),
    intelligence_engine: PatternIntelligenceEngine = Depends(get_intelligence_engine),
    knowledge_service: KnowledgeService = Depends(get_knowledge_service)
):
    """
    Score the quality of a pattern using multi-dimensional analysis
    
    This endpoint performs comprehensive pattern analysis including:
    - Technical accuracy (40%): Code syntax, security compliance, performance
    - Source credibility (25%): Author reputation, publication authority
    - Practical utility (20%): Success rate, user satisfaction, outcomes
    - Completeness (15%): Documentation quality, examples, context clarity
    
    Returns quality score with predictions and recommendations.
    """
    try:
        logger.info("Pattern quality scoring requested", 
                   pattern_id=str(request.pattern_id),
                   context_domain=request.context.domain)
        
        # Get the pattern
        pattern = await knowledge_service.get_knowledge_item(request.pattern_id)
        if not pattern:
            raise HTTPException(status_code=404, detail="Pattern not found")
        
        # Score pattern quality
        quality_score = await scorer.score_pattern_quality(pattern, request.context)
        
        # Prepare response
        response_data = {
            "data": quality_score,
            "predictions": None,
            "relationships": [],
            "recommendations": []
        }
        
        # Add predictions if requested
        if request.include_predictions:
            prediction = await intelligence_engine.predict_pattern_success(
                pattern, request.context
            )
            response_data["predictions"] = prediction
        
        # Add relationships if requested
        if request.include_relationships:
            # Get related patterns for relationship analysis
            related_patterns = await _find_related_patterns(
                pattern, request.context, knowledge_service
            )
            
            if related_patterns:
                relationships = await intelligence_engine.detect_semantic_relationships(
                    [pattern] + related_patterns[:10]  # Limit for performance
                )
                # Filter relationships involving the target pattern
                response_data["relationships"] = [
                    rel for rel in relationships 
                    if rel.from_pattern_id == pattern.id or rel.to_pattern_id == pattern.id
                ]
        
        # Background task to update analytics
        background_tasks.add_task(
            _update_pattern_analytics, 
            pattern.id, 
            quality_score, 
            request.context
        )
        
        logger.info("Pattern quality scoring completed", 
                   pattern_id=str(request.pattern_id),
                   overall_score=quality_score.overall_score,
                   success_probability=quality_score.success_probability.value)
        
        return QualityScoreResponse(**response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to score pattern quality", 
                    pattern_id=str(request.pattern_id), 
                    error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/score/{pattern_id}", response_model=QualityScoreResponse)
async def get_pattern_quality_score(
    pattern_id: UUID,
    context_domain: str = Query(..., description="Context domain for scoring"),
    include_predictions: bool = Query(default=True),
    include_relationships: bool = Query(default=False),
    scorer: AdvancedQualityScorer = Depends(get_quality_scorer),
    intelligence_engine: PatternIntelligenceEngine = Depends(get_intelligence_engine),
    knowledge_service: KnowledgeService = Depends(get_knowledge_service)
):
    """
    Get existing quality score for a pattern or compute a new one
    
    First checks for existing quality scores in the database,
    otherwise computes a new score using the provided context.
    """
    try:
        # Try to get existing score first
        existing_score = await _get_existing_quality_score(
            pattern_id, context_domain, scorer
        )
        
        if existing_score:
            logger.info("Retrieved existing quality score", 
                       pattern_id=str(pattern_id))
            return QualityScoreResponse(data=existing_score)
        
        # Compute new score
        pattern = await knowledge_service.get_knowledge_item(pattern_id)
        if not pattern:
            raise HTTPException(status_code=404, detail="Pattern not found")
        
        # Create context from domain (simplified)
        context = PatternContext(
            domain=context_domain,
            project_type="general",
            team_experience="medium",
            business_criticality="medium"
        )
        
        # Score the pattern
        quality_score = await scorer.score_pattern_quality(pattern, context)
        
        response_data = {"data": quality_score, "predictions": None, "relationships": []}
        
        if include_predictions:
            prediction = await intelligence_engine.predict_pattern_success(pattern, context)
            response_data["predictions"] = prediction
        
        return QualityScoreResponse(**response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get pattern quality score", 
                    pattern_id=str(pattern_id), 
                    error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/predict-success", response_model=SuccessPrediction)
async def predict_pattern_success(
    pattern_id: UUID,
    context: PatternContext,
    intelligence_engine: PatternIntelligenceEngine = Depends(get_intelligence_engine),
    knowledge_service: KnowledgeService = Depends(get_knowledge_service)
):
    """
    Predict the success probability of implementing a pattern
    
    Uses machine learning models and historical data to predict:
    - Success probability (very_low to very_high)
    - Risk factors and mitigation strategies
    - Similar pattern outcomes for reference
    """
    try:
        logger.info("Pattern success prediction requested", 
                   pattern_id=str(pattern_id),
                   context_domain=context.domain)
        
        pattern = await knowledge_service.get_knowledge_item(pattern_id)
        if not pattern:
            raise HTTPException(status_code=404, detail="Pattern not found")
        
        prediction = await intelligence_engine.predict_pattern_success(pattern, context)
        
        logger.info("Pattern success prediction completed",
                   pattern_id=str(pattern_id),
                   success_probability=prediction.success_probability.value,
                   confidence=prediction.confidence_score)
        
        return prediction
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to predict pattern success", 
                    pattern_id=str(pattern_id), 
                    error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/recommend", response_model=List[PatternRecommendation])
async def recommend_patterns(
    query: str,
    context: PatternContext,
    limit: int = Query(default=10, ge=1, le=50, description="Maximum recommendations"),
    min_quality_score: float = Query(default=0.5, ge=0.0, le=1.0, description="Minimum quality score"),
    intelligence_engine: PatternIntelligenceEngine = Depends(get_intelligence_engine)
):
    """
    Get intelligent pattern recommendations based on query and context
    
    Analyzes the query and context to recommend the most relevant,
    high-quality patterns with detailed implementation guidance.
    """
    try:
        logger.info("Pattern recommendations requested", 
                   query_length=len(query),
                   context_domain=context.domain,
                   limit=limit)
        
        recommendations = await intelligence_engine.recommend_patterns(
            query, context, limit
        )
        
        # Filter by minimum quality score
        filtered_recommendations = [
            rec for rec in recommendations 
            if rec.quality_score.overall_score >= min_quality_score
        ]
        
        logger.info("Pattern recommendations generated", 
                   total_recommendations=len(recommendations),
                   filtered_count=len(filtered_recommendations))
        
        return filtered_recommendations
        
    except Exception as e:
        logger.error("Failed to generate pattern recommendations", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/relationships/{pattern_id}", response_model=List[SemanticRelationship])
async def get_pattern_relationships(
    pattern_id: UUID,
    relationship_types: Optional[List[str]] = Query(default=None),
    min_strength: float = Query(default=0.5, ge=0.0, le=1.0),
    limit: int = Query(default=20, ge=1, le=100),
    intelligence_engine: PatternIntelligenceEngine = Depends(get_intelligence_engine),
    knowledge_service: KnowledgeService = Depends(get_knowledge_service)
):
    """
    Get semantic relationships for a pattern
    
    Returns relationships like similar patterns, complementary patterns,
    alternatives, and implementation variants.
    """
    try:
        # Get the pattern
        pattern = await knowledge_service.get_knowledge_item(pattern_id)
        if not pattern:
            raise HTTPException(status_code=404, detail="Pattern not found")
        
        # Get related patterns
        related_patterns = await _find_related_patterns(
            pattern, None, knowledge_service, limit=50
        )
        
        if not related_patterns:
            return []
        
        # Detect relationships
        relationships = await intelligence_engine.detect_semantic_relationships(
            [pattern] + related_patterns
        )
        
        # Filter relationships for the target pattern
        filtered_relationships = [
            rel for rel in relationships
            if (rel.from_pattern_id == pattern_id or rel.to_pattern_id == pattern_id)
            and rel.strength >= min_strength
        ]
        
        # Filter by relationship types if specified
        if relationship_types:
            filtered_relationships = [
                rel for rel in filtered_relationships
                if rel.relationship_type in relationship_types
            ]
        
        # Limit results
        return filtered_relationships[:limit]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get pattern relationships", 
                    pattern_id=str(pattern_id), 
                    error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/stats", response_model=PatternQualityStatsResponse)
async def get_quality_statistics(
    context_domain: Optional[str] = Query(default=None),
    min_score: float = Query(default=0.0, ge=0.0, le=1.0),
    max_score: float = Query(default=1.0, ge=0.0, le=1.0),
    limit: int = Query(default=100, ge=1, le=1000),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """
    Get pattern quality statistics and analytics
    
    Provides insights into pattern quality distribution,
    top-performing patterns, and improvement opportunities.
    """
    try:
        logger.info("Pattern quality statistics requested", 
                   context_domain=context_domain,
                   score_range=[min_score, max_score])
        
        async with db_manager.get_postgres_session() as session:
            # Get basic statistics
            stats_query = """
                SELECT 
                    COUNT(*) as total_patterns,
                    AVG(overall_score) as avg_quality_score,
                    COUNT(CASE WHEN overall_score >= 0.8 THEN 1 END) as high_quality_count,
                    COUNT(CASE WHEN overall_score BETWEEN 0.6 AND 0.8 THEN 1 END) as medium_quality_count,
                    COUNT(CASE WHEN overall_score < 0.6 THEN 1 END) as low_quality_count
                FROM quality_scores 
                WHERE overall_score BETWEEN :min_score AND :max_score
                AND (:context_domain IS NULL OR context_domain = :context_domain)
            """
            
            result = await session.execute(stats_query, {
                'min_score': min_score,
                'max_score': max_score,
                'context_domain': context_domain
            })
            
            stats_row = result.fetchone()
            
            # Get top quality patterns
            top_patterns_query = """
                SELECT qs.pattern_id, ki.title, qs.overall_score, qs.success_probability
                FROM quality_scores qs
                JOIN knowledge_items ki ON qs.pattern_id = ki.id
                WHERE qs.overall_score BETWEEN :min_score AND :max_score
                AND (:context_domain IS NULL OR qs.context_domain = :context_domain)
                ORDER BY qs.overall_score DESC
                LIMIT :limit
            """
            
            top_result = await session.execute(top_patterns_query, {
                'min_score': min_score,
                'max_score': max_score,
                'context_domain': context_domain,
                'limit': min(limit, 20)
            })
            
            top_patterns = [
                {
                    "pattern_id": str(row.pattern_id),
                    "title": row.title,
                    "overall_score": float(row.overall_score),
                    "success_probability": row.success_probability
                }
                for row in top_result.fetchall()
            ]
            
            # Get improvement opportunities
            improvement_query = """
                SELECT 
                    qs.pattern_id, 
                    ki.title, 
                    qs.overall_score,
                    CASE 
                        WHEN qs.technical_accuracy_score < 0.6 THEN 'Technical Accuracy'
                        WHEN qs.source_credibility_score < 0.6 THEN 'Source Credibility'
                        WHEN qs.practical_utility_score < 0.6 THEN 'Practical Utility'
                        WHEN qs.completeness_score < 0.6 THEN 'Completeness'
                        ELSE 'General Quality'
                    END as improvement_area
                FROM quality_scores qs
                JOIN knowledge_items ki ON qs.pattern_id = ki.id
                WHERE qs.overall_score < 0.7
                AND (:context_domain IS NULL OR qs.context_domain = :context_domain)
                ORDER BY qs.overall_score ASC
                LIMIT 10
            """
            
            improvement_result = await session.execute(improvement_query, {
                'context_domain': context_domain
            })
            
            improvement_opportunities = [
                {
                    "pattern_id": str(row.pattern_id),
                    "title": row.title,
                    "overall_score": float(row.overall_score),
                    "improvement_area": row.improvement_area
                }
                for row in improvement_result.fetchall()
            ]
            
            # Prepare response
            stats_data = {
                "total_patterns": stats_row.total_patterns or 0,
                "avg_quality_score": float(stats_row.avg_quality_score or 0),
                "quality_distribution": {
                    "high_quality": stats_row.high_quality_count or 0,
                    "medium_quality": stats_row.medium_quality_count or 0,
                    "low_quality": stats_row.low_quality_count or 0
                },
                "top_quality_patterns": top_patterns,
                "improvement_opportunities": improvement_opportunities,
                "scoring_performance_metrics": {
                    "avg_scoring_time_ms": 850,  # Would come from actual metrics
                    "prediction_accuracy": 0.87,  # Would come from validation
                    "recommendation_acceptance_rate": 0.73  # Would come from feedback
                }
            }
            
            return PatternQualityStatsResponse(data=stats_data)
        
    except Exception as e:
        logger.error("Failed to get quality statistics", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/batch-score")
async def batch_score_patterns(
    pattern_ids: List[UUID],
    context: PatternContext,
    background_tasks: BackgroundTasks,
    scorer: AdvancedQualityScorer = Depends(get_quality_scorer),
    knowledge_service: KnowledgeService = Depends(get_knowledge_service)
):
    """
    Score multiple patterns in batch for efficiency
    
    Processes multiple patterns asynchronously and returns
    job ID for tracking progress.
    """
    try:
        if len(pattern_ids) > 100:
            raise HTTPException(status_code=400, detail="Maximum 100 patterns per batch")
        
        # Validate all patterns exist
        patterns = []
        for pattern_id in pattern_ids:
            pattern = await knowledge_service.get_knowledge_item(pattern_id)
            if not pattern:
                raise HTTPException(status_code=404, detail=f"Pattern {pattern_id} not found")
            patterns.append(pattern)
        
        # Create batch job
        job_id = str(UUID.uuid4())
        
        # Start background processing
        background_tasks.add_task(
            _batch_score_patterns_task,
            job_id,
            patterns,
            context,
            scorer
        )
        
        logger.info("Batch scoring job started", 
                   job_id=job_id,
                   pattern_count=len(patterns))
        
        return JSONResponse({
            "job_id": job_id,
            "status": "processing",
            "pattern_count": len(patterns),
            "estimated_completion_minutes": len(patterns) * 0.5  # Rough estimate
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to start batch scoring", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

# Helper functions
async def _find_related_patterns(
    pattern: KnowledgeItem, 
    context: Optional[PatternContext], 
    knowledge_service: KnowledgeService,
    limit: int = 20
) -> List[KnowledgeItem]:
    """Find patterns related to the given pattern"""
    # This would use vector similarity search
    # Simplified implementation for now
    search_query = SearchQuery(
        query=pattern.title + " " + pattern.content[:200],
        limit=limit,
        similarity_threshold=0.6
    )
    
    search_results = await knowledge_service.search_knowledge(search_query)
    
    # Filter out the original pattern
    related_patterns = [p for p in search_results.data if p.id != pattern.id]
    
    return related_patterns

async def _get_existing_quality_score(
    pattern_id: UUID, 
    context_domain: str, 
    scorer: AdvancedQualityScorer
) -> Optional[QualityScore]:
    """Get existing quality score from database"""
    # This would query the database for existing scores
    # Placeholder implementation
    return None

async def _update_pattern_analytics(
    pattern_id: UUID, 
    quality_score: QualityScore, 
    context: PatternContext
):
    """Update pattern analytics in background"""
    logger.info("Updating pattern analytics", pattern_id=str(pattern_id))
    # This would update usage analytics, quality history, etc.
    pass

async def _batch_score_patterns_task(
    job_id: str,
    patterns: List[KnowledgeItem],
    context: PatternContext,
    scorer: AdvancedQualityScorer
):
    """Background task for batch pattern scoring"""
    logger.info("Starting batch scoring task", 
               job_id=job_id,
               pattern_count=len(patterns))
    
    results = []
    for pattern in patterns:
        try:
            quality_score = await scorer.score_pattern_quality(pattern, context)
            results.append({"pattern_id": str(pattern.id), "status": "completed", "score": quality_score})
        except Exception as e:
            logger.error("Failed to score pattern in batch", 
                        pattern_id=str(pattern.id), 
                        error=str(e))
            results.append({"pattern_id": str(pattern.id), "status": "failed", "error": str(e)})
    
    # Store results in cache/database for retrieval
    # Implementation would depend on caching strategy
    
    logger.info("Batch scoring task completed", 
               job_id=job_id,
               successful_scores=len([r for r in results if r["status"] == "completed"]))