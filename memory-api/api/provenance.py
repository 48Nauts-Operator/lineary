"""
ABOUTME: API endpoints for data provenance tracking and queries in BETTY
ABOUTME: Provides comprehensive audit trail access for knowledge pattern sources
"""

from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from ..core.dependencies import get_db_connection
from ..core.security import get_current_user
from ..models.base import BaseResponse
from ..services.provenance_service import ProvenanceService

router = APIRouter(prefix="/provenance", tags=["provenance"])

# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class DataSourceResponse(BaseModel):
    """Data source information"""
    id: UUID
    source_name: str
    source_type: str
    base_url: Optional[str] = None
    description: Optional[str] = None
    reliability_score: float
    update_frequency: Optional[str] = None
    access_method: Optional[str] = None
    is_active: bool
    last_accessed_at: Optional[datetime] = None
    last_successful_extraction: Optional[datetime] = None
    consecutive_failures: int
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ExtractionJobResponse(BaseModel):
    """Extraction job information"""
    id: UUID
    job_name: str
    job_type: str
    extraction_method: str
    extraction_version: str
    target_url: Optional[str] = None
    target_query: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str
    items_discovered: int
    items_processed: int
    items_successful: int
    items_failed: int
    items_duplicated: int
    error_message: Optional[str] = None
    data_quality_score: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class TransformationStepResponse(BaseModel):
    """Transformation step details"""
    id: UUID
    step_name: str
    step_order: int
    processor_name: str
    processor_version: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    execution_time_ms: Optional[int] = None
    status: str
    input_hash: Optional[str] = None
    output_hash: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    results: Dict[str, Any] = Field(default_factory=dict)
    changes_made: List[Any] = Field(default_factory=list)
    error_message: Optional[str] = None
    quality_impact_score: Optional[float] = None

class QualityLineageResponse(BaseModel):
    """Quality assessment and approval information"""
    id: UUID
    assessment_type: str
    assessor_name: Optional[str] = None
    assessor_type: Optional[str] = None
    overall_quality_score: float
    accuracy_score: Optional[float] = None
    completeness_score: Optional[float] = None
    relevance_score: Optional[float] = None
    freshness_score: Optional[float] = None
    quality_criteria: Dict[str, Any] = Field(default_factory=dict)
    assessment_results: Dict[str, Any] = Field(default_factory=dict)
    issues_found: List[Any] = Field(default_factory=list)
    recommendations: List[Any] = Field(default_factory=list)
    approval_status: str
    approval_reason: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    assessed_at: datetime

class KnowledgeProvenanceResponse(BaseModel):
    """Complete provenance information for a knowledge item"""
    id: UUID
    knowledge_item_id: UUID
    data_source: DataSourceResponse
    extraction_job: ExtractionJobResponse
    original_source_url: str
    source_timestamp: Optional[datetime] = None
    original_content_id: Optional[str] = None
    original_content_hash: str
    processed_content_hash: str
    extraction_timestamp: datetime
    extraction_method_version: str
    extraction_parameters: Dict[str, Any] = Field(default_factory=dict)
    processing_steps: List[Any] = Field(default_factory=list)
    transformation_log: List[Any] = Field(default_factory=list)
    validation_status: str
    validated_by: Optional[str] = None
    validated_at: Optional[datetime] = None
    version_number: int
    is_current_version: bool
    internal_notes: Optional[str] = None
    quality_lineage: Optional[List[QualityLineageResponse]] = None
    transformation_steps: Optional[List[TransformationStepResponse]] = None

class InternalAnnotationResponse(BaseModel):
    """Internal development team annotation"""
    id: UUID
    target_type: str
    target_id: UUID
    annotation_type: str
    title: Optional[str] = None
    content: str
    priority: str
    created_by: str
    assigned_to: Optional[str] = None
    status: str
    resolution_notes: Optional[str] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    tags: List[str] = Field(default_factory=list)
    visibility: str
    created_at: datetime
    updated_at: datetime

