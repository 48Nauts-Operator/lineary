# ABOUTME: Knowledge management API endpoints for BETTY Memory System
# ABOUTME: Handles knowledge item CRUD operations, search, and ingestion

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional
from uuid import UUID
import structlog
import time

from models.knowledge import (
    KnowledgeItemCreate,
    KnowledgeItemUpdate,
    KnowledgeItemResponse,
    KnowledgeItemListResponse,
    SearchQuery,
    SearchResponse,
    KnowledgeStatsResponse,
    BulkImportRequest,
    BulkImportResponse
)
from models.base import PaginationParams, ErrorResponse
from core.dependencies import DatabaseDependencies, get_all_databases, get_core_databases
from core.security import get_current_user, SecurityManager
from models.auth import CurrentUser
from services.knowledge_service import KnowledgeService

logger = structlog.get_logger(__name__)
router = APIRouter()

@router.post("/", response_model=KnowledgeItemResponse, status_code=status.HTTP_201_CREATED)
async def create_knowledge_item(
    item: KnowledgeItemCreate,
    databases: DatabaseDependencies = Depends(get_core_databases),
    current_user: Optional[CurrentUser] = Depends(get_current_user)
) -> KnowledgeItemResponse:
    """Create a new knowledge item"""
    start_time = time.time()
    
    try:
        # Sanitize input
        item.title = SecurityManager.sanitize_input(item.title, 500)
        item.content = SecurityManager.sanitize_input(item.content, 50000)
        
        if item.summary:
            item.summary = SecurityManager.sanitize_input(item.summary, 1000)
        
        # Set user_id from current user if authenticated
        if not item.user_id and current_user:
            item.user_id = str(current_user.user_id) if hasattr(current_user, 'user_id') else current_user.get("user_id") if isinstance(current_user, dict) else None
        
        # Create knowledge item using service
        knowledge_service = KnowledgeService(databases)
        created_item = await knowledge_service.create_knowledge_item(item)
        
        duration = time.time() - start_time
        logger.info(
            "Knowledge item created",
            item_id=str(created_item.id),
            knowledge_type=created_item.knowledge_type,
            duration_ms=f"{duration * 1000:.2f}",
            user_id=str(current_user.user_id) if hasattr(current_user, 'user_id') else current_user.get("user_id") if current_user else None
        )
        
        return KnowledgeItemResponse(
            message="Knowledge item created successfully",
            data=created_item
        )
        
    except Exception as e:
        logger.error("Failed to create knowledge item", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create knowledge item: {str(e)}"
        )

@router.post("", response_model=KnowledgeItemResponse, status_code=status.HTTP_201_CREATED)
async def create_knowledge_item_no_slash(
    item: KnowledgeItemCreate,
    databases: DatabaseDependencies = Depends(get_core_databases),
    current_user: Optional[CurrentUser] = Depends(get_current_user)
) -> KnowledgeItemResponse:
    """Create a new knowledge item (no trailing slash variant)"""
    return await create_knowledge_item(item, databases, current_user)

@router.get("/stats", response_model=KnowledgeStatsResponse)
async def get_knowledge_stats(
    databases: DatabaseDependencies = Depends(get_all_databases),
    current_user: Optional[CurrentUser] = Depends(get_current_user)
) -> KnowledgeStatsResponse:
    """Get knowledge base statistics"""
    try:
        knowledge_service = KnowledgeService(databases)
        stats = await knowledge_service.get_knowledge_stats()
        
        logger.info("Knowledge stats retrieved", total_items=stats.total_items)
        
        return KnowledgeStatsResponse(
            message="Knowledge statistics retrieved successfully",
            data=stats
        )
        
    except Exception as e:
        logger.error("Failed to get knowledge stats", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve statistics: {str(e)}"
        )

@router.get("/{item_id}", response_model=KnowledgeItemResponse)
async def get_knowledge_item(
    item_id: UUID,
    databases: DatabaseDependencies = Depends(get_all_databases),
    current_user: Optional[CurrentUser] = Depends(get_current_user)
) -> KnowledgeItemResponse:
    """Get a specific knowledge item by ID"""
    try:
        knowledge_service = KnowledgeService(databases)
        item = await knowledge_service.get_knowledge_item(item_id)
        
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Knowledge item not found"
            )
        
        # Update access tracking
        await knowledge_service.update_access_tracking(item_id)
        
        logger.info("Knowledge item retrieved", item_id=str(item_id))
        
        return KnowledgeItemResponse(
            message="Knowledge item retrieved successfully",
            data=item
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get knowledge item", item_id=str(item_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve knowledge item: {str(e)}"
        )

@router.put("/{item_id}", response_model=KnowledgeItemResponse)
async def update_knowledge_item(
    item_id: UUID,
    updates: KnowledgeItemUpdate,
    databases: DatabaseDependencies = Depends(get_all_databases),
    current_user: Optional[CurrentUser] = Depends(get_current_user)
) -> KnowledgeItemResponse:
    """Update a knowledge item"""
    try:
        # Sanitize input
        if updates.title:
            updates.title = SecurityManager.sanitize_input(updates.title, 500)
        if updates.content:
            updates.content = SecurityManager.sanitize_input(updates.content, 50000)
        if updates.summary:
            updates.summary = SecurityManager.sanitize_input(updates.summary, 1000)
        
        knowledge_service = KnowledgeService(databases)
        updated_item = await knowledge_service.update_knowledge_item(item_id, updates)
        
        if not updated_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Knowledge item not found"
            )
        
        logger.info("Knowledge item updated", item_id=str(item_id))
        
        return KnowledgeItemResponse(
            message="Knowledge item updated successfully",
            data=updated_item
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update knowledge item", item_id=str(item_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update knowledge item: {str(e)}"
        )

@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_knowledge_item(
    item_id: UUID,
    databases: DatabaseDependencies = Depends(get_all_databases),
    current_user: Optional[CurrentUser] = Depends(get_current_user)
):
    """Delete a knowledge item"""
    try:
        knowledge_service = KnowledgeService(databases)
        deleted = await knowledge_service.delete_knowledge_item(item_id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Knowledge item not found"
            )
        
        logger.info("Knowledge item deleted", item_id=str(item_id))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete knowledge item", item_id=str(item_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete knowledge item: {str(e)}"
        )

@router.get("/", response_model=KnowledgeItemListResponse)
async def list_knowledge_items(
    pagination: PaginationParams = Depends(),
    knowledge_type: Optional[str] = Query(None, description="Filter by knowledge type"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    session_id: Optional[UUID] = Query(None, description="Filter by session"),
    project_id: Optional[UUID] = Query(None, description="Filter by project"),
    databases: DatabaseDependencies = Depends(get_core_databases),
    current_user: Optional[CurrentUser] = Depends(get_current_user)
) -> KnowledgeItemListResponse:
    """List knowledge items with filtering and pagination"""
    try:
        knowledge_service = KnowledgeService(databases)
        
        filters = {}
        if knowledge_type:
            filters["knowledge_type"] = knowledge_type
        if tags:
            filters["tags"] = tags
        if session_id:
            filters["session_id"] = session_id
        if project_id:
            filters["project_id"] = project_id
        
        items, total_count = await knowledge_service.list_knowledge_items(
            pagination=pagination,
            filters=filters
        )
        
        response = KnowledgeItemListResponse.create(
            items=items,
            total_items=total_count,
            pagination=pagination,
            message=f"Found {len(items)} knowledge items"
        )
        
        logger.info(
            "Knowledge items listed",
            total_items=total_count,
            page=pagination.page,
            page_size=pagination.page_size
        )
        
        return response
        
    except Exception as e:
        logger.error("Failed to list knowledge items", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list knowledge items: {str(e)}"
        )

@router.post("/search", response_model=SearchResponse)
async def search_knowledge(
    query: SearchQuery,
    databases: DatabaseDependencies = Depends(get_all_databases),
    current_user: Optional[CurrentUser] = Depends(get_current_user)
) -> SearchResponse:
    """Search knowledge items using semantic and keyword search"""
    start_time = time.time()
    
    try:
        # Sanitize search query
        query.query = SecurityManager.sanitize_input(query.query, 1000)
        
        knowledge_service = KnowledgeService(databases)
        results = await knowledge_service.search_knowledge(query)
        
        search_time = time.time() - start_time
        
        logger.info(
            "Knowledge search completed",
            query=query.query[:100],  # Log first 100 chars
            results_count=len(results),
            search_time_ms=f"{search_time * 1000:.2f}",
            search_type=query.search_type
        )
        
        return SearchResponse(
            message=f"Found {len(results)} matching items",
            data=results,
            query=query.query,
            total_results=len(results),
            search_time_ms=search_time * 1000,
            search_type=query.search_type
        )
        
    except Exception as e:
        logger.error("Knowledge search failed", query=query.query, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )

@router.post("/bulk-import", response_model=BulkImportResponse)
async def bulk_import_knowledge(
    request: BulkImportRequest,
    databases: DatabaseDependencies = Depends(get_all_databases),
    current_user: Optional[CurrentUser] = Depends(get_current_user)
) -> BulkImportResponse:
    """Bulk import knowledge items"""
    start_time = time.time()
    
    try:
        # Sanitize all items
        for item in request.items:
            item.title = SecurityManager.sanitize_input(item.title, 500)
            item.content = SecurityManager.sanitize_input(item.content, 50000)
            if item.summary:
                item.summary = SecurityManager.sanitize_input(item.summary, 1000)
            
            # Set user_id if not provided
            if not item.user_id:
                item.user_id = str(current_user.user_id) if hasattr(current_user, 'user_id') else current_user.get("user_id") if isinstance(current_user, dict) else None
        
        knowledge_service = KnowledgeService(databases)
        result = await knowledge_service.bulk_import_knowledge(request)
        
        duration = time.time() - start_time
        
        logger.info(
            "Bulk import completed",
            total_items=result.total_items,
            imported_items=result.imported_items,
            failed_items=result.failed_items,
            duration_ms=f"{duration * 1000:.2f}"
        )
        
        return result
        
    except Exception as e:
        logger.error("Bulk import failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk import failed: {str(e)}"
        )