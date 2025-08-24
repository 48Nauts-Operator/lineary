"""
BETTY Memory System Python SDK - Data Models

This module provides Pydantic models for all BETTY API requests and responses,
ensuring type safety and data validation throughout the SDK.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from enum import Enum


class SearchType(str, Enum):
    """Supported search types."""
    SEMANTIC = "semantic"
    KEYWORD = "keyword"
    HYBRID = "hybrid"


class PatternType(str, Enum):
    """Supported pattern matching types."""
    PATH = "path"
    SUBGRAPH = "subgraph"
    TEMPORAL = "temporal"
    ANOMALY = "anomaly"
    COMMUNITY = "community"
    CENTRALITY = "centrality"


class ClusteringAlgorithm(str, Enum):
    """Supported clustering algorithms."""
    HIERARCHICAL = "hierarchical"
    KMEANS = "kmeans"
    DBSCAN = "dbscan"
    SPECTRAL = "spectral"
    GAUSSIAN_MIXTURE = "gaussian_mixture"


class FilterOperator(str, Enum):
    """Supported filter operators."""
    EQ = "eq"
    NE = "ne"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    IN = "in"
    CONTAINS = "contains"


class OperationStatus(str, Enum):
    """Batch operation statuses."""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# Base Models

class BaseModel(BaseModel):
    """Base model with common configuration."""
    
    class Config:
        """Pydantic configuration."""
        extra = "allow"
        use_enum_values = True
        validate_assignment = True
        allow_population_by_field_name = True


class BaseResponse(BaseModel):
    """Base response model for all API responses."""
    
    success: bool = Field(..., description="Whether the request was successful")
    message: Optional[str] = Field(None, description="Human-readable message")
    api_version: Optional[str] = Field(None, description="API version")
    execution_time_ms: Optional[float] = Field(None, description="Execution time in milliseconds")
    timestamp: Optional[datetime] = Field(None, description="Response timestamp")
    request_id: Optional[str] = Field(None, description="Request tracking ID")
    data: Optional[Any] = Field(None, description="Response data")


class ErrorDetails(BaseModel):
    """Error details for API responses."""
    
    error_code: Optional[str] = Field(None, description="Specific error code")
    field_errors: Optional[Dict[str, List[str]]] = Field(None, description="Field-specific errors")
    missing_permissions: Optional[List[str]] = Field(None, description="Missing permissions")
    suggestion: Optional[str] = Field(None, description="How to fix the error")
    documentation_url: Optional[str] = Field(None, description="Link to relevant docs")


class ErrorResponse(BaseResponse):
    """Error response model."""
    
    success: bool = Field(False, description="Always false for errors")
    error: str = Field(..., description="Error type")
    details: Optional[ErrorDetails] = Field(None, description="Detailed error information")


# Filter and Query Models

class Filter(BaseModel):
    """Query filter model."""
    
    field: str = Field(..., description="Field to filter on")
    operator: FilterOperator = Field(..., description="Filter operator")
    value: Union[str, int, float, List[Any]] = Field(..., description="Filter value")


class TimeRange(BaseModel):
    """Time range filter model."""
    
    start: Optional[datetime] = Field(None, description="Start time (inclusive)")
    end: Optional[datetime] = Field(None, description="End time (inclusive)")


# Knowledge Models

class KnowledgeMetadata(BaseModel):
    """Knowledge item metadata."""
    
    tags: Optional[List[str]] = Field(None, description="Tags associated with the item")
    quality_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Quality score (0-1)")
    source: Optional[str] = Field(None, description="Source of the knowledge item")
    language: Optional[str] = Field(None, description="Content language")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")


class KnowledgeItem(BaseModel):
    """Knowledge item model."""
    
    id: str = Field(..., description="Unique knowledge item ID")
    title: str = Field(..., description="Knowledge item title")
    content: str = Field(..., description="Main content")
    knowledge_type: str = Field(..., description="Type of knowledge item")
    project_id: Optional[str] = Field(None, description="Parent project ID")
    metadata: Optional[KnowledgeMetadata] = Field(None, description="Additional metadata")


class SearchResult(KnowledgeItem):
    """Search result model with additional scoring information."""
    
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Similarity score (0-1)")
    ranking_score: float = Field(..., ge=0.0, description="Ranking score")
    highlights: Optional[List[str]] = Field(None, description="Matching text snippets")
    search_perspective: Optional[str] = Field(None, description="Search perspective used")


# Advanced Search Models

class AdvancedSearchRequest(BaseModel):
    """Advanced search request model."""
    
    query: str = Field(..., min_length=1, description="Search query text")
    search_type: SearchType = Field(SearchType.HYBRID, description="Type of search")
    similarity_threshold: float = Field(0.7, ge=0.0, le=1.0, description="Minimum similarity score")
    max_results: int = Field(20, ge=1, le=100, description="Maximum results to return")
    filters: Optional[List[Filter]] = Field(None, description="Query filters")
    time_range: Optional[TimeRange] = Field(None, description="Time range filter")
    ranking_algorithm: str = Field("bm25_semantic_hybrid", description="Ranking algorithm")
    include_metadata: bool = Field(True, description="Include item metadata")
    group_by: Optional[str] = Field(None, description="Field to group results by")
    project_ids: Optional[List[str]] = Field(None, description="Filter by project IDs")


class QueryAnalysis(BaseModel):
    """Query analysis information."""
    
    search_type_used: str = Field(..., description="Search type that was used")
    semantic_expansion: Optional[List[str]] = Field(None, description="Semantic query expansion terms")
    filters_applied: int = Field(..., description="Number of filters applied")
    execution_time_ms: float = Field(..., description="Query execution time")


class SearchFacets(BaseModel):
    """Search result facets."""
    
    knowledge_type: Optional[Dict[str, int]] = Field(None, description="Knowledge type counts")
    tags: Optional[Dict[str, int]] = Field(None, description="Tag counts")
    projects: Optional[Dict[str, int]] = Field(None, description="Project counts")


class AdvancedSearchData(BaseModel):
    """Advanced search response data."""
    
    results: List[SearchResult] = Field(..., description="Search results")
    total_results: int = Field(..., description="Total number of results")
    query_analysis: QueryAnalysis = Field(..., description="Query analysis")
    facets: Optional[SearchFacets] = Field(None, description="Result facets")


class AdvancedSearchResponse(BaseResponse):
    """Advanced search response model."""
    
    data: AdvancedSearchData = Field(..., description="Search response data")


# Pattern Matching Models

class NodeConstraint(BaseModel):
    """Pattern node constraints."""
    
    knowledge_type: Optional[str] = Field(None, description="Required knowledge type")
    tags: Optional[List[str]] = Field(None, description="Required tags")
    metadata_filters: Optional[Dict[str, Any]] = Field(None, description="Metadata filters")


class PatternDefinition(BaseModel):
    """Pattern definition for matching."""
    
    path_structure: Optional[str] = Field(None, description="Path structure (e.g., 'A->B->C')")
    relationship_types: Optional[List[str]] = Field(None, description="Allowed relationship types")
    node_constraints: Optional[Dict[str, NodeConstraint]] = Field(None, description="Node constraints")
    temporal_window: Optional[str] = Field(None, description="Time window for temporal patterns")
    algorithm_params: Optional[Dict[str, Any]] = Field(None, description="Algorithm-specific parameters")


class PatternMatchRequest(BaseModel):
    """Pattern matching request model."""
    
    pattern_type: PatternType = Field(..., description="Type of pattern to match")
    pattern_definition: Optional[PatternDefinition] = Field(None, description="Pattern definition")
    max_depth: int = Field(5, ge=1, le=10, description="Maximum path depth")
    min_confidence: float = Field(0.6, ge=0.0, le=1.0, description="Minimum pattern confidence")
    max_results: int = Field(50, ge=1, le=100, description="Maximum patterns to return")
    project_ids: Optional[List[str]] = Field(None, description="Filter by project IDs")


class PatternNode(BaseModel):
    """Pattern node model."""
    
    id: str = Field(..., description="Node ID")
    title: str = Field(..., description="Node title")
    type: str = Field(..., description="Node type")
    role: str = Field(..., description="Node role in pattern")


class PatternRelationship(BaseModel):
    """Pattern relationship model."""
    
    from_node: str = Field(..., alias="from", description="Source node ID")
    to_node: str = Field(..., alias="to", description="Target node ID")
    type: str = Field(..., description="Relationship type")
    strength: float = Field(..., ge=0.0, le=1.0, description="Relationship strength")


class Pattern(BaseModel):
    """Discovered pattern model."""
    
    pattern_id: str = Field(..., description="Pattern ID")
    pattern_type: str = Field(..., description="Pattern type")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    support_count: int = Field(..., description="Support count")
    nodes: List[PatternNode] = Field(..., description="Pattern nodes")
    relationships: List[PatternRelationship] = Field(..., description="Pattern relationships")
    pattern_description: str = Field(..., description="Human-readable description")
    examples: List[str] = Field(..., description="Example instance IDs")


class PatternAnalysis(BaseModel):
    """Pattern analysis information."""
    
    strongest_pattern: Optional[str] = Field(None, description="ID of strongest pattern")
    most_frequent_relationship: Optional[str] = Field(None, description="Most frequent relationship type")
    pattern_distribution: Dict[str, int] = Field(..., description="Pattern type distribution")


class PatternMatchData(BaseModel):
    """Pattern matching response data."""
    
    patterns: List[Pattern] = Field(..., description="Discovered patterns")
    total_patterns: int = Field(..., description="Total number of patterns")
    analysis: PatternAnalysis = Field(..., description="Pattern analysis")


class PatternMatchResponse(BaseResponse):
    """Pattern matching response model."""
    
    data: PatternMatchData = Field(..., description="Pattern matching data")


# Semantic Clustering Models

class SemanticClusteringRequest(BaseModel):
    """Semantic clustering request model."""
    
    algorithm: ClusteringAlgorithm = Field(ClusteringAlgorithm.HIERARCHICAL, description="Clustering algorithm")
    num_clusters: Optional[int] = Field(None, ge=2, le=50, description="Number of clusters")
    auto_clusters: bool = Field(True, description="Auto-determine optimal cluster count")
    min_cluster_size: int = Field(5, ge=1, description="Minimum items per cluster")
    max_cluster_size: int = Field(100, ge=1, description="Maximum items per cluster")
    similarity_threshold: float = Field(0.6, ge=0.0, le=1.0, description="Minimum intra-cluster similarity")
    project_ids: Optional[List[str]] = Field(None, description="Filter by project IDs")
    knowledge_types: Optional[List[str]] = Field(None, description="Filter by knowledge types")
    use_content: bool = Field(True, description="Use content for clustering")
    use_metadata: bool = Field(True, description="Use metadata features")
    use_relationships: bool = Field(False, description="Use relationship information")
    include_visualization: bool = Field(False, description="Generate visualization data")
    include_topics: bool = Field(True, description="Extract cluster topics")
    max_items_per_cluster: int = Field(100, ge=1, description="Maximum items per cluster")


class ClusterTopic(BaseModel):
    """Cluster topic model."""
    
    term: str = Field(..., description="Topic term")
    weight: float = Field(..., ge=0.0, le=1.0, description="Topic weight")


class RepresentativeItem(BaseModel):
    """Representative cluster item."""
    
    id: str = Field(..., description="Item ID")
    title: str = Field(..., description="Item title")
    similarity_to_centroid: float = Field(..., ge=0.0, le=1.0, description="Similarity to cluster centroid")


class ClusterCharacteristics(BaseModel):
    """Cluster characteristics."""
    
    avg_quality_score: float = Field(..., description="Average quality score")
    primary_knowledge_types: List[str] = Field(..., description="Primary knowledge types")
    time_range: Optional[TimeRange] = Field(None, description="Time range of items")


class Cluster(BaseModel):
    """Knowledge cluster model."""
    
    cluster_id: int = Field(..., description="Cluster ID")
    label: str = Field(..., description="Cluster label")
    size: int = Field(..., description="Number of items in cluster")
    centroid_score: float = Field(..., ge=0.0, le=1.0, description="Centroid quality score")
    coherence_score: float = Field(..., ge=0.0, le=1.0, description="Cluster coherence score")
    items: List[str] = Field(..., description="Item IDs in cluster")
    representative_items: List[RepresentativeItem] = Field(..., description="Representative items")
    topics: List[ClusterTopic] = Field(..., description="Cluster topics")
    characteristics: ClusterCharacteristics = Field(..., description="Cluster characteristics")


class QualityMetrics(BaseModel):
    """Clustering quality metrics."""
    
    silhouette_score: float = Field(..., description="Silhouette coefficient")
    davies_bouldin_score: float = Field(..., description="Davies-Bouldin index")
    calinski_harabasz_score: float = Field(..., description="Calinski-Harabasz index")


class VisualizationData(BaseModel):
    """Cluster visualization data."""
    
    type: str = Field(..., description="Visualization type")
    data_url: str = Field(..., description="URL to visualization data")


class SemanticClusteringData(BaseModel):
    """Semantic clustering response data."""
    
    clusters: List[Cluster] = Field(..., description="Generated clusters")
    clusters_count: int = Field(..., description="Number of clusters")
    algorithm_used: str = Field(..., description="Algorithm used")
    quality_metrics: QualityMetrics = Field(..., description="Quality metrics")
    visualization: Optional[VisualizationData] = Field(None, description="Visualization data")


class SemanticClusteringResponse(BaseResponse):
    """Semantic clustering response model."""
    
    data: SemanticClusteringData = Field(..., description="Clustering data")


# Batch Operation Models

class ValidationRules(BaseModel):
    """Batch import validation rules."""
    
    min_content_length: Optional[int] = Field(None, ge=0, description="Minimum content length")
    max_content_length: Optional[int] = Field(None, ge=1, description="Maximum content length")
    required_fields: Optional[List[str]] = Field(None, description="Required field names")
    content_filters: Optional[List[str]] = Field(None, description="Content filtering rules")


class ProcessingOptions(BaseModel):
    """Batch processing options."""
    
    generate_embeddings: bool = Field(True, description="Generate vector embeddings")
    auto_categorize: bool = Field(True, description="Auto-detect knowledge types")
    extract_entities: bool = Field(False, description="Extract named entities")
    detect_language: bool = Field(False, description="Detect content language")
    quality_scoring: bool = Field(True, description="Compute quality scores")


class SourceConfig(BaseModel):
    """Source configuration for batch import."""
    
    file_path: Optional[str] = Field(None, description="File path for file sources")
    url: Optional[str] = Field(None, description="URL for URL sources")
    connection_string: Optional[str] = Field(None, description="Database connection string")
    api_endpoint: Optional[str] = Field(None, description="API endpoint URL")
    encoding: str = Field("utf-8", description="File encoding")
    headers: Optional[Dict[str, str]] = Field(None, description="HTTP headers")


class BatchImportRequest(BaseModel):
    """Batch import request model."""
    
    source_type: str = Field(..., description="Source type (file, url, database, api)")
    format: str = Field(..., description="Data format (json, csv, xml, yaml, markdown)")
    source_config: SourceConfig = Field(..., description="Source configuration")
    target_project_id: str = Field(..., description="Target project UUID")
    duplicate_handling: str = Field("skip", description="Duplicate handling strategy")
    validation_rules: Optional[ValidationRules] = Field(None, description="Validation rules")
    processing_options: Optional[ProcessingOptions] = Field(None, description="Processing options")
    batch_size: int = Field(100, ge=1, le=1000, description="Items per batch")
    max_errors: int = Field(50, ge=0, description="Maximum errors before stopping")
    notify_webhook: Optional[str] = Field(None, description="Webhook URL for notifications")


class BatchOperationData(BaseModel):
    """Batch operation data."""
    
    operation_id: str = Field(..., description="Operation UUID")
    status: OperationStatus = Field(..., description="Operation status")
    estimated_total_items: Optional[int] = Field(None, description="Estimated total items")
    estimated_duration_seconds: Optional[int] = Field(None, description="Estimated duration")
    created_at: datetime = Field(..., description="Creation timestamp")
    progress_url: str = Field(..., description="Progress monitoring URL")
    websocket_url: Optional[str] = Field(None, description="WebSocket URL for real-time updates")


class BatchImportResponse(BaseResponse):
    """Batch import response model."""
    
    data: BatchOperationData = Field(..., description="Operation data")


class ProgressPhase(BaseModel):
    """Progress phase information."""
    
    name: str = Field(..., description="Phase name")
    status: str = Field(..., description="Phase status")
    progress_percentage: float = Field(..., ge=0.0, le=100.0, description="Phase progress")
    duration_seconds: Optional[float] = Field(None, description="Phase duration")
    estimated_duration_seconds: Optional[float] = Field(None, description="Estimated duration")


class ProgressStatistics(BaseModel):
    """Progress statistics."""
    
    avg_processing_time_per_item: float = Field(..., description="Average processing time per item")
    memory_usage_mb: float = Field(..., description="Memory usage in MB")
    cpu_usage_percentage: float = Field(..., description="CPU usage percentage")


class ProgressError(BaseModel):
    """Progress error information."""
    
    item_id: Optional[str] = Field(None, description="Item ID that caused error")
    error_message: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code")
    timestamp: datetime = Field(..., description="Error timestamp")


class ProgressData(BaseModel):
    """Batch operation progress data."""
    
    operation_id: str = Field(..., description="Operation ID")
    status: OperationStatus = Field(..., description="Operation status")
    progress_percentage: float = Field(..., ge=0.0, le=100.0, description="Overall progress")
    processed_items: int = Field(..., description="Items processed")
    successful_items: int = Field(..., description="Successfully processed items")
    failed_items: int = Field(..., description="Failed items")
    total_items: int = Field(..., description="Total items to process")
    current_phase: str = Field(..., description="Current processing phase")
    phase_progress: float = Field(..., ge=0.0, le=100.0, description="Current phase progress")
    estimated_time_remaining: Optional[int] = Field(None, description="Estimated time remaining (seconds)")
    throughput_items_per_second: float = Field(..., description="Processing throughput")
    started_at: datetime = Field(..., description="Start timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    phases: List[ProgressPhase] = Field(..., description="Processing phases")
    statistics: ProgressStatistics = Field(..., description="Processing statistics")
    recent_errors: List[ProgressError] = Field(..., description="Recent errors")


# WebSocket Models

class WebSocketMessage(BaseModel):
    """WebSocket message model."""
    
    type: str = Field(..., description="Message type")
    id: Optional[str] = Field(None, description="Message ID")
    timestamp: datetime = Field(..., description="Message timestamp")
    data: Any = Field(..., description="Message data")


# Cross-Project Models

class ProjectConnection(BaseModel):
    """Project connection model."""
    
    connection_id: str = Field(..., description="Connection ID")
    source_project_id: str = Field(..., description="Source project ID")
    target_project_id: str = Field(..., description="Target project ID")
    connection_type: str = Field(..., description="Connection type")
    status: str = Field(..., description="Connection status")
    permissions: Dict[str, bool] = Field(..., description="Connection permissions")
    created_at: datetime = Field(..., description="Creation timestamp")


class ProjectBreakdown(BaseModel):
    """Cross-project search breakdown."""
    
    results: int = Field(..., description="Number of results from project")
    max_score: float = Field(..., description="Maximum score from project")


class CrossProjectSearchData(AdvancedSearchData):
    """Cross-project search response data."""
    
    project_breakdown: Dict[str, ProjectBreakdown] = Field(..., description="Results by project")
    search_statistics: Dict[str, Any] = Field(..., description="Cross-project search statistics")