class UpdateHistoryResponse(BaseModel):
    """Knowledge item update history"""
    id: UUID
    knowledge_item_id: UUID
    update_type: str
    update_source: Optional[str] = None
    update_reason: Optional[str] = None
    fields_changed: List[str] = Field(default_factory=list)
    old_values: Dict[str, Any] = Field(default_factory=dict)
    new_values: Dict[str, Any] = Field(default_factory=dict)
    change_summary: Optional[str] = None
    updated_by: str
    update_method: Optional[str] = None
    impact_level: str
    affects_relationships: bool
    updated_at: datetime

class CreateAnnotationRequest(BaseModel):
    """Request to create internal annotation"""
    target_type: str = Field(..., description="Type of target entity")
    target_id: UUID = Field(..., description="ID of target entity")
    annotation_type: str = Field(..., description="Type of annotation")
    title: Optional[str] = Field(None, description="Annotation title")
    content: str = Field(..., description="Annotation content")
    priority: str = Field("normal", description="Priority level")
    assigned_to: Optional[str] = Field(None, description="Assigned developer")
    tags: List[str] = Field(default_factory=list, description="Annotation tags")

class ProvenanceQueryRequest(BaseModel):
    """Request for provenance queries"""
    knowledge_item_ids: Optional[List[UUID]] = None
    source_names: Optional[List[str]] = None
    extraction_methods: Optional[List[str]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    validation_status: Optional[List[str]] = None
    quality_score_min: Optional[float] = None
    include_transformations: bool = False
    include_quality_lineage: bool = False
    include_internal_notes: bool = False

# =============================================================================
# API ENDPOINTS
# =============================================================================

@router.get("/knowledge-item/{knowledge_item_id}", response_model=KnowledgeProvenanceResponse)
async def get_knowledge_provenance(
    knowledge_item_id: UUID,
    include_transformations: bool = Query(False, description="Include transformation steps"),
    include_quality: bool = Query(False, description="Include quality lineage"),
    include_internal: bool = Query(False, description="Include internal notes (dev team only)"),
    db=Depends(get_db_connection),
    current_user=Depends(get_current_user)
):
    """Get complete provenance information for a specific knowledge item"""
    service = ProvenanceService(db)
    
    try:
        provenance = await service.get_knowledge_provenance(
            knowledge_item_id=knowledge_item_id,
            include_transformations=include_transformations,
            include_quality=include_quality,
            include_internal=include_internal
        )
        
        if not provenance:
            raise HTTPException(status_code=404, detail="Knowledge item provenance not found")
            
        return provenance
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving provenance: {str(e)}")

@router.post("/query", response_model=List[KnowledgeProvenanceResponse])
async def query_provenance(
    query: ProvenanceQueryRequest,
    limit: int = Query(100, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db=Depends(get_db_connection),
    current_user=Depends(get_current_user)
):
    """Query provenance records with flexible filtering"""
    service = ProvenanceService(db)
    
    try:
        results = await service.query_provenance(
            query_params=query.dict(exclude_unset=True),
            limit=limit,
            offset=offset
        )
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying provenance: {str(e)}")

@router.get("/data-sources", response_model=List[DataSourceResponse])
async def get_data_sources(
    active_only: bool = Query(True, description="Only return active sources"),
    db=Depends(get_db_connection),
    current_user=Depends(get_current_user)
):
    """Get all data sources with summary statistics"""
    service = ProvenanceService(db)
    
    try:
        sources = await service.get_data_sources(active_only=active_only)
        return sources
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving data sources: {str(e)}")

@router.get("/data-sources/{source_id}/summary")
async def get_data_source_summary(
    source_id: UUID,
    db=Depends(get_db_connection),
    current_user=Depends(get_current_user)
):
    """Get detailed summary for a specific data source"""
    service = ProvenanceService(db)
    
    try:
        summary = await service.get_data_source_summary(source_id)
        
        if not summary:
            raise HTTPException(status_code=404, detail="Data source not found")
            
        return summary
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving source summary: {str(e)}")

@router.get("/extraction-jobs", response_model=List[ExtractionJobResponse])
async def get_extraction_jobs(
    source_id: Optional[UUID] = Query(None, description="Filter by data source"),
    status: Optional[str] = Query(None, description="Filter by status"),
    job_type: Optional[str] = Query(None, description="Filter by job type"),
    date_from: Optional[datetime] = Query(None, description="Filter from date"),
    date_to: Optional[datetime] = Query(None, description="Filter to date"),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db=Depends(get_db_connection),
    current_user=Depends(get_current_user)
):
    """Get extraction jobs with filtering options"""
    service = ProvenanceService(db)
    
    try:
        jobs = await service.get_extraction_jobs(
            source_id=source_id,
            status=status,
            job_type=job_type,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
            offset=offset
        )
        
        return jobs
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving extraction jobs: {str(e)}")

@router.get("/extraction-jobs/{job_id}/details")
async def get_extraction_job_details(
    job_id: UUID,
    include_provenance: bool = Query(False, description="Include related provenance records"),
    db=Depends(get_db_connection),
    current_user=Depends(get_current_user)
):
    """Get detailed information about a specific extraction job"""
    service = ProvenanceService(db)
    
    try:
        details = await service.get_extraction_job_details(
            job_id=job_id,
            include_provenance=include_provenance
        )
        
        if not details:
            raise HTTPException(status_code=404, detail="Extraction job not found")
            
        return details
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving job details: {str(e)}")

@router.get("/knowledge-item/{knowledge_item_id}/history", response_model=List[UpdateHistoryResponse])
async def get_knowledge_update_history(
    knowledge_item_id: UUID,
    limit: int = Query(50, le=200),
    db=Depends(get_db_connection),
    current_user=Depends(get_current_user)
):
    """Get complete update history for a knowledge item"""
    service = ProvenanceService(db)
    
    try:
        history = await service.get_knowledge_update_history(
            knowledge_item_id=knowledge_item_id,
            limit=limit
        )
        
        return history
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving update history: {str(e)}")

@router.post("/annotations", response_model=InternalAnnotationResponse)
async def create_internal_annotation(
    annotation: CreateAnnotationRequest,
    db=Depends(get_db_connection),
    current_user=Depends(get_current_user)
):
    """Create internal annotation (development team only)"""
    service = ProvenanceService(db)
    
    try:
        created_annotation = await service.create_internal_annotation(
            target_type=annotation.target_type,
            target_id=annotation.target_id,
            annotation_type=annotation.annotation_type,
            title=annotation.title,
            content=annotation.content,
            created_by=current_user.username,
            priority=annotation.priority,
            assigned_to=annotation.assigned_to,
            tags=annotation.tags
        )
        
        return created_annotation
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating annotation: {str(e)}")

@router.get("/annotations/{target_type}/{target_id}", response_model=List[InternalAnnotationResponse])
async def get_internal_annotations(
    target_type: str,
    target_id: UUID,
    status: Optional[str] = Query(None, description="Filter by status"),
    annotation_type: Optional[str] = Query(None, description="Filter by annotation type"),
    db=Depends(get_db_connection),
    current_user=Depends(get_current_user)
):
    """Get internal annotations for a specific entity"""
    service = ProvenanceService(db)
    
    try:
        annotations = await service.get_internal_annotations(
            target_type=target_type,
            target_id=target_id,
            status=status,
            annotation_type=annotation_type
        )
        
        return annotations
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving annotations: {str(e)}")

@router.put("/annotations/{annotation_id}/resolve")
async def resolve_annotation(
    annotation_id: UUID,
    resolution_notes: str,
    db=Depends(get_db_connection),
    current_user=Depends(get_current_user)
):
    """Resolve an internal annotation"""
    service = ProvenanceService(db)
    
    try:
        result = await service.resolve_annotation(
            annotation_id=annotation_id,
            resolution_notes=resolution_notes,
            resolved_by=current_user.username
        )
        
        if not result:
            raise HTTPException(status_code=404, detail="Annotation not found")
            
        return {"status": "resolved", "annotation_id": annotation_id}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resolving annotation: {str(e)}")

@router.get("/quality/scores")
async def get_quality_score_distribution(
    source_names: Optional[List[str]] = Query(None, description="Filter by source names"),
    date_from: Optional[datetime] = Query(None, description="Filter from date"),
    date_to: Optional[datetime] = Query(None, description="Filter to date"),
    db=Depends(get_db_connection),
    current_user=Depends(get_current_user)
):
    """Get quality score distribution across knowledge items"""
    service = ProvenanceService(db)
    
    try:
        distribution = await service.get_quality_score_distribution(
            source_names=source_names,
            date_from=date_from,
            date_to=date_to
        )
        
        return distribution
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving quality distribution: {str(e)}")

@router.get("/validation/summary")
async def get_validation_summary(
    source_names: Optional[List[str]] = Query(None, description="Filter by source names"),
    db=Depends(get_db_connection),
    current_user=Depends(get_current_user)
):
    """Get validation status summary across all knowledge items"""
    service = ProvenanceService(db)
    
    try:
        summary = await service.get_validation_summary(source_names=source_names)
        return summary
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving validation summary: {str(e)}")

@router.get("/debug/{knowledge_item_id}")
async def debug_knowledge_provenance(
    knowledge_item_id: UUID,
    db=Depends(get_db_connection),
    current_user=Depends(get_current_user)
):
    """Debug endpoint for comprehensive provenance information (development team only)"""
    service = ProvenanceService(db)
    
    try:
        debug_info = await service.get_debug_provenance(knowledge_item_id)
        
        if not debug_info:
            raise HTTPException(status_code=404, detail="Knowledge item not found")
            
        return debug_info
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving debug information: {str(e)}")

@router.get("/reports/source-reliability")
async def get_source_reliability_report(
    include_inactive: bool = Query(False, description="Include inactive sources"),
    db=Depends(get_db_connection),
    current_user=Depends(get_current_user)
):
    """Generate source reliability report for data quality assessment"""
    service = ProvenanceService(db)
    
    try:
        report = await service.generate_source_reliability_report(
            include_inactive=include_inactive
        )
        
        return report
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating reliability report: {str(e)}")

@router.get("/reports/extraction-performance")
async def get_extraction_performance_report(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    source_id: Optional[UUID] = Query(None, description="Filter by specific source"),
    db=Depends(get_db_connection),
    current_user=Depends(get_current_user)
):
    """Generate extraction performance report"""
    service = ProvenanceService(db)
    
    try:
        report = await service.generate_extraction_performance_report(
            days=days,
            source_id=source_id
        )
        
        return report
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating performance report: {str(e)}")

# =============================================================================
# BATCH OPERATIONS FOR PROVENANCE MANAGEMENT
# =============================================================================

@router.post("/batch/validate")
async def batch_validate_provenance(
    knowledge_item_ids: List[UUID],
    validation_type: str = Query("automated", description="Type of validation to perform"),
    db=Depends(get_db_connection),
    current_user=Depends(get_current_user)
):
    """Batch validate provenance records"""
    service = ProvenanceService(db)
    
    try:
        results = await service.batch_validate_provenance(
            knowledge_item_ids=knowledge_item_ids,
            validation_type=validation_type,
            validated_by=current_user.username
        )
        
        return {
            "batch_id": results["batch_id"],
            "total_items": len(knowledge_item_ids),
            "successful": results["successful"],
            "failed": results["failed"],
            "results": results["details"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in batch validation: {str(e)}")

@router.post("/batch/annotate")
async def batch_create_annotations(
    target_ids: List[UUID],
    target_type: str,
    annotation_type: str,
    content: str,
    title: Optional[str] = None,
    priority: str = "normal",
    tags: List[str] = Field(default_factory=list),
    db=Depends(get_db_connection),
    current_user=Depends(get_current_user)
):
    """Create annotations for multiple targets in batch"""
    service = ProvenanceService(db)
    
    try:
        results = await service.batch_create_annotations(
            target_ids=target_ids,
            target_type=target_type,
            annotation_type=annotation_type,
            content=content,
            title=title,
            priority=priority,
            tags=tags,
            created_by=current_user.username
        )
        
        return {
            "total_items": len(target_ids),
            "successful": results["successful"],
            "failed": results["failed"],
            "annotation_ids": results["annotation_ids"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in batch annotation creation: {str(e)}")