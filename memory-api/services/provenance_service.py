"""
ABOUTME: Service layer for data provenance tracking and management in BETTY
ABOUTME: Handles complex provenance queries, quality tracking, and internal annotations
"""

import json
import hashlib
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID, uuid4

import asyncpg
from ..core.logging_config import get_logger

logger = get_logger(__name__)

class ProvenanceService:
    """Service for managing data provenance tracking and queries"""
    
    def __init__(self, db_connection: asyncpg.Connection):
        self.db = db_connection
    
    async def get_knowledge_provenance(
        self,
        knowledge_item_id: UUID,
        include_transformations: bool = False,
        include_quality: bool = False,
        include_internal: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Get complete provenance information for a knowledge item"""
        
        query = """
        SELECT 
            kp.*,
            ds.source_name, ds.source_type, ds.base_url, ds.description as source_description,
            ds.reliability_score, ds.update_frequency, ds.access_method, ds.is_active,
            ds.last_accessed_at, ds.last_successful_extraction, ds.consecutive_failures,
            ds.metadata as source_metadata,
            ej.job_name, ej.job_type, ej.extraction_method, ej.extraction_version,
            ej.target_url, ej.target_query, ej.started_at as job_started_at,
            ej.completed_at as job_completed_at, ej.status as job_status,
            ej.items_discovered, ej.items_processed, ej.items_successful,
            ej.items_failed, ej.items_duplicated, ej.error_message as job_error,
            ej.data_quality_score, ej.metadata as job_metadata
        FROM knowledge_provenance kp
        JOIN data_sources ds ON kp.data_source_id = ds.id
        JOIN extraction_jobs ej ON kp.extraction_job_id = ej.id
        WHERE kp.knowledge_item_id = $1 AND kp.is_current_version = true
        """
        
        row = await self.db.fetchrow(query, knowledge_item_id)
        if not row:
            return None
        
        # Build base provenance response
        provenance = {
            "id": row["id"],
            "knowledge_item_id": row["knowledge_item_id"],
            "data_source": {
                "id": row["data_source_id"],
                "source_name": row["source_name"],
                "source_type": row["source_type"],
                "base_url": row["base_url"],
                "description": row["source_description"],
                "reliability_score": row["reliability_score"],
                "update_frequency": row["update_frequency"],
                "access_method": row["access_method"],
                "is_active": row["is_active"],
                "last_accessed_at": row["last_accessed_at"],
                "last_successful_extraction": row["last_successful_extraction"],
                "consecutive_failures": row["consecutive_failures"],
                "metadata": row["source_metadata"] or {}
            },
            "extraction_job": {
                "id": row["extraction_job_id"],
                "job_name": row["job_name"],
                "job_type": row["job_type"],
                "extraction_method": row["extraction_method"],
                "extraction_version": row["extraction_version"],
                "target_url": row["target_url"],
                "target_query": row["target_query"],
                "started_at": row["job_started_at"],
                "completed_at": row["job_completed_at"],
                "status": row["job_status"],
                "items_discovered": row["items_discovered"],
                "items_processed": row["items_processed"],
                "items_successful": row["items_successful"],
                "items_failed": row["items_failed"],
                "items_duplicated": row["items_duplicated"],
                "error_message": row["job_error"],
                "data_quality_score": row["data_quality_score"],
                "metadata": row["job_metadata"] or {}
            },
            "original_source_url": row["original_source_url"],
            "source_timestamp": row["source_timestamp"],
            "original_content_id": row["original_content_id"],
            "original_content_hash": row["original_content_hash"],
            "processed_content_hash": row["processed_content_hash"],
            "extraction_timestamp": row["extraction_timestamp"],
            "extraction_method_version": row["extraction_method_version"],
            "extraction_parameters": row["extraction_parameters"] or {},
            "processing_steps": row["processing_steps"] or [],
            "transformation_log": row["transformation_log"] or [],
            "validation_status": row["validation_status"],
            "validated_by": row["validated_by"],
            "validated_at": row["validated_at"],
            "version_number": row["version_number"],
            "is_current_version": row["is_current_version"],
            "internal_notes": row["internal_notes"] if include_internal else None
        }
        
        # Include transformation steps if requested
        if include_transformations:
            transformations = await self._get_transformation_steps(row["id"])
            provenance["transformation_steps"] = transformations
        
        # Include quality lineage if requested  
        if include_quality:
            quality_lineage = await self._get_quality_lineage(row["id"])
            provenance["quality_lineage"] = quality_lineage
        
        return provenance
    
    async def _get_transformation_steps(self, provenance_id: UUID) -> List[Dict[str, Any]]:
        """Get transformation steps for a provenance record"""
        
        query = """
        SELECT *
        FROM transformation_steps
        WHERE knowledge_provenance_id = $1
        ORDER BY step_order
        """
        
        rows = await self.db.fetch(query, provenance_id)
        
        return [
            {
                "id": row["id"],
                "step_name": row["step_name"],
                "step_order": row["step_order"],
                "processor_name": row["processor_name"],
                "processor_version": row["processor_version"],
                "started_at": row["started_at"],
                "completed_at": row["completed_at"],
                "execution_time_ms": row["execution_time_ms"],
                "status": row["status"],
                "input_hash": row["input_hash"],
                "output_hash": row["output_hash"],
                "parameters": row["parameters"] or {},
                "results": row["results"] or {},
                "changes_made": row["changes_made"] or [],
                "error_message": row["error_message"],
                "quality_impact_score": row["quality_impact_score"]
            }
            for row in rows
        ]
    
    async def _get_quality_lineage(self, provenance_id: UUID) -> List[Dict[str, Any]]:
        """Get quality lineage for a provenance record"""
        
        query = """
        SELECT *
        FROM quality_lineage
        WHERE knowledge_provenance_id = $1
        ORDER BY assessed_at DESC
        """
        
        rows = await self.db.fetch(query, provenance_id)
        
        return [
            {
                "id": row["id"],
                "assessment_type": row["assessment_type"],
                "assessor_name": row["assessor_name"],
                "assessor_type": row["assessor_type"],
                "overall_quality_score": row["overall_quality_score"],
                "accuracy_score": row["accuracy_score"],
                "completeness_score": row["completeness_score"],
                "relevance_score": row["relevance_score"],
                "freshness_score": row["freshness_score"],
                "quality_criteria": row["quality_criteria"] or {},
                "assessment_results": row["assessment_results"] or {},
                "issues_found": row["issues_found"] or [],
                "recommendations": row["recommendations"] or [],
                "approval_status": row["approval_status"],
                "approval_reason": row["approval_reason"],
                "approved_by": row["approved_by"],
                "approved_at": row["approved_at"],
                "assessed_at": row["assessed_at"]
            }
            for row in rows
        ]
    
    async def query_provenance(
        self,
        query_params: Dict[str, Any],
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Query provenance records with flexible filtering"""
        
        conditions = []
        params = []
        param_count = 0
        
        # Build dynamic query based on parameters
        base_query = """
        SELECT kp.*, ds.source_name, ds.source_type, ds.reliability_score,
               ej.job_name, ej.extraction_method, ej.extraction_version
        FROM knowledge_provenance kp
        JOIN data_sources ds ON kp.data_source_id = ds.id
        JOIN extraction_jobs ej ON kp.extraction_job_id = ej.id
        WHERE kp.is_current_version = true
        """
        
        if query_params.get("knowledge_item_ids"):
            param_count += 1
            conditions.append(f"kp.knowledge_item_id = ANY(${param_count})")
            params.append(query_params["knowledge_item_ids"])
        
        if query_params.get("source_names"):
            param_count += 1
            conditions.append(f"ds.source_name = ANY(${param_count})")
            params.append(query_params["source_names"])
        
        if query_params.get("extraction_methods"):
            param_count += 1
            conditions.append(f"ej.extraction_method = ANY(${param_count})")
            params.append(query_params["extraction_methods"])
        
        if query_params.get("date_from"):
            param_count += 1
            conditions.append(f"kp.extraction_timestamp >= ${param_count}")
            params.append(query_params["date_from"])
        
        if query_params.get("date_to"):
            param_count += 1
            conditions.append(f"kp.extraction_timestamp <= ${param_count}")
            params.append(query_params["date_to"])
        
        if query_params.get("validation_status"):
            param_count += 1
            conditions.append(f"kp.validation_status = ANY(${param_count})")
            params.append(query_params["validation_status"])
        
        if query_params.get("quality_score_min"):
            # Need to join with quality_lineage for this
            base_query = base_query.replace(
                "FROM knowledge_provenance kp",
                "FROM knowledge_provenance kp LEFT JOIN quality_lineage ql ON kp.id = ql.knowledge_provenance_id"
            )
            param_count += 1
            conditions.append(f"ql.overall_quality_score >= ${param_count}")
            params.append(query_params["quality_score_min"])
        
        # Add conditions to query
        if conditions:
            base_query += " AND " + " AND ".join(conditions)
        
        # Add ordering and pagination
        base_query += f" ORDER BY kp.extraction_timestamp DESC LIMIT ${param_count + 1} OFFSET ${param_count + 2}"
        params.extend([limit, offset])
        
        rows = await self.db.fetch(base_query, *params)
        
        results = []
        for row in rows:
            provenance = {
                "id": row["id"],
                "knowledge_item_id": row["knowledge_item_id"],
                "data_source": {
                    "source_name": row["source_name"],
                    "source_type": row["source_type"],
                    "reliability_score": row["reliability_score"]
                },
                "extraction_job": {
                    "job_name": row["job_name"],
                    "extraction_method": row["extraction_method"],
                    "extraction_version": row["extraction_version"]
                },
                "original_source_url": row["original_source_url"],
                "extraction_timestamp": row["extraction_timestamp"],
                "validation_status": row["validation_status"],
                "version_number": row["version_number"]
            }
            
            # Add detailed information if requested
            if query_params.get("include_transformations"):
                provenance["transformation_steps"] = await self._get_transformation_steps(row["id"])
            
            if query_params.get("include_quality_lineage"):
                provenance["quality_lineage"] = await self._get_quality_lineage(row["id"])
            
            results.append(provenance)
        
        return results
    
    async def get_data_sources(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get all data sources with summary statistics"""
        
        query = """
        SELECT ds.*, 
               COUNT(DISTINCT ej.id) as total_extraction_jobs,
               COUNT(DISTINCT kp.knowledge_item_id) as total_knowledge_items,
               AVG(ql.overall_quality_score) as avg_quality_score,
               MAX(ej.completed_at) as last_extraction,
               SUM(ej.items_successful) as total_items_extracted,
               SUM(ej.items_failed) as total_items_failed
        FROM data_sources ds
        LEFT JOIN extraction_jobs ej ON ds.id = ej.data_source_id
        LEFT JOIN knowledge_provenance kp ON ej.id = kp.extraction_job_id
        LEFT JOIN quality_lineage ql ON kp.id = ql.knowledge_provenance_id
        """
        
        params = []
        if active_only:
            query += " WHERE ds.is_active = true"
        
        query += " GROUP BY ds.id ORDER BY ds.source_name"
        
        rows = await self.db.fetch(query)
        
        return [
            {
                "id": row["id"],
                "source_name": row["source_name"],
                "source_type": row["source_type"],
                "base_url": row["base_url"],
                "description": row["description"],
                "reliability_score": row["reliability_score"],
                "update_frequency": row["update_frequency"],
                "access_method": row["access_method"],
                "is_active": row["is_active"],
                "last_accessed_at": row["last_accessed_at"],
                "last_successful_extraction": row["last_successful_extraction"],
                "consecutive_failures": row["consecutive_failures"],
                "metadata": row["metadata"] or {},
                "total_extraction_jobs": row["total_extraction_jobs"] or 0,
                "total_knowledge_items": row["total_knowledge_items"] or 0,
                "avg_quality_score": row["avg_quality_score"],
                "last_extraction": row["last_extraction"],
                "total_items_extracted": row["total_items_extracted"] or 0,
                "total_items_failed": row["total_items_failed"] or 0
            }
            for row in rows
        ]
    
    async def get_data_source_summary(self, source_id: UUID) -> Optional[Dict[str, Any]]:
        """Get detailed summary for a specific data source"""
        
        query = """
        SELECT * FROM data_source_summary WHERE id = $1
        """
        
        row = await self.db.fetchrow(query, source_id)
        if not row:
            return None
        
        return dict(row)
    
    async def get_extraction_jobs(
        self,
        source_id: Optional[UUID] = None,
        status: Optional[str] = None,
        job_type: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get extraction jobs with filtering options"""
        
        conditions = []
        params = []
        param_count = 0
        
        query = "SELECT * FROM extraction_jobs WHERE 1=1"
        
        if source_id:
            param_count += 1
            conditions.append(f"data_source_id = ${param_count}")
            params.append(source_id)
        
        if status:
            param_count += 1
            conditions.append(f"status = ${param_count}")
            params.append(status)
        
        if job_type:
            param_count += 1
            conditions.append(f"job_type = ${param_count}")
            params.append(job_type)
        
        if date_from:
            param_count += 1
            conditions.append(f"started_at >= ${param_count}")
            params.append(date_from)
        
        if date_to:
            param_count += 1
            conditions.append(f"started_at <= ${param_count}")
            params.append(date_to)
        
        if conditions:
            query += " AND " + " AND ".join(conditions)
        
        query += f" ORDER BY started_at DESC LIMIT ${param_count + 1} OFFSET ${param_count + 2}"
        params.extend([limit, offset])
        
        rows = await self.db.fetch(query, *params)
        
        return [dict(row) for row in rows]
    
    async def get_knowledge_update_history(
        self,
        knowledge_item_id: UUID,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get complete update history for a knowledge item"""
        
        query = """
        SELECT *
        FROM knowledge_update_history
        WHERE knowledge_item_id = $1
        ORDER BY updated_at DESC
        LIMIT $2
        """
        
        rows = await self.db.fetch(query, knowledge_item_id, limit)
        
        return [
            {
                "id": row["id"],
                "knowledge_item_id": row["knowledge_item_id"],
                "update_type": row["update_type"],
                "update_source": row["update_source"],
                "update_reason": row["update_reason"],
                "fields_changed": row["fields_changed"] or [],
                "old_values": row["old_values"] or {},
                "new_values": row["new_values"] or {},
                "change_summary": row["change_summary"],
                "updated_by": row["updated_by"],
                "update_method": row["update_method"],
                "impact_level": row["impact_level"],
                "affects_relationships": row["affects_relationships"],
                "updated_at": row["updated_at"]
            }
            for row in rows
        ]
    
    async def create_internal_annotation(
        self,
        target_type: str,
        target_id: UUID,
        annotation_type: str,
        content: str,
        created_by: str,
        title: Optional[str] = None,
        priority: str = "normal",
        assigned_to: Optional[str] = None,
        tags: List[str] = None
    ) -> Dict[str, Any]:
        """Create internal annotation"""
        
        annotation_id = uuid4()
        tags = tags or []
        
        query = """
        INSERT INTO internal_annotations (
            id, target_type, target_id, annotation_type, title, content,
            priority, created_by, assigned_to, tags
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        RETURNING *
        """
        
        row = await self.db.fetchrow(
            query, annotation_id, target_type, target_id, annotation_type,
            title, content, priority, created_by, assigned_to, json.dumps(tags)
        )
        
        return dict(row)
    
    async def get_internal_annotations(
        self,
        target_type: str,
        target_id: UUID,
        status: Optional[str] = None,
        annotation_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get internal annotations for a specific entity"""
        
        conditions = ["target_type = $1", "target_id = $2"]
        params = [target_type, target_id]
        param_count = 2
        
        if status:
            param_count += 1
            conditions.append(f"status = ${param_count}")
            params.append(status)
        
        if annotation_type:
            param_count += 1
            conditions.append(f"annotation_type = ${param_count}")
            params.append(annotation_type)
        
        query = f"""
        SELECT *
        FROM internal_annotations
        WHERE {' AND '.join(conditions)}
        ORDER BY created_at DESC
        """
        
        rows = await self.db.fetch(query, *params)
        
        return [dict(row) for row in rows]
    
    async def resolve_annotation(
        self,
        annotation_id: UUID,
        resolution_notes: str,
        resolved_by: str
    ) -> bool:
        """Resolve an internal annotation"""
        
        query = """
        UPDATE internal_annotations
        SET status = 'resolved',
            resolution_notes = $2,
            resolved_by = $3,
            resolved_at = CURRENT_TIMESTAMP,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = $1
        RETURNING id
        """
        
        row = await self.db.fetchrow(query, annotation_id, resolution_notes, resolved_by)
        return row is not None
    
    async def get_quality_score_distribution(
        self,
        source_names: Optional[List[str]] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get quality score distribution across knowledge items"""
        
        conditions = []
        params = []
        param_count = 0
        
        query = """
        SELECT 
            COUNT(*) as total_items,
            AVG(ql.overall_quality_score) as avg_score,
            MIN(ql.overall_quality_score) as min_score,
            MAX(ql.overall_quality_score) as max_score,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ql.overall_quality_score) as median_score,
            COUNT(CASE WHEN ql.overall_quality_score >= 0.8 THEN 1 END) as high_quality_count,
            COUNT(CASE WHEN ql.overall_quality_score BETWEEN 0.5 AND 0.8 THEN 1 END) as medium_quality_count,
            COUNT(CASE WHEN ql.overall_quality_score < 0.5 THEN 1 END) as low_quality_count
        FROM knowledge_provenance kp
        JOIN quality_lineage ql ON kp.id = ql.knowledge_provenance_id
        JOIN data_sources ds ON kp.data_source_id = ds.id
        WHERE kp.is_current_version = true
        """
        
        if source_names:
            param_count += 1
            conditions.append(f"ds.source_name = ANY(${param_count})")
            params.append(source_names)
        
        if date_from:
            param_count += 1
            conditions.append(f"ql.assessed_at >= ${param_count}")
            params.append(date_from)
        
        if date_to:
            param_count += 1
            conditions.append(f"ql.assessed_at <= ${param_count}")
            params.append(date_to)
        
        if conditions:
            query += " AND " + " AND ".join(conditions)
        
        row = await self.db.fetchrow(query, *params)
        
        return dict(row) if row else {}
    
    async def get_validation_summary(
        self,
        source_names: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get validation status summary across all knowledge items"""
        
        conditions = []
        params = []
        param_count = 0
        
        query = """
        SELECT 
            COUNT(*) as total_items,
            COUNT(CASE WHEN validation_status = 'passed' THEN 1 END) as passed_count,
            COUNT(CASE WHEN validation_status = 'failed' THEN 1 END) as failed_count,
            COUNT(CASE WHEN validation_status = 'warning' THEN 1 END) as warning_count,
            COUNT(CASE WHEN validation_status = 'pending' THEN 1 END) as pending_count,
            COUNT(CASE WHEN validation_status = 'needs_review' THEN 1 END) as needs_review_count
        FROM knowledge_provenance kp
        JOIN data_sources ds ON kp.data_source_id = ds.id
        WHERE kp.is_current_version = true
        """
        
        if source_names:
            param_count += 1
            conditions.append(f"ds.source_name = ANY(${param_count})")
            params.append(source_names)
        
        if conditions:
            query += " AND " + " AND ".join(conditions)
        
        row = await self.db.fetchrow(query, *params)
        
        return dict(row) if row else {}
    
    async def get_debug_provenance(self, knowledge_item_id: UUID) -> Optional[Dict[str, Any]]:
        """Debug endpoint for comprehensive provenance information"""
        
        # Get full provenance with all details
        provenance = await self.get_knowledge_provenance(
            knowledge_item_id=knowledge_item_id,
            include_transformations=True,
            include_quality=True,
            include_internal=True
        )
        
        if not provenance:
            return None
        
        # Add additional debug information
        debug_info = {
            "provenance": provenance,
            "annotations": await self.get_internal_annotations("knowledge_item", knowledge_item_id),
            "update_history": await self.get_knowledge_update_history(knowledge_item_id, limit=20),
            "raw_content_analysis": {
                "original_content_hash": provenance["original_content_hash"],
                "processed_content_hash": provenance["processed_content_hash"],
                "hash_match": provenance["original_content_hash"] == provenance["processed_content_hash"],
                "processing_steps_count": len(provenance.get("transformation_steps", [])),
                "quality_assessments_count": len(provenance.get("quality_lineage", []))
            }
        }
        
        return debug_info
    
    async def generate_source_reliability_report(
        self, include_inactive: bool = False
    ) -> Dict[str, Any]:
        """Generate source reliability report for data quality assessment"""
        
        query = """
        SELECT 
            ds.source_name,
            ds.source_type,
            ds.reliability_score,
            ds.is_active,
            ds.consecutive_failures,
            COUNT(DISTINCT ej.id) as total_jobs,
            COUNT(DISTINCT CASE WHEN ej.status = 'completed' THEN ej.id END) as successful_jobs,
            COUNT(DISTINCT CASE WHEN ej.status = 'failed' THEN ej.id END) as failed_jobs,
            AVG(ej.data_quality_score) as avg_data_quality,
            COUNT(DISTINCT kp.knowledge_item_id) as total_knowledge_items,
            AVG(ql.overall_quality_score) as avg_quality_score
        FROM data_sources ds
        LEFT JOIN extraction_jobs ej ON ds.id = ej.data_source_id
        LEFT JOIN knowledge_provenance kp ON ej.id = kp.extraction_job_id AND kp.is_current_version = true
        LEFT JOIN quality_lineage ql ON kp.id = ql.knowledge_provenance_id
        """
        
        if not include_inactive:
            query += " WHERE ds.is_active = true"
        
        query += " GROUP BY ds.id, ds.source_name, ds.source_type, ds.reliability_score, ds.is_active, ds.consecutive_failures"
        query += " ORDER BY ds.reliability_score DESC, total_knowledge_items DESC"
        
        rows = await self.db.fetch(query)
        
        sources = []
        for row in rows:
            success_rate = 0.0
            if row["total_jobs"]:
                success_rate = row["successful_jobs"] / row["total_jobs"]
            
            sources.append({
                "source_name": row["source_name"],
                "source_type": row["source_type"],
                "reliability_score": row["reliability_score"],
                "is_active": row["is_active"],
                "consecutive_failures": row["consecutive_failures"],
                "total_jobs": row["total_jobs"] or 0,
                "successful_jobs": row["successful_jobs"] or 0,
                "failed_jobs": row["failed_jobs"] or 0,
                "success_rate": success_rate,
                "avg_data_quality": row["avg_data_quality"],
                "total_knowledge_items": row["total_knowledge_items"] or 0,
                "avg_quality_score": row["avg_quality_score"]
            })
        
        # Calculate overall statistics
        total_sources = len(sources)
        active_sources = len([s for s in sources if s["is_active"]])
        avg_reliability = sum(s["reliability_score"] for s in sources) / total_sources if total_sources > 0 else 0
        
        return {
            "report_generated_at": datetime.now(timezone.utc),
            "summary": {
                "total_sources": total_sources,
                "active_sources": active_sources,
                "inactive_sources": total_sources - active_sources,
                "avg_reliability_score": avg_reliability
            },
            "sources": sources
        }
    
    async def generate_extraction_performance_report(
        self,
        days: int = 30,
        source_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Generate extraction performance report"""
        
        date_cutoff = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        date_cutoff = date_cutoff.replace(day=date_cutoff.day - days)
        
        conditions = ["started_at >= $1"]
        params = [date_cutoff]
        param_count = 1
        
        if source_id:
            param_count += 1
            conditions.append(f"data_source_id = ${param_count}")
            params.append(source_id)
        
        query = f"""
        SELECT 
            DATE(started_at) as extraction_date,
            COUNT(*) as total_jobs,
            COUNT(CASE WHEN status = 'completed' THEN 1 END) as successful_jobs,
            COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_jobs,
            SUM(items_successful) as total_items_extracted,
            SUM(items_failed) as total_items_failed,
            AVG(EXTRACT(EPOCH FROM (completed_at - started_at))) as avg_duration_seconds,
            AVG(data_quality_score) as avg_quality_score
        FROM extraction_jobs
        WHERE {' AND '.join(conditions)}
        GROUP BY DATE(started_at)
        ORDER BY extraction_date DESC
        """
        
        daily_stats = await self.db.fetch(query, *params)
        
        # Overall statistics
        overall_query = f"""
        SELECT 
            COUNT(*) as total_jobs,
            COUNT(CASE WHEN status = 'completed' THEN 1 END) as successful_jobs,
            COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_jobs,
            SUM(items_successful) as total_items_extracted,
            SUM(items_failed) as total_items_failed,
            AVG(EXTRACT(EPOCH FROM (completed_at - started_at))) as avg_duration_seconds,
            AVG(data_quality_score) as avg_quality_score
        FROM extraction_jobs
        WHERE {' AND '.join(conditions)}
        """
        
        overall_row = await self.db.fetchrow(overall_query, *params)
        
        return {
            "report_generated_at": datetime.now(timezone.utc),
            "period_days": days,
            "period_start": date_cutoff,
            "overall_stats": dict(overall_row) if overall_row else {},
            "daily_stats": [dict(row) for row in daily_stats]
        }
    
    async def batch_validate_provenance(
        self,
        knowledge_item_ids: List[UUID],
        validation_type: str,
        validated_by: str
    ) -> Dict[str, Any]:
        """Batch validate provenance records"""
        
        batch_id = uuid4()
        successful = 0
        failed = 0
        results = []
        
        for knowledge_item_id in knowledge_item_ids:
            try:
                # Update validation status
                query = """
                UPDATE knowledge_provenance
                SET validation_status = $1,
                    validated_by = $2,
                    validated_at = CURRENT_TIMESTAMP
                WHERE knowledge_item_id = $3 AND is_current_version = true
                RETURNING id
                """
                
                row = await self.db.fetchrow(query, "passed", validated_by, knowledge_item_id)
                
                if row:
                    successful += 1
                    results.append({
                        "knowledge_item_id": knowledge_item_id,
                        "status": "success",
                        "message": "Validation updated"
                    })
                else:
                    failed += 1
                    results.append({
                        "knowledge_item_id": knowledge_item_id,
                        "status": "failed",
                        "message": "Provenance record not found"
                    })
                
            except Exception as e:
                logger.error(f"Error validating provenance for {knowledge_item_id}: {str(e)}")
                failed += 1
                results.append({
                    "knowledge_item_id": knowledge_item_id,
                    "status": "error",
                    "message": str(e)
                })
        
        return {
            "batch_id": batch_id,
            "successful": successful,
            "failed": failed,
            "details": results
        }
    
    async def batch_create_annotations(
        self,
        target_ids: List[UUID],
        target_type: str,
        annotation_type: str,
        content: str,
        created_by: str,
        title: Optional[str] = None,
        priority: str = "normal",
        tags: List[str] = None
    ) -> Dict[str, Any]:
        """Create annotations for multiple targets in batch"""
        
        tags = tags or []
        successful = 0
        failed = 0
        annotation_ids = []
        
        for target_id in target_ids:
            try:
                annotation = await self.create_internal_annotation(
                    target_type=target_type,
                    target_id=target_id,
                    annotation_type=annotation_type,
                    content=content,
                    created_by=created_by,
                    title=title,
                    priority=priority,
                    tags=tags
                )
                
                successful += 1
                annotation_ids.append(annotation["id"])
                
            except Exception as e:
                logger.error(f"Error creating annotation for {target_id}: {str(e)}")
                failed += 1
        
        return {
            "successful": successful,
            "failed": failed,
            "annotation_ids": annotation_ids
        }