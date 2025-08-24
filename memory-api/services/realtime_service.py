# ABOUTME: Core real-time service for WebSocket connections and event broadcasting
# ABOUTME: Handles connection management, Redis pub/sub messaging, and real-time event distribution

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Set, Callable
from uuid import UUID, uuid4
import redis.asyncio as redis
import structlog
from fastapi import WebSocket, WebSocketDisconnect
from collections import defaultdict

from models.websocket import (
    WebSocketMessage, WebSocketMessageType, ConnectionMetadata, EventFilter,
    WebSocketHeartbeat, WebSocketError, create_error_message, create_notification_message
)
from models.webhooks import EventType
# from core.security import decode_jwt_token  # Not available

logger = structlog.get_logger(__name__)


class ConnectionManager:
    """Manages active WebSocket connections"""
    
    def __init__(self):
        # Active connections: connection_id -> WebSocket
        self.active_connections: Dict[UUID, WebSocket] = {}
        
        # Connection metadata: connection_id -> ConnectionMetadata
        self.connection_metadata: Dict[UUID, ConnectionMetadata] = {}
        
        # User connections: user_id -> Set[connection_id]
        self.user_connections: Dict[UUID, Set[UUID]] = defaultdict(set)
        
        # Session connections: session_id -> Set[connection_id]
        self.session_connections: Dict[UUID, Set[UUID]] = defaultdict(set)
        
        # Room connections: room_id -> Set[connection_id]
        self.room_connections: Dict[str, Set[UUID]] = defaultdict(set)
        
        # Connection statistics
        self.connection_stats: Dict[UUID, Dict[str, Any]] = defaultdict(dict)
        
        # Rate limiting: connection_id -> message_timestamps
        self.rate_limiting: Dict[UUID, List[float]] = defaultdict(list)
    
    async def connect(
        self, 
        websocket: WebSocket, 
        connection_id: UUID,
        user_id: Optional[UUID] = None,
        session_id: Optional[UUID] = None
    ) -> bool:
        """Accept and register a new WebSocket connection"""
        try:
            await websocket.accept()
            
            # Store connection
            self.active_connections[connection_id] = websocket
            
            # Create metadata
            metadata = ConnectionMetadata(
                connection_id=connection_id,
                user_id=user_id,
                session_id=session_id,
                ip_address=websocket.client.host if websocket.client else None,
                user_agent=websocket.headers.get("user-agent"),
                connected_at=datetime.utcnow(),
                last_activity=datetime.utcnow()
            )
            self.connection_metadata[connection_id] = metadata
            
            # Initialize statistics
            self.connection_stats[connection_id] = {
                "messages_sent": 0,
                "messages_received": 0,
                "bytes_sent": 0,
                "bytes_received": 0,
                "errors": 0,
                "connected_at": time.time()
            }
            
            # Register by user and session
            if user_id:
                self.user_connections[user_id].add(connection_id)
            
            if session_id:
                self.session_connections[session_id].add(connection_id)
            
            logger.info(
                "WebSocket connection established",
                connection_id=str(connection_id),
                user_id=str(user_id) if user_id else None,
                session_id=str(session_id) if session_id else None,
                ip=metadata.ip_address
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Failed to establish WebSocket connection",
                error=str(e),
                connection_id=str(connection_id)
            )
            return False
    
    async def disconnect(self, connection_id: UUID):
        """Disconnect and cleanup a WebSocket connection"""
        try:
            # Get metadata before cleanup
            metadata = self.connection_metadata.get(connection_id)
            
            # Remove from active connections
            if connection_id in self.active_connections:
                del self.active_connections[connection_id]
            
            # Cleanup metadata
            if connection_id in self.connection_metadata:
                del self.connection_metadata[connection_id]
            
            # Remove from user connections
            if metadata and metadata.user_id:
                self.user_connections[metadata.user_id].discard(connection_id)
                if not self.user_connections[metadata.user_id]:
                    del self.user_connections[metadata.user_id]
            
            # Remove from session connections
            if metadata and metadata.session_id:
                self.session_connections[metadata.session_id].discard(connection_id)
                if not self.session_connections[metadata.session_id]:
                    del self.session_connections[metadata.session_id]
            
            # Remove from all rooms
            for room_id, connections in list(self.room_connections.items()):
                connections.discard(connection_id)
                if not connections:
                    del self.room_connections[room_id]
            
            # Cleanup rate limiting
            if connection_id in self.rate_limiting:
                del self.rate_limiting[connection_id]
            
            # Cleanup statistics
            if connection_id in self.connection_stats:
                del self.connection_stats[connection_id]
            
            logger.info(
                "WebSocket connection cleaned up",
                connection_id=str(connection_id),
                user_id=str(metadata.user_id) if metadata and metadata.user_id else None
            )
            
        except Exception as e:
            logger.error(
                "Error during WebSocket cleanup",
                error=str(e),
                connection_id=str(connection_id)
            )
    
    async def send_to_connection(self, connection_id: UUID, message: WebSocketMessage) -> bool:
        """Send message to a specific connection"""
        try:
            websocket = self.active_connections.get(connection_id)
            if not websocket:
                return False
            
            # Check rate limiting
            if not self._check_rate_limit(connection_id):
                logger.warning(
                    "Rate limit exceeded for connection",
                    connection_id=str(connection_id)
                )
                return False
            
            # Serialize message
            message_data = message.dict()
            message_json = json.dumps(message_data, default=str)
            
            # Send message
            await websocket.send_text(message_json)
            
            # Update statistics
            self.connection_stats[connection_id]["messages_sent"] += 1
            self.connection_stats[connection_id]["bytes_sent"] += len(message_json)
            
            # Update last activity
            if connection_id in self.connection_metadata:
                self.connection_metadata[connection_id].last_activity = datetime.utcnow()
            
            return True
            
        except WebSocketDisconnect:
            # Connection closed, cleanup
            await self.disconnect(connection_id)
            return False
        except Exception as e:
            logger.error(
                "Failed to send WebSocket message",
                error=str(e),
                connection_id=str(connection_id)
            )
            
            # Update error statistics
            self.connection_stats[connection_id]["errors"] += 1
            return False
    
    async def send_to_user(self, user_id: UUID, message: WebSocketMessage) -> int:
        """Send message to all connections for a user"""
        connections = self.user_connections.get(user_id, set())
        sent_count = 0
        
        for connection_id in connections.copy():  # Copy to avoid modification during iteration
            success = await self.send_to_connection(connection_id, message)
            if success:
                sent_count += 1
        
        return sent_count
    
    async def send_to_session(self, session_id: UUID, message: WebSocketMessage) -> int:
        """Send message to all connections in a session"""
        connections = self.session_connections.get(session_id, set())
        sent_count = 0
        
        for connection_id in connections.copy():
            success = await self.send_to_connection(connection_id, message)
            if success:
                sent_count += 1
        
        return sent_count
    
    async def send_to_room(self, room_id: str, message: WebSocketMessage) -> int:
        """Send message to all connections in a room"""
        connections = self.room_connections.get(room_id, set())
        sent_count = 0
        
        for connection_id in connections.copy():
            success = await self.send_to_connection(connection_id, message)
            if success:
                sent_count += 1
        
        return sent_count
    
    async def broadcast(self, message: WebSocketMessage, exclude: Optional[Set[UUID]] = None) -> int:
        """Broadcast message to all active connections"""
        exclude = exclude or set()
        sent_count = 0
        
        for connection_id in list(self.active_connections.keys()):
            if connection_id not in exclude:
                success = await self.send_to_connection(connection_id, message)
                if success:
                    sent_count += 1
        
        return sent_count
    
    def join_room(self, connection_id: UUID, room_id: str) -> bool:
        """Add connection to a room"""
        try:
            if connection_id in self.active_connections:
                self.room_connections[room_id].add(connection_id)
                
                # Update connection metadata
                metadata = self.connection_metadata.get(connection_id)
                if metadata:
                    if "rooms" not in metadata.filters:
                        metadata.filters["rooms"] = []
                    if room_id not in metadata.filters["rooms"]:
                        metadata.filters["rooms"].append(room_id)
                
                logger.debug(
                    "Connection joined room",
                    connection_id=str(connection_id),
                    room_id=room_id
                )
                return True
        except Exception as e:
            logger.error(
                "Failed to join room",
                error=str(e),
                connection_id=str(connection_id),
                room_id=room_id
            )
        
        return False
    
    def leave_room(self, connection_id: UUID, room_id: str) -> bool:
        """Remove connection from a room"""
        try:
            self.room_connections[room_id].discard(connection_id)
            
            # Cleanup empty room
            if not self.room_connections[room_id]:
                del self.room_connections[room_id]
            
            # Update connection metadata
            metadata = self.connection_metadata.get(connection_id)
            if metadata and "rooms" in metadata.filters:
                if room_id in metadata.filters["rooms"]:
                    metadata.filters["rooms"].remove(room_id)
            
            logger.debug(
                "Connection left room",
                connection_id=str(connection_id),
                room_id=room_id
            )
            return True
            
        except Exception as e:
            logger.error(
                "Failed to leave room",
                error=str(e),
                connection_id=str(connection_id),
                room_id=room_id
            )
            return False
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        total_connections = len(self.active_connections)
        total_users = len(self.user_connections)
        total_sessions = len(self.session_connections)
        total_rooms = len(self.room_connections)
        
        # Calculate total messages and bytes
        total_messages_sent = sum(stats.get("messages_sent", 0) for stats in self.connection_stats.values())
        total_messages_received = sum(stats.get("messages_received", 0) for stats in self.connection_stats.values())
        total_bytes_sent = sum(stats.get("bytes_sent", 0) for stats in self.connection_stats.values())
        total_bytes_received = sum(stats.get("bytes_received", 0) for stats in self.connection_stats.values())
        total_errors = sum(stats.get("errors", 0) for stats in self.connection_stats.values())
        
        return {
            "total_connections": total_connections,
            "total_users": total_users,
            "total_sessions": total_sessions,
            "total_rooms": total_rooms,
            "total_messages_sent": total_messages_sent,
            "total_messages_received": total_messages_received,
            "total_bytes_sent": total_bytes_sent,
            "total_bytes_received": total_bytes_received,
            "total_errors": total_errors
        }
    
    def _check_rate_limit(self, connection_id: UUID, max_messages_per_minute: int = 60) -> bool:
        """Check if connection is within rate limits"""
        now = time.time()
        timestamps = self.rate_limiting[connection_id]
        
        # Remove old timestamps (older than 1 minute)
        timestamps[:] = [ts for ts in timestamps if now - ts < 60]
        
        # Check limit
        if len(timestamps) >= max_messages_per_minute:
            return False
        
        # Add current timestamp
        timestamps.append(now)
        return True


class RealTimeService:
    """Main real-time service for WebSocket and event management"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.connection_manager = ConnectionManager()
        self.event_handlers: Dict[str, List[Callable]] = defaultdict(list)
        self.is_running = False
        self.subscriber_tasks: List[asyncio.Task] = []
        
        # Redis channels
        self.event_channel = "betty:realtime:events"
        self.progress_channel = "betty:realtime:progress"
        self.notification_channel = "betty:realtime:notifications"
        
        # Heartbeat configuration
        self.heartbeat_interval = 30  # seconds
        self.heartbeat_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start the real-time service"""
        try:
            self.is_running = True
            
            # Start Redis subscribers
            await self._start_redis_subscribers()
            
            # Start heartbeat task
            self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            
            logger.info("RealTime service started successfully")
            
        except Exception as e:
            logger.error("Failed to start RealTime service", error=str(e))
            raise
    
    async def stop(self):
        """Stop the real-time service"""
        try:
            self.is_running = False
            
            # Cancel subscriber tasks
            for task in self.subscriber_tasks:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
            # Cancel heartbeat task
            if self.heartbeat_task:
                self.heartbeat_task.cancel()
                try:
                    await self.heartbeat_task
                except asyncio.CancelledError:
                    pass
            
            # Disconnect all connections
            for connection_id in list(self.connection_manager.active_connections.keys()):
                await self.connection_manager.disconnect(connection_id)
            
            logger.info("RealTime service stopped successfully")
            
        except Exception as e:
            logger.error("Error stopping RealTime service", error=str(e))
    
    async def authenticate_connection(self, websocket: WebSocket, token: str) -> Optional[Dict[str, Any]]:
        """Authenticate WebSocket connection using JWT token"""
        try:
            # Decode JWT token
            # TODO: Implement proper JWT decoding
            payload = {"user_id": "mock_user", "role": "user"}  # Mock for now
            if not payload:
                return None
            
            return {
                "user_id": UUID(payload.get("sub")) if payload.get("sub") else None,
                "permissions": payload.get("permissions", []),
                "session_id": UUID(payload.get("session_id")) if payload.get("session_id") else None
            }
            
        except Exception as e:
            logger.error("WebSocket authentication failed", error=str(e))
            return None
    
    async def publish_event(self, event_type: str, data: Dict[str, Any], **kwargs):
        """Publish event to Redis for distribution"""
        try:
            event_data = {
                "id": str(uuid4()),
                "type": event_type,
                "timestamp": datetime.utcnow().isoformat(),
                "data": data,
                **kwargs
            }
            
            # Publish to Redis
            await self.redis.publish(
                self.event_channel,
                json.dumps(event_data, default=str)
            )
            
            # Also handle locally for current instance
            await self._handle_event(event_data)
            
            logger.debug("Event published", event_type=event_type)
            
        except Exception as e:
            logger.error("Failed to publish event", error=str(e))
    
    async def publish_progress_update(self, operation_id: UUID, progress_data: Dict[str, Any]):
        """Publish progress update"""
        try:
            event_data = {
                "operation_id": str(operation_id),
                "timestamp": datetime.utcnow().isoformat(),
                **progress_data
            }
            
            await self.redis.publish(
                self.progress_channel,
                json.dumps(event_data, default=str)
            )
            
            logger.debug("Progress update published", operation_id=str(operation_id))
            
        except Exception as e:
            logger.error("Failed to publish progress update", error=str(e))
    
    async def publish_notification(self, level: str, title: str, message: str, **kwargs):
        """Publish system notification"""
        try:
            notification_data = {
                "id": str(uuid4()),
                "level": level,
                "title": title,
                "message": message,
                "timestamp": datetime.utcnow().isoformat(),
                **kwargs
            }
            
            await self.redis.publish(
                self.notification_channel,
                json.dumps(notification_data, default=str)
            )
            
            logger.debug("Notification published", level=level, title=title)
            
        except Exception as e:
            logger.error("Failed to publish notification", error=str(e))
    
    async def _start_redis_subscribers(self):
        """Start Redis pub/sub subscribers"""
        try:
            # Create subscriber tasks
            self.subscriber_tasks = [
                asyncio.create_task(self._subscribe_to_events()),
                asyncio.create_task(self._subscribe_to_progress()),
                asyncio.create_task(self._subscribe_to_notifications())
            ]
            
            logger.info("Redis subscribers started")
            
        except Exception as e:
            logger.error("Failed to start Redis subscribers", error=str(e))
            raise
    
    async def _subscribe_to_events(self):
        """Subscribe to general events channel"""
        try:
            pubsub = self.redis.pubsub()
            await pubsub.subscribe(self.event_channel)
            
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        event_data = json.loads(message["data"])
                        await self._handle_event(event_data)
                    except Exception as e:
                        logger.error("Failed to handle event message", error=str(e))
                        
        except Exception as e:
            logger.error("Error in event subscriber", error=str(e))
    
    async def _subscribe_to_progress(self):
        """Subscribe to progress updates channel"""
        try:
            pubsub = self.redis.pubsub()
            await pubsub.subscribe(self.progress_channel)
            
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        progress_data = json.loads(message["data"])
                        await self._handle_progress_update(progress_data)
                    except Exception as e:
                        logger.error("Failed to handle progress message", error=str(e))
                        
        except Exception as e:
            logger.error("Error in progress subscriber", error=str(e))
    
    async def _subscribe_to_notifications(self):
        """Subscribe to notifications channel"""
        try:
            pubsub = self.redis.pubsub()
            await pubsub.subscribe(self.notification_channel)
            
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        notification_data = json.loads(message["data"])
                        await self._handle_notification(notification_data)
                    except Exception as e:
                        logger.error("Failed to handle notification message", error=str(e))
                        
        except Exception as e:
            logger.error("Error in notification subscriber", error=str(e))
    
    async def _handle_event(self, event_data: Dict[str, Any]):
        """Handle incoming event"""
        try:
            event_type = event_data.get("type")
            if not event_type:
                return
            
            # Create WebSocket message
            ws_message = WebSocketMessage(
                type=WebSocketMessageType.EVENT,
                data=event_data
            )
            
            # Broadcast to all connections (could be filtered based on event type)
            await self.connection_manager.broadcast(ws_message)
            
            logger.debug("Event broadcasted", event_type=event_type)
            
        except Exception as e:
            logger.error("Failed to handle event", error=str(e))
    
    async def _handle_progress_update(self, progress_data: Dict[str, Any]):
        """Handle progress update"""
        try:
            operation_id = progress_data.get("operation_id")
            if not operation_id:
                return
            
            # Create progress WebSocket message
            ws_message = WebSocketMessage(
                type=WebSocketMessageType.PROGRESS_UPDATE,
                data=progress_data
            )
            
            # Send to all connections (could be filtered by operation subscription)
            await self.connection_manager.broadcast(ws_message)
            
            logger.debug("Progress update broadcasted", operation_id=operation_id)
            
        except Exception as e:
            logger.error("Failed to handle progress update", error=str(e))
    
    async def _handle_notification(self, notification_data: Dict[str, Any]):
        """Handle system notification"""
        try:
            # Create notification WebSocket message
            ws_message = create_notification_message(
                level=notification_data.get("level", "info"),
                title=notification_data.get("title", ""),
                message=notification_data.get("message", ""),
                action_url=notification_data.get("action_url")
            )
            
            # Broadcast to all connections
            await self.connection_manager.broadcast(ws_message)
            
            logger.debug("Notification broadcasted", level=notification_data.get("level"))
            
        except Exception as e:
            logger.error("Failed to handle notification", error=str(e))
    
    async def _heartbeat_loop(self):
        """Heartbeat loop for connection health monitoring"""
        try:
            while self.is_running:
                await asyncio.sleep(self.heartbeat_interval)
                
                if not self.is_running:
                    break
                
                # Send heartbeat to all connections
                heartbeat_message = WebSocketMessage(
                    type=WebSocketMessageType.PING,
                    data={
                        "timestamp": datetime.utcnow().isoformat(),
                        "server_time": datetime.utcnow().isoformat()
                    }
                )
                
                await self.connection_manager.broadcast(heartbeat_message)
                
                logger.debug("Heartbeat sent to all connections")
                
        except Exception as e:
            logger.error("Error in heartbeat loop", error=str(e))
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Get real-time service statistics"""
        connection_stats = self.connection_manager.get_connection_stats()
        
        return {
            **connection_stats,
            "service_status": "running" if self.is_running else "stopped",
            "subscriber_tasks": len(self.subscriber_tasks),
            "event_handlers": len(self.event_handlers),
            "uptime_seconds": time.time() - getattr(self, "_start_time", time.time())
        }