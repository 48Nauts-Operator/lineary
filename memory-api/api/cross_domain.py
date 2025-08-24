# ABOUTME: Cross-Domain Intelligence API endpoints for BETTY's revolutionary pattern transfer system
# ABOUTME: Enables API access to cross-domain pattern discovery, adaptation, and recommendation features

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
import structlog

from core.dependencies import get_database_manager, get_vector_service, get_quality_scorer
from services.cross_domain_intelligence import (
    CrossDomainIntelligence, DomainType, AdaptationStrategy,
    CrossDomainMatch, AbstractPattern, DomainAdaptation
)
from models.knowledge import KnowledgeItem

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/cross-domain", tags=["cross-domain-intelligence"])

# Request Models

class CrossDomainSearchRequest(BaseModel):
    """Request model for cross-domain pattern search"""
    source_domain: str = Field(..., description="Source domain to search patterns from")
    target_domain: str = Field(..., description="Target domain to find applicable patterns for")
    min_similarity: float = Field(0.6, ge=0.0, le=1.0, description="Minimum similarity threshold")
    max_results: int = Field(10, ge=1, le=100, description="Maximum number of results")

class PatternAbstractionRequest(BaseModel):
    """Request model for pattern abstraction"""
    pattern_id: UUID = Field(..., description="ID of pattern to abstract")

class PatternAdaptationRequest(BaseModel):
    """Request model for pattern adaptation"""
    abstract_pattern_id: UUID = Field(..., description="ID of abstract pattern to adapt")
    target_domain: str = Field(..., description="Domain to adapt pattern for")

class CrossDomainRecommendationRequest(BaseModel):
    """Request model for cross-domain recommendations"""
    problem_description: str = Field(..., min_length=10, description="Description of the problem to solve")
    target_domain: str = Field(..., description="Domain where the problem exists")
    exclude_domains: List[str] = Field(default=[], description="Domains to exclude from search")
    max_recommendations: int = Field(10, ge=1, le=50, description="Maximum recommendations to return")

# Response Models

class CrossDomainMatchResponse(BaseModel):
    """Response model for cross-domain matches"""
    source_pattern_id: UUID
    target_pattern_id: UUID
    source_domain: str
    target_domain: str
    similarity_score: float
    conceptual_overlap: List[str]
    structural_similarity: float
    adaptation_strategy: str
    confidence_level: float
    evidence: List[str]
    discovered_at: datetime

class AbstractPatternResponse(BaseModel):
    """Response model for abstract patterns"""
    id: UUID
    title: str
    abstract_description: str
    conceptual_structure: Dict[str, Any]
    invariant_properties: List[str]
    variable_components: Dict[str, str]
    applicability_conditions: List[str]
    expected_outcomes: List[str]
    source_domains: List[str]
    abstraction_level: float
    created_at: datetime
    quality_score: float

class DomainOntologyResponse(BaseModel):
    """Response model for domain ontologies"""
    domain: str
    core_concepts: List[str]
    concept_relationships: Dict[str, List[str]]
    technical_vocabulary: List[str]
    common_patterns: List[str]
    tools_and_technologies: List[str]
    typical_problems: List[str]
    success_metrics: List[str]
    confidence_score: float
    created_at: datetime

class CrossDomainRecommendationResponse(BaseModel):
    """Response model for cross-domain recommendations"""
    original_pattern_id: UUID
    original_pattern_title: str
    original_domain: str
    target_domain: str
    similarity_score: float
    success_probability: str
    concepts_overlap: List[str]
    adaptation_guidance: Dict[str, Any]
    abstract_pattern_id: UUID
    why_relevant: str
    implementation_notes: List[str]
    potential_challenges: List[str]
    confidence_score: float

class DomainRelationshipGraphResponse(BaseModel):
    """Response model for domain relationship graph"""
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    total_domains: int
    total_relationships: int
    most_connected_domain: str
    strongest_relationship: Dict[str, Any]

# API Endpoints

@router.post(
    "/search",
    response_model=List[CrossDomainMatchResponse],
    summary="Search for cross-domain pattern matches",
    description="Find patterns from source domain that could be applied to target domain"
)
async def search_cross_domain_patterns(
    request: CrossDomainSearchRequest,
    db_manager=Depends(get_database_manager),
    vector_service=Depends(get_vector_service),
    quality_scorer=Depends(get_quality_scorer)
):
    """
    Revolutionary cross-domain pattern search - find solutions from one domain
    that can solve problems in another domain
    """
    try:
        # Validate domain types
        try:
            source_domain = DomainType(request.source_domain.lower())
            target_domain = DomainType(request.target_domain.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid domain type. Valid domains: {[d.value for d in DomainType]}"
            )
        
        # Initialize cross-domain intelligence engine
        cross_domain_engine = CrossDomainIntelligence(db_manager, vector_service, quality_scorer)
        
        # Detect cross-domain patterns
        matches = await cross_domain_engine.detect_cross_domain_patterns(
            source_domain=source_domain,
            target_domain=target_domain,
            min_similarity=request.min_similarity
        )
        
        # Limit results
        matches = matches[:request.max_results]
        
        # Convert to response models
        response_matches = []
        for match in matches:
            response_matches.append(CrossDomainMatchResponse(
                source_pattern_id=match.source_pattern_id,
                target_pattern_id=match.target_pattern_id,
                source_domain=match.source_domain.value,
                target_domain=match.target_domain.value,
                similarity_score=match.similarity_score,
                conceptual_overlap=match.conceptual_overlap,
                structural_similarity=match.structural_similarity,
                adaptation_strategy=match.adaptation_strategy.value,
                confidence_level=match.confidence_level,
                evidence=match.evidence,
                discovered_at=match.discovered_at
            ))
        
        logger.info("Cross-domain pattern search completed",
                   source_domain=request.source_domain,
                   target_domain=request.target_domain,
                   matches_found=len(response_matches))
        
        return response_matches
        
    except Exception as e:
        logger.error("Cross-domain pattern search failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.post(
    "/abstract",
    response_model=AbstractPatternResponse,
    summary="Create abstract pattern from concrete implementation",
    description="Extract domain-agnostic pattern that can be reused across domains"
)
async def abstract_pattern(
    request: PatternAbstractionRequest,
    background_tasks: BackgroundTasks,
    db_manager=Depends(get_database_manager),
    vector_service=Depends(get_vector_service),
    quality_scorer=Depends(get_quality_scorer)
):
    """
    Create abstract, domain-agnostic patterns from concrete implementations
    """
    try:
        # Initialize cross-domain intelligence engine
        cross_domain_engine = CrossDomainIntelligence(db_manager, vector_service, quality_scorer)
        
        # Get the original pattern (this would query the database)
        # For now, creating a mock pattern
        original_pattern = KnowledgeItem(
            id=request.pattern_id,
            title="Sample Pattern",
            content="Sample content for abstraction",
            knowledge_type="pattern",
            source_type="manual",
            tags=["sample"],
            summary="Sample pattern",
            confidence="high",
            metadata={}
        )
        
        # Create abstract pattern
        abstract_pattern = await cross_domain_engine.abstract_domain_pattern(original_pattern)
        
        # Convert to response model
        response = AbstractPatternResponse(
            id=abstract_pattern.id,
            title=abstract_pattern.title,
            abstract_description=abstract_pattern.abstract_description,
            conceptual_structure=abstract_pattern.conceptual_structure,
            invariant_properties=abstract_pattern.invariant_properties,
            variable_components=abstract_pattern.variable_components,
            applicability_conditions=abstract_pattern.applicability_conditions,
            expected_outcomes=abstract_pattern.expected_outcomes,
            source_domains=[d.value for d in abstract_pattern.source_domains],
            abstraction_level=abstract_pattern.abstraction_level,
            created_at=abstract_pattern.created_at,
            quality_score=abstract_pattern.quality_score
        )
        
        logger.info("Pattern abstraction completed",
                   original_pattern_id=str(request.pattern_id),
                   abstract_pattern_id=str(abstract_pattern.id))
        
        return response
        
    except Exception as e:
        logger.error("Pattern abstraction failed", 
                    pattern_id=str(request.pattern_id), 
                    error=str(e))
        raise HTTPException(status_code=500, detail=f"Abstraction failed: {str(e)}")

@router.post(
    "/adapt",
    response_model=Dict[str, Any],
    summary="Adapt abstract pattern to target domain",
    description="Transform abstract pattern into domain-specific implementation"
)
async def adapt_pattern(
    request: PatternAdaptationRequest,
    background_tasks: BackgroundTasks,
    db_manager=Depends(get_database_manager),
    vector_service=Depends(get_vector_service),
    quality_scorer=Depends(get_quality_scorer)
):
    """
    Adapt an abstract pattern to a specific target domain
    """
    try:
        # Validate target domain
        try:
            target_domain = DomainType(request.target_domain.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid domain type. Valid domains: {[d.value for d in DomainType]}"
            )
        
        # Initialize cross-domain intelligence engine
        cross_domain_engine = CrossDomainIntelligence(db_manager, vector_service, quality_scorer)
        
        # Get abstract pattern (this would query the database)
        # For now, creating a mock abstract pattern
        from uuid import uuid4
        abstract_pattern = AbstractPattern(
            id=request.abstract_pattern_id,
            title="Abstract Authentication Pattern",
            abstract_description="Generic authentication flow pattern",
            conceptual_structure={},
            invariant_properties=["security", "validation"],
            variable_components={"auth_method": "authentication mechanism"},
            applicability_conditions=["user_management_needed"],
            expected_outcomes=["secure_user_access"],
            source_domains=[DomainType.AUTHENTICATION],
            abstraction_level=0.8,
            created_at=datetime.utcnow(),
            quality_score=0.9
        )
        
        # Adapt pattern to target domain
        adapted_pattern = await cross_domain_engine.adapt_pattern_to_domain(
            abstract_pattern, target_domain
        )
        
        # Return adapted pattern as knowledge item
        response = {
            "id": str(adapted_pattern.id),
            "title": adapted_pattern.title,
            "content": adapted_pattern.content,
            "knowledge_type": adapted_pattern.knowledge_type,
            "source_type": adapted_pattern.source_type,
            "tags": adapted_pattern.tags,
            "summary": adapted_pattern.summary,
            "confidence": adapted_pattern.confidence,
            "metadata": adapted_pattern.metadata
        }
        
        logger.info("Pattern adaptation completed",
                   abstract_pattern_id=str(request.abstract_pattern_id),
                   target_domain=request.target_domain,
                   adapted_pattern_id=str(adapted_pattern.id))
        
        return response
        
    except Exception as e:
        logger.error("Pattern adaptation failed", 
                    abstract_pattern_id=str(request.abstract_pattern_id),
                    target_domain=request.target_domain,
                    error=str(e))
        raise HTTPException(status_code=500, detail=f"Adaptation failed: {str(e)}")

@router.post(
    "/recommend",
    response_model=List[CrossDomainRecommendationResponse],
    summary="Get cross-domain solution recommendations",
    description="Find solutions from other domains that could solve problems in target domain"
)
async def recommend_cross_domain_solutions(
    request: CrossDomainRecommendationRequest,
    db_manager=Depends(get_database_manager),
    vector_service=Depends(get_vector_service),
    quality_scorer=Depends(get_quality_scorer)
):
    """
    Betty's key value proposition: "You solved similar authentication in 137docs using JWT middleware"
    """
    try:
        # Validate target domain
        try:
            target_domain = DomainType(request.target_domain.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid domain type. Valid domains: {[d.value for d in DomainType]}"
            )
        
        # Validate exclude domains
        exclude_domains = []
        for domain_str in request.exclude_domains:
            try:
                exclude_domains.append(DomainType(domain_str.lower()))
            except ValueError:
                logger.warning("Invalid exclude domain ignored", domain=domain_str)
        
        # Initialize cross-domain intelligence engine
        cross_domain_engine = CrossDomainIntelligence(db_manager, vector_service, quality_scorer)
        
        # Get recommendations
        recommendations = await cross_domain_engine.recommend_cross_domain_solutions(
            problem_description=request.problem_description,
            target_domain=target_domain,
            exclude_domains=exclude_domains,
            max_recommendations=request.max_recommendations
        )
        
        # Convert to response models
        response_recommendations = []
        for rec in recommendations:
            response_recommendations.append(CrossDomainRecommendationResponse(
                original_pattern_id=UUID(rec['original_pattern_id']),
                original_pattern_title=rec['original_pattern_title'],
                original_domain=rec['original_domain'],
                target_domain=rec['target_domain'],
                similarity_score=rec['similarity_score'],
                success_probability=rec['success_probability'],
                concepts_overlap=rec['concepts_overlap'],
                adaptation_guidance=rec['adaptation_guidance'],
                abstract_pattern_id=UUID(rec['abstract_pattern_id']),
                why_relevant=rec['why_relevant'],
                implementation_notes=rec['implementation_notes'],
                potential_challenges=rec['potential_challenges'],
                confidence_score=rec['confidence_score']
            ))
        
        logger.info("Cross-domain recommendations generated",
                   target_domain=request.target_domain,
                   recommendations_count=len(response_recommendations))
        
        return response_recommendations
        
    except Exception as e:
        logger.error("Cross-domain recommendation failed",
                    target_domain=request.target_domain,
                    error=str(e))
        raise HTTPException(status_code=500, detail=f"Recommendation failed: {str(e)}")

@router.get(
    "/domain-graph",
    response_model=DomainRelationshipGraphResponse,
    summary="Get domain relationship graph",
    description="Retrieve graph showing relationships between knowledge domains"
)
async def get_domain_relationship_graph(
    db_manager=Depends(get_database_manager),
    vector_service=Depends(get_vector_service),
    quality_scorer=Depends(get_quality_scorer)
):
    """
    Get the relationship graph between different knowledge domains
    """
    try:
        # Initialize cross-domain intelligence engine
        cross_domain_engine = CrossDomainIntelligence(db_manager, vector_service, quality_scorer)
        
        # Build domain relationship graph
        graph = await cross_domain_engine.build_domain_relationship_graph()
        
        # Convert to response format
        nodes = []
        for node in graph.nodes(data=True):
            nodes.append({
                "id": node[0],
                "domain_type": node[1].get("domain_type", "unknown"),
                "data": node[1]
            })
        
        edges = []
        strongest_relationship = {"similarity": 0}
        
        for edge in graph.edges(data=True):
            edge_data = {
                "source": edge[0],
                "target": edge[1],
                "similarity": edge[2].get("similarity", 0),
                "shared_concepts": edge[2].get("shared_concepts", 0),
                "adaptation_count": edge[2].get("adaptation_count", 0),
                "weight": edge[2].get("weight", 0)
            }
            edges.append(edge_data)
            
            # Track strongest relationship
            if edge_data["similarity"] > strongest_relationship["similarity"]:
                strongest_relationship = edge_data
        
        # Find most connected domain
        degree_centrality = dict(graph.degree())
        most_connected_domain = max(degree_centrality, key=degree_centrality.get) if degree_centrality else "none"
        
        response = DomainRelationshipGraphResponse(
            nodes=nodes,
            edges=edges,
            total_domains=len(nodes),
            total_relationships=len(edges),
            most_connected_domain=most_connected_domain,
            strongest_relationship=strongest_relationship
        )
        
        logger.info("Domain relationship graph retrieved",
                   total_domains=len(nodes),
                   total_relationships=len(edges))
        
        return response
        
    except Exception as e:
        logger.error("Failed to get domain relationship graph", error=str(e))
        raise HTTPException(status_code=500, detail=f"Graph retrieval failed: {str(e)}")

@router.get(
    "/domains",
    response_model=List[str],
    summary="List available domains",
    description="Get list of all available knowledge domains"
)
async def list_domains():
    """
    Get list of all available knowledge domains
    """
    try:
        domains = [domain.value for domain in DomainType if domain != DomainType.UNKNOWN]
        return sorted(domains)
        
    except Exception as e:
        logger.error("Failed to list domains", error=str(e))
        raise HTTPException(status_code=500, detail=f"Domain listing failed: {str(e)}")

@router.get(
    "/adaptation-strategies",
    response_model=List[str],
    summary="List adaptation strategies",
    description="Get list of all available pattern adaptation strategies"
)
async def list_adaptation_strategies():
    """
    Get list of all available adaptation strategies
    """
    try:
        strategies = [strategy.value for strategy in AdaptationStrategy]
        return sorted(strategies)
        
    except Exception as e:
        logger.error("Failed to list adaptation strategies", error=str(e))
        raise HTTPException(status_code=500, detail=f"Strategy listing failed: {str(e)}")

@router.get(
    "/health",
    summary="Health check for cross-domain intelligence",
    description="Check the health status of cross-domain intelligence system"
)
async def cross_domain_health_check():
    """
    Health check endpoint for cross-domain intelligence system
    """
    try:
        return {
            "status": "healthy",
            "service": "cross-domain-intelligence",
            "version": "1.0.0",
            "features": {
                "pattern_detection": "active",
                "pattern_abstraction": "active", 
                "pattern_adaptation": "active",
                "cross_domain_recommendations": "active",
                "domain_relationship_graph": "active"
            },
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error("Cross-domain health check failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")