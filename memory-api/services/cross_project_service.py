# ABOUTME: Service class for cross-project intelligence and knowledge sharing
# ABOUTME: Handles project connections, knowledge transfer, pattern sharing, and collaborative filtering

import asyncio
import time
import json
from typing import Dict, List, Any, Optional, Union, Tuple
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np
import structlog

from models.base import PaginationParams
from models.cross_project import (
    ProjectConnection,
    ProjectConnectionCreate,
    KnowledgeTransferRequest,
    PatternSharingRequest,
    ProjectSimilarityRequest,
    CrossProjectSearchRequest,
    ProjectKnowledgeMapRequest,
    CollaborativeFilteringRequest,
    ProjectInsightsRequest,
    KnowledgeGapAnalysisRequest,
    ConnectionType,
    TransferStrategy,
    RecommendationType
)
from core.dependencies import DatabaseDependencies
from services.base_service import BaseService
from services.knowledge_service import KnowledgeService
from services.vector_service import VectorService
from services.cache_intelligence import CacheIntelligence

logger = structlog.get_logger(__name__)

class CrossProjectService(BaseService):
    """Service for cross-project intelligence operations"""
    
    def __init__(self, databases: DatabaseDependencies):
        super().__init__(databases)
        self.knowledge_service = KnowledgeService(databases)
        self.vector_service = VectorService(databases)
        self.cache = CacheIntelligence(databases.redis)
    
    # Project Connection Management
    async def create_project_connection(
        self,
        connection: ProjectConnectionCreate,
        user_id: UUID
    ) -> ProjectConnection:
        """Create a new project connection"""
        try:
            # Validate projects exist and user has permissions
            await self._validate_project_access(connection.source_project_id, user_id)
            await self._validate_project_access(connection.target_project_id, user_id)
            
            # Check for existing connection
            existing = await self._get_existing_connection(
                connection.source_project_id,
                connection.target_project_id
            )
            
            if existing:
                raise ValueError("Connection already exists between these projects")
            
            # Create connection record
            connection_id = uuid4()
            query = """
                INSERT INTO project_connections (
                    id, source_project_id, target_project_id, connection_type,
                    permissions, sharing_rules, description, tags, 
                    connection_strength, is_active, created_by, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                RETURNING *
            """
            
            row = await self.databases.postgres.fetchrow(
                query,
                connection_id,
                connection.source_project_id,
                connection.target_project_id,
                connection.connection_type.value,
                json.dumps(connection.permissions or {}),
                json.dumps(connection.sharing_rules or {}),
                connection.description,
                connection.tags,
                1.0,  # Initial connection strength
                True,
                user_id,
                datetime.utcnow()
            )
            
            logger.info(
                "Project connection created",
                connection_id=str(connection_id),
                source=str(connection.source_project_id),
                target=str(connection.target_project_id)
            )
            
            return ProjectConnection(**dict(row))
            
        except Exception as e:
            logger.error("Failed to create project connection", error=str(e))
            raise
    
    async def validate_connection_permissions(
        self,
        source_project_id: UUID,
        target_project_id: UUID,
        user_id: UUID
    ):
        """Validate user has permissions for both projects"""
        await self._validate_project_access(source_project_id, user_id)
        await self._validate_project_access(target_project_id, user_id)
    
    async def validate_transfer_permissions(
        self,
        source_project_id: UUID,
        target_project_id: UUID,
        user_id: UUID
    ):
        """Validate user can transfer knowledge between projects"""
        # Check connection exists
        connection = await self._get_existing_connection(source_project_id, target_project_id)
        if not connection:
            raise ValueError("No connection exists between these projects")
        
        # Validate permissions
        await self.validate_connection_permissions(source_project_id, target_project_id, user_id)
    
    # Knowledge Transfer Operations
    async def transfer_knowledge(self, request: KnowledgeTransferRequest) -> Dict[str, Any]:
        """Transfer knowledge between projects"""
        start_time = time.time()
        
        try:
            # Get knowledge items to transfer
            items_to_transfer = await self._get_transfer_items(request)
            
            transferred_count = 0
            failed_count = 0
            conflicts_resolved = 0
            transfer_log = []
            
            for item in items_to_transfer:
                try:
                    # Check for conflicts in target project
                    conflict = await self._check_transfer_conflicts(item, request)
                    
                    if conflict:
                        # Resolve conflict based on strategy
                        resolution = await self._resolve_transfer_conflict(item, conflict, request)
                        if resolution.get("resolved"):
                            conflicts_resolved += 1
                        else:
                            failed_count += 1
                            continue
                    
                    # Transform item if needed
                    transformed_item = await self._transform_knowledge_item(item, request)
                    
                    # Perform transfer based on strategy
                    if request.transfer_strategy == TransferStrategy.COPY:
                        success = await self._copy_knowledge_item(transformed_item, request.target_project_id)
                    elif request.transfer_strategy == TransferStrategy.MOVE:
                        success = await self._move_knowledge_item(transformed_item, request.target_project_id)
                    elif request.transfer_strategy == TransferStrategy.LINK:
                        success = await self._link_knowledge_item(transformed_item, request.target_project_id)
                    elif request.transfer_strategy == TransferStrategy.SYNC:
                        success = await self._sync_knowledge_item(transformed_item, request.target_project_id)
                    
                    if success:
                        transferred_count += 1
                        transfer_log.append({
                            "item_id": str(item.get("id")),
                            "status": "transferred",
                            "strategy": request.transfer_strategy.value
                        })
                    else:
                        failed_count += 1
                        
                except Exception as item_error:
                    logger.error(f"Failed to transfer item {item.get('id')}", error=str(item_error))
                    failed_count += 1
                    transfer_log.append({
                        "item_id": str(item.get("id")),
                        "status": "failed",
                        "error": str(item_error)
                    })
            
            execution_time = time.time() - start_time
            
            logger.info(
                "Knowledge transfer completed",
                source_project=str(request.source_project_id),
                target_project=str(request.target_project_id),
                transferred=transferred_count,
                failed=failed_count,
                execution_time_ms=execution_time * 1000
            )
            
            return {
                "transferred_count": transferred_count,
                "failed_count": failed_count,
                "conflicts_resolved": conflicts_resolved,
                "total_items": len(items_to_transfer),
                "success_rate": transferred_count / len(items_to_transfer) if items_to_transfer else 0,
                "transfer_log": transfer_log,
                "execution_time_seconds": execution_time
            }
            
        except Exception as e:
            logger.error("Knowledge transfer failed", error=str(e))
            raise
    
    # Pattern Sharing Operations
    async def share_patterns(self, request: PatternSharingRequest) -> Dict[str, Any]:
        """Share patterns between projects"""
        try:
            # Extract patterns from source project
            source_patterns = await self._extract_project_patterns(
                request.source_project_id,
                request.pattern_types,
                request.pattern_filters,
                request.confidence_threshold
            )
            
            shared_count = 0
            failed_count = 0
            sharing_results = []
            
            for target_project_id in request.target_project_ids:
                try:
                    # Validate compatibility if requested
                    if request.validate_compatibility:
                        compatibility = await self._check_pattern_compatibility(
                            source_patterns,
                            target_project_id
                        )
                        if not compatibility.get("compatible", True):
                            failed_count += 1
                            continue
                    
                    # Apply patterns to target project
                    applied_patterns = await self._apply_patterns_to_project(
                        source_patterns,
                        target_project_id,
                        request
                    )
                    
                    shared_count += len(applied_patterns)
                    sharing_results.append({
                        "target_project_id": str(target_project_id),
                        "patterns_applied": len(applied_patterns),
                        "patterns": applied_patterns
                    })
                    
                except Exception as target_error:
                    logger.error(f"Failed to share patterns to project {target_project_id}", error=str(target_error))
                    failed_count += 1
                    sharing_results.append({
                        "target_project_id": str(target_project_id),
                        "status": "failed",
                        "error": str(target_error)
                    })
            
            logger.info(
                "Pattern sharing completed",
                source_project=str(request.source_project_id),
                target_projects=len(request.target_project_ids),
                patterns_shared=shared_count
            )
            
            return {
                "source_patterns_count": len(source_patterns),
                "target_projects_count": len(request.target_project_ids),
                "patterns_shared": shared_count,
                "failed_shares": failed_count,
                "sharing_results": sharing_results
            }
            
        except Exception as e:
            logger.error("Pattern sharing failed", error=str(e))
            raise
    
    # Project Analysis Operations
    async def analyze_project_similarity(self, request: ProjectSimilarityRequest) -> Dict[str, Any]:
        """Analyze similarity between projects"""
        start_time = time.time()
        
        try:
            # Get projects to analyze
            project_ids = request.project_ids or await self._get_all_accessible_projects()
            
            if len(project_ids) < 2:
                return {
                    "overall_similarity": 0.0,
                    "similarity_matrix": [],
                    "recommendations": [],
                    "error": "Need at least 2 projects for similarity analysis"
                }
            
            # Compute similarity matrix
            similarity_data = {}
            
            if request.analyze_content:
                content_similarity = await self._compute_content_similarity(
                    project_ids, request.similarity_algorithm
                )
                similarity_data["content"] = content_similarity
            
            if request.analyze_structure:
                structure_similarity = await self._compute_structure_similarity(project_ids)
                similarity_data["structure"] = structure_similarity
            
            if request.analyze_activity:
                activity_similarity = await self._compute_activity_similarity(
                    project_ids, request.time_window_days
                )
                similarity_data["activity"] = activity_similarity
            
            if request.analyze_users:
                user_similarity = await self._compute_user_similarity(project_ids)
                similarity_data["users"] = user_similarity
            
            if request.analyze_topics:
                topic_similarity = await self._compute_topic_similarity(project_ids)
                similarity_data["topics"] = topic_similarity
            
            # Combine similarities into overall score
            overall_similarity = await self._compute_overall_similarity(similarity_data)
            
            # Generate recommendations if requested
            recommendations = []
            if request.include_recommendations:
                recommendations = await self._generate_similarity_recommendations(
                    similarity_data, project_ids, request.max_recommendations
                )
            
            execution_time = time.time() - start_time
            
            logger.info(
                "Project similarity analysis completed",
                projects_analyzed=len(project_ids),
                overall_similarity=overall_similarity,
                execution_time_ms=execution_time * 1000
            )
            
            return {
                "overall_similarity": overall_similarity,
                "similarity_breakdown": similarity_data,
                "projects_analyzed": len(project_ids),
                "recommendations": recommendations,
                "analysis_metadata": {
                    "algorithm": request.similarity_algorithm,
                    "time_window_days": request.time_window_days,
                    "execution_time_seconds": execution_time
                }
            }
            
        except Exception as e:
            logger.error("Project similarity analysis failed", error=str(e))
            raise
    
    # Cross-Project Search
    async def cross_project_search(
        self,
        request: CrossProjectSearchRequest,
        accessible_projects: List[UUID]
    ) -> Dict[str, Any]:
        """Search across multiple projects"""
        start_time = time.time()
        
        try:
            # For now, search across all knowledge regardless of project
            # This gives us working cross-project search functionality
            from services.knowledge_service import KnowledgeService
            from models.knowledge import SearchQuery
            
            # Debug log to check databases structure
            logger.info("Cross-project search - database types", 
                       postgres_type=type(self.databases.postgres).__name__ if self.databases.postgres else "None",
                       redis_type=type(self.databases.redis).__name__ if self.databases.redis else "None")
            
            knowledge_service = KnowledgeService(self.databases)
            
            # Convert cross-project request to knowledge search
            search_query = SearchQuery(
                query=request.query,
                k=request.max_results_per_project * len(accessible_projects),
                search_type=request.search_type if hasattr(request, 'search_type') else "hybrid",
                include_metadata=True
            )
            
            # Perform the search
            knowledge_results = await knowledge_service.search_knowledge(search_query)
            
            search_results = []
            projects_searched = 1  # We're searching across all knowledge
            
            # Convert knowledge results to cross-project format
            for result in knowledge_results:
                cross_project_result = {
                    "id": result.get("id"),
                    "title": result.get("title", "Untitled"),
                    "content": result.get("content", ""),
                    "knowledge_type": result.get("knowledge_type", "unknown"),
                    "tags": result.get("tags", []),
                    "created_at": result.get("created_at"),
                    "updated_at": result.get("updated_at"),
                    "score": result.get("score", 0.0),
                    "source_project_id": "default",  # All in default project for now
                    "cross_project_score": result.get("score", 0.0),
                    "metadata": result.get("metadata", {})
                }
                search_results.append(cross_project_result)
            
            # Simple ranking by score
            ranked_results = sorted(search_results, key=lambda x: x.get("score", 0), reverse=True)
            
            # Group by project if requested
            if getattr(request, 'group_by_project', False):
                grouped_results = {
                    "default": ranked_results
                }
            else:
                grouped_results = {"all_projects": ranked_results}
            
            # Find cross-references if requested (simplified)
            cross_references = []
            if getattr(request, 'include_cross_references', False):
                # Simple cross-referencing based on common tags
                for i, result1 in enumerate(ranked_results[:10]):  # Limit for performance
                    for result2 in ranked_results[i+1:20]:  # Compare with next 10
                        if result1.get("tags") and result2.get("tags"):
                            common_tags = set(result1["tags"]) & set(result2["tags"])
                            if common_tags:
                                cross_references.append({
                                    "source_id": result1["id"],
                                    "target_id": result2["id"],
                                    "relationship": "shared_tags",
                                    "common_tags": list(common_tags),
                                    "strength": len(common_tags) / max(len(result1["tags"]), len(result2["tags"]))
                                })
            
            execution_time = time.time() - start_time
            
            logger.info(
                "Cross-project search completed",
                query=request.query[:50],
                projects_searched=projects_searched,
                results_found=len(ranked_results),
                execution_time_ms=execution_time * 1000
            )
            
            return {
                "results": grouped_results,
                "cross_references": cross_references,
                "search_metadata": {
                    "query": request.query,
                    "search_type": getattr(request, 'search_type', 'hybrid'),
                    "projects_searched": projects_searched,
                    "total_results": len(ranked_results),
                    "execution_time_seconds": execution_time
                }
            }
            
        except Exception as e:
            logger.error("Cross-project search failed", error=str(e))
            raise
    
    # Knowledge Mapping
    async def generate_knowledge_map(self, request: ProjectKnowledgeMapRequest) -> Dict[str, Any]:
        """Generate knowledge map across projects"""
        start_time = time.time()
        
        try:
            # Get projects to map
            project_ids = request.project_ids or await self._get_all_accessible_projects()
            
            # Extract knowledge nodes and relationships
            nodes = []
            edges = []
            
            for project_id in project_ids:
                project_nodes = await self._extract_project_knowledge_nodes(project_id, request)
                project_edges = await self._extract_project_knowledge_edges(project_id, request)
                
                nodes.extend(project_nodes)
                edges.extend(project_edges)
            
            # Find inter-project connections
            if request.include_relationships:
                inter_project_edges = await self._find_inter_project_connections(project_ids, request)
                edges.extend(inter_project_edges)
            
            # Add user activity if requested
            if request.include_user_activity:
                activity_nodes, activity_edges = await self._add_user_activity_to_map(project_ids, request)
                nodes.extend(activity_nodes)
                edges.extend(activity_edges)
            
            # Add temporal flow if requested
            if request.include_temporal_flow:
                temporal_edges = await self._add_temporal_flow_to_map(nodes, request)
                edges.extend(temporal_edges)
            
            # Filter by connection strength
            if request.min_connection_strength > 0:
                edges = [e for e in edges if e.get("strength", 1.0) >= request.min_connection_strength]
            
            # Apply clustering if requested
            clusters = []
            if request.cluster_nodes:
                clusters = await self._cluster_knowledge_nodes(nodes, edges, request)
            
            # Apply layout algorithm
            layout_data = await self._apply_layout_algorithm(nodes, edges, request.layout_algorithm)
            
            execution_time = time.time() - start_time
            
            logger.info(
                "Knowledge map generated",
                projects_mapped=len(project_ids),
                nodes_count=len(nodes),
                edges_count=len(edges),
                execution_time_ms=execution_time * 1000
            )
            
            result = {
                "nodes": nodes,
                "edges": edges,
                "clusters": clusters,
                "layout": layout_data,
                "nodes_count": len(nodes),
                "connections_count": len(edges),
                "projects_mapped": len(project_ids),
                "execution_time_seconds": execution_time
            }
            
            # Export if requested
            if request.export_format:
                export_data = await self._export_knowledge_map(result, request.export_format)
                result["export_data"] = export_data
            
            return result
            
        except Exception as e:
            logger.error("Knowledge map generation failed", error=str(e))
            raise
    
    # Collaborative Filtering
    async def collaborative_filtering(self, request: CollaborativeFilteringRequest) -> Dict[str, Any]:
        """Generate recommendations using collaborative filtering"""
        start_time = time.time()
        
        try:
            recommendations = []
            
            if request.recommendation_type == RecommendationType.KNOWLEDGE:
                recommendations = await self._recommend_knowledge_items(request)
            elif request.recommendation_type == RecommendationType.PATTERNS:
                recommendations = await self._recommend_patterns(request)
            elif request.recommendation_type == RecommendationType.COLLABORATORS:
                recommendations = await self._recommend_collaborators(request)
            elif request.recommendation_type == RecommendationType.PROJECTS:
                recommendations = await self._recommend_projects(request)
            elif request.recommendation_type == RecommendationType.TOPICS:
                recommendations = await self._recommend_topics(request)
            
            # Apply time decay if specified
            if request.time_decay_factor < 1.0:
                recommendations = await self._apply_time_decay(recommendations, request.time_decay_factor)
            
            # Filter out already known items if requested
            if request.exclude_already_known:
                recommendations = await self._filter_known_items(recommendations, request)
            
            # Limit to max recommendations
            recommendations = recommendations[:request.max_recommendations]
            
            # Add explanations if requested
            if request.include_explanations:
                for rec in recommendations:
                    rec["explanation"] = await self._generate_recommendation_explanation(rec, request)
            
            execution_time = time.time() - start_time
            
            logger.info(
                "Collaborative filtering completed",
                recommendation_type=request.recommendation_type.value,
                recommendations_count=len(recommendations),
                execution_time_ms=execution_time * 1000
            )
            
            return {
                "recommendations": recommendations,
                "recommendation_metadata": {
                    "type": request.recommendation_type.value,
                    "similarity_metric": request.similarity_metric,
                    "min_similarity": request.min_similarity,
                    "time_decay_factor": request.time_decay_factor,
                    "execution_time_seconds": execution_time
                }
            }
            
        except Exception as e:
            logger.error("Collaborative filtering failed", error=str(e))
            raise
    
    # Project Insights
    async def generate_project_insights(self, request: ProjectInsightsRequest) -> Dict[str, Any]:
        """Generate insights from cross-project analysis"""
        start_time = time.time()
        
        try:
            # Get projects to analyze
            project_ids = request.project_ids or await self._get_all_accessible_projects()
            
            insights = []
            
            # Generate different types of insights
            insight_types = request.insight_types or [
                "trends", "anomalies", "opportunities", "benchmarks", "predictions"
            ]
            
            for insight_type in insight_types:
                try:
                    if insight_type == "trends":
                        trend_insights = await self._generate_trend_insights(project_ids, request)
                        insights.extend(trend_insights)
                    elif insight_type == "anomalies":
                        anomaly_insights = await self._generate_anomaly_insights(project_ids, request)
                        insights.extend(anomaly_insights)
                    elif insight_type == "opportunities":
                        opportunity_insights = await self._generate_opportunity_insights(project_ids, request)
                        insights.extend(opportunity_insights)
                    elif insight_type == "benchmarks" and request.include_benchmarks:
                        benchmark_insights = await self._generate_benchmark_insights(project_ids, request)
                        insights.extend(benchmark_insights)
                    elif insight_type == "predictions" and request.include_predictions:
                        prediction_insights = await self._generate_prediction_insights(project_ids, request)
                        insights.extend(prediction_insights)
                        
                except Exception as insight_error:
                    logger.error(f"Failed to generate {insight_type} insights", error=str(insight_error))
            
            # Sort insights by priority/impact
            sorted_insights = sorted(insights, key=lambda x: x.get("priority", 0), reverse=True)
            
            # Generate visualization data if requested
            visualization_data = []
            if request.include_visualizations:
                visualization_data = await self._generate_insights_visualizations(sorted_insights)
            
            execution_time = time.time() - start_time
            
            logger.info(
                "Project insights generated",
                projects_analyzed=len(project_ids),
                insights_generated=len(sorted_insights),
                execution_time_ms=execution_time * 1000
            )
            
            result = {
                "insights": sorted_insights,
                "insights_summary": await self._summarize_insights(sorted_insights),
                "projects_analyzed": len(project_ids),
                "insight_types": insight_types,
                "execution_time_seconds": execution_time
            }
            
            if visualization_data:
                result["visualizations"] = visualization_data
            
            return result
            
        except Exception as e:
            logger.error("Project insights generation failed", error=str(e))
            raise
    
    # Knowledge Gap Analysis
    async def analyze_knowledge_gaps(self, request: KnowledgeGapAnalysisRequest) -> Dict[str, Any]:
        """Analyze knowledge gaps between projects"""
        start_time = time.time()
        
        try:
            # Get reference project knowledge profile
            reference_profile = await self._build_project_knowledge_profile(
                request.reference_project_id, request
            )
            
            gaps = []
            opportunities = []
            
            # Analyze each comparison project
            for comparison_project_id in request.comparison_project_ids:
                try:
                    # Build comparison project profile
                    comparison_profile = await self._build_project_knowledge_profile(
                        comparison_project_id, request
                    )
                    
                    # Find gaps and opportunities
                    project_gaps = await self._identify_knowledge_gaps(
                        reference_profile,
                        comparison_profile,
                        request
                    )
                    
                    project_opportunities = await self._identify_transfer_opportunities(
                        reference_profile,
                        comparison_profile,
                        comparison_project_id,
                        request
                    )
                    
                    gaps.extend(project_gaps)
                    opportunities.extend(project_opportunities)
                    
                except Exception as comparison_error:
                    logger.error(f"Gap analysis failed for project {comparison_project_id}", error=str(comparison_error))
            
            # Prioritize gaps if requested
            if request.prioritize_gaps:
                gaps = await self._prioritize_knowledge_gaps(gaps, request)
                opportunities = await self._prioritize_transfer_opportunities(opportunities, request)
            
            # Generate recommendations if requested
            recommendations = []
            if request.include_recommendations:
                recommendations = await self._generate_gap_filling_recommendations(gaps, opportunities, request)
            
            execution_time = time.time() - start_time
            
            logger.info(
                "Knowledge gap analysis completed",
                reference_project=str(request.reference_project_id),
                comparison_projects=len(request.comparison_project_ids),
                gaps_identified=len(gaps),
                opportunities_found=len(opportunities),
                execution_time_ms=execution_time * 1000
            )
            
            return {
                "gaps": gaps,
                "opportunities": opportunities,
                "recommendations": recommendations,
                "analysis_summary": {
                    "reference_project_id": str(request.reference_project_id),
                    "comparison_projects_count": len(request.comparison_project_ids),
                    "total_gaps": len(gaps),
                    "high_priority_gaps": len([g for g in gaps if g.get("priority", 0) > 7]),
                    "transfer_opportunities": len(opportunities),
                    "confidence_level": request.confidence_level
                },
                "execution_time_seconds": execution_time
            }
            
        except Exception as e:
            logger.error("Knowledge gap analysis failed", error=str(e))
            raise
    
    # Connection Management
    async def list_user_connections(
        self,
        user_id: UUID,
        project_id: Optional[UUID] = None,
        connection_type: Optional[str] = None,
        pagination: Optional[PaginationParams] = None
    ) -> List[ProjectConnection]:
        """List project connections for user"""
        try:
            conditions = ["created_by = $1 OR $1 IN (SELECT user_id FROM project_members WHERE project_id IN (source_project_id, target_project_id))"]
            params = [user_id]
            param_count = 1
            
            if project_id:
                param_count += 1
                conditions.append(f"(source_project_id = ${param_count} OR target_project_id = ${param_count})")
                params.extend([project_id, project_id])
                param_count += 1
            
            if connection_type:
                param_count += 1
                conditions.append(f"connection_type = ${param_count}")
                params.append(connection_type)
            
            where_clause = " AND ".join(conditions)
            
            # Add pagination
            limit_offset = ""
            if pagination:
                param_count += 1
                limit_offset = f" LIMIT ${param_count}"
                params.append(pagination.limit)
                
                param_count += 1
                limit_offset += f" OFFSET ${param_count}"
                params.append(pagination.offset)
            
            query = f"""
                SELECT * FROM project_connections 
                WHERE {where_clause}
                ORDER BY created_at DESC
                {limit_offset}
            """
            
            rows = await self.databases.postgres.fetch(query, *params)
            
            connections = []
            for row in rows:
                data = dict(row)
                data['permissions'] = json.loads(data['permissions']) if data['permissions'] else {}
                data['sharing_rules'] = json.loads(data['sharing_rules']) if data['sharing_rules'] else {}
                connections.append(ProjectConnection(**data))
            
            return connections
            
        except Exception as e:
            logger.error("Failed to list user connections", error=str(e))
            raise
    
    async def delete_project_connection(self, connection_id: UUID, user_id: UUID) -> bool:
        """Delete a project connection"""
        try:
            query = """
                DELETE FROM project_connections 
                WHERE id = $1 AND created_by = $2
                RETURNING id
            """
            
            row = await self.databases.postgres.fetchrow(query, connection_id, user_id)
            return row is not None
            
        except Exception as e:
            logger.error("Failed to delete project connection", error=str(e))
            return False
    
    async def get_user_accessible_projects(self, user_id: UUID) -> List[UUID]:
        """Get projects accessible to user"""
        try:
            query = """
                SELECT DISTINCT p.id 
                FROM projects p
                LEFT JOIN project_members pm ON p.id = pm.project_id
                WHERE p.created_by = $1 OR pm.user_id = $1
            """
            
            rows = await self.databases.postgres.fetch(query, user_id)
            return [row['id'] for row in rows]
            
        except Exception as e:
            logger.error("Failed to get accessible projects", error=str(e))
            return []
    
    # Private helper methods
    async def _validate_project_access(self, project_id: UUID, user_id: UUID):
        """Validate user has access to project"""
        query = """
            SELECT 1 FROM projects p
            LEFT JOIN project_members pm ON p.id = pm.project_id
            WHERE p.id = $1 AND (p.created_by = $2 OR pm.user_id = $2)
        """
        
        row = await self.databases.postgres.fetchrow(query, project_id, user_id)
        if not row:
            raise ValueError(f"User does not have access to project {project_id}")
    
    async def _get_existing_connection(self, source_id: UUID, target_id: UUID) -> Optional[ProjectConnection]:
        """Check for existing connection between projects"""
        query = """
            SELECT * FROM project_connections
            WHERE (source_project_id = $1 AND target_project_id = $2)
               OR (source_project_id = $2 AND target_project_id = $1)
        """
        
        row = await self.databases.postgres.fetchrow(query, source_id, target_id)
        if row:
            data = dict(row)
            data['permissions'] = json.loads(data['permissions']) if data['permissions'] else {}
            data['sharing_rules'] = json.loads(data['sharing_rules']) if data['sharing_rules'] else {}
            return ProjectConnection(**data)
        
        return None
    
    # Placeholder implementations for complex operations
    # These would be fully implemented based on specific requirements
    
    async def _get_transfer_items(self, request: KnowledgeTransferRequest) -> List[Dict[str, Any]]:
        """Get items for transfer"""
        return []  # Placeholder
    
    async def _check_transfer_conflicts(self, item: Dict[str, Any], request: KnowledgeTransferRequest) -> Optional[Dict[str, Any]]:
        """Check for transfer conflicts"""
        return None  # Placeholder
    
    async def _resolve_transfer_conflict(self, item: Dict[str, Any], conflict: Dict[str, Any], request: KnowledgeTransferRequest) -> Dict[str, Any]:
        """Resolve transfer conflicts"""
        return {"resolved": True}  # Placeholder
    
    async def _transform_knowledge_item(self, item: Dict[str, Any], request: KnowledgeTransferRequest) -> Dict[str, Any]:
        """Transform knowledge item for transfer"""
        return item  # Placeholder
    
    async def _copy_knowledge_item(self, item: Dict[str, Any], target_project_id: UUID) -> bool:
        """Copy knowledge item to target project"""
        return True  # Placeholder
    
    async def _move_knowledge_item(self, item: Dict[str, Any], target_project_id: UUID) -> bool:
        """Move knowledge item to target project"""
        return True  # Placeholder
    
    async def _link_knowledge_item(self, item: Dict[str, Any], target_project_id: UUID) -> bool:
        """Link knowledge item to target project"""
        return True  # Placeholder
    
    async def _sync_knowledge_item(self, item: Dict[str, Any], target_project_id: UUID) -> bool:
        """Sync knowledge item with target project"""
        return True  # Placeholder
    
    # Additional placeholder implementations...
    async def _get_all_accessible_projects(self) -> List[UUID]:
        """Get all accessible projects"""
        return []  # Placeholder
    
    async def _compute_content_similarity(self, project_ids: List[UUID], algorithm: str) -> Dict[str, Any]:
        """Compute content similarity between projects"""
        return {"similarity_matrix": []}  # Placeholder
    
    async def _compute_overall_similarity(self, similarity_data: Dict[str, Any]) -> float:
        """Compute overall similarity score"""
        return 0.5  # Placeholder