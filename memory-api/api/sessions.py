# ABOUTME: Session management API endpoints for BETTY Memory System  
# ABOUTME: Handles chat sessions, messages, and conversation context management

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional
from uuid import UUID
import structlog
import time

from models.session import (
    SessionCreate,
    SessionUpdate,
    SessionResponse,
    SessionListResponse,
    MessageCreate,
    MessageUpdate,
    MessageResponse,
    MessageListResponse,
    ConversationResponse,
    SessionStatsResponse,
    SessionSearchQuery,
    MessageSearchQuery,
    ContextRequest,
    ContextResponse
)
from models.base import PaginationParams
from core.dependencies import DatabaseDependencies, get_all_databases
from core.security import get_current_user, SecurityManager
from services.session_service import SessionService

logger = structlog.get_logger(__name__)
router = APIRouter()

# Session endpoints
@router.post("/", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    session: SessionCreate,
    databases: DatabaseDependencies = Depends(get_all_databases),
    current_user: dict = Depends(get_current_user)
) -> SessionResponse:
    """Create a new chat session"""
    start_time = time.time()
    
    try:
        # Sanitize input
        session.title = SecurityManager.sanitize_input(session.title, 200)
        if session.description:
            session.description = SecurityManager.sanitize_input(session.description, 1000)
        
        # Set user_id from current user
        if not session.user_id:
            session.user_id = current_user.user_id
        
        session_service = SessionService(databases)
        created_session = await session_service.create_session(session)
        
        duration = time.time() - start_time
        logger.info(
            "Session created",
            session_id=str(created_session.id),
            title=created_session.title,
            duration_ms=f"{duration * 1000:.2f}",
            user_id=str(current_user.user_id)
        )
        
        return SessionResponse(
            message="Session created successfully",
            data=created_session
        )
        
    except Exception as e:
        logger.error("Failed to create session", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {str(e)}"
        )

@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: UUID,
    databases: DatabaseDependencies = Depends(get_all_databases),
    current_user: dict = Depends(get_current_user)
) -> SessionResponse:
    """Get a specific session by ID"""
    try:
        session_service = SessionService(databases)
        session = await session_service.get_session(session_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Update access tracking
        await session_service.update_access_tracking(session_id)
        
        logger.info("Session retrieved", session_id=str(session_id))
        
        return SessionResponse(
            message="Session retrieved successfully",
            data=session
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get session", session_id=str(session_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve session: {str(e)}"
        )

@router.put("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: UUID,
    updates: SessionUpdate,
    databases: DatabaseDependencies = Depends(get_all_databases),
    current_user: dict = Depends(get_current_user)
) -> SessionResponse:
    """Update a session"""
    try:
        # Sanitize input
        if updates.title:
            updates.title = SecurityManager.sanitize_input(updates.title, 200)
        if updates.description:
            updates.description = SecurityManager.sanitize_input(updates.description, 1000)
        
        session_service = SessionService(databases)
        updated_session = await session_service.update_session(session_id, updates)
        
        if not updated_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        logger.info("Session updated", session_id=str(session_id))
        
        return SessionResponse(
            message="Session updated successfully",
            data=updated_session
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update session", session_id=str(session_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update session: {str(e)}"
        )

@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: UUID,
    databases: DatabaseDependencies = Depends(get_all_databases),
    current_user: dict = Depends(get_current_user)
):
    """Delete a session and all its messages"""
    try:
        session_service = SessionService(databases)
        deleted = await session_service.delete_session(session_id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        logger.info("Session deleted", session_id=str(session_id))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete session", session_id=str(session_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete session: {str(e)}"
        )

@router.get("/", response_model=SessionListResponse)
async def list_sessions(
    pagination: PaginationParams = Depends(),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    project_id: Optional[UUID] = Query(None, description="Filter by project"),
    databases: DatabaseDependencies = Depends(get_all_databases),
    current_user: dict = Depends(get_current_user)
) -> SessionListResponse:
    """List sessions with filtering and pagination"""
    try:
        session_service = SessionService(databases)
        
        filters = {}
        if status_filter:
            filters["status"] = status_filter
        if tags:
            filters["tags"] = tags
        if project_id:
            filters["project_id"] = project_id
        
        # Filter by current user
        filters["user_id"] = current_user.user_id
        
        sessions, total_count = await session_service.list_sessions(
            pagination=pagination,
            filters=filters
        )
        
        response = SessionListResponse.create(
            items=sessions,
            total_items=total_count,
            pagination=pagination,
            message=f"Found {len(sessions)} sessions",
            data=sessions
        )
        
        logger.info(
            "Sessions listed",
            total_sessions=total_count,
            page=pagination.page,
            page_size=pagination.page_size
        )
        
        return response
        
    except Exception as e:
        logger.error("Failed to list sessions", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list sessions: {str(e)}"
        )

