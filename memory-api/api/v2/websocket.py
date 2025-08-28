# ABOUTME: WebSocket API endpoints for real-time communication and progress streaming
# ABOUTME: Handles WebSocket connections, authentication, live search, and collaborative sessions

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4
import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from core.database import DatabaseManager
from core.dependencies import get_database_manager
from core.security import get_current_user
from models.websocket import (
    WebSocketMessage, WebSocketMessageType, WebSocketAuthMessage, WebSocketProgressMessage,
    WebSocketSearchMessage, WebSocketCollaborationMessage, WebSocketNotificationMessage,
    ConnectionMetadata, EventFilter, LiveSearchRequest, CollaborationCursor,
    create_progress_message, create_search_result_message, create_notification_message,
    create_error_message
)
from models.webhooks import EventType
from services.realtime_service import RealTimeService
from services.advanced_query_service import AdvancedQueryService
from services.progress_tracker import ProgressTracker
import redis.asyncio as redis

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v2/websocket", tags=["WebSocket v2"])

# Global real-time service instance (initialized in main.py)
realtime_service: Optional[RealTimeService] = None


def get_realtime_service() -> RealTimeService:
    """Get the real-time service instance"""
    global realtime_service
    if not realtime_service:
        raise HTTPException(status_code=503, detail="Real-time service not available")
    return realtime_service


async def init_realtime_service(redis_client: redis.Redis):
    """Initialize the real-time service"""
    global realtime_service
    try:
        realtime_service = RealTimeService(redis_client)
        await realtime_service.start()
        logger.info("Real-time service initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize real-time service", error=str(e))
        raise


@router.websocket("/progress/{operation_id}")
async def websocket_progress_stream(
    websocket: WebSocket,
    operation_id: UUID,
    token: Optional[str] = Query(None, description="JWT authentication token")
):
    """WebSocket endpoint for real-time progress updates of batch operations"""
    connection_id = uuid4()
    rt_service = get_realtime_service()
    
    try:
        # Authenticate if token provided
        user_data = None
        if token:
            user_data = await rt_service.authenticate_connection(websocket, token)
            if not user_data:
                await websocket.close(code=4001, reason="Authentication failed")
                return
        
        # Establish connection
        success = await rt_service.connection_manager.connect(
            websocket, 
            connection_id,
            user_id=user_data.get("user_id") if user_data else None
        )
        
        if not success:
            logger.error("Failed to establish WebSocket connection", connection_id=str(connection_id))
            return
        
        # Subscribe to progress updates for this operation
        progress_room = f"progress:{operation_id}"
        rt_service.connection_manager.join_room(connection_id, progress_room)
        
        # Send initial connection success message
        welcome_message = WebSocketMessage(
            type=WebSocketMessageType.CONNECT,
            data={
                "connection_id": str(connection_id),
                "operation_id": str(operation_id),
                "message": "Connected to progress stream"
            }
        )
        await rt_service.connection_manager.send_to_connection(connection_id, welcome_message)
        
        # Get current progress if available
        progress_tracker = ProgressTracker(rt_service.redis)
        current_progress = await progress_tracker.get_progress(operation_id)
        
        if current_progress:
            progress_message = create_progress_message(operation_id, current_progress)
            await rt_service.connection_manager.send_to_connection(connection_id, progress_message)
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for messages from client (pings, etc.)
                message_data = await websocket.receive_text()
                
                try:
                    message = json.loads(message_data)
                    message_type = message.get("type")
                    
                    if message_type == "ping":
                        # Respond to ping with pong
                        pong_message = WebSocketMessage(
                            type=WebSocketMessageType.PONG,
                            data={"timestamp": datetime.utcnow().isoformat()}
                        )
                        await rt_service.connection_manager.send_to_connection(connection_id, pong_message)
                    
                    elif message_type == "get_current_progress":
                        # Send current progress
                        current_progress = await progress_tracker.get_progress(operation_id)
                        if current_progress:
                            progress_message = create_progress_message(operation_id, current_progress)
                            await rt_service.connection_manager.send_to_connection(connection_id, progress_message)
                    
                except json.JSONDecodeError:
                    error_message = create_error_message(
                        "INVALID_MESSAGE",
                        "Invalid JSON message format"
                    )
                    await rt_service.connection_manager.send_to_connection(connection_id, error_message)
                
            except WebSocketDisconnect:
                logger.info("WebSocket client disconnected", connection_id=str(connection_id))
                break
            except Exception as e:
                logger.error("Error handling WebSocket message", error=str(e))
                error_message = create_error_message(
                    "MESSAGE_HANDLING_ERROR",
                    f"Error handling message: {str(e)}"
                )
                await rt_service.connection_manager.send_to_connection(connection_id, error_message)
    
    except Exception as e:
        logger.error("WebSocket connection error", error=str(e), connection_id=str(connection_id))
    
    finally:
        # Cleanup connection
        await rt_service.connection_manager.disconnect(connection_id)


@router.websocket("/search")
async def websocket_live_search(
    websocket: WebSocket,
    token: Optional[str] = Query(None, description="JWT authentication token")
):
    """WebSocket endpoint for real-time search results as you type"""
    connection_id = uuid4()
    rt_service = get_realtime_service()
    
    try:
        # Authenticate if token provided
        user_data = None
        if token:
            user_data = await rt_service.authenticate_connection(websocket, token)
            if not user_data:
                await websocket.close(code=4001, reason="Authentication failed")
                return
        
        # Establish connection
        success = await rt_service.connection_manager.connect(
            websocket, 
            connection_id,
            user_id=user_data.get("user_id") if user_data else None
        )
        
        if not success:
            return
        
        # Send connection success
        welcome_message = WebSocketMessage(
            type=WebSocketMessageType.CONNECT,
            data={
                "connection_id": str(connection_id),
                "message": "Connected to live search"
            }
        )
        await rt_service.connection_manager.send_to_connection(connection_id, welcome_message)
        
        # Track active searches for debouncing
        active_searches = {}
        
        # Handle incoming search requests
        while True:
            try:
                message_data = await websocket.receive_text()
                
                try:
                    message = json.loads(message_data)
                    message_type = message.get("type")
                    
                    if message_type == "search":
                        # Handle live search request
                        search_data = message.get("data", {})
                        
                        try:
                            search_request = LiveSearchRequest(**search_data)
                            
                            # Cancel previous search if exists
                            if search_request.query_id in active_searches:
                                active_searches[search_request.query_id].cancel()
                            
                            # Start new search with debouncing
                            search_task = asyncio.create_task(
                                _handle_live_search(
                                    connection_id, 
                                    search_request, 
                                    rt_service,
                                    user_data.get("user_id") if user_data else None
                                )
                            )
                            active_searches[search_request.query_id] = search_task
                            
                        except Exception as e:
                            error_message = create_error_message(
                                "INVALID_SEARCH_REQUEST",
                                f"Invalid search request: {str(e)}"
                            )
                            await rt_service.connection_manager.send_to_connection(connection_id, error_message)
                    
                    elif message_type == "ping":
                        pong_message = WebSocketMessage(
                            type=WebSocketMessageType.PONG,
                            data={"timestamp": datetime.utcnow().isoformat()}
                        )
                        await rt_service.connection_manager.send_to_connection(connection_id, pong_message)
                
                except json.JSONDecodeError:
                    error_message = create_error_message(
                        "INVALID_MESSAGE",
                        "Invalid JSON message format"
                    )
                    await rt_service.connection_manager.send_to_connection(connection_id, error_message)
                
            except WebSocketDisconnect:
                # Cancel all active searches
                for task in active_searches.values():
                    task.cancel()
                break
            except Exception as e:
                logger.error("Error handling live search", error=str(e))
    
    finally:
        await rt_service.connection_manager.disconnect(connection_id)


@router.websocket("/session/{session_id}")
async def websocket_collaborative_session(
    websocket: WebSocket,
    session_id: UUID,
    token: str = Query(..., description="JWT authentication token")
):
    """WebSocket endpoint for collaborative multi-user sessions"""
    connection_id = uuid4()
    rt_service = get_realtime_service()
    
    try:
        # Authentication required for collaborative sessions
        user_data = await rt_service.authenticate_connection(websocket, token)
        if not user_data:
            await websocket.close(code=4001, reason="Authentication required")
            return
        
        user_id = user_data.get("user_id")
        if not user_id:
            await websocket.close(code=4001, reason="User ID required")
            return
        
        # Establish connection
        success = await rt_service.connection_manager.connect(
            websocket, 
            connection_id,
            user_id=user_id,
            session_id=session_id
        )
        
        if not success:
            return
        
        # Join session room
        session_room = f"session:{session_id}"
        rt_service.connection_manager.join_room(connection_id, session_room)
        
        # Notify other participants about new user joining
        join_message = WebSocketMessage(
            type=WebSocketMessageType.COLLABORATION_JOIN,
            data={
                "session_id": str(session_id),
                "user_id": str(user_id),
                "connection_id": str(connection_id),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        # Send to all other connections in the session
        await rt_service.connection_manager.send_to_session(session_id, join_message)
        
        # Send welcome message to new connection
        welcome_message = WebSocketMessage(
            type=WebSocketMessageType.CONNECT,
            data={
                "connection_id": str(connection_id),
                "session_id": str(session_id),
                "message": "Connected to collaborative session"
            }
        )
        await rt_service.connection_manager.send_to_connection(connection_id, welcome_message)
        
        # Handle collaborative messages
        while True:
            try:
                message_data = await websocket.receive_text()
                
                try:
                    message = json.loads(message_data)
                    message_type = message.get("type")
                    
                    if message_type == "collaboration_update":
                        # Handle collaboration update (cursor, content changes, etc.)
                        collab_data = message.get("data", {})
                        
                        collab_message = WebSocketMessage(
                            type=WebSocketMessageType.COLLABORATION_UPDATE,
                            data={
                                "session_id": str(session_id),
                                "user_id": str(user_id),
                                "connection_id": str(connection_id),
                                "timestamp": datetime.utcnow().isoformat(),
                                **collab_data
                            }
                        )
                        
                        # Broadcast to all other connections in session
                        connections_in_session = rt_service.connection_manager.session_connections.get(session_id, set())
                        exclude_connections = {connection_id}  # Don't send back to sender
                        
                        for other_connection_id in connections_in_session:
                            if other_connection_id not in exclude_connections:
                                await rt_service.connection_manager.send_to_connection(
                                    other_connection_id, 
                                    collab_message
                                )
                    
                    elif message_type == "cursor_update":
                        # Handle cursor position updates
                        cursor_data = message.get("data", {})
                        
                        cursor_message = WebSocketMessage(
                            type=WebSocketMessageType.COLLABORATION_CURSOR,
                            data={
                                "session_id": str(session_id),
                                "user_id": str(user_id),
                                "connection_id": str(connection_id),
                                "timestamp": datetime.utcnow().isoformat(),
                                **cursor_data
                            }
                        )
                        
                        # Broadcast cursor position to other participants
                        connections_in_session = rt_service.connection_manager.session_connections.get(session_id, set())
                        for other_connection_id in connections_in_session:
                            if other_connection_id != connection_id:
                                await rt_service.connection_manager.send_to_connection(
                                    other_connection_id, 
                                    cursor_message
                                )
                    
                    elif message_type == "ping":
                        pong_message = WebSocketMessage(
                            type=WebSocketMessageType.PONG,
                            data={"timestamp": datetime.utcnow().isoformat()}
                        )
                        await rt_service.connection_manager.send_to_connection(connection_id, pong_message)
                
                except json.JSONDecodeError:
                    error_message = create_error_message(
                        "INVALID_MESSAGE",
                        "Invalid JSON message format"
                    )
                    await rt_service.connection_manager.send_to_connection(connection_id, error_message)
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error("Error handling collaborative session", error=str(e))
    
    finally:
        # Notify other participants about user leaving
        leave_message = WebSocketMessage(
            type=WebSocketMessageType.COLLABORATION_LEAVE,
            data={
                "session_id": str(session_id),
                "user_id": str(user_id),
                "connection_id": str(connection_id),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        # Send to remaining connections in session
        await rt_service.connection_manager.send_to_session(session_id, leave_message)
        
        # Cleanup connection
        await rt_service.connection_manager.disconnect(connection_id)


@router.websocket("/notifications")
async def websocket_system_notifications(
    websocket: WebSocket,
    token: Optional[str] = Query(None, description="JWT authentication token")
):
    """WebSocket endpoint for real-time system notifications"""
    connection_id = uuid4()
    rt_service = get_realtime_service()
    
    try:
        # Authenticate if token provided
        user_data = None
        if token:
            user_data = await rt_service.authenticate_connection(websocket, token)
            if not user_data:
                await websocket.close(code=4001, reason="Authentication failed")
                return
        
        # Establish connection
        success = await rt_service.connection_manager.connect(
            websocket, 
            connection_id,
            user_id=user_data.get("user_id") if user_data else None
        )
        
        if not success:
            return
        
        # Join notifications room
        rt_service.connection_manager.join_room(connection_id, "notifications")
        
        # Send connection success
        welcome_message = WebSocketMessage(
            type=WebSocketMessageType.CONNECT,
            data={
                "connection_id": str(connection_id),
                "message": "Connected to system notifications"
            }
        )
        await rt_service.connection_manager.send_to_connection(connection_id, welcome_message)
        
        # Handle incoming messages (mostly pings)
        while True:
            try:
                message_data = await websocket.receive_text()
                
                try:
                    message = json.loads(message_data)
                    message_type = message.get("type")
                    
                    if message_type == "ping":
                        pong_message = WebSocketMessage(
                            type=WebSocketMessageType.PONG,
                            data={"timestamp": datetime.utcnow().isoformat()}
                        )
                        await rt_service.connection_manager.send_to_connection(connection_id, pong_message)
                
                except json.JSONDecodeError:
                    pass  # Ignore invalid messages for notifications endpoint
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error("Error handling notifications WebSocket", error=str(e))
    
    finally:
        await rt_service.connection_manager.disconnect(connection_id)


# REST API endpoints for WebSocket management

@router.get("/connections/stats")
async def get_websocket_stats(
    current_user = Depends(get_current_user)
):
    """Get WebSocket connection statistics"""
    try:
        rt_service = get_realtime_service()
        stats = rt_service.get_service_stats()
        
        return JSONResponse(content={
            "success": True,
            "data": stats,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error("Failed to get WebSocket stats", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get WebSocket statistics")


@router.post("/connections/{connection_id}/close")
async def close_websocket_connection(
    connection_id: UUID,
    current_user = Depends(get_current_user)
):
    """Close a specific WebSocket connection"""
    try:
        rt_service = get_realtime_service()
        
        # Check if connection exists
        if connection_id not in rt_service.connection_manager.active_connections:
            raise HTTPException(status_code=404, detail="Connection not found")
        
        # Close connection
        await rt_service.connection_manager.disconnect(connection_id)
        
        return JSONResponse(content={
            "success": True,
            "message": f"Connection {connection_id} closed successfully"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to close WebSocket connection", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to close connection")


@router.post("/broadcast")
async def broadcast_message(
    message_data: Dict[str, Any],
    current_user = Depends(get_current_user)
):
    """Broadcast message to all WebSocket connections"""
    try:
        rt_service = get_realtime_service()
        
        # Create WebSocket message
        message = WebSocketMessage(
            type=WebSocketMessageType.SYSTEM_NOTIFICATION,
            data=message_data
        )
        
        # Broadcast to all connections
        sent_count = await rt_service.connection_manager.broadcast(message)
        
        return JSONResponse(content={
            "success": True,
            "message": "Message broadcasted successfully",
            "sent_to_connections": sent_count
        })
        
    except Exception as e:
        logger.error("Failed to broadcast message", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to broadcast message")


# Helper functions

async def _handle_live_search(
    connection_id: UUID,
    search_request: LiveSearchRequest,
    rt_service: RealTimeService,
    user_id: Optional[UUID] = None
):
    """Handle live search request with debouncing"""
    try:
        # Debounce the search
        if search_request.debounce_ms > 0:
            await asyncio.sleep(search_request.debounce_ms / 1000)
        
        # Perform search using advanced query service
        # This would integrate with your existing search functionality
        db_manager = get_database_manager()  # This would need to be passed or injected
        
        # Mock search results for now - replace with actual search
        start_time = time.time()
        
        # Simulate search delay
        await asyncio.sleep(0.1)
        
        # Mock results
        results = [
            {
                "id": f"result_{i}",
                "title": f"Search result {i} for '{search_request.query}'",
                "content": f"Content matching '{search_request.query}'",
                "relevance_score": 0.95 - (i * 0.1),
                "timestamp": datetime.utcnow().isoformat()
            }
            for i in range(min(search_request.limit, 5))
        ]
        
        execution_time_ms = (time.time() - start_time) * 1000
        
        # Create search result message
        search_result_message = create_search_result_message(
            query_id=search_request.query_id,
            query=search_request.query,
            results=results,
            is_complete=True,
            execution_time_ms=execution_time_ms
        )
        
        # Send results to connection
        await rt_service.connection_manager.send_to_connection(connection_id, search_result_message)
        
    except asyncio.CancelledError:
        # Search was cancelled (new search started)
        pass
    except Exception as e:
        logger.error("Error handling live search", error=str(e))
        
        # Send error message
        error_message = create_error_message(
            "SEARCH_ERROR",
            f"Search failed: {str(e)}"
        )
        await rt_service.connection_manager.send_to_connection(connection_id, error_message)