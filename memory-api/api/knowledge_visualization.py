# ABOUTME: Knowledge visualization API endpoints for BETTY Memory System
# ABOUTME: Handles code analysis, documentation browsing, and knowledge graph visualization

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional, Dict, Any
from uuid import UUID
import structlog
import time
import json

from models.base import PaginationParams, ErrorResponse
from core.dependencies import DatabaseDependencies, get_all_databases
from core.security import get_current_user, SecurityManager
from services.knowledge_visualization_service import KnowledgeVisualizationService
from pydantic import BaseModel

logger = structlog.get_logger(__name__)
router = APIRouter()

# Request/Response Models for Knowledge Visualization

class CodeRepositoryAnalysis(BaseModel):
    repository_name: str
    total_files: int
    total_lines: int
    programming_languages: Dict[str, int]
    file_types: Dict[str, int]
    complexity_metrics: Dict[str, Any]
    architecture_patterns: List[str]
    dependencies: List[str]
    last_analyzed: str

class DocumentationSource(BaseModel):
    source_id: str
    source_name: str
    source_type: str
    document_count: int
    total_words: int
    categories: List[str]
    knowledge_depth: float
    last_updated: str

class KnowledgeGraphNode(BaseModel):
    id: str
    label: str
    type: str
    properties: Dict[str, Any]
    connections: int

class KnowledgeGraphEdge(BaseModel):
    source: str
    target: str
    relationship_type: str
    weight: float

class KnowledgeGraph(BaseModel):
    nodes: List[KnowledgeGraphNode]
    edges: List[KnowledgeGraphEdge]
    stats: Dict[str, Any]

class LearningTimelineEntry(BaseModel):
    timestamp: str
    event_type: str
    description: str
    knowledge_area: str
    impact_score: float

class ExpertiseLevel(BaseModel):
    domain: str
    confidence_score: float
    knowledge_items_count: int
    last_updated: str
    proficiency_level: str

class CodeFileDetails(BaseModel):
    file_path: str
    file_name: str
    programming_language: str
    lines_of_code: int
    functions: List[Dict[str, Any]]
    classes: List[Dict[str, Any]]
    imports: List[str]
    complexity_score: float
    documentation_coverage: float

class KnowledgeVisualizationStats(BaseModel):
    total_code_lines: int
    total_repositories: int
    total_documentation_sources: int
    programming_languages: Dict[str, int]
    knowledge_domains: Dict[str, int]
    learning_velocity: float
    expertise_areas: List[ExpertiseLevel]
    recent_learning: List[LearningTimelineEntry]

@router.get("/dashboard/stats", response_model=KnowledgeVisualizationStats)
async def get_visualization_dashboard_stats(
    databases: DatabaseDependencies = Depends(get_all_databases),
    current_user: dict = Depends(get_current_user)
):
    """Get comprehensive knowledge visualization dashboard statistics"""
    try:
        service = KnowledgeVisualizationService(databases)
        stats_data = await service.get_comprehensive_stats()
        
        # Convert to Pydantic model
        stats = KnowledgeVisualizationStats(
            total_code_lines=stats_data.get("total_code_lines", 0),
            total_repositories=stats_data.get("total_repositories", 0),
            total_documentation_sources=stats_data.get("total_documentation_sources", 0),
            programming_languages=stats_data.get("programming_languages", {}),
            knowledge_domains=stats_data.get("knowledge_domains", {}),
            learning_velocity=stats_data.get("learning_velocity", 0.0),
            expertise_areas=[
                ExpertiseLevel(**area) for area in stats_data.get("expertise_areas", [])
            ],
            recent_learning=[
                LearningTimelineEntry(**event) for event in stats_data.get("recent_learning", [])
            ]
        )
        
        logger.info("Knowledge visualization stats retrieved", total_code_lines=stats.total_code_lines)
        return stats
        
    except Exception as e:
        logger.error("Failed to get visualization stats", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve visualization statistics: {str(e)}"
        )

@router.get("/code/repositories", response_model=List[CodeRepositoryAnalysis])
async def get_code_repositories(
    programming_language: Optional[str] = Query(None),
    min_lines: Optional[int] = Query(None),
    databases: DatabaseDependencies = Depends(get_all_databases),
    current_user: dict = Depends(get_current_user)
):
    """Get analyzed code repositories with filtering options"""
    try:
        service = KnowledgeVisualizationService(databases)
        repositories = await service.get_code_repositories(
            programming_language=programming_language,
            min_lines=min_lines
        )
        
        logger.info("Code repositories retrieved", count=len(repositories))
        return repositories
        
    except Exception as e:
        logger.error("Failed to get code repositories", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve code repositories: {str(e)}"
        )

@router.get("/code/files/{repository_name}", response_model=List[CodeFileDetails])
async def get_repository_files(
    repository_name: str,
    file_type: Optional[str] = Query(None),
    pagination: PaginationParams = Depends(),
    databases: DatabaseDependencies = Depends(get_all_databases),
    current_user: dict = Depends(get_current_user)
):
    """Get detailed file information for a specific repository"""
    try:
        service = KnowledgeVisualizationService(databases)
        files = await service.get_repository_files(
            repository_name=repository_name,
            file_type=file_type,
            pagination=pagination
        )
        
        logger.info("Repository files retrieved", repository=repository_name, count=len(files))
        return files
        
    except Exception as e:
        logger.error("Failed to get repository files", repository=repository_name, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve repository files: {str(e)}"
        )

@router.get("/code/file-content/{file_id}")
async def get_file_content_with_highlighting(
    file_id: str,
    databases: DatabaseDependencies = Depends(get_all_databases),
    current_user: dict = Depends(get_current_user)
):
    """Get file content with syntax highlighting and analysis"""
    try:
        service = KnowledgeVisualizationService(databases)
        content = await service.get_file_content_with_highlighting(file_id)
        
        logger.info("File content retrieved with highlighting", file_id=file_id)
        return content
        
    except Exception as e:
        logger.error("Failed to get file content", file_id=file_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve file content: {str(e)}"
        )

@router.get("/documentation/sources", response_model=List[DocumentationSource])
async def get_documentation_sources(
    source_type: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    databases: DatabaseDependencies = Depends(get_all_databases),
    current_user: dict = Depends(get_current_user)
):
    """Get documentation sources with knowledge depth metrics"""
    try:
        service = KnowledgeVisualizationService(databases)
        sources = await service.get_documentation_sources(
            source_type=source_type,
            category=category
        )
        
        logger.info("Documentation sources retrieved", count=len(sources))
        return sources
        
    except Exception as e:
        logger.error("Failed to get documentation sources", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve documentation sources: {str(e)}"
        )

@router.get("/documentation/search")
async def search_documentation(
    query: str = Query(...),
    source_type: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    limit: int = Query(20),
    databases: DatabaseDependencies = Depends(get_all_databases),
    current_user: dict = Depends(get_current_user)
):
    """Advanced search across all learned documentation"""
    try:
        # Sanitize search query
        query = SecurityManager.sanitize_input(query, 1000)
        
        service = KnowledgeVisualizationService(databases)
        results = await service.search_documentation(
            query=query,
            source_type=source_type,
            category=category,
            limit=limit
        )
        
        logger.info("Documentation search completed", query=query[:50], results_count=len(results))
        return results
        
    except Exception as e:
        logger.error("Documentation search failed", query=query, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Documentation search failed: {str(e)}"
        )

@router.get("/knowledge-graph", response_model=KnowledgeGraph)
async def get_knowledge_graph(
    focus_area: Optional[str] = Query(None),
    depth: int = Query(3),
    max_nodes: int = Query(100),
    databases: DatabaseDependencies = Depends(get_all_databases),
    current_user: dict = Depends(get_current_user)
):
    """Generate knowledge graph visualization"""
    try:
        service = KnowledgeVisualizationService(databases)
        graph = await service.generate_knowledge_graph(
            focus_area=focus_area,
            depth=depth,
            max_nodes=max_nodes
        )
        
        logger.info("Knowledge graph generated", nodes=len(graph.nodes), edges=len(graph.edges))
        return graph
        
    except Exception as e:
        logger.error("Failed to generate knowledge graph", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate knowledge graph: {str(e)}"
        )

@router.get("/learning-timeline", response_model=List[LearningTimelineEntry])
async def get_learning_timeline(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    knowledge_area: Optional[str] = Query(None),
    limit: int = Query(50),
    databases: DatabaseDependencies = Depends(get_all_databases),
    current_user: dict = Depends(get_current_user)
):
    """Get learning timeline with knowledge acquisition events"""
    try:
        service = KnowledgeVisualizationService(databases)
        timeline = await service.get_learning_timeline(
            start_date=start_date,
            end_date=end_date,
            knowledge_area=knowledge_area,
            limit=limit
        )
        
        logger.info("Learning timeline retrieved", entries=len(timeline))
        return timeline
        
    except Exception as e:
        logger.error("Failed to get learning timeline", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve learning timeline: {str(e)}"
        )

@router.get("/expertise-levels", response_model=List[ExpertiseLevel])
async def get_expertise_levels(
    min_confidence: Optional[float] = Query(None),
    domain: Optional[str] = Query(None),
    databases: DatabaseDependencies = Depends(get_all_databases),
    current_user: dict = Depends(get_current_user)
):
    """Get expertise levels across different knowledge domains"""
    try:
        service = KnowledgeVisualizationService(databases)
        expertise = await service.get_expertise_levels(
            min_confidence=min_confidence,
            domain=domain
        )
        
        logger.info("Expertise levels retrieved", domains=len(expertise))
        return expertise
        
    except Exception as e:
        logger.error("Failed to get expertise levels", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve expertise levels: {str(e)}"
        )

@router.get("/cross-references/{knowledge_id}")
async def get_knowledge_cross_references(
    knowledge_id: str,
    max_depth: int = Query(2),
    relationship_types: Optional[List[str]] = Query(None),
    databases: DatabaseDependencies = Depends(get_all_databases),
    current_user: dict = Depends(get_current_user)
):
    """Get cross-references and relationships for a specific knowledge item"""
    try:
        service = KnowledgeVisualizationService(databases)
        references = await service.get_cross_references(
            knowledge_id=knowledge_id,
            max_depth=max_depth,
            relationship_types=relationship_types
        )
        
        logger.info("Cross-references retrieved", knowledge_id=knowledge_id, count=len(references))
        return references
        
    except Exception as e:
        logger.error("Failed to get cross-references", knowledge_id=knowledge_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve cross-references: {str(e)}"
        )

@router.post("/analyze/code-patterns")
async def analyze_code_patterns(
    repository_names: Optional[List[str]] = None,
    programming_languages: Optional[List[str]] = None,
    databases: DatabaseDependencies = Depends(get_all_databases),
    current_user: dict = Depends(get_current_user)
):
    """Analyze code patterns and architecture across repositories"""
    try:
        service = KnowledgeVisualizationService(databases)
        analysis = await service.analyze_code_patterns(
            repository_names=repository_names,
            programming_languages=programming_languages
        )
        
        logger.info("Code pattern analysis completed", repositories=len(repository_names or []))
        return analysis
        
    except Exception as e:
        logger.error("Code pattern analysis failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Code pattern analysis failed: {str(e)}"
        )

@router.get("/confidence-metrics")
async def get_knowledge_confidence_metrics(
    knowledge_type: Optional[str] = Query(None),
    databases: DatabaseDependencies = Depends(get_all_databases),
    current_user: dict = Depends(get_current_user)
):
    """Get confidence metrics and validation status for knowledge base"""
    try:
        service = KnowledgeVisualizationService(databases)
        metrics = await service.get_confidence_metrics(knowledge_type=knowledge_type)
        
        logger.info("Confidence metrics retrieved")
        return metrics
        
    except Exception as e:
        logger.error("Failed to get confidence metrics", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve confidence metrics: {str(e)}"
        )