# Message endpoints
@router.post("/{session_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def create_message(
    session_id: UUID,
    message: MessageCreate,
    databases: DatabaseDependencies = Depends(get_all_databases),
    current_user: dict = Depends(get_current_user)
) -> MessageResponse:
    """Create a new message in a session"""
    start_time = time.time()
    
    try:
        # Sanitize input
        message.content = SecurityManager.sanitize_input(message.content, 100000)
        
        # Set session_id from URL
        message.session_id = session_id
        
        session_service = SessionService(databases)
        created_message = await session_service.create_message(message)
        
        duration = time.time() - start_time
        logger.info(
            "Message created",
            message_id=str(created_message.id),
            session_id=str(session_id),
            role=created_message.role,
            duration_ms=f"{duration * 1000:.2f}"
        )
        
        return MessageResponse(
            message="Message created successfully",
            data=created_message
        )
        
    except Exception as e:
        logger.error("Failed to create message", session_id=str(session_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create message: {str(e)}"
        )

@router.get("/{session_id}/messages", response_model=MessageListResponse)
async def get_session_messages(
    session_id: UUID,
    pagination: PaginationParams = Depends(),
    include_context: bool = Query(False, description="Include message context"),
    databases: DatabaseDependencies = Depends(get_all_databases),
    current_user: dict = Depends(get_current_user)
) -> MessageListResponse:
    """Get messages for a specific session"""
    try:
        session_service = SessionService(databases)
        
        messages, total_count = await session_service.get_session_messages(
            session_id=session_id,
            pagination=pagination,
            include_context=include_context
        )
        
        response = MessageListResponse.create(
            items=messages,
            total_items=total_count,
            pagination=pagination,
            message=f"Found {len(messages)} messages",
            data=messages
        )
        
        logger.info(
            "Session messages retrieved",
            session_id=str(session_id),
            message_count=len(messages)
        )
        
        return response
        
    except Exception as e:
        logger.error("Failed to get session messages", session_id=str(session_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve messages: {str(e)}"
        )

@router.get("/{session_id}/conversation", response_model=ConversationResponse)
async def get_conversation(
    session_id: UUID,
    include_stats: bool = Query(True, description="Include conversation statistics"),
    databases: DatabaseDependencies = Depends(get_all_databases),
    current_user: dict = Depends(get_current_user)
) -> ConversationResponse:
    """Get complete conversation for a session"""
    try:
        session_service = SessionService(databases)
        conversation = await session_service.get_conversation(session_id, include_stats)
        
        if not conversation["session"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        logger.info(
            "Conversation retrieved",
            session_id=str(session_id),
            message_count=conversation["total_messages"]
        )
        
        return ConversationResponse(
            message="Conversation retrieved successfully",
            **conversation
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get conversation", session_id=str(session_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve conversation: {str(e)}"
        )

@router.post("/{session_id}/context", response_model=ContextResponse)
async def build_context(
    session_id: UUID,
    request: ContextRequest,
    databases: DatabaseDependencies = Depends(get_all_databases),
    current_user: dict = Depends(get_current_user)
) -> ContextResponse:
    """Build conversation context for AI processing"""
    start_time = time.time()
    
    try:
        # Set session_id from URL
        request.session_id = session_id
        
        session_service = SessionService(databases)
        context = await session_service.build_context(request)
        
        duration = time.time() - start_time
        logger.info(
            "Context built",
            session_id=str(session_id),
            message_count=len(context["messages"]),
            total_tokens=context["total_tokens"],
            truncated=context["truncated"],
            duration_ms=f"{duration * 1000:.2f}"
        )
        
        return ContextResponse(
            message="Context built successfully",
            **context
        )
        
    except Exception as e:
        logger.error("Failed to build context", session_id=str(session_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to build context: {str(e)}"
        )

@router.get("/stats", response_model=SessionStatsResponse)
async def get_session_stats(
    databases: DatabaseDependencies = Depends(get_all_databases),
    current_user: dict = Depends(get_current_user)
) -> SessionStatsResponse:
    """Get session statistics"""
    try:
        session_service = SessionService(databases)
        stats = await session_service.get_session_stats(current_user.user_id)
        
        logger.info("Session stats retrieved", total_sessions=stats.total_sessions)
        
        return SessionStatsResponse(
            message="Session statistics retrieved successfully",
            data=stats
        )
        
    except Exception as e:
        logger.error("Failed to get session stats", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve statistics: {str(e)}"
        )

@router.post("/search", response_model=SessionListResponse)
async def search_sessions(
    query: SessionSearchQuery,
    pagination: PaginationParams = Depends(),
    databases: DatabaseDependencies = Depends(get_all_databases),
    current_user: dict = Depends(get_current_user)
) -> SessionListResponse:
    """Search sessions"""
    try:
        # Sanitize search query
        if query.query:
            query.query = SecurityManager.sanitize_input(query.query, 1000)
        
        # Set user filter
        query.user_id = current_user.user_id
        
        session_service = SessionService(databases)
        sessions, total_count = await session_service.search_sessions(query, pagination)
        
        response = SessionListResponse.create(
            items=sessions,
            total_items=total_count,
            pagination=pagination,
            message=f"Found {len(sessions)} matching sessions",
            data=sessions
        )
        
        logger.info(
            "Session search completed",
            query=query.query[:100] if query.query else "no query",
            results_count=len(sessions)
        )
        
        return response
        
    except Exception as e:
        logger.error("Session search failